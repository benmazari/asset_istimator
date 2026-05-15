"""
web_app.py — Flask web interface for the amortissement estimator.

Run with:
    python web_app.py
Then open http://localhost:5000 in your browser.
"""

import os
import sys
import uuid
import queue
import threading
import yaml
from datetime import datetime, date
from flask import (
    Flask, render_template, request, jsonify,
    Response, send_file, stream_with_context,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generator import generate

app = Flask(__name__, template_folder=os.path.join(SCRIPT_DIR, "templates"))

# ── In-memory job store ───────────────────────────────────────────────────────
# job_id → { "status": "running"|"done"|"error", "log_q": Queue, "file": str|None }
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _load_config():
    path = os.path.join(SCRIPT_DIR, "config.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    cfg = _load_config()
    categories = cfg.get("categories", [])
    return render_template("index.html", categories=categories)


@app.route("/api/categories")
def api_categories():
    cfg = _load_config()
    return jsonify(cfg.get("categories", []))


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}

    # Validate + parse inputs
    selected_labels = set(data.get("categories", []))
    output_format   = data.get("format", "excel")          # excel|csv|both
    granularity     = data.get("granularity", "monthly")   # monthly|daily|both
    asset_id_raw    = data.get("asset_id", "").strip()
    from_date_raw   = data.get("from_date", "").strip()

    asset_id = int(asset_id_raw) if asset_id_raw.isdigit() else None

    from_date = None
    if from_date_raw:
        try:
            from_date = datetime.strptime(from_date_raw, "%d/%m/%Y").date()
        except ValueError:
            return jsonify({"error": f"Date invalide '{from_date_raw}' — format JJ/MM/AAAA requis."}), 400

    cfg = _load_config()
    all_cats = cfg.get("categories", [])
    categories = [c for c in all_cats if c.get("label") in selected_labels]

    if not categories:
        return jsonify({"error": "Aucune catégorie sélectionnée."}), 400

    # Output dir
    raw_dir = cfg.get("output", {}).get("directory", "output")
    out_dir = raw_dir if os.path.isabs(raw_dir) else os.path.join(SCRIPT_DIR, raw_dir)

    # Create job
    job_id = str(uuid.uuid4())
    log_q: queue.Queue = queue.Queue()

    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "log_q": log_q, "file": None}

    def run():
        def log_fn(msg):
            log_q.put(msg)

        fp = generate(
            categories=categories,
            output_format=output_format,
            output_dir=out_dir,
            asset_id=asset_id,
            granularity=granularity,
            from_date=from_date,
            log_fn=log_fn,
        )

        with _jobs_lock:
            _jobs[job_id]["file"]   = fp
            _jobs[job_id]["status"] = "done" if fp else "error"

        log_q.put(None)  # sentinel — stream ends

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def api_stream(job_id):
    """Server-Sent Events: stream log lines for a running job."""

    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404

    log_q = job["log_q"]

    def generate_events():
        while True:
            try:
                msg = log_q.get(timeout=30)
            except queue.Empty:
                yield "event: keepalive\ndata: \n\n"
                continue

            if msg is None:          # sentinel — job finished
                with _jobs_lock:
                    j = _jobs.get(job_id, {})
                status = j.get("status", "error")
                fp     = j.get("file")
                yield f"event: done\ndata: {status}|{fp or ''}\n\n"
                break

            # Escape newlines inside a single SSE data line
            safe = msg.replace("\n", " ")
            yield f"data: {safe}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404
    return jsonify({"status": job["status"], "file": job.get("file")})


@app.route("/api/download/<job_id>")
def api_download(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job or not job.get("file"):
        return jsonify({"error": "Fichier introuvable."}), 404
    fp = job["file"]
    if not os.path.exists(fp):
        return jsonify({"error": "Fichier introuvable sur le disque."}), 404
    return send_file(fp, as_attachment=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Amortissement Web — http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
