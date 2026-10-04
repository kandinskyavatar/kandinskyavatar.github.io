#!/usr/bin/env python3
"""Scan examples/ and write videos.json used by the site.

Also extracts a first-frame poster per clip into previews/ so the grid shows
the video content before playback.

To change the page: edit SECTIONS below (titles, blurbs, folder order, or
which folders appear) or BEFORE (clip order), add/remove .mp4 files in
examples/<folder>/, then rerun:

    python build_manifest.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
PREVIEWS = ROOT / "previews"

# (anchor id, folder name, section title, blurb)
SECTIONS = [
    (
        "alignment",
        "alingment",
        "Accurate, natural Lips–Audio Alignment",
        "Speech features from the Qwen2.5-Omni audio tower are injected directly into "
        "the DiT, and an area-adaptive face loss keeps the lip-sync signal strong even "
        "when the visible face is small.",
    ),
    (
        "multilanguage",
        "multilanguage",
        "Multi-language",
        "Trained on a multilingual single-speaker corpus with English and Russian "
        "captions, the model keeps lip motion consistent with the driving speech across "
        "languages.",
    ),
    (
        "sng",
        "sng",
        "The best for Russian and other widely used languages across Eastern Europe, "
        "the Caucasus, and Central Asia",
        "25.8% of the training corpus is Russian speech, so Russian-language control "
        "works without a separate fine-tuning stage — together with the other "
        "languages widely spoken across Eastern Europe, the Caucasus, and Central Asia.",
    ),
    (
        "generalization",
        "generalizations",
        "Generalization to cartoon characters and animals",
        "Kandinsky Avatar starts from the Kandinsky 5.0 Video foundation models, and the "
        "same conditioning drives speakers that are not photographed humans.",
    ),
    (
        "long",
        "long",
        "Long-Duration Video Generation",
        "Long videos are composed from 5-second chunks at 25 fps with an explicit "
        "three-scale FramePack visual memory and mixed reference-memory placement, "
        "which limits pose copying and autoregressive looping.",
    ),
]

# Clips moved right before another clip, overriding the order by file name:
# folder -> {clip stem: stem of the clip it goes before}, applied in order.
BEFORE = {
    "alingment": {
        "109__TEST_10s_s2v": "411",
        # swap 402 and 405
        "405": "402",
        "402": "407",
    },
}


def probe(path: Path):
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "csv=p=0", str(path),
        ],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h, dur = out.split(",")[:3]
    return int(w), int(h), float(dur)


def make_poster(video: Path, folder: str) -> str:
    out = PREVIEWS / folder / (video.stem + ".jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.stat().st_mtime < video.stat().st_mtime:
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(video),
                "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", str(out),
            ],
            check=True,
        )
    return f"previews/{folder}/{out.name}"


def natural_key(p: Path):
    return (0, int(p.stem), "") if p.stem.isdigit() else (1, 0, p.stem)


def ordered(clips, folder: str):
    clips = sorted(clips, key=natural_key)
    for stem, anchor in BEFORE.get(folder, {}).items():
        by_stem = {c.stem: c for c in clips}
        if stem in by_stem and anchor in by_stem:
            clips.remove(by_stem[stem])
            clips.insert(clips.index(by_stem[anchor]), by_stem[stem])
    return clips


def prune_posters(folder: str, keep: set):
    """Drop posters left over from clips that are no longer in examples/."""
    d = PREVIEWS / folder
    if not d.is_dir():
        return
    for jpg in d.glob("*.jpg"):
        if jpg.stem not in keep:
            jpg.unlink()
            print(f"  pruned {jpg.relative_to(ROOT)}")


def main():
    sections = []
    for anchor, folder, title, blurb in SECTIONS:
        d = EXAMPLES / folder
        if not d.is_dir():
            print(f"skip: {d} not found")
            continue
        clips = ordered(d.glob("*.mp4"), folder)
        prune_posters(folder, {f.stem for f in clips})
        videos = []
        for f in clips:
            w, h, dur = probe(f)
            videos.append({
                "src": f"examples/{folder}/{f.name}",
                "poster": make_poster(f, folder),
                "width": w,
                "height": h,
                "duration": round(dur, 1),
            })
        print(f"{folder}: {len(videos)} videos")
        sections.append({
            "id": anchor,
            "title": title,
            "blurb": blurb,
            "videos": videos,
        })

    (ROOT / "videos.json").write_text(
        json.dumps({"sections": sections}, ensure_ascii=False, indent=2) + "\n"
    )
    print("wrote videos.json")


if __name__ == "__main__":
    main()
