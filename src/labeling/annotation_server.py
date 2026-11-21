# -*- coding: utf-8 -*-
"""Local Flask server for the pixel-mask annotation tool (Option B).

Serves the browser UI, chip previews, and accepts mask PNG uploads.
All data stays on disk under C:\\New folder\\annotation — nothing is uploaded.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import project_config as cfg  # noqa: E402

ROOT = cfg.WORKSPACE_ROOT / "annotation"
IMAGES = ROOT / "images"
MASKS = ROOT / "masks"
UI = REPO / "src" / "labeling" / "annotation_ui.html"

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    return send_from_directory(str(UI.parent), UI.name)


@app.route("/images/<name>")
def images(name):
    return send_from_directory(str(IMAGES), name)


@app.route("/api/chips")
def chips():
    entries = json.loads((ROOT / "chips.json").read_text(encoding="utf-8"))
    for e in entries:
        e["mask_exists"] = (MASKS / f"{e['chip_id']}_mask.png").exists()
    return jsonify(entries)


@app.route("/api/mask/<chip_id>")
def get_mask(chip_id):
    p = MASKS / f"{chip_id}_mask.png"
    if not p.exists():
        return jsonify({"mask": None})
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return jsonify({"mask": "data:image/png;base64," + b64})


@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json(force=True)
    chip_id = data.get("chip_id", "")
    png = data.get("png", "")
    if not chip_id or not png.startswith("data:image/png;base64,"):
        return jsonify({"ok": False, "error": "bad payload"}), 400
    # guard against path traversal
    if any(c in chip_id for c in ("/", "\\", "..")):
        return jsonify({"ok": False, "error": "bad chip_id"}), 400
    raw = base64.b64decode(png.split(",", 1)[1])
    (MASKS / f"{chip_id}_mask.png").write_bytes(raw)
    return jsonify({"ok": True, "chip_id": chip_id, "bytes": len(raw)})


@app.route("/api/progress")
def progress():
    entries = json.loads((ROOT / "chips.json").read_text(encoding="utf-8"))
    done = sum(1 for e in entries
               if (MASKS / f"{e['chip_id']}_mask.png").exists())
    return jsonify({"done": done, "total": len(entries)})


if __name__ == "__main__":
    print("Annotation tool: http://127.0.0.1:8765")
    print("Output folder:", MASKS)
    app.run(host="127.0.0.1", port=8765, debug=False)
