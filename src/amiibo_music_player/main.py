import signal
import subprocess
import time
from pathlib import Path

from amiibo_reader import UnknownTag, close_reader, read_tag

from amiibo_music_player.music_player import play_music, play_sound

process: subprocess.Popen[bytes] | None = None
running = True

ALLOW_RECURSIVE = True
PLAY_NEXT_ON_END = True


def stop_music() -> None:
    global process

    if process is not None:
        if process.poll() is None:
            process.terminate()
            process.wait()

        process = None


def handle_signal(signum: int, frame: object) -> None:
    global running
    print(f"\nSignal {signum}, clean exit...")
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

print("Starting amiibo music player...")
play_sound(Path("hey_listen.mp3"))

try:
    while running:
        tag = read_tag()
        recursive: bool = ALLOW_RECURSIVE
        music_dir: Path

        if tag is None:
            print("No tag detected.")
            continue

        if isinstance(tag, UnknownTag):
            music_dir = Path("musics")
        else:
            music_dir = Path("musics") / tag.series / tag.character
            recursive = False

        print(f"Read tag: id={tag.id}")

        stop_music()
        process = play_music(music_dir, recursive=recursive)

        time.sleep(0.5)

        # Block until the tag is removed
        failed_reads = 0

        while running and failed_reads < 10:
            time.sleep(0.05)

            if PLAY_NEXT_ON_END and process is not None and process.poll() is not None:
                time.sleep(1)
                process = play_music(music_dir, recursive=recursive)

            if read_tag() is None:
                failed_reads += 1
            else:
                failed_reads = 0

        print("tag removed.")
        stop_music()

        time.sleep(0.1)

finally:
    print("Cleaning up...")
    stop_music()
    close_reader()
    print("Reader closed.")
