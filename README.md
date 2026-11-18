# The Year Without a Summer

An eight-act, narrated video edit assembled from the supplied stick-figure illustrations and voiceover.

## Deliverables

- `The_Year_Without_a_Summer.mp4` — 1280×720, 24 fps, approximately 17:02.5, with AAC narration and chapter metadata.
- `edit_manifest.json` — the 397-scene edit map, asset/archive references, frame timings, act chapters, and mid-roll markers.
- `build_video.py` — script to recreate the edit from the image ZIPs and supplied MP3 in this directory.

The cut contains 315 unique illustrations, including 82 planned reprises. The three mid-roll points are **04:56**, **09:24**, and **13:34**; each is also an act/chapter boundary in the video.

## Rebuild

Requires Python 3 and FFmpeg with the `libx264`, `aac`, `xfade`, and `drawtext` support used by the renderer. The script looks for FFmpeg on `PATH`, then for the Python package `imageio-ffmpeg`.

```bash
python3 -m pip install imageio-ffmpeg  # if FFmpeg is not already available
python3 build_video.py --plan-only    # regenerate the manifest and inspect the edit plan
python3 build_video.py                # render the MP4 and manifest
```

The default render uses CRF 31 and the `medium` preset. Use `--crf` and `--preset` to change the encode settings. `--output` and `--work-dir` can select alternate output and temporary-render locations. The source archives and narration are expected to retain their supplied filenames in the project root.
