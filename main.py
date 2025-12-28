import cv2
import numpy as np
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from collections import deque
import time

# Initialize SPI with maximum VALID baudrate
serial = spi(
    port=0,
    device=0,
    gpio_DC=24,
    gpio_RST=25,
    bus_speed_hz=52000000  # Maximum allowed: 52MHz
)

# Initialize device
device = ili9341(serial, rotate=0)

# Pre-calculate target dimensions
TARGET_WIDTH = 320
TARGET_HEIGHT = 240

# Buffer settings - adjustable for your needs
INITIAL_LOAD_SECONDS = 4  # Load 5 seconds initially
BUFFER_SECONDS = 3  # Keep 4 seconds in buffer during playback
FPS = 60  # Your video FPS

INITIAL_FRAMES = INITIAL_LOAD_SECONDS * FPS
BUFFER_FRAMES = BUFFER_SECONDS * FPS
LOAD_AHEAD_FRAMES = FPS  # Load 1 second ahead

# Open video
cap = cv2.VideoCapture("/home/lenovo/projects/1.gif")
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Get actual video FPS if available
video_fps = cap.get(cv2.CAP_PROP_FPS)
if video_fps > 0:
    FPS = int(video_fps)
    INITIAL_FRAMES = INITIAL_LOAD_SECONDS * FPS
    BUFFER_FRAMES = BUFFER_SECONDS * FPS
    LOAD_AHEAD_FRAMES = FPS
    print(f"Detected video FPS: {FPS}")

# Cache functions
cvtColor = cv2.cvtColor
fromarray = Image.fromarray
resize = cv2.resize

# Use deque for efficient pop from front
frame_buffer = deque(maxlen=BUFFER_FRAMES + LOAD_AHEAD_FRAMES)

def load_frame():
    """Load and process a single frame"""
    ret, frame = cap.read()
    if not ret:
        return None

    # Resize if needed
    if frame.shape[1] != TARGET_WIDTH or frame.shape[0] != TARGET_HEIGHT:
        frame = resize(frame, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_LINEAR)

    # Convert color space
    frame = cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to PIL Image
    return fromarray(frame).convert('RGB')

print(f"Loading initial {INITIAL_LOAD_SECONDS} seconds ({INITIAL_FRAMES} frames)...")

# Load initial buffer
for i in range(INITIAL_FRAMES):
    img = load_frame()
    if img is None:
        print(f"Video is shorter than {INITIAL_LOAD_SECONDS} seconds")
        break
    frame_buffer.append(img)
    if (i + 1) % FPS == 0:
        print(f"Loaded {(i + 1) // FPS} seconds...")

print(f"Initial buffer loaded: {len(frame_buffer)} frames")
print("Starting playback with streaming buffer...")

# Display setup
display = device.display
frame_time = 1.0 / FPS

frame_counter = 0
frames_until_reload = FPS  # Reload after 1 second

try:
    while True:
        # Check if we have frames to display
        if len(frame_buffer) == 0:
            # Try to load more frames
            img = load_frame()
            if img is None:
                # Video ended, restart
                print("Video ended, restarting...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                # Reload initial buffer
                frame_buffer.clear()
                for i in range(INITIAL_FRAMES):
                    img = load_frame()
                    if img is None:
                        break
                    frame_buffer.append(img)
                continue
            frame_buffer.append(img)

        # Get next frame from buffer
        img = frame_buffer.popleft()

        start = time.perf_counter()

        # Display frame
        display(img)

        frame_counter += 1
        frames_until_reload -= 1

        # Load new frames every second
        if frames_until_reload <= 0:
            # Load next second of frames
            for _ in range(LOAD_AHEAD_FRAMES):
                new_frame = load_frame()
                if new_frame is not None:
                    frame_buffer.append(new_frame)
                else:
                    break

            frames_until_reload = FPS
            print(f"Buffer: {len(frame_buffer)} frames | Played: {frame_counter} frames ({frame_counter // FPS}s)")

        # Maintain frame rate
        elapsed = time.perf_counter() - start
        sleep_time = frame_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\nPlayback stopped")
finally:
    cap.release()
