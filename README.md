# Amortissement — Asset Depreciation Estimator (Odoo 8)

Estimates monthly depreciation schedules for fixed assets from an Odoo 8 PostgreSQL database.
Supports multiple asset categories, each with its own amortization duration.

---

## Setup

```bash
cd amortissement
pip install -r requirements.txt
```

---

## Configuration

Edit `config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  dbname: your_odoo_db
  user: odoo
  password: secret

categories:
  - pattern: "%bâtiment%"
    years: 30
  # Add more later:
  # - pattern: "%véhicule%"
  #   years: 5

output:
  directory: output
  format: excel   # excel | csv | both
```

**To add a new category**: add 3 lines under `categories:`. No code changes needed.

---

## Usage

```bash
# Run all categories → exports to output/amortissement_YYYY-MM-DD.xlsx
python main.py

# Test with a single asset (compares against known SQL output)
python main.py --asset-id 34473

# Use a custom config file
python main.py --config prod_config.yaml
```

---

## Output

- `output/amortissement_YYYY-MM-DD.xlsx`
  - One sheet per category (e.g., "bâtiment")
  - One combined sheet "Tout" (when multiple categories)
- Columns match your original SQL query exactly

---

## Project Structure

```
amortissement/
├── config.yaml          ← DB credentials + category/years mapping
├── requirements.txt     ← pip dependencies
├── main.py              ← Entry point
├── db.py                ← PostgreSQL connection
├── query_builder.py     ← Parameterized SQL builder
├── exporter.py          ← Excel/CSV export with formatting
└── output/              ← Generated files (auto-created)
```
