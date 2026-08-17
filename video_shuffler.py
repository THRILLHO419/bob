#!/usr/bin/env python3
"""Split videos into random-length segments and shuffle them into an mpv EDL playlist.

No re-encoding happens: this only probes durations with ffprobe and writes an
EDL (Edit Decision List) file that mpv plays back seamlessly, cutting between
source files on the fly.
"""
import argparse
import random
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".ts"}


def find_videos(root: Path, extensions: set[str], recursive: bool) -> list[Path]:
    pattern_iter = root.rglob("*") if recursive else root.glob("*")
    return sorted(
        p for p in pattern_iter if p.is_file() and p.suffix.lower() in extensions
    )


def probe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def split_into_segments(
    duration: float, min_len: float, max_len: float, min_tail: float
) -> list[tuple[float, float]]:
    """Partition [0, duration) into consecutive (start, length) chunks."""
    segments: list[tuple[float, float]] = []
    start = 0.0
    while start < duration:
        remaining = duration - start
        if remaining < min_len:
            if segments:
                prev_start, prev_len = segments[-1]
                segments[-1] = (prev_start, prev_len + remaining)
            break
        length = random.uniform(min_len, max_len)
        if remaining - length < min_tail:
            length = remaining
        else:
            length = min(length, remaining)
        segments.append((start, length))
        start += length
    return segments


def edl_field(text: str) -> str:
    """Encode a field using mpv's %len% syntax so commas in paths are safe."""
    encoded = text.encode("utf-8")
    return f"%{len(encoded)}%{text}"


def write_edl(segments: list[tuple[Path, float, float]], output: Path) -> None:
    lines = ["# mpv EDL v0"]
    for path, start, length in segments:
        lines.append(f"{edl_field(str(path.resolve()))},{start:.3f},{length:.3f}")
    output.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Directory containing source videos")
    parser.add_argument("-o", "--output", type=Path, default=Path("shuffle.edl"))
    parser.add_argument("--min-len", type=float, default=15.0, help="Minimum segment length in seconds")
    parser.add_argument("--max-len", type=float, default=45.0, help="Maximum segment length in seconds")
    parser.add_argument(
        "--min-tail", type=float, default=5.0,
        help="Leftover shorter than this gets merged into the previous segment instead of dropped",
    )
    parser.add_argument("--ext", nargs="+", default=None, help="Extra file extensions to include (e.g. .flv)")
    parser.add_argument("--no-recursive", action="store_true", help="Don't scan subdirectories")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible shuffles")
    parser.add_argument("--play", action="store_true", help="Launch mpv on the generated playlist")
    args = parser.parse_args()

    if args.min_len <= 0 or args.max_len < args.min_len:
        parser.error("require 0 < min-len <= max-len")

    if shutil.which("ffprobe") is None:
        parser.error("ffprobe not found on PATH (install ffmpeg)")

    if args.seed is not None:
        random.seed(args.seed)

    extensions = set(DEFAULT_EXTENSIONS)
    if args.ext:
        extensions.update(e if e.startswith(".") else f".{e}" for e in args.ext)

    videos = find_videos(args.input_dir, extensions, recursive=not args.no_recursive)
    if not videos:
        print(f"No video files found under {args.input_dir}", file=sys.stderr)
        return 1

    all_segments: list[tuple[Path, float, float]] = []
    for video in videos:
        duration = probe_duration(video)
        if duration is None:
            print(f"warning: could not probe duration, skipping: {video}", file=sys.stderr)
            continue
        if duration < args.min_len:
            print(f"warning: shorter than --min-len, skipping: {video}", file=sys.stderr)
            continue
        segments = split_into_segments(duration, args.min_len, args.max_len, args.min_tail)
        all_segments.extend((video, start, length) for start, length in segments)

    if not all_segments:
        print("No usable segments were produced.", file=sys.stderr)
        return 1

    random.shuffle(all_segments)
    write_edl(all_segments, args.output)

    total_hours = sum(length for _, _, length in all_segments) / 3600
    print(f"Wrote {len(all_segments)} segments ({total_hours:.1f}h total) to {args.output}")

    if args.play:
        if shutil.which("mpv") is None:
            print("mpv not found on PATH; install it or run: mpv " + str(args.output), file=sys.stderr)
            return 1
        subprocess.run(["mpv", str(args.output)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
