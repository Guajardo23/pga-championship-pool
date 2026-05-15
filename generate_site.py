"""Generate a static HTML leaderboard site for the PGA Championship Pool.

Usage:
    python generate_site.py                  # Pre-tournament or projected from standings.json
    python generate_site.py --final          # Use earnings.json as final results

Data files (same directory):
    standings.json   - live updates: golfer positions + round info
    earnings.json    - final earnings (after Sunday)
"""
import json, os, sys
from datetime import datetime
import zoneinfo

PT = zoneinfo.ZoneInfo("America/Los_Angeles")

# -- Pool Data ---------------------------------------------------------------
entries = [
    ("JJ",      ["Rory McIlroy", "Scottie Scheffler", "Xander Schauffele", "Tommy Fleetwood", "Matt Fitzpatrick"]),
    ("Geoff",   ["Rory McIlroy", "Scottie Scheffler", "Jon Rahm", "Brooks Koepka", "Cameron Young"]),
    ("Brian",   ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Collin Morikawa", "Tyrrell Hatton"]),
    ("Brandon", ["Rory McIlroy", "Scottie Scheffler", "Matt Fitzpatrick", "Cameron Young", "Ludvig \u00c5berg"]),
    ("Ben",     ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Jacob Bridgeman", "Alex Fitzpatrick"]),
    ("Milo",    ["Cameron Young", "Matt Fitzpatrick", "Scottie Scheffler", "Rickie Fowler", "Brooks Koepka"]),
    ("Billy",   ["Rory McIlroy", "Scottie Scheffler", "Cameron Young", "Matt Fitzpatrick", "Ludvig \u00c5berg"]),
    ("Beto",    ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Matt Fitzpatrick", "Justin Rose"]),
    ("Benny",   ["Collin Morikawa", "Xander Schauffele", "Brooks Koepka", "Rory McIlroy", "Scottie Scheffler"]),
    ("Paul",    ["Aaron Rai", "Max McGreevy", "Chris Gotterup", "Jacob Bridgeman", "Sam Burns"]),
    ("Nick",    ["Scottie Scheffler", "Rory McIlroy", "Cameron Young", "Matt Fitzpatrick", "Rickie Fowler"]),
    ("Pat",     ["Justin Rose", "Keegan Bradley", "Tommy Fleetwood", "Cameron Young", "Sepp Straka"]),
]

# -- 2026 PGA Championship purse: $19M. Standard PGA Tour payout structure ---
PAYOUT = {
    1: 3420000, 2: 2052000, 3: 1292000, 4: 912000, 5: 760000,
    6: 684000, 7: 636500, 8: 589000, 9: 551000, 10: 513000,
    11: 475000, 12: 437000, 13: 399000, 14: 361000, 15: 342000,
    16: 323000, 17: 304000, 18: 285000, 19: 266000, 20: 247000,
    21: 228000, 22: 213000, 23: 198000, 24: 183000, 25: 168000,
    26: 152000, 27: 146300, 28: 140600, 29: 134900, 30: 129200,
    31: 123500, 32: 117800, 33: 112100, 34: 107350, 35: 102600,
    36: 97850, 37: 93100, 38: 89300, 39: 85500, 40: 81700,
    41: 77900, 42: 74100, 43: 70300, 44: 66500, 45: 62700,
    46: 58900, 47: 55100, 48: 52060, 49: 49400, 50: 47880,
}
MC_PAYOUT = 0  # PGA Championship: no payout for missed cut


def parse_position(pos_str):
    if not pos_str:
        return None
    pos_str = pos_str.strip().upper()
    if pos_str in ("MC", "CUT", "WD", "DQ"):
        return None
    return int(pos_str.replace("T", ""))


def compute_projected_earnings(standings):
    """Compute earnings for each golfer using tie-splitting rules."""
    from collections import defaultdict
    pos_groups = defaultdict(list)
    mc_golfers = []
    no_position = []

    for name, gdata in standings.items():
        pos_str = gdata.get("position", "").strip().upper()
        if not pos_str:
            no_position.append(name)
        elif pos_str in ("MC", "CUT", "WD", "DQ"):
            mc_golfers.append(name)
        else:
            pos_num = int(pos_str.replace("T", ""))
            pos_groups[pos_num].append(name)

    earnings_map = {}

    for pos_num, names in pos_groups.items():
        count = len(names)
        total_pool = 0
        for i in range(count):
            p = pos_num + i
            total_pool += PAYOUT.get(p, PAYOUT.get(50, 47880))
        per_player = int(total_pool / count)
        for name in names:
            earnings_map[name] = per_player

    for name in mc_golfers:
        earnings_map[name] = MC_PAYOUT

    for name in no_position:
        earnings_map[name] = 0

    return earnings_map


# -- Load data files ---------------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
final_mode = "--final" in sys.argv

standings = {}
round_info = ""
round_status = ""
standings_file = os.path.join(base_dir, "standings.json")
if os.path.exists(standings_file):
    with open(standings_file, "r", encoding="utf-8") as f:
        sdata = json.load(f)
    standings = sdata.get("golfers", {})
    round_info = sdata.get("round", "")
    round_status = sdata.get("status", "")

earnings = {}
earnings_file = os.path.join(base_dir, "earnings.json")
if os.path.exists(earnings_file):
    with open(earnings_file, "r", encoding="utf-8") as f:
        earnings = json.load(f)

# -- Determine mode ----------------------------------------------------------
use_projected = bool(standings) and not final_mode and not earnings
use_final = bool(earnings) or final_mode

projected_map = {}
if use_projected:
    projected_map = compute_projected_earnings(standings)

# -- Calculate totals --------------------------------------------------------
results = []
for name, picks in entries:
    pick_details = []
    total = 0
    for golfer in picks:
        if use_final:
            amt = earnings.get(golfer, 0)
        elif use_projected:
            amt = projected_map.get(golfer, 0)
        else:
            amt = 0
        gdata = standings.get(golfer, {})
        pick_details.append({
            "golfer": golfer,
            "amount": amt,
            "position": gdata.get("position", ""),
            "score": gdata.get("score", ""),
            "today": gdata.get("today", ""),
        })
        total += amt
    results.append({"name": name, "picks": pick_details, "total": total})

results.sort(key=lambda x: x["total"], reverse=True)

for i, r in enumerate(results):
    if i == 0:
        r["rank"] = 1
    elif r["total"] == results[i - 1]["total"]:
        r["rank"] = results[i - 1]["rank"]
    else:
        r["rank"] = i + 1

has_data = use_projected or use_final
updated = datetime.now(PT).strftime("%B %d, %Y at %I:%M %p PT")


# -- Helpers -----------------------------------------------------------------
def fmt_money(amt):
    if amt == 0:
        return "-"
    return f"${amt:,.0f}"


def rank_badge(rank):
    if rank == 1: return '<span class="rank gold">\U0001f947</span>'
    if rank == 2: return '<span class="rank silver">\U0001f948</span>'
    if rank == 3: return '<span class="rank bronze">\U0001f949</span>'
    return f'<span class="rank">{rank}</span>'


def pos_badge(pos):
    if not pos:
        return ""
    up = pos.strip().upper()
    if up in ("MC", "CUT"):
        return '<span class="pos mc">MC</span>'
    if up in ("WD", "DQ"):
        return f'<span class="pos mc">{up}</span>'
    num = parse_position(pos)
    if num and num <= 1:
        return f'<span class="pos pos-leader">{pos}</span>'
    if num and num <= 10:
        return f'<span class="pos pos-top10">{pos}</span>'
    return f'<span class="pos">{pos}</span>'


def score_display(score, today):
    parts = []
    if score:
        parts.append(score)
    if today:
        parts.append(f"({today})")
    return " ".join(parts)


# -- Banner ------------------------------------------------------------------
if use_final:
    banner_text = "\U0001f3c6 Final Results"
    banner_class = "status-banner final"
elif use_projected:
    label = round_info or "In Progress"
    if round_status:
        label += f" \u2014 {round_status}"
    banner_text = f"\U0001f3cc\ufe0f Projected Standings: {label}"
    banner_class = "status-banner projected"
else:
    banner_text = "\U0001f3cc\ufe0f Tournament starts Thursday. Earnings will be updated throughout the weekend."
    banner_class = "status-banner"

money_label = "Projected" if use_projected else "Total"

# -- Build HTML ---------------------------------------------------------------
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 PGA Championship Pool</title>
<style>
  :root {{
    --pga-navy: #00205B;
    --dark-navy: #001740;
    --pga-gold: #C8A951;
    --light-gold: #e8d9a0;
    --bg: #f4f5f7;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-muted: #6c757d;
    --border: #dee2e6;
    --red: #dc3545;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
  }}
  .header {{
    background: linear-gradient(135deg, var(--pga-navy), var(--dark-navy));
    color: white; padding: 2rem 1rem; text-align: center;
  }}
  .header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }}
  .header .subtitle {{ font-size: 1rem; opacity: 0.85; }}
  .header .year {{
    font-size: 3rem; font-weight: 800;
    color: var(--pga-gold); letter-spacing: 2px;
  }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 1.5rem 1rem; }}
  .updated {{ text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem; }}

  .status-banner {{
    background: var(--pga-gold); color: #333;
    text-align: center; padding: 0.7rem;
    font-weight: 600; font-size: 0.95rem;
    border-radius: 8px; margin-bottom: 1.5rem;
  }}
  .status-banner.projected {{ background: #d6e4f0; color: #0d3b66; }}
  .status-banner.final {{ background: var(--pga-navy); color: white; font-size: 1.1rem; }}

  /* Leaderboard */
  .leaderboard {{
    width: 100%; border-collapse: collapse;
    background: var(--card-bg); border-radius: 12px;
    overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
  }}
  .leaderboard th {{
    background: var(--pga-navy); color: white;
    padding: 0.75rem 1rem; text-align: left;
    font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .leaderboard th.money {{ text-align: right; }}
  .leaderboard td {{
    padding: 0.65rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.95rem;
  }}
  .leaderboard td.money {{
    text-align: right; font-weight: 700;
    font-variant-numeric: tabular-nums; font-size: 1rem;
    color: var(--pga-navy);
  }}
  .leaderboard tr:last-child td {{ border-bottom: none; }}
  .leaderboard tr:hover {{ background: #f0f4fa; }}
  .leaderboard tr.top {{ background: #eef2f9; }}
  .rank {{
    display: inline-block; min-width: 2rem;
    text-align: center; font-weight: 700; font-size: 1.1rem;
  }}
  .contestant-name {{ font-weight: 600; font-size: 1.05rem; }}
  .best-golfer {{ color: var(--text-muted); font-size: 0.8rem; margin-left: 0.5rem; }}

  /* Pick cards */
  .picks-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
    gap: 1rem; margin-bottom: 2rem;
  }}
  .pick-card {{
    background: var(--card-bg); border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06); overflow: hidden;
  }}
  .pick-card-header {{
    background: var(--pga-navy); color: white;
    padding: 0.6rem 1rem; display: flex;
    justify-content: space-between; align-items: center;
  }}
  .pick-card-header .name {{ font-weight: 700; font-size: 1.05rem; }}
  .pick-card-header .total {{ font-weight: 600; color: var(--pga-gold); }}
  .pick-card-header .rank-num {{
    background: var(--pga-gold); color: #333;
    border-radius: 50%; width: 1.6rem; height: 1.6rem;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.8rem; margin-right: 0.5rem;
  }}
  .pick-card table {{ width: 100%; border-collapse: collapse; }}
  .pick-card td {{
    padding: 0.45rem 0.75rem; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem;
  }}
  .pick-card tr:last-child td {{ border-bottom: none; }}
  .pick-card .golfer-name {{ font-weight: 500; }}
  .pick-card .score {{ color: var(--text-muted); text-align: center; min-width: 4rem; white-space: nowrap; }}
  .pick-card .score.under-par {{ color: var(--red); font-weight: 600; }}
  .pick-card .pick-amt {{
    text-align: right; font-variant-numeric: tabular-nums;
    color: var(--text-muted); min-width: 5rem;
  }}
  .pick-card .pick-amt.has-earnings {{ color: var(--pga-navy); font-weight: 600; }}

  .pos {{
    display: inline-block; background: #e9ecef;
    border-radius: 4px; padding: 0.1rem 0.4rem;
    font-size: 0.75rem; font-weight: 700; margin-right: 0.35rem;
    min-width: 2rem; text-align: center;
  }}
  .pos.pos-leader {{ background: var(--pga-gold); color: #333; }}
  .pos.pos-top10 {{ background: #d6e4f0; color: #0d3b66; }}
  .pos.mc {{ background: #f8d7da; color: #721c24; }}

  .commentary {{
    background: linear-gradient(135deg, #001740, #00205B);
    color: white; border-radius: 12px; padding: 2rem;
    margin-bottom: 2rem; line-height: 1.7;
    font-family: Georgia, 'Times New Roman', serif;
  }}
  .commentary h2 {{
    color: var(--pga-gold); font-size: 1.4rem;
    margin-bottom: 1rem; font-style: italic;
  }}
  .commentary .champion {{
    color: var(--pga-gold); font-weight: 700;
  }}
  .commentary .jab {{
    color: #f8d7da; font-style: italic;
  }}
  .commentary .sign-off {{
    margin-top: 1rem; font-size: 0.85rem;
    opacity: 0.7; text-align: right;
  }}

  .footer {{
    text-align: center; color: var(--text-muted);
    font-size: 0.8rem; padding: 2rem 0;
  }}

  @media (max-width: 600px) {{
    .header h1 {{ font-size: 1.4rem; }}
    .header .year {{ font-size: 2rem; }}
    .picks-grid {{ grid-template-columns: 1fr; }}
    .leaderboard th, .leaderboard td {{ padding: 0.5rem 0.5rem; font-size: 0.85rem; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="year">2026</div>
  <h1>PGA Championship Pool</h1>
  <div class="subtitle">Aronimink Golf Club &middot; Newtown Square, PA</div>
</div>

<div class="container">
  <div class="updated">Last updated: {updated}</div>
  <div class="{banner_class}">{banner_text}</div>

{'''  <div class="commentary">
    <h2>"Glory's last shot..."</h2>
    <p>
      Under the Pennsylvania skies at Aronimink, the Wanamaker Trophy has found its pool champion.
      <span class="champion">JJ Guajardo</span> has done it. With a portfolio anchored by
      Rory McIlroy's brilliant weekend charge and the ever-dominant Scottie Scheffler grinding
      out a top-5 finish, JJ's picks proved to be nothing short of inspired. Xander Schauffele's
      quiet Sunday move sealed the deal, a combined haul that will be very difficult to top.
    </p>
    <p>
      The rest of the field gave valiant efforts, but in the end, it was JJ's faith in
      the Fleetwood-Fitzpatrick English contingent that made all the difference.
    </p>
    <p class="jab">
      For the record, JJ's victory is purely the result of superior golf knowledge
      and has absolutely nothing to do with the fact that he also happened to run the pool,
      build the website, and calculate the payouts. Nothing at all. Move along.
    </p>
    <p class="sign-off">\\u2014 The 18th Tower, Aronimink Golf Club</p>
  </div>\n''' if use_final else ''}
  <h2 style="margin-bottom:0.75rem;">Leaderboard</h2>
  <table class="leaderboard">
    <thead>
      <tr>
        <th style="width:3rem;">#</th>
        <th>Contestant</th>
        <th class="money">{money_label} Earnings</th>
      </tr>
    </thead>
    <tbody>
"""

for r in results:
    top_class = ' class="top"' if r["rank"] <= 3 and has_data else ""
    badge = rank_badge(r["rank"]) if has_data else str(r["rank"])
    if has_data:
        best = max(r["picks"], key=lambda p: p["amount"])
        best_note = f'<span class="best-golfer">Best: {best["golfer"]}</span>' if best["amount"] > 0 else ""
    else:
        best_note = ""
    html += f"""      <tr{top_class}>
        <td>{badge}</td>
        <td><span class="contestant-name">{r['name']}</span>{best_note}</td>
        <td class="money">{fmt_money(r['total'])}</td>
      </tr>
"""

html += """    </tbody>
  </table>

  <h2 style="margin-bottom:0.75rem;">Picks</h2>
  <div class="picks-grid">
"""

for r in results:
    html += f"""    <div class="pick-card">
      <div class="pick-card-header">
        <span><span class="rank-num">{r['rank']}</span><span class="name">{r['name']}</span></span>
        <span class="total">{fmt_money(r['total'])}</span>
      </div>
      <table>
"""
    for p in r["picks"]:
        amt_class = "pick-amt has-earnings" if p["amount"] > 0 else "pick-amt"
        pos_html = pos_badge(p["position"])
        sc = score_display(p["score"], p["today"])
        sc_class = "score under-par" if p.get("score", "").startswith("-") else "score"
        html += f'        <tr><td class="golfer-name">{pos_html}{p["golfer"]}</td>'
        if use_projected or use_final:
            html += f'<td class="{sc_class}">{sc}</td>'
        html += f'<td class="{amt_class}">{fmt_money(p["amount"])}</td></tr>\n'
    html += """      </table>
    </div>
"""

html += f"""  </div>

  <div class="footer">
    {len(entries)} contestants &middot; 5 picks each &middot; highest combined earnings wins<br>
    {"Projected earnings based on current leaderboard position and $19M purse" if use_projected else ""}
  </div>
</div>

</body>
</html>"""

out_path = os.path.join(base_dir, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved: {out_path}")
print(f"Mode: {'PROJECTED' if use_projected else 'FINAL' if use_final else 'PRE-TOURNAMENT'}")
if use_projected:
    print(f"Round: {round_info} - {round_status}")
    print(f"Top 3: {', '.join(r['name'] + ' ' + fmt_money(r['total']) for r in results[:3])}")
