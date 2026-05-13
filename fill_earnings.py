"""Fill in the earnings column of the existing PGA Championship Pool spreadsheet."""
import json, openpyxl

XLSX = r"C:\Users\jjg\SandboxSpace\PGAPool\pga_pool_2026.xlsx"
EARNINGS = r"C:\Users\jjg\SandboxSpace\PGAPool\PGAPool\earnings.json"

with open(EARNINGS, encoding="utf-8") as f:
    earnings = json.load(f)

wb = openpyxl.load_workbook(XLSX)
ws = wb["Golfer Earnings"]

filled = 0
for row in range(4, ws.max_row + 1):
    name = ws.cell(row=row, column=1).value
    if name and name in earnings:
        ws.cell(row=row, column=2, value=earnings[name])
        ws.cell(row=row, column=2).number_format = '$#,##0'
        filled += 1

wb.save(XLSX)
print(f"Filled {filled} golfer earnings in {XLSX}")
print("Pool Entries tab will auto-calculate via VLOOKUP formulas.")
