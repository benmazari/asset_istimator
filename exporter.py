"""
exporter.py — Writes results to Excel with professional formatting.

One sheet per category + one combined "Tout" sheet.
"""

import os
from datetime import date
import pandas as pd
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter


# ── Color palette ────────────────────────────────────────────────────────────
HEADER_BG   = "1F3864"   # dark navy
HEADER_FG   = "FFFFFF"   # white
ALT_ROW_BG  = "EBF0FA"   # light blue-gray
BORDER_CLR  = "C0C8D8"

def _clean_illegal_xml_chars(val):
    if not isinstance(val, str):
        return val
    # Remove characters that are not allowed in XML/Excel
    return "".join(c for c in val if (
        ord(c) in {0x9, 0xA, 0xD} or 
        (0x20 <= ord(c) <= 0xD7FF) or 
        (0xE000 <= ord(c) <= 0xFFFD) or 
        (0x10000 <= ord(c) <= 0x10FFFF)
    ))


def _style_sheet(ws, df: pd.DataFrame):
    """Apply header style, alternating rows, column widths to a worksheet."""

    thin = Side(style="thin", color=BORDER_CLR)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ── Header row ───────────────────────────────────────────────────────────
    header_font   = Font(bold=True, color=HEADER_FG, name="Calibri", size=10)
    header_fill   = PatternFill("solid", fgColor=HEADER_BG)
    header_align  = Alignment(horizontal="center", vertical="center",
                               wrap_text=True)

    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align
        cell.border    = border

    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"

    # ── Auto column widths ───────────────────────────────────────────────────
    for col_idx, col_name in enumerate(df.columns, start=1):
        col_letter = get_column_letter(col_idx)
        # Width = max of header length vs max data length, capped at 40
        max_data_len = df[col_name].head(1000).astype(str).str.len().max() if len(df) else 0
        width = min(max(len(str(col_name)), max_data_len, 10) + 2, 40)
        ws.column_dimensions[col_letter].width = width


def export_to_excel(results: dict[str, pd.DataFrame], output_dir: str):
    """
    Export category DataFrames to a single Excel file.

    Args:
        results:    {category_label: DataFrame}
        output_dir: Directory where the file will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    today = date.today().isoformat()
    filepath = os.path.join(output_dir, f"amortissement_{today}.xlsx")

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:

        # ── One sheet per category ────────────────────────────────────────────
        for label, df in results.items():
            # Excel sheet names: max 31 chars, no [] : * ? / \
            import re
            sheet_name = re.sub(r'[\[\]\:\*\?\/\\]', '-', label[:31])
            if not sheet_name: sheet_name = "Sheet"
            
            # Clean data: only on object (string) columns for speed and reliability
            df_clean = df.copy()
            for col in df_clean.columns:
                if df_clean[col].dtype == object:
                    df_clean[col] = df_clean[col].apply(_clean_illegal_xml_chars)
            
            df_clean.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            _style_sheet(ws, df_clean)

        # ── Combined "Tout" sheet ─────────────────────────────────────────────
        if len(results) > 1:
            combined = pd.concat(
                [df.assign(**{"Catégorie (filtre)": label})
                 for label, df in results.items()],
                ignore_index=True
            )
            combined_clean = combined.copy()
            for col in combined_clean.columns:
                if combined_clean[col].dtype == object:
                    combined_clean[col] = combined_clean[col].apply(_clean_illegal_xml_chars)
                    
            combined_clean.to_excel(writer, sheet_name="Tout", index=False)
            ws = writer.sheets["Tout"]
            _style_sheet(ws, combined_clean)

    print(f"\n[OK] Export termine : {filepath}")
    return filepath


def export_to_csv(results: dict[str, pd.DataFrame], output_dir: str):
    """Export each category as a separate CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    today = date.today().isoformat()
    paths = []
    for label, df in results.items():
        safe_label = label.replace("%", "").replace(" ", "_").strip("_")
        filepath = os.path.join(output_dir, f"amortissement_{safe_label}_{today}.csv")
        df.to_csv(filepath, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compat
        paths.append(filepath)
        print(f"[OK] CSV : {filepath}")
    return paths



