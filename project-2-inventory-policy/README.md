# Project 2: Forecast-to-Inventory Policy Tool

**Tools:** Python (data prep), Excel (policy model), VBA (scenario automation) | **Data:** Walmart M5, store CA_1 (same 2,717 SKUs as [Project 1](../project-1-forecast-fva/)) | **Status:** In progress (Step 2 of 6 done)

## Business Question
How much safety stock does each SKU need to hit a target service level, what does that inventory cost to hold, and how many dollars does a more accurate forecast free up?

## Data
- Inputs come from Project 1's processed weekly data (`project-1-forecast-fva/data/processed/`)
- `data/sku_policy_inputs_CA_1.csv`: one row per SKU with average demand, 1-week forecast error (naive and moving average), bias, and a slow-mover flag
- `data/holdout_demand_CA_1.csv`: actual weekly demand in the 13-week holdout quarter, used to test the policy
- M5 has no lead times, unit costs, or ordering costs. These are **assumptions** set on the Excel Assumptions sheet:

| Assumption | Base case | Why |
|---|---|---|
| Lead time $L$ | 1 week | Store shelves are replenished weekly from a distribution center |
| Unit cost $C$ | 70% of last training-period shelf price | M5 has retail prices only |
| Holding rate $h$ | 25% per year | Typical range is 20 to 30% (capital, space, shrink) |
| Cost per order $S$ | $5 per SKU order | Handling and receiving at store level |
| Service target | 95% cycle service level ($z$ = 1.645) | Common retail base case; swept from 90% to 99% in VBA |

## Approach
| Step | What it does | Status |
|---|---|---|
| 1 | `notebooks/01_policy_inputs.ipynb`: rolling 1-week-ahead backtest over the last 52 training weeks to measure forecast error per SKU | Built |
| 2 | `excel/inventory_policy_CA_1.xlsx` (built by `scripts/build_workbook.py`): Assumptions, Summary, SKU_Policy (2,717 rows of live formulas), and SKU_Example (one SKU worked end to end) | Built |
| 3 | VBA: service-level and lead-time scenario sweep that writes a cost vs service trade-off table and chart | Planned |
| 4 | Holdout test: simulate the policy on the 13-week holdout quarter and compare achieved vs target service level | Planned |
| 5 | Dollar impact: safety stock cost with naive error vs moving average error | Planned |
| 6 | Recommendation, README results, resume bullets, interview pitch | Planned |

**Formulas** (continuous review, reorder point policy)
- $\sigma_1$ = RMSE of 1-week-ahead forecast error, in units
- $L$ = replenishment lead time, in weeks
- $\sigma_L = \sigma_1 \sqrt{L}$ = forecast error over the lead time (assumes weekly errors are independent)
- $z$ = standard normal value for the target cycle service level (for example 1.645 for 95%)
- Safety stock $SS = z \cdot \sigma_L$
- Reorder point $ROP = \bar{d} \cdot L + SS$, where $\bar{d}$ = forecast weekly demand
- $D$ = annual demand $= 52 \bar{d}$; $S$ = cost per order; $H$ = annual holding cost per unit $= h \cdot C$, where $h$ = holding rate and $C$ = unit cost
- Order quantity $EOQ = \sqrt{2DS / H}$
- Average inventory $= EOQ/2 + SS$; annual cost $= H \cdot (EOQ/2 + SS) + S \cdot D / EOQ$

## Results
_To be completed. Only real results will be reported here._

## Decision / Recommendation
_To be completed._

## Limitations
- M5 records sales, not demand. Stockouts hide unmet demand
- Lead time, unit cost, holding rate, and ordering cost are assumptions, not Walmart data
- The normal-error safety stock formula is weak for slow, lumpy sellers. These SKUs are flagged in Step 1 and reported separately

## How to Run
1. Complete Project 1 first (this project reads its processed data)
2. Install requirements: `pip install -r requirements.txt` (Python 3.11)
3. Run `notebooks/01_policy_inputs.ipynb`
4. Open `excel/inventory_policy_CA_1.xlsx` and change the yellow cells on the Assumptions sheet. To rebuild the workbook from the CSV: `pip install openpyxl` then `python scripts/build_workbook.py data/sku_policy_inputs_CA_1.csv excel/inventory_policy_CA_1.xlsx`

## Folder Structure
```
project-2-inventory-policy/
├── data/             # SKU inputs and holdout demand exported by notebook 01
├── notebooks/        # Python data prep
├── excel/            # Inventory policy workbook (.xlsm)
├── scripts/          # build_workbook.py: writes the Excel model from the notebook 01 CSV
├── vba/              # Exported VBA modules (.bas) so the code is readable on GitHub
├── outputs/figures/  # Charts used in this README
└── requirements.txt
```
