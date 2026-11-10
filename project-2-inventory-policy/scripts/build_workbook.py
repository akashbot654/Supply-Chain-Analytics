"""Build the Project 2 inventory policy workbook from sku_policy_inputs_CA_1.csv.

All policy calculations are live Excel formulas that point to named cells on the
Assumptions sheet, so changing an assumption recalculates every SKU.
"""
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

SRC, OUT = sys.argv[1], sys.argv[2]
df = pd.read_csv(SRC).sort_values(["cat_id", "dept_id", "item_id"]).reset_index(drop=True)
N = len(df)

FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF")
BLACK = Font(name=FONT, color="000000")
GREEN = Font(name=FONT, color="008000")
BOLD = Font(name=FONT, bold=True)
TITLE = Font(name=FONT, bold=True, size=14)
HDR_FONT = Font(name=FONT, bold=True, color="FFFFFF")
HDR_FILL = PatternFill("solid", fgColor="1F4E79")
INPUT_FILL = PatternFill("solid", fgColor="FFFF00")
SEC_FILL = PatternFill("solid", fgColor="D9E1F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()

# ---------------------------------------------------------------- Assumptions
a = wb.active
a.title = "Assumptions"
a["A1"] = "Inventory Policy Tool: Walmart M5, store CA_1"
a["A1"].font = TITLE
a["A2"] = ("Edit only the yellow cells (blue text). Every number on SKU_Policy, Summary, and "
           "SKU_Example recalculates from them. M5 has no lead time or cost data, so these "
           "are stated assumptions, not Walmart data.")
a["A2"].font = Font(name=FONT, italic=True)
a["A2"].alignment = WRAP
a.merge_cells("A2:D2")
a.row_dimensions[2].height = 45

for c, h in zip("ABCD", ["Assumption", "Value", "Symbol", "Why / source"]):
    cell = a[f"{c}4"]
    cell.value, cell.font, cell.fill = h, HDR_FONT, HDR_FILL

rows = [
    ("Lead time (weeks)", 1, "L", "LeadTime",
     "Assumption: store shelves are replenished weekly from a distribution center", "0"),
    ("Unit cost as % of shelf price", 0.70, "C / price", "CostPct",
     "Assumption: M5 has retail prices only; cost = 70% of last training-period price", "0%"),
    ("Holding rate (% of unit cost per year)", 0.25, "h", "HoldRate",
     "Assumption: typical range 20 to 30% (capital, space, shrink)", "0%"),
    ("Cost per order ($ per SKU order)", 5, "S", "OrderCost",
     "Assumption: handling and receiving at store level", "$#,##0.00"),
    ("Target cycle service level", 0.95, "CSL", "ServiceLevel",
     "Probability of no stockout during one replenishment cycle. Base case 95%", "0.0%"),
    ("Weeks per year", 52, "", "WeeksPerYear", "Constant", "0"),
    ("Max order size (weeks of supply)", 4, "Wmax", "MaxWeeksSupply",
     "Assumption: shelf space and shelf life limit one order to 4 weeks of average demand", "0"),
]
for i, (label, val, sym, name, why, fmt) in enumerate(rows, start=5):
    a[f"A{i}"], a[f"B{i}"], a[f"C{i}"], a[f"D{i}"] = label, val, sym, why
    for c in "ACD":
        a[f"{c}{i}"].font = BLACK
    a[f"B{i}"].font, a[f"B{i}"].fill, a[f"B{i}"].number_format = BLUE, INPUT_FILL, fmt
    wb.defined_names[name] = DefinedName(name, attr_text=f"Assumptions!$B${i}")

zr = 5 + len(rows)
a[f"A{zr}"], a[f"B{zr}"], a[f"C{zr}"] = "Safety factor (from service level)", "=NORMSINV(ServiceLevel)", "z"
a[f"D{zr}"] = "Calculated: standard normal value with CSL probability below it (95% gives 1.645)"
a[f"B{zr}"].number_format = "0.000"
for c in "ABCD":
    a[f"{c}{zr}"].font = BLACK
wb.defined_names["z"] = DefinedName("z", attr_text=f"Assumptions!$B${zr}")
z_row = zr

fr = zr + 2
a[f"A{fr}"] = "Formulas used on SKU_Policy"
a[f"A{fr}"].font = BOLD
formulas = [
    ("sigma_1", "RMSE of 1-week-ahead forecast error, units (from notebook 01)"),
    ("sigma_L = sigma_1 x SQRT(L)", "Forecast error over the lead time (assumes independent weekly errors)"),
    ("SS = z x sigma_L", "Safety stock, units"),
    ("ROP = d x L + SS", "Reorder point, units. d = average weekly demand"),
    ("D = d x 52", "Annual demand, units"),
    ("C = price x CostPct", "Unit cost, $"),
    ("H = h x C", "Holding cost per unit per year, $"),
    ("EOQ = SQRT(2 x D x S / H)", "Economic order quantity, units"),
    ("Q = MIN(EOQ, Wmax x d)", "Order quantity used: EOQ capped at Wmax weeks of supply"),
    ("Avg inventory = Q / 2 + SS", "Cycle stock plus safety stock, units"),
    ("Annual cost = H x Avg inventory + S x D / Q", "Holding cost plus ordering cost, $ per year"),
]
for j, (f, d) in enumerate(formulas, start=fr + 1):
    a[f"A{j}"], a[f"B{j}"] = f, d
    a[f"A{j}"].font = a[f"B{j}"].font = BLACK
    a.merge_cells(f"B{j}:D{j}")

a.column_dimensions["A"].width = 44
a.column_dimensions["B"].width = 14
a.column_dimensions["C"].width = 12
a.column_dimensions["D"].width = 80

# ---------------------------------------------------------------- SKU_Policy
s = wb.create_sheet("SKU_Policy")
cols = [
    # header, width, number format, kind ("in" = input from Python, "f" = formula), value/formula template
    ("Item", 15, "@", "in", "item_id"),
    ("Dept", 11, "@", "in", "dept_id"),
    ("Category", 11, "@", "in", "cat_id"),
    ("Slow mover", 9, "@", "in", "slow"),
    ("Shelf price ($)", 10, "$#,##0.00", "in", "last_train_price"),
    ("Avg weekly demand d (units)", 11, "#,##0.00", "in", "avg_weekly_demand"),
    ("sigma_1 naive (units)", 10, "#,##0.00", "in", "rmse_naive"),
    ("sigma_1 moving avg (units)", 10, "#,##0.00", "in", "rmse_ma"),
    ("Unit cost C ($)", 10, "$#,##0.00", "f", "=E{r}*CostPct"),
    ("Annual demand D (units)", 11, "#,##0", "f", "=F{r}*WeeksPerYear"),
    ("Holding cost H ($/unit/yr)", 11, "$#,##0.00", "f", "=I{r}*HoldRate"),
    ("sigma_L moving avg (units)", 10, "#,##0.00", "f", "=H{r}*SQRT(LeadTime)"),
    ("Safety stock SS (units)", 10, "#,##0.0", "f", "=z*L{r}"),
    ("Reorder point ROP (units)", 10, "#,##0.0", "f", "=F{r}*LeadTime+M{r}"),
    ("EOQ (units)", 10, "#,##0.0", "f", "=IF(AND(J{r}>0,K{r}>0),SQRT(2*J{r}*OrderCost/K{r}),0)"),
    ("Order qty Q (units, capped)", 10, "#,##0.0", "f", "=IF(O{r}>0,MIN(O{r},MaxWeeksSupply*F{r}),0)"),
    ("Avg inventory (units)", 10, "#,##0.0", "f", "=P{r}/2+M{r}"),
    ("Avg inventory ($)", 11, "$#,##0", "f", "=Q{r}*I{r}"),
    ("Annual holding cost ($)", 11, "$#,##0", "f", "=K{r}*Q{r}"),
    ("Annual ordering cost ($)", 11, "$#,##0", "f", "=IF(P{r}>0,OrderCost*J{r}/P{r},0)"),
    ("Total annual cost ($)", 11, "$#,##0", "f", "=S{r}+T{r}"),
    ("SS $ moving avg", 11, "$#,##0.00", "f", "=M{r}*I{r}"),
    ("SS units naive", 10, "#,##0.0", "f", "=z*G{r}*SQRT(LeadTime)"),
    ("SS $ naive", 11, "$#,##0.00", "f", "=W{r}*I{r}"),
    ("SS $ saved by moving avg", 11, "$#,##0.00;[Red]($#,##0.00);-", "f", "=X{r}-V{r}"),
    ("Order capped?", 9, "@", "f", "=IF(P{r}<O{r},\"Yes\",\"No\")"),
]
assert get_column_letter(len(cols)) == "Z"

s.row_dimensions[1].height = 48
for j, (h, w, _, kind, _) in enumerate(cols, start=1):
    c = s.cell(row=1, column=j, value=h)
    c.font, c.fill = HDR_FONT, HDR_FILL
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    s.column_dimensions[get_column_letter(j)].width = w

s["E1"].comment = Comment("Last price in the training period (notebook 01). Source: M5 sell_prices.csv", "Akash")
s["G1"].comment = Comment("RMSE of 1-week-ahead naive forecast error, last 52 training weeks (notebook 01)", "Akash")
s["H1"].comment = Comment("RMSE of 1-week-ahead 4-week moving average error, last 52 training weeks (notebook 01)", "Akash")
s["D1"].comment = Comment("Yes = avg demand under 1 unit/week or over 50% zero-sales weeks. "
                          "Normal-error safety stock is unreliable for these.", "Akash")

df["slow"] = df["slow_mover_flag"].map({True: "Yes", False: "No"})
for i, row in enumerate(df.itertuples(index=False), start=2):
    rec = row._asdict()
    for j, (_, _, fmt, kind, src) in enumerate(cols, start=1):
        c = s.cell(row=i, column=j)
        if kind == "in":
            c.value = rec[src]
            c.font = BLUE
        else:
            c.value = src.format(r=i)
            c.font = BLACK
        c.number_format = fmt

LAST = N + 1
s.freeze_panes = "B2"
s.auto_filter.ref = f"A1:Z{LAST}"

# ---------------------------------------------------------------- Summary
m = wb.create_sheet("Summary")
m["A1"] = "Inventory policy summary, store CA_1"
m["A1"].font = TITLE
m["A2"] = "=\"Base case: lead time \"&LeadTime&\" wk, \"&TEXT(ServiceLevel,\"0.0%\")&\" service level (z = \"&TEXT(z,\"0.000\")&\"), cost \"&TEXT(CostPct,\"0%\")&\" of price, holding \"&TEXT(HoldRate,\"0%\")&\"/yr, $\"&TEXT(OrderCost,\"0.00\")&\" per order\""
m["A2"].font = Font(name=FONT, italic=True)

R = lambda col: f"SKU_Policy!${col}$2:${col}${LAST}"

def block(top, title, group_col, groups):
    m.cell(row=top, column=1, value=title).font = BOLD
    hdr = ["Group", "SKUs", "Safety stock (units)", "Safety stock $ (moving avg)",
           "Safety stock $ (naive)", "SS $ saved by moving avg", "SS $ saved (%)",
           "Avg inventory $", "Total annual cost $", "SKUs with order capped"]
    for j, h in enumerate(hdr, start=1):
        c = m.cell(row=top + 1, column=j, value=h)
        c.font, c.fill = HDR_FONT, HDR_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    m.row_dimensions[top + 1].height = 32
    first = top + 2
    for k, g in enumerate(groups):
        r = first + k
        crit = f"{R(group_col)},\"{g}\""
        m.cell(row=r, column=1, value=g).font = BLACK
        m.cell(row=r, column=2, value=f"=COUNTIFS({crit})")
        m.cell(row=r, column=3, value=f"=SUMIFS({R('M')},{crit})")
        m.cell(row=r, column=4, value=f"=SUMIFS({R('V')},{crit})")
        m.cell(row=r, column=5, value=f"=SUMIFS({R('X')},{crit})")
        m.cell(row=r, column=6, value=f"=E{r}-D{r}")
        m.cell(row=r, column=7, value=f"=IF(E{r}>0,F{r}/E{r},0)")
        m.cell(row=r, column=8, value=f"=SUMIFS({R('R')},{crit})")
        m.cell(row=r, column=9, value=f"=SUMIFS({R('U')},{crit})")
        m.cell(row=r, column=10, value=f"=COUNTIFS({crit},{R('Z')},\"Yes\")")
    tr = first + len(groups)
    m.cell(row=tr, column=1, value="Total").font = BOLD
    for j in [2, 3, 4, 5, 6, 8, 9, 10]:
        L = get_column_letter(j)
        m.cell(row=tr, column=j, value=f"=SUM({L}{first}:{L}{tr - 1})").font = BOLD
    m.cell(row=tr, column=7, value=f"=IF(E{tr}>0,F{tr}/E{tr},0)").font = BOLD
    fmts = {2: "#,##0", 3: "#,##0", 4: "$#,##0", 5: "$#,##0", 6: "$#,##0;[Red]($#,##0);-",
            7: "0.0%;[Red]-0.0%;-", 8: "$#,##0", 9: "$#,##0", 10: "#,##0"}
    for r in range(first, tr + 1):
        for j, f in fmts.items():
            m.cell(row=r, column=j).number_format = f
            if r < tr:
                m.cell(row=r, column=j).font = GREEN if j in (2, 3, 4, 5, 8, 9, 10) else BLACK
        for j in range(1, 11):
            m.cell(row=r, column=j).border = BOX
    return tr

end1 = block(4, "By category", "C", ["FOODS", "HOBBIES", "HOUSEHOLD"])
# Named totals, read by the VBA scenario sweep
for name, col in [("Tot_SS_Units", "C"), ("Tot_SS_MA", "D"), ("Tot_SS_Naive", "E"),
                  ("Tot_AvgInv", "H"), ("Tot_Cost", "I"), ("Tot_Capped", "J")]:
    wb.defined_names[name] = DefinedName(name, attr_text=f"Summary!${col}${end1}")
end2 = block(end1 + 3, "Regular vs slow movers (slow = under 1 unit/week or over 50% zero weeks)",
             "D", ["No", "Yes"])
m.cell(row=end2 - 2, column=1, value="Regular (No)")
m.cell(row=end2 - 1, column=1, value="Slow movers (Yes)")
# keep criteria text matching the flag values: rewrite labels only, formulas use "No"/"Yes"

note = end2 + 2
m.cell(row=note, column=1, value="How to read this").font = BOLD
for k, t in enumerate([
    "Safety stock is proportional to forecast error, so a lower-error forecast needs less buffer for the same service level.",
    "SS $ saved compares safety stock valued at unit cost under naive error vs moving average error. It is inventory $ tied up, not annual cost.",
    "Slow movers use the same formula, but their lumpy demand breaks the normal-error assumption. Treat their numbers as rough.",
    "Order size is EOQ capped at the max weeks of supply (Assumptions sheet). Pure EOQ suggested months of stock per order for cheap items, which a shelf cannot hold.",
    "All dollar figures depend on the assumptions on the Assumptions sheet.",
], start=note + 1):
    m.cell(row=k, column=1, value=f"- {t}").font = BLACK

m.column_dimensions["A"].width = 18
for j in range(2, 11):
    m.column_dimensions[get_column_letter(j)].width = 15

# ---------------------------------------------------------------- SKU_Example
e = wb.create_sheet("SKU_Example")
e["A1"] = "Worked example: one SKU from forecast error to policy"
e["A1"].font = TITLE
e["A3"], e["B3"] = "Item (type any item_id)", df.loc[df["slow"] == "No", "item_id"].iloc[0]
e["A3"].font = BOLD
e["B3"].font, e["B3"].fill = BLUE, INPUT_FILL
e["A4"] = "=IF(ISNA(MATCH(B3,SKU_Policy!$A$2:$A$" + str(LAST) + ",0)),\"Item not found\",\"Row \"&(MATCH(B3,SKU_Policy!$A$2:$A$" + str(LAST) + ",0)+1)&\" on SKU_Policy\")"
e["A4"].font = Font(name=FONT, italic=True)

for j, h in enumerate(["Step", "Value", "Formula", "What it means"], start=1):
    c = e.cell(row=6, column=j, value=h)
    c.font, c.fill = HDR_FONT, HDR_FILL

look = lambda col: f"=INDEX(SKU_Policy!${col}$2:${col}${LAST},MATCH($B$3,SKU_Policy!$A$2:$A${LAST},0))"
steps = [
    ("Category", look("C"), "@", "input", "Product group"),
    ("Slow mover?", look("D"), "@", "input", "If Yes, treat the result as rough"),
    ("Shelf price ($)", look("E"), "$#,##0.00", "input", "Last training-period price"),
    ("Avg weekly demand d (units)", look("F"), "#,##0.00", "input", "Expected sales per week"),
    ("sigma_1 moving avg (units)", look("H"), "#,##0.00", "input", "Typical size of a 1-week forecast miss"),
    ("Lead time L (weeks)", "=LeadTime", "0", "assumption", "Time from order to shelf"),
    ("sigma_L (units)", "=B11*SQRT(B12)", "#,##0.00", "sigma_1 x SQRT(L)", "Forecast miss over the whole lead time"),
    ("z", "=z", "0.000", "NORMSINV(CSL)", "How many sigmas of buffer the service target needs"),
    ("Safety stock SS (units)", "=B14*B13", "#,##0.0", "z x sigma_L", "Buffer held for forecast misses"),
    ("Reorder point ROP (units)", "=B10*B12+B15", "#,##0.0", "d x L + SS", "Order when stock falls to this level"),
    ("Unit cost C ($)", "=B9*CostPct", "$#,##0.00", "price x CostPct", "Cost to the retailer"),
    ("Annual demand D (units)", "=B10*WeeksPerYear", "#,##0", "d x 52", ""),
    ("Holding cost H ($/unit/yr)", "=B17*HoldRate", "$#,##0.00", "h x C", "Cost to keep one unit for a year"),
    ("EOQ (units)", "=IF(AND(B18>0,B19>0),SQRT(2*B18*OrderCost/B19),0)", "#,##0.0",
     "SQRT(2 x D x S / H)", "Order size that balances ordering and holding cost"),
    ("Order qty Q (units)", "=IF(B20>0,MIN(B20,MaxWeeksSupply*B10),0)", "#,##0.0",
     "MIN(EOQ, Wmax x d)", "EOQ capped at the weeks of supply a shelf can hold"),
    ("Avg inventory (units)", "=B21/2+B15", "#,##0.0", "Q / 2 + SS", "Cycle stock plus safety stock"),
    ("Annual cost ($)", "=B19*B22+IF(B21>0,OrderCost*B18/B21,0)", "$#,##0.00",
     "H x avg inv + S x D / Q", "Holding plus ordering cost per year"),
    ("Check vs SKU_Policy total cost", look("U"), "$#,##0.00", "lookup", "Should equal the row above"),
]
for k, (lab, f, fmt, formula_txt, meaning) in enumerate(steps, start=7):
    e[f"A{k}"], e[f"B{k}"], e[f"C{k}"], e[f"D{k}"] = lab, f, formula_txt, meaning
    e[f"B{k}"].number_format = fmt
    e[f"B{k}"].font = GREEN if f.startswith("=INDEX") or f in ("=LeadTime", "=z") else BLACK
    for c in "ACD":
        e[f"{c}{k}"].font = BLACK
    for c in "ABCD":
        e[f"{c}{k}"].border = BOX
e.column_dimensions["A"].width = 32
e.column_dimensions["B"].width = 14
e.column_dimensions["C"].width = 26
e.column_dimensions["D"].width = 52

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = ws.title != "Assumptions"
wb.move_sheet("Summary", offset=-1)  # order: Assumptions, Summary, SKU_Policy, SKU_Example
wb.save(OUT)
print(f"Saved {OUT} with {N} SKUs")
