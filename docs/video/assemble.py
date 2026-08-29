"""Assemble frames -> demo.mp4 with per-scene durations matched to the voiceover script.

Timing (target ~4:45 with headroom):
  01_title      8s
  02_problem   30s
  03_baseline  45s
  04_design    40s
  05_trajectory 80s   (the meat: real repair cycles)
  06_results   60s
  07_close     35s
  total: 298s = 4:58
"""
import subprocess
from pathlib import Path

FFMPEG = "C:/Users/Lenovo/Downloads/ffmpeg/bin/ffmpeg.exe"
FRAMES = Path(__file__).parent / "frames"
OUT = Path(__file__).parent / "demo.mp4"

SCENES = [("01_title.png", 8), ("02_problem.png", 30), ("03_baseline.png", 45),
          ("04_design.png", 40), ("05_trajectory.png", 80), ("06_results.png", 60),
          ("07_close.png", 35)]


def main():
    # build a concat list with absolute forward-slash paths (Windows concat demuxer
    # is picky about relative paths + backslashes)
    lst = Path(__file__).parent / "concat.txt"
    with lst.open("w", newline="\n") as f:
        for name, dur in SCENES:
            p = (FRAMES / name).as_posix()
            f.write(f"file '{p}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{(FRAMES / SCENES[-1][0]).as_posix()}'\n")
    r = subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst).replace("\\", "/"),
        "-vf", "fps=24,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-movflags", "+faststart", str(OUT).replace("\\", "/")],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(1)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
