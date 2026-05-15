"""
app_desktop.py - Native desktop GUI for the amortization estimator.

Run with:
    python app_desktop.py
"""

import os
import sys
import threading
from datetime import datetime, date as date_type

import customtkinter as ctk
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generator import generate

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG     = "#0f1117"
SURFACE     = "#1a1d27"
SURFACE2    = "#22263a"
BORDER      = "#2e3350"
ACCENT      = "#4f7df3"
SUCCESS     = "#22c55e"
ERROR       = "#ef4444"
TEXT        = "#e2e8f0"
MUTED       = "#8892aa"


def load_config():
    path = os.path.join(SCRIPT_DIR, "config.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Main App ──────────────────────────────────────────────────────────────────

class AmortissementApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Amortissement — Generateur")
        self.geometry("950x680")
        self.minsize(800, 580)
        self.configure(fg_color=DARK_BG)

        self._job_thread = None
        self._output_file = None
        self._cat_vars = []      # list of (BooleanVar, category_dict)

        self._build_ui()
        self._load_config()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header bar ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚙  Amortissement",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT
        ).pack(side="left", padx=24, pady=14)

        ctk.CTkLabel(
            header, text="Generateur d'estimations d'amortissement",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        ).pack(side="left", pady=14)

        # ── Body: left + right ────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        body.columnconfigure(0, weight=0, minsize=300)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # LEFT
        left = ctk.CTkFrame(body, fg_color=DARK_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._build_left(left)

        # RIGHT
        right = ctk.CTkFrame(body, fg_color=DARK_BG)
        right.grid(row=0, column=1, sticky="nsew")
        self._build_right(right)

    def _build_left(self, parent):
        parent.columnconfigure(0, weight=1)

        # ── Categories card ───────────────────────────────────────────────────
        cat_card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12)
        cat_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        cat_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cat_card, text="CATEGORIES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self._cat_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
        self._cat_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 14))
        self._cat_frame.columnconfigure(0, weight=1)

        # ── Options card ──────────────────────────────────────────────────────
        opt_card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12)
        opt_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        opt_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            opt_card, text="OPTIONS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        # Format selector
        ctk.CTkLabel(
            opt_card, text="Format de sortie",
            font=ctk.CTkFont(size=12), text_color=MUTED
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 4))

        self._fmt_var = ctk.StringVar(value="excel")
        self._fmt_combo = ctk.CTkOptionMenu(
            opt_card,
            values=["Excel (.xlsx)", "CSV", "Excel + CSV"],
            variable=self._fmt_var,
            fg_color=SURFACE2,
            button_color=ACCENT,
            button_hover_color="#3a6bda",
            dropdown_fg_color=SURFACE2,
            text_color=TEXT,
            font=ctk.CTkFont(size=13),
            width=260,
        )
        self._fmt_combo.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="w")

        # Granularity selector
        ctk.CTkLabel(
            opt_card, text="Granularité du calcul",
            font=ctk.CTkFont(size=12), text_color=MUTED
        ).grid(row=3, column=0, sticky="w", padx=18, pady=(0, 4))

        self._gran_var = ctk.StringVar(value="monthly")
        self._gran_combo = ctk.CTkOptionMenu(
            opt_card,
            values=["Mensuelle", "Journalière", "Mensuelle + Journalière"],
            fg_color=SURFACE2,
            button_color=ACCENT,
            button_hover_color="#3a6bda",
            dropdown_fg_color=SURFACE2,
            text_color=TEXT,
            font=ctk.CTkFont(size=13),
            width=260,
            command=self._on_gran_change,
        )
        self._gran_combo.set("Mensuelle")
        self._gran_combo.grid(row=4, column=0, padx=18, pady=(0, 10), sticky="w")

        # Asset ID filter
        ctk.CTkLabel(
            opt_card, text="ID immobilisation (optionnel — vide = tout)",
            font=ctk.CTkFont(size=12), text_color=MUTED
        ).grid(row=5, column=0, sticky="w", padx=18, pady=(4, 4))

        self._asset_entry = ctk.CTkEntry(
            opt_card,
            placeholder_text="ex: 34473",
            fg_color=SURFACE2,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color=MUTED,
            font=ctk.CTkFont(size=13),
            width=260,
        )
        self._asset_entry.grid(row=6, column=0, padx=18, pady=(0, 14), sticky="w")

        # From-date filter
        ctk.CTkLabel(
            opt_card,
            text="A partir du (JJ/MM/AAAA — vide = depuis le début)",
            font=ctk.CTkFont(size=12), text_color=MUTED,
        ).grid(row=7, column=0, sticky="w", padx=18, pady=(4, 4))

        self._from_date_entry = ctk.CTkEntry(
            opt_card,
            placeholder_text="ex: 01/01/2024",
            fg_color=SURFACE2,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color=MUTED,
            font=ctk.CTkFont(size=13),
            width=260,
        )
        self._from_date_entry.grid(row=8, column=0, padx=18, pady=(0, 14), sticky="w")

        # ── Buttons ───────────────────────────────────────────────────────────
        self._btn_generate = ctk.CTkButton(
            parent,
            text="▶  Generer le fichier",
            command=self._start_generation,
            fg_color=ACCENT,
            hover_color="#3a6bda",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=10,
        )
        self._btn_generate.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self._btn_open = ctk.CTkButton(
            parent,
            text="⬇  Ouvrir le fichier",
            command=self._open_file,
            fg_color="transparent",
            border_color=SUCCESS,
            border_width=2,
            text_color=SUCCESS,
            hover_color="#1a3a28",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=10,
            state="disabled",
        )
        self._btn_open.grid(row=3, column=0, sticky="ew")

    def _build_right(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # ── Stats row ─────────────────────────────────────────────────────────
        stats = ctk.CTkFrame(parent, fg_color=DARK_BG)
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        stats.columnconfigure((0, 1, 2), weight=1)

        self._stat_cats  = self._stat_card(stats, "CATEGORIES", "0",  0)
        self._stat_rows  = self._stat_card(stats, "LIGNES TOTALES", "—", 1)
        self._stat_stat  = self._stat_card(stats, "STATUT", "En attente", 2, color=MUTED)

        # ── Log terminal card ─────────────────────────────────────────────────
        log_card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12)
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        log_header.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            log_header, text="JOURNAL D'EXECUTION",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTED
        ).grid(row=0, column=0, sticky="w")

        self._status_badge = ctk.CTkLabel(
            log_header, text="  Pret  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=MUTED,
            fg_color=SURFACE2,
            corner_radius=10,
        )
        self._status_badge.grid(row=0, column=1, sticky="e")

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            log_card, mode="indeterminate",
            fg_color=SURFACE2, progress_color=ACCENT, height=4,
        )
        self._progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        self._progress.grid_remove()

        # Log text box
        self._log_text = ctk.CTkTextbox(
            log_card,
            fg_color="#0a0c12",
            text_color="#a8b4cc",
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            wrap="word",
            state="disabled",
        )
        self._log_text.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # Tag colors for log lines
        self._log_text._textbox.tag_configure("ok",   foreground="#4ade80")
        self._log_text._textbox.tag_configure("err",  foreground="#f87171")
        self._log_text._textbox.tag_configure("warn", foreground="#fbbf24")
        self._log_text._textbox.tag_configure("info", foreground="#a8b4cc")

    def _stat_card(self, parent, label, value, col, color=None):
        card = ctk.CTkFrame(parent, fg_color=SURFACE2, corner_radius=10)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont(size=10, weight="bold"), text_color=MUTED
        ).pack(anchor="w", padx=14, pady=(12, 2))
        val_lbl = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color or ACCENT
        )
        val_lbl.pack(anchor="w", padx=14, pady=(0, 12))
        return val_lbl

    # ── Config loading ────────────────────────────────────────────────────────

    def _load_config(self):
        try:
            cfg = load_config()
            cats = cfg.get("categories", [])
            fmt  = cfg.get("output", {}).get("format", "excel")
        except Exception as e:
            self._log(f"Erreur config: {e}", "err")
            return

        # Set format
        fmt_map = {"excel": "Excel (.xlsx)", "csv": "CSV", "both": "Excel + CSV"}
        self._fmt_combo.set(fmt_map.get(fmt, "Excel (.xlsx)"))

        # Build category checkboxes
        self._cat_vars.clear()
        for widget in self._cat_frame.winfo_children():
            widget.destroy()

        for i, cat in enumerate(cats):
            label = cat.get("label", f"Catégorie {i+1}")
            
            # Support both new 'ids' format and old 'pattern' format
            if "ids" not in cat and "pattern" in cat:
                label = cat["pattern"].replace("%", "").strip()

            var = ctk.BooleanVar(value=True)
            row = ctk.CTkFrame(self._cat_frame, fg_color=SURFACE2, corner_radius=8)
            row.grid(row=i, column=0, sticky="ew", pady=4)
            row.columnconfigure(1, weight=1)

            cb = ctk.CTkCheckBox(
                row, text="", variable=var,
                fg_color=ACCENT, hover_color="#3a6bda",
                border_color=BORDER, checkmark_color="white",
                width=20,
                command=self._update_cat_count,
            )
            cb.grid(row=0, column=0, padx=(10, 6), pady=10)

            ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
            ).grid(row=0, column=1, sticky="w")

            ctk.CTkLabel(
                row, text=f"{cat['years']} ans",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color="#1a2a5a", corner_radius=8,
            ).grid(row=0, column=2, padx=(6, 10), pady=8)

            self._cat_vars.append((var, cat))

        self._update_cat_count()

    def _update_cat_count(self):
        count = sum(1 for v, _ in self._cat_vars if v.get())
        self._stat_cats.configure(text=str(count))

    def _on_gran_change(self, value: str):
        """Warn the user when daily is selected (can be slow for large datasets)."""
        if "Journalière" in value:
            self._log(
                "Attention : la granularité journalière génère ~30x plus de lignes "
                "— peut être lente sur de grands ensembles.",
                "warn",
            )

    # ── Generation ────────────────────────────────────────────────────────────

    def _start_generation(self):
        selected = [(v, c) for v, c in self._cat_vars if v.get()]
        if not selected:
            self._log("Selectionnez au moins une categorie.", "warn")
            return

        asset_id_str = self._asset_entry.get().strip()
        asset_id = int(asset_id_str) if asset_id_str.isdigit() else None

        fmt_map = {"Excel (.xlsx)": "excel", "CSV": "csv", "Excel + CSV": "both"}
        output_format = fmt_map.get(self._fmt_combo.get(), "excel")

        gran_map = {
            "Mensuelle":               "monthly",
            "Journalière":             "daily",
            "Mensuelle + Journalière": "both",
        }
        granularity = gran_map.get(self._gran_combo.get(), "monthly")

        # Parse from_date
        from_date = None
        from_date_str = self._from_date_entry.get().strip()
        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str, "%d/%m/%Y").date()
            except ValueError:
                self._log(
                    f"Date invalide '{from_date_str}' — utilisez le format JJ/MM/AAAA.",
                    "err",
                )
                return

        # Reset UI
        self._clear_log()
        self._output_file = None
        self._btn_generate.configure(state="disabled")
        self._btn_open.configure(state="disabled", text="⬇  Ouvrir le fichier")
        self._set_status("running")
        self._stat_rows.configure(text="...")

        cats = [c for _, c in selected]
        self._job_thread = threading.Thread(
            target=self._run_generation,
            args=(cats, output_format, asset_id, granularity, from_date),
            daemon=True
        )
        self._job_thread.start()

    def _run_generation(self, categories, output_format, asset_id, granularity="monthly", from_date=None):
        import yaml
        cfg_path = os.path.join(SCRIPT_DIR, "config.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        raw = cfg.get("output", {}).get("directory", "output")
        out_dir = raw if os.path.isabs(raw) else os.path.join(SCRIPT_DIR, raw)

        def log(msg, kind="info"):
            self._log(msg, kind)

        fp = generate(
            categories=categories,
            output_format=output_format,
            output_dir=out_dir,
            asset_id=asset_id,
            granularity=granularity,
            from_date=from_date,
            log_fn=lambda msg: log(
                msg,
                "err"  if "[ERREUR]" in msg
                else "ok"   if any(w in msg for w in ("succes", "cree", "trouvee"))
                else "warn" if "ignore" in msg
                else "info"
            ),
        )

        self._output_file = fp
        if fp:
            self.after(0, self._on_done)
        else:
            self.after(0, self._on_error)

    def _on_done(self):
        self._set_status("done")
        self._btn_generate.configure(state="normal")
        self._btn_open.configure(state="normal")

    def _on_error(self):
        self._set_status("error")
        self._btn_generate.configure(state="normal")

    def _open_file(self):
        if self._output_file and os.path.exists(self._output_file):
            os.startfile(self._output_file)

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log(self, msg: str, kind: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        tag  = kind  # "ok" | "err" | "warn" | "info"

        def _insert():
            self._log_text.configure(state="normal")
            self._log_text._textbox.insert("end", line, tag)
            self._log_text._textbox.see("end")
            self._log_text.configure(state="disabled")

        self.after(0, _insert)

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("0.0", "end")
        self._log_text.configure(state="disabled")

    # ── Status helpers ────────────────────────────────────────────────────────

    def _set_status(self, s: str):
        if s == "running":
            self._status_badge.configure(text="  En cours...  ", text_color=ACCENT, fg_color="#1a2a5a")
            self._stat_stat.configure(text="En cours", text_color=ACCENT)
            self._progress.grid()
            self._progress.start()
        elif s == "done":
            self._status_badge.configure(text="  Termine  ", text_color=SUCCESS, fg_color="#12301e")
            self._stat_stat.configure(text="Termine", text_color=SUCCESS)
            self._progress.stop()
            self._progress.grid_remove()
        elif s == "error":
            self._status_badge.configure(text="  Erreur  ", text_color=ERROR, fg_color="#2a1212")
            self._stat_stat.configure(text="Erreur", text_color=ERROR)
            self._progress.stop()
            self._progress.grid_remove()
        else:
            self._status_badge.configure(text="  Pret  ", text_color=MUTED, fg_color=SURFACE2)
            self._stat_stat.configure(text="En attente", text_color=MUTED)
            self._progress.stop()
            self._progress.grid_remove()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = AmortissementApp()
    app.mainloop()
