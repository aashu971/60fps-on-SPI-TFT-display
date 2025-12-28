# 60fps-on-SPI-TFT-display
Near 60 FPS video playback on a 2.4" SPI TFT (ILI9341) using a Raspberry Pi Zero 2 W with a heatsink. SPI at 52 MHz, optional spidev.bufsiz tweaks, overclocking, and Python with OpenCV, PIL, and luma.lcd with buffered 320×240 frames enable smooth playback. Full code is in this repo.
I wanted to share how I managed to get close to 60 FPS video playback on a 2.4-inch SPI TFT touchscreen (ILI9341) using a Raspberry Pi Zero 2 W. SPI displays are usually pretty slow, especially on smaller Pis, so I figured this might be useful to document.
This is just a technical write-up of what worked on my setup.
Hardware
•	Raspberry Pi Zero 2 W (with a heatsink)
•	2.4" SPI TFT touchscreen (ILI9341)
•	Short, decent-quality SPI wiring
OS
•	Raspberry Pi OS (64-bit)
System Setup
SPI Buffer Size
I experimented with increasing the SPI buffer size in the kernel command line:
````spidev.bufsiz=1600000````
On my setup, this didn’t make a huge difference once the value was “large enough.” I also tested values around 200000, and FPS was about the same. Going higher mostly just added some headroom and stability rather than raw speed.
That said, this doesn’t behave the same everywhere. On other kernels or SPI workloads, increasing spidev.bufsiz can matter more. It just wasn’t a major factor for me compared to other changes.
Clock / Voltage Settings
In /boot/firmware/config.txt I increased clocks to avoid non-CPU bottlenecks:
````arm_freq=1300
over_voltage=6

core_freq=550
gpu_freq=550
v3d_freq=550

sdram_freq=550
over_voltage_sdram=2````
SPI was enabled via raspi-config. These settings were stable on my Zero 2 W with a heatsink, but obviously overclocking depends on cooling and silicon quality.
Display and SPI
•	ILI9341 driven directly over SPI
•	SPI clock set to 52 MHz
•	320×240 resolution
•	16-bit RGB color
•	No HDMI mirroring or desktop involved
SPI clock speed made a much bigger difference than most other tweaks.
Software Approach
The playback code is written in Python and uses:
•	OpenCV for decoding and resizing
•	PIL for image conversion
•	luma.lcd for SPI output
Things that helped performance the most:
•	Frames are resized once to 320×240
•	Frames are buffered so decoding doesn’t block display output
•	No per-pixel Python loops
•	No alpha blending
•	Simple frame-timed loop targeting ~60 FPS
Instead of decoding and drawing at the same time, the code stays slightly ahead by buffering frames and focuses on pushing data to the display during playback
Results
On my Raspberry Pi Zero 2 W, this gets very close to 60 FPS and looks smooth in motion. CPU usage is reasonable for Python + SPI, and performance is much better than typical SPI TFT examples.

Notes
•	Results will vary depending on wiring and display quality
•	SPI bandwidth is still the main limitation
•	Overclocking may not be safe on every board
