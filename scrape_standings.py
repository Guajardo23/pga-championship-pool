"""Scrape the PGA Championship leaderboard from ESPN API and write standings.json."""
import json, os, urllib.request, ssl

SCORES_URL = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STANDINGS_FILE = os.path.join(BASE_DIR, "standings.json")

PAR = 70  # Aronimink Golf Club championship par


def fetch_json():
    ctx = ssl.create_default_context()
    req = urllib.request.Request(SCORES_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def main():
    print("Fetching ESPN PGA Championship leaderboard...")
    data = fetch_json()

    events = data.get("events", [])
    if not events:
        print("ERROR: No events found.")
        return False

    event = events[0]
    event_name = event.get("name", "")
    print(f"Event: {event_name}")

    competitions = event.get("competitions", [])
    if not competitions:
        print("ERROR: No competition data.")
        return False

    comp = competitions[0]
    competitors = comp.get("competitors", [])
    print(f"Found {len(competitors)} players")

    if not competitors:
        print("ERROR: No players found.")
        return False

    # Determine round and status from event-level status
    event_status = event.get("status", {})
    state = event_status.get("type", {}).get("state", "pre")  # pre, in, post
    period = event_status.get("period", 0)

    # ESPN sometimes reports period=0 during play; infer from linescores
    if period == 0 and state == "in":
        for c in competitors[:5]:
            ls = c.get("linescores", [])
            if ls:
                period = max(l.get("period", 0) for l in ls)
                if period > 0:
                    break
        if period == 0:
            period = 1  # fallback to Round 1

    if state == "pre":
        round_info = "Not Started"
        status = "Not Started"
    elif state == "in":
        round_info = f"Round {period}"
        status = "In Progress"
    else:
        round_info = "Final"
        status = "Complete"

    # First pass: collect all competitor data sorted by ESPN's order field
    raw_list = []
    for c in competitors:
        athlete = c.get("athlete", {})
        name = athlete.get("displayName", "") or athlete.get("fullName", "")
        if not name:
            continue

        score = c.get("score", "")
        order = c.get("order", 999)

        # Check for cut/WD/DQ from status
        c_status = c.get("status", {})
        c_type = c_status.get("type", {})
        c_state_name = c_type.get("name", "")
        special = ""
        if c_state_name in ("STATUS_CUT",):
            special = "MC"
        elif c_state_name in ("STATUS_WD",):
            special = "WD"
        elif c_state_name in ("STATUS_DQ",):
            special = "DQ"

        # ESPN doesn't always flag MC via status; detect via linescore count.
        # If we're in round 3+ and a player only has 2 rounds, they missed the cut.
        linescores = c.get("linescores", [])
        if not special and period >= 3 and len(linescores) < period:
            special = "MC"
        elif c_state_name in ("STATUS_WD",):
            special = "WD"
        elif c_state_name in ("STATUS_DQ",):
            special = "DQ"

        # Also check position from status if available
        pos_data = c_status.get("position", {})
        status_pos = pos_data.get("displayName", "") if pos_data else ""

        # Thru
        thru = c_status.get("thru", "")
        if isinstance(thru, int):
            if thru == 18:
                thru = "F"
            elif thru == 0 and state != "pre":
                thru = ""
            else:
                thru = str(thru)
        else:
            thru = str(thru) if thru else ""

        # Today: compute from linescores for the current round
        today = ""
        linescores = c.get("linescores", [])
        if period > 0 and linescores:
            for ls in linescores:
                if ls.get("period") == period and "value" in ls:
                    val = ls["value"]
                    if thru == "F":
                        today_num = val - PAR
                        if today_num > 0:
                            today = f"+{today_num}"
                        elif today_num == 0:
                            today = "E"
                        else:
                            today = str(today_num)
                    break

        raw_list.append({
            "name": name, "score": score, "order": order,
            "special": special, "status_pos": status_pos,
            "today": today, "thru": thru,
        })

    # Sort by ESPN order (leaderboard rank)
    raw_list.sort(key=lambda x: x["order"])

    # Second pass: compute positions with ties using score grouping
    # Group by score to detect ties
    from collections import Counter
    score_counts = Counter(p["score"] for p in raw_list if not p["special"])
    score_to_rank = {}
    rank = 1
    seen_scores = []
    for p in raw_list:
        if p["special"]:
            continue
        sc = p["score"]
        if sc not in score_to_rank:
            score_to_rank[sc] = rank
        rank += 1

    golfers = {}
    for p in raw_list:
        if p["special"]:
            position = p["special"]
        elif p["status_pos"]:
            position = p["status_pos"]
        elif state != "pre" and p["score"]:
            r = score_to_rank.get(p["score"], p["order"])
            cnt = score_counts.get(p["score"], 1)
            if cnt > 1:
                position = f"T{r}"
            else:
                position = str(r)
        else:
            position = ""

        golfers[p["name"]] = {
            "position": position,
            "score": p["score"],
            "today": p["today"],
            "thru": p["thru"],
        }

    standings = {
        "tournament": "PGA Championship",
        "round": round_info,
        "status": status,
        "golfers": golfers,
    }

    with open(STANDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(standings, f, indent=4, ensure_ascii=False)

    print(f"Saved: {STANDINGS_FILE}")
    print(f"Round: {round_info} - {status}")

    # Show pool-relevant golfers
    pool_golfers = [
        "Scottie Scheffler", "Rory McIlroy", "Xander Schauffele", "Tommy Fleetwood",
        "Matt Fitzpatrick", "Jon Rahm", "Brooks Koepka", "Cameron Young",
        "Collin Morikawa", "Tyrrell Hatton", "Ludvig Åberg", "Jacob Bridgeman",
        "Alex Fitzpatrick", "Rickie Fowler",
    ]
    print("\nPool golfer positions:")
    for name in pool_golfers:
        g = golfers.get(name, {})
        pos = g.get("position", "") or "\u2014"
        sc = g.get("score", "") or ""
        th = g.get("thru", "") or ""
        print(f"  {name:25s}  {pos:6s}  {sc:5s}  thru {th}")

    return True


if __name__ == "__main__":
    main()
