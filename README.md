# Video Segment Shuffler

Splits your videos into random-length chunks and shuffles them into a
playlist that plays back-to-back with no gaps and no re-encoding.

## One-time setup

Install two things:

- **ffmpeg** (for `ffprobe`) — `brew install ffmpeg` (Mac) / `sudo apt install ffmpeg` (Linux) / `winget install ffmpeg` (Windows)
- **mpv** — `brew install mpv` (Mac) / `sudo apt install mpv` (Linux) / `winget install mpv` (Windows)

## Running it

Mac/Linux:
```
./run.sh /path/to/your/videos --play
```

Windows:
```
run.bat C:\path\to\your\videos --play
```

This always grabs the latest version of the script before running, so you
don't need to manage updates yourself.

## Useful options

- `--target-duration 2h` — cap the total playlist length (also accepts `90m`, `5400s`)
- `--min-len 15 --max-len 45` — random segment length range in seconds (default)
- `--seg-len 20` — use one fixed segment length instead of random
- `--seed 42` — reproducible shuffle (same seed = same playlist)
- `--no-recursive` — only scan the top-level folder, skip subfolders
- `-o myfile.edl` — change the output playlist filename
