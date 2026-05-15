"""
main.py - Entry point for the amortization estimation program.

Usage:
    # Run all categories from config.yaml (production):
    python main.py

    # Test a single asset (debug mode):
    python main.py --asset-id 34473

    # Override config file path:
    python main.py --config my_config.yaml
"""

import argparse
import sys
import os
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generator import generate


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    # If path is relative, resolve it against the script directory
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    if not os.path.exists(path):
        print(f"[ERROR] Config file not found: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Estimation des amortissements immobilisations (Odoo 8)"
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to config.yaml (default: config.yaml next to main.py)"
    )
    parser.add_argument(
        "--asset-id", type=int, default=None,
        help="Filter to a single asset ID (for testing/debugging)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    categories     = cfg.get("categories", [])
    raw_output_dir = cfg.get("output", {}).get("directory", "output")
    output_dir     = raw_output_dir if os.path.isabs(raw_output_dir) \
                     else os.path.join(SCRIPT_DIR, raw_output_dir)
    output_format  = cfg.get("output", {}).get("format", "excel")

    if not categories:
        print("[ERROR] No categories defined in config.yaml")
        sys.exit(1)

    fp = generate(
        categories=categories,
        output_format=output_format,
        output_dir=output_dir,
        asset_id=args.asset_id,
        log_fn=print,
    )

    if fp:
        print(f"\n[DONE] Fichier : {fp}")
    else:
        print("\n[ERROR] Generation echouee.")
        sys.exit(1)


if __name__ == "__main__":
    main()
