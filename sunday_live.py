"""Sunday final round live updater.

Runs auto_update.py every 5 minutes until 5pm PT.
Keeps your PC awake during the window by preventing sleep via Windows API.

Usage:
    python sunday_live.py          # Runs noon-5pm PT
    python sunday_live.py --now    # Start immediately, runs until 5pm PT
"""
import ctypes, subprocess, sys, os, time
from datetime import datetime, timedelta
import zoneinfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
PT = zoneinfo.ZoneInfo("America/Los_Angeles")

# Windows sleep prevention
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def prevent_sleep():
    """Tell Windows not to sleep."""
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    print("[POWER] Sleep prevention enabled.")


def allow_sleep():
    """Restore normal sleep behavior."""
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print("[POWER] Sleep prevention disabled.")


def run_update():
    ts = datetime.now(PT).strftime("%I:%M:%S %p PT")
    print(f"\n[{ts}] Running update...")
    result = subprocess.run(
        [PYTHON, os.path.join(BASE_DIR, "auto_update.py")],
        capture_output=True, text=True, cwd=BASE_DIR, timeout=120
    )
    if result.returncode == 0:
        print(f"[{ts}] Update complete.")
    else:
        print(f"[{ts}] Update failed: {result.stderr[:200]}")


def main():
    start_now = "--now" in sys.argv
    interval = 300  # 5 minutes

    now_pt = datetime.now(PT)
    today = now_pt.date()

    # Always end at 5pm PT
    end_time = datetime(today.year, today.month, today.day, 17, 0, tzinfo=PT)

    if now_pt >= end_time:
        print("Past 5pm PT. Nothing to do.")
        return

    if start_now:
        start_time = now_pt
        print(f"Starting immediately. Will run until {end_time.strftime('%I:%M %p PT')}.")
    else:
        start_time = datetime(today.year, today.month, today.day, 9, 0, tzinfo=PT)

        if now_pt < start_time:
            wait = (start_time - now_pt).total_seconds()
            print(f"Waiting until 9am PT ({int(wait // 60)} minutes)...")
            print("(Your PC will stay awake.)")
            prevent_sleep()
            time.sleep(wait)

    print(f"\nLive updates every 5 minutes until {end_time.strftime('%I:%M %p PT')}.")
    print("Press Ctrl+C to stop early.\n")

    prevent_sleep()
    try:
        while datetime.now(PT) < end_time:
            run_update()
            next_run = datetime.now(PT) + timedelta(seconds=interval)
            if next_run >= end_time:
                break
            wait = (next_run - datetime.now(PT)).total_seconds()
            if wait > 0:
                next_str = next_run.strftime("%I:%M:%S %p")
                print(f"Next update at {next_str} PT...")
                time.sleep(wait)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        allow_sleep()
        print("Done. Sleep prevention removed.")


if __name__ == "__main__":
    main()
