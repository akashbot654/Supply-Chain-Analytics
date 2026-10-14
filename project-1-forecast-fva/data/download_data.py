"""Download the M5 Forecasting - Accuracy files from Kaggle into data/raw/.

Requires:
  - pip install kaggle
  - A Kaggle API token saved at ~/.kaggle/kaggle.json
  - Competition rules accepted at https://www.kaggle.com/c/m5-forecasting-accuracy
"""
import subprocess
import zipfile
from pathlib import Path

# Paths are relative to this script, so it works on any computer
RAW_DIR = Path(__file__).resolve().parent / "raw"
COMPETITION = "m5-forecasting-accuracy"
FILES_NEEDED = ["sales_train_evaluation.csv", "calendar.csv", "sell_prices.csv"]

RAW_DIR.mkdir(parents=True, exist_ok=True)

# Download the competition zip using the Kaggle command line tool
subprocess.run(
    ["kaggle", "competitions", "download", "-c", COMPETITION, "-p", str(RAW_DIR)],
    check=True,
)

# Extract only the three files this project uses
zip_path = RAW_DIR / f"{COMPETITION}.zip"
with zipfile.ZipFile(zip_path) as z:
    for name in FILES_NEEDED:
        z.extract(name, RAW_DIR)

zip_path.unlink()  # remove the zip to save space
print(f"Done. Files saved to {RAW_DIR}")
