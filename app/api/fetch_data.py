import os
import sys
import csv
from datetime import datetime

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

for _p in [_ROOT_DIR, _APP_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from services.main_db import get_all_files_from_db

# Output CSV will be saved in the same folder as this file
OUTPUT_CSV = os.path.join(_CURRENT_DIR, "files_export.csv")


def fetch_and_save_to_csv(output_path: str = OUTPUT_CSV) -> str:
    """
    Fetches all file records from MongoDB (is_latest=True)
    and writes them to a CSV at output_path.

    Returns the path to the saved CSV.
    """
    records = get_all_files_from_db()

    if not records:
        print("No records found in MongoDB.")
        return ""

    # Determine column order (union of all keys, common ones first)
    priority_cols = [
        "file_id", "file_name", "file_type", "version",
        "source_platform", "hosted_link", "local_path",
        "file_size", "file_hash", "is_latest", "created_at",
    ]
    all_keys = set()
    for r in records:
        all_keys.update(r.keys())

    # Build final column list: priority cols first, then any extras
    columns = [c for c in priority_cols if c in all_keys]
    columns += sorted(all_keys - set(columns))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"Exported {len(records)} records to: {output_path}")
    return output_path


if __name__ == "__main__":
    path = fetch_and_save_to_csv()
    if path:
        print(f"Done. CSV saved at: {path}")
