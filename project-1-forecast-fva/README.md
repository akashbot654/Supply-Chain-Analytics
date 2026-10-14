# Project 1: Forecast Accuracy Benchmark + Forecast Value Added (FVA)

## Business Question
Which forecasting method should a planner use for each product group, and do manual planner adjustments add value or destroy it?

## Data
Walmart M5 Forecasting - Accuracy (Kaggle): https://www.kaggle.com/c/m5-forecasting-accuracy

- Files used: `sales_train_evaluation.csv`, `calendar.csv`, `sell_prices.csv`
- Subset: one store, daily sales aggregated to weekly by SKU
- Raw files are not stored in this repo (too large). See How to Run.

## Approach
_To be completed._

## Results
_To be completed. Only real results will be reported here._

## Decision / Recommendation
_To be completed._

## Limitations
- M5 records sales, not true demand. Stockouts hide unmet demand, so actual demand may be understated.
- Planner overrides in this project are simulated, not real planner decisions.

## How to Run
1. Install requirements: `pip install -r requirements.txt`
2. Get a Kaggle API token (Kaggle > Settings > API > Create New Token) and place `kaggle.json` in `~/.kaggle/`
3. Accept the competition rules on the Kaggle competition page
4. Download the data: `python data/download_data.py`
5. Run the notebooks in `notebooks/` in numbered order

## Folder Structure
```
project-1-forecast-fva/
├── data/
│   ├── raw/          # Original Kaggle files (not committed)
│   ├── processed/    # Cleaned weekly subset created by the notebooks
│   └── download_data.py
├── notebooks/        # Analysis notebooks, numbered in run order
├── src/              # Reusable Python functions (metrics, models)
├── outputs/figures/  # Charts used in this README
└── requirements.txt
```
