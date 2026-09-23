# amiibo-music-player

Raspberry Pi-based music player controlled by amiibo figures or any NTAG215 tags.

The project uses the [`amiibo-reader`](https://github.com/p-beger/amiibo-reader) library to detect and identify amiibo tags with an MFRC522 NFC reader.

## How the Amiibo Music Player Works

When an amiibo (or any NTAG215 tag) is placed on the reader:

1. The tag UID is detected by the MFRC522 reader.
2. `amiibo-reader` attempts to identify the tag as an amiibo.
3. If the amiibo is recognized, its series and character are used to find the corresponding music directory.
4. A music file is randomly selected from the corresponding directory.
5. If the tag is unknown, a random music file is selected from the `musics` directory.
6. The selected music is played with `mpg123`.
7. When the tag remains on the reader and the music ends, another random track is played.
8. When the tag is removed from the reader, the music stops.

## Equipment

* Raspberry Pi
* MFRC522 NFC reader
* Amiibo figures / any NTAG215 tags
* SD card with Raspberry Pi OS Lite
* USB drive for additional music (optional)
* Speakers or headphones
* Internet connection for initial setup

## Requirements

* Python 3.13 or later
* [`amiibo-reader`](https://github.com/p-beger/amiibo-reader)
* `mpg123` for audio playback
* `systemd` and `udev` for automatic USB mounting
* SPI interface enabled on the Raspberry Pi
* FAT32-formatted USB drive (optional)

Install `mpg123` with:

```bash
sudo apt install mpg123
```

## Setup Instructions

### 1. Clone the repository

Clone the repository to your Raspberry Pi:

```bash
git clone https://github.com/p-beger/amiibo-music-player.git

cd amiibo-music-player
```

### 2. Create a virtual environment

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

If creating the virtual environment fails, make sure `python3-full` is installed:

```bash
sudo apt install python3-full
```

### 3. Install the application

Install the project and its Python dependencies:

```bash
python -m pip install .
```

This installs `amiibo-music-player` and its dependency on `amiibo-reader`.

For development, install the development dependencies as well:

```bash
python -m pip install --group dev
```

This installs tools such as Ruff and mypy.

### 4. Connect the MFRC522

Connect the MFRC522 reader to the Raspberry Pi according to the pin configuration used by `amiibo-reader`.

Make sure the SPI interface is enabled on the Raspberry Pi.

### 5. Prepare the music

Music files are not included in this repository.

The music directory structure follows the amiibo series and character names returned by `amiibo-reader`.

For example:

```text
musics/
├── Super Mario/
│   ├── Mario (Wedding Outfit)/
│   │   ├── song1.mp3
│   │   └── song2.mp3
│   └── Peach (Wedding Outfit)/
│       └── song1.mp3
├── Super Smash Bros./
│   ├── Mario/
│   │   └── song1.mp3
│   └── Link/
│       └── song1.mp3
├── The Legend of Zelda: Breath of the Wild/
│   └── Link (Archer)/
│       └── song1.mp3
└── ...
```

For a recognized amiibo, the player looks for music in:

```text
musics/<series>/<character>/
```

If no music is found for a recognized amiibo, the player falls back to the complete `musics` directory.

For an unknown NTAG215 tag, the player directly selects a random track from `musics`.

Music files can also be organized in subdirectories when recursive playback is enabled.

## USB Music

A USB drive can be used to provide additional music without storing all the files on the Raspberry Pi's SD card.

The USB drive must be formatted as FAT32.

### USB directory structure

Create the same directory structure as the local music directory:

```text
USB/
└── musics/
    ├── Super Mario/
    │   └── Mario (Wedding Outfit)/
    │       ├── song1.mp3
    │       └── song2.mp3
    ├── Super Smash Bros./
    │   └── Mario/
    │       └── song1.mp3
    └── ...
```

When a compatible USB drive is connected, it is automatically mounted at:

```text
/mnt/usb
```

The music player searches both:

```text
musics/
```

and:

```text
/mnt/usb/musics/
```

If matching music is found on the USB drive, it is included in the available tracks.

### Automatic USB mounting

Create the mount point:

```bash
sudo mkdir -p /mnt/usb
```

Create the USB mounting script:

```bash
sudo nano /usr/local/bin/mount-usb-music.sh
```

Add:

```bash
#!/bin/bash

DEVICE="/dev/$1"
MOUNT_POINT="/mnt/usb"

mkdir -p "$MOUNT_POINT"

if mountpoint -q "$MOUNT_POINT"; then
    exit 0
fi

mount -t vfat "$DEVICE" "$MOUNT_POINT"
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/mount-usb-music.sh
```

Create the systemd service:

```bash
sudo nano /etc/systemd/system/mount-usb@.service
```

Add:

```ini
[Unit]
Description=Mount USB music device %I
After=dev-%i.device
BindsTo=dev-%i.device

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/mount-usb-music.sh %i
ExecStop=/bin/umount /mnt/usb

[Install]
WantedBy=multi-user.target
```

Create the `udev` rule:

```bash
sudo nano /etc/udev/rules.d/99-usb-music.rules
```

Add:

```ini
ACTION=="add", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", ENV{ID_BUS}=="usb", ENV{ID_FS_TYPE}=="vfat", TAG+="systemd", ENV{SYSTEMD_WANTS}="mount-usb@%k.service"
```

Reload the configuration:

```bash
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

Unplug and reconnect the USB drive.

Verify that it is mounted:

```bash
lsblk -f
```

You should see `/mnt/usb` as the mount point:

```text
sda
└─sda1  vfat  ...  /mnt/usb
```

## Run the application

Make sure the virtual environment is activated:

```bash
source .venv/bin/activate
```

Run the application with:

```bash
python -m amiibo_music_player.main
```

The player will start and wait for an amiibo or NTAG215 tag to be detected.

## Run as a systemd service

The systemd service can use the Python interpreter from the virtual environment.

### 1. Create the service file

Create:

```bash
sudo nano /etc/systemd/system/amiibo-music-player.service
```

Add:

```ini
[Unit]
Description=Amiibo Music Player
After=local-fs.target
Wants=local-fs.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/amiibo-music-player
ExecStart=/path/to/amiibo-music-player/.venv/bin/python -m amiibo_music_player.main
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Replace `your-username` and `/path/to/amiibo-music-player` with the appropriate values for your Raspberry Pi.

### 2. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 3. Enable the service at boot

```bash
sudo systemctl enable amiibo-music-player.service
```

### 4. Start the service

```bash
sudo systemctl start amiibo-music-player.service
```

### 5. Check the service status

```bash
sudo systemctl status amiibo-music-player.service
```

## License

This project is licensed under the MIT License.

This project is independent and is not affiliated with, endorsed by, or sponsored by Nintendo.
