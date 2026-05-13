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

    if state == "pre":
        round_info = "Not Started"
        status = "Not Started"
    elif state == "in":
        round_info = f"Round {period}"
        status = "In Progress"
    else:
        round_info = "Final"
        status = "Complete"

    golfers = {}
    for c in competitors:
        athlete = c.get("athlete", {})
        name = athlete.get("displayName", "") or athlete.get("fullName", "")
        if not name:
            continue

        # Overall score to par (e.g., "-4", "+2", "E")
        score = c.get("score", "")

        # Position and thru from competitor-level status (only during/after play)
        c_status = c.get("status", {})
        pos_data = c_status.get("position", {})
        position = pos_data.get("displayName", "") if pos_data else ""

        # Check for cut/WD/DQ
        c_type = c_status.get("type", {})
        c_state_name = c_type.get("name", "")
        if c_state_name in ("STATUS_CUT",):
            position = "MC"
        elif c_state_name in ("STATUS_WD",):
            position = "WD"
        elif c_state_name in ("STATUS_DQ",):
            position = "DQ"

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
                    # Only show "today" if player has finished the round
                    if thru == "F":
                        today_num = val - PAR
                        if today_num > 0:
                            today = f"+{today_num}"
                        elif today_num == 0:
                            today = "E"
                        else:
                            today = str(today_num)
                    break

        golfers[name] = {
            "position": position,
            "score": score,
            "today": today,
            "thru": thru,
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
