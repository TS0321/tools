#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matrix-style HTML gallery for model comparison:

Row 1: [ org_img | model0/allResult | model0/est_center_map | model0/img_bb ]
Row 2: [   empty | model1/allResult | model1/est_center_map | model1/img_bb ]
Row 3: [   empty | model2/allResult | model2/est_center_map | model2/img_bb ]
...

- Models: arbitrary number (first model appears on the first row).
- Subfolders: default ["allResult","est_center_map","img_bb"], overridable via --folders.
- All images embedded as Base64 data URIs.

Usage:
  python build_gallery_matrix.py --org ./org_img --models ./modelA ./modelB --out ./gallery.html
  python build_gallery_matrix.py --org ./org_img --models ./modelA ./modelB --folders allResult est_center_map img_bb --out ./gallery.html
"""

import argparse
import base64
import html
import mimetypes
from pathlib import Path
from typing import List

# ---- Defaults ----
DEFAULT_SUBFOLDERS: List[str] = ["allResult", "est_center_map", "img_bb"]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".bmp": "image/bmp", ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


def encode_data_uri(path: Path) -> str:
    with open(path, "rb") as f:
        b = f.read()
    b64 = base64.b64encode(b).decode("ascii")
    return f"data:{guess_mime(path)};base64,{b64}"


def list_org_files(org_dir: Path) -> List[str]:
    return sorted(
        [p.name for p in org_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    )


def build_html(org_dir: Path, models: List[Path], subfolders: List[str],
               title: str, max_height: int) -> str:
    org_files = list_org_files(org_dir)
    model_labels = [m.name for m in models]
    cols = 1 + len(subfolders)  # col0 = org_img, col1..N = subfolders

    css = f"""
    :root {{
      --cell-pad: 8px;
      --card-bg: #0c1117;
      --card-bd: #1e2530;
      --missing-bg: #3f1d1d;
      --missing-bd: #7f1d1d;
      --text-dim: #a1adb9;
    }}
    html,body{{background:#0b0c10;color:#e6edf3;margin:0}}
    .page{{max-width:1400px;margin:0 auto;padding:24px}}
    h1{{font-size:22px;margin:0 0 8px}}
    .meta{{font-size:12px;color:#9da7b3;margin-bottom:18px}}
    .block{{background:#0e141b;border:1px solid #1f2630;border-radius:14px;margin:18px 0;overflow:hidden}}
    .block_head{{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#111821;border-bottom:1px solid #1f2630}}
    .fname{{font-weight:700}}
    .chips{{font-size:12px;color:#9da7b3}}
    .grid{{display:grid;gap:10px;padding:12px 12px 18px 12px;grid-template-columns:
           minmax(220px, 1fr) repeat({len(subfolders)}, minmax(220px, 1fr));}}
    .hdr{{font-size:12px;color:{'#9cd1ff'};align-self:end}}
    .cell{{background:var(--card-bg);border:1px solid var(--card-bd);border-radius:10px;padding:var(--cell-pad)}}
    .label{{font-size:12px;color:var(--text-dim);margin:2px 0 6px 0}}
    img{{max-height:{max_height}px;max-width:100%;display:block;border-radius:6px}}
    .missing{{font-size:12px;color:#fca5a5;padding:6px 8px;border:1px solid var(--missing-bd);
              background:var(--missing-bg);border-radius:6px}}
    .center{{display:flex;align-items:center;justify-content:center;min-height:60px}}
    .placeholder{{background:transparent;border:0}}
    """

    parts = [
        "<!DOCTYPE html>",
        "<html lang='ja'><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<style>", css, "</style>",
        "</head><body><div class='page'>",
        f"<h1>{html.escape(title)}</h1>",
        "<div class='meta'>",
        f"Org: <code>{html.escape(str(org_dir))}</code> | ",
        "Models: " + ", ".join(f"<code>{html.escape(str(m))}</code>" for m in models) + " | ",
        "Folders: " + ", ".join(f"<code>{html.escape(s)}</code>" for s in subfolders),
        "</div>",
    ]

    # column headers: col0 empty title “Original”, cols1.. show subfolder names
    for fname in org_files:
        parts.append("<section class='block'>")
        parts.append("<div class='block_head'>")
        parts.append(f"<div class='fname'>{html.escape(fname)}</div>")
        parts.append("<div class='chips'>org + per-folder model comparison</div>")
        parts.append("</div>")

        parts.append("<div class='grid'>")

        # Header row
        parts.append("<div class='hdr'></div>")  # (col 0) blank header
        for sub in subfolders:
            parts.append(f"<div class='hdr'>{html.escape(sub)}</div>")

        # Row 1: org + first model
        # col 0: org image
        org_path = org_dir / fname
        if org_path.exists():
            parts.append("<div class='cell'>")
            parts.append("<div class='label'>org_img</div>")
            parts.append(f"<img src='{encode_data_uri(org_path)}' alt='org:{html.escape(fname)}'>")
            parts.append("</div>")
        else:
            parts.append("<div class='cell center'><div class='missing'>Original MISSING</div></div>")

        if models:
            m0, label0 = models[0], model_labels[0]
            for sub in subfolders:
                p = m0 / sub / fname
                parts.append("<div class='cell'>")
                parts.append(f"<div class='label'>{html.escape(label0)} / {html.escape(sub)}</div>")
                if p.exists():
                    parts.append(f"<img src='{encode_data_uri(p)}' alt='{html.escape(label0)}/{html.escape(sub)}:{html.escape(fname)}'>")
                else:
                    parts.append("<div class='missing'>MISSING</div>")
                parts.append("</div>")
        else:
            # If no models, still fill placeholders for subfolders
            for _ in subfolders:
                parts.append("<div class='cell center'><div class='missing'>No model</div></div>")

        # Rows 2..: other models (col 0 remains empty placeholder)
        for m, label in zip(models[1:], model_labels[1:]):
            parts.append("<div class='cell placeholder'></div>")  # empty under org
            for sub in subfolders:
                p = m / sub / fname
                parts.append("<div class='cell'>")
                parts.append(f"<div class='label'>{html.escape(label)} / {html.escape(sub)}</div>")
                if p.exists():
                    parts.append(f"<img src='{encode_data_uri(p)}' alt='{html.escape(label)}/{html.escape(sub)}:{html.escape(fname)}'>")
                else:
                    parts.append("<div class='missing'>MISSING</div>")
                parts.append("</div>")

        parts.append("</div>")  # grid
        parts.append("</section>")  # block

    parts.append("</div></body></html>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Matrix-style HTML gallery for comparing models by subfolder.")
    ap.add_argument("--org", required=True, type=Path, help="Path to org_img directory")
    ap.add_argument("--models", required=True, nargs="+", type=Path, help="Model directories (order matters)")
    ap.add_argument("--folders", nargs="+", default=None, help="Subfolders to compare (default: allResult est_center_map img_bb)")
    ap.add_argument("--out", required=True, type=Path, help="Output HTML file")
    ap.add_argument("--title", default="Model Comparison Matrix", help="HTML title")
    ap.add_argument("--max-height", type=int, default=420, help="Max image height (px)")
    args = ap.parse_args()

    if not args.org.is_dir():
        raise SystemExit(f"[ERROR] org dir not found or not a directory: {args.org}")
    for m in args.models:
        if not m.is_dir():
            raise SystemExit(f"[ERROR] model dir not found or not a directory: {m}")

    subfolders = args.folders if args.folders else list(DEFAULT_SUBFOLDERS)
    html_str = build_html(args.org.resolve(), [m.resolve() for m in args.models], subfolders, args.title, args.max_height)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_str, encoding="utf-8")
    print(f"[OK] Wrote: {args.out}")


if __name__ == "__main__":
    main()
