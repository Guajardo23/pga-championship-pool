"""Auto-update: scrape standings, regenerate site, and optionally git push."""
import subprocess, sys, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
LOG_FILE = os.path.join(BASE_DIR, "update_log.txt")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or BASE_DIR, timeout=60)
    if result.returncode != 0:
        log(f"  WARN: {' '.join(cmd)} returned {result.returncode}: {result.stderr.strip()[:200]}")
    return result.returncode == 0


def main():
    log("=== PGA Championship Pool Auto-Update ===")

    # Step 1: Scrape
    log("Scraping standings...")
    ok = run([PYTHON, os.path.join(BASE_DIR, "scrape_standings.py")])
    if not ok:
        log("Scrape failed. Aborting.")
        return

    # Step 2: Generate site
    log("Generating site...")
    ok = run([PYTHON, os.path.join(BASE_DIR, "generate_site.py")])
    if not ok:
        log("Site generation failed. Aborting.")
        return

    # Step 3: Git push (if repo is set up)
    git_dir = os.path.join(BASE_DIR, ".git")
    if os.path.exists(git_dir):
        log("Git repo found. Committing and pushing...")
        run(["git", "add", "index.html", "standings.json"])
        ts = datetime.now().strftime("%b %d %I:%M %p")
        run(["git", "commit", "-m", f"Update standings: {ts}"])
        ok = run(["git", "push"])
        if ok:
            log("Pushed to GitHub.")
        else:
            log("Git push failed (check credentials).")
    else:
        log("No git repo found. Skipping push. Set up repo to enable auto-push.")

    log("Done.\n")


if __name__ == "__main__":
    main()
