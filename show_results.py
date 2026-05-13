import json

entries = [
    ("JJ",      ["Rory McIlroy", "Scottie Scheffler", "Xander Schauffele", "Tommy Fleetwood", "Matt Fitzpatrick"]),
    ("Geoff",   ["Rory McIlroy", "Scottie Scheffler", "Jon Rahm", "Brooks Koepka", "Cameron Young"]),
    ("Brian",   ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Collin Morikawa", "Tyrrell Hatton"]),
    ("Brandon", ["Rory McIlroy", "Scottie Scheffler", "Matt Fitzpatrick", "Cameron Young", "Ludvig \u00c5berg"]),
    ("Ben",     ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Jacob Bridgeman", "Alex Fitzpatrick"]),
    ("Milo",    ["Cameron Young", "Matt Fitzpatrick", "Scottie Scheffler", "Rickie Fowler", "Brooks Koepka"]),
]

with open(r"C:\Users\jjg\SandboxSpace\PGAPool\PGAPool\earnings.json", encoding="utf-8") as f:
    earn = json.load(f)

results = []
for name, picks in entries:
    details = [(g, earn.get(g, 0)) for g in picks]
    total = sum(d[1] for d in details)
    results.append((name, details, total))
results.sort(key=lambda x: -x[2])

print("=" * 70)
print("  2026 PGA CHAMPIONSHIP POOL - FINAL RESULTS")
print("=" * 70)
print(f"{'#':>2}  {'Name':<10}  {'Total':>12}")
print("-" * 35)
for i, (name, details, total) in enumerate(results, 1):
    marker = " <<< WINNER!" if i == 1 else ""
    print(f"{i:>2}  {name:<10}  ${total:>11,}{marker}")
print()
print("PICK DETAILS:")
print("-" * 70)
for i, (name, details, total) in enumerate(results, 1):
    print(f"\n{i}. {name} (${total:,})")
    for g, amt in details:
        print(f"   {g:<25} ${amt:>10,}")
