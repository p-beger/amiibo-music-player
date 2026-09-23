import random
import subprocess
from pathlib import Path

MUSICS_DIR = Path("musics")
USB_MOUNT_DIR = Path("/mnt/usb")


def find_music_files(directory: Path, recursive: bool = False) -> list[Path]:
    music_files = []

    # Local musics
    if recursive:
        music_files = list(directory.rglob("*.mp3"))
    else:
        music_files = list(directory.glob("*.mp3"))

    # USB musics
    if USB_MOUNT_DIR.is_mount():
        external_directory = USB_MOUNT_DIR / directory

        if recursive:
            music_files.extend(external_directory.rglob("*.mp3"))
        else:
            music_files.extend(external_directory.glob("*.mp3"))

    # Fallback to all musics
    if not music_files and directory != MUSICS_DIR:
        music_files = find_music_files(MUSICS_DIR, recursive=True)

    return music_files


def play_music(directory: Path, recursive: bool = False) -> subprocess.Popen[bytes] | None:
    try:
        music_files = find_music_files(directory, recursive)

        if not music_files:
            print("No music files found.")
            return None

        music = random.choice(music_files)

        print(f"Selected music: {music.name}")

        return subprocess.Popen(
            ["mpg123", str(music)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except OSError as error:
        print(f"Error playing music: {error}")
        return None


def play_sound(file: Path) -> None:
    try:
        subprocess.run(
            ["mpg123", "-q", str(file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        print(f"Error playing sound: {error}")
