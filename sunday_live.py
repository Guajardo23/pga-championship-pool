"""Sunday final round live updater.

Runs auto_update.py every 5 minutes from noon-5pm ET.
Keeps your PC awake during the window by preventing sleep via Windows API.

Usage:
    python sunday_live.py          # Runs noon-5pm ET
    python sunday_live.py --now    # Start immediately (for testing)
"""
import ctypes, subprocess, sys, os, time
from datetime import datetime, timedelta
import zoneinfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
ET = zoneinfo.ZoneInfo("America/New_York")

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
    ts = datetime.now(ET).strftime("%I:%M:%S %p ET")
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

    now_et = datetime.now(ET)
    today = now_et.date()

    if start_now:
        start_time = now_et
        end_time = now_et + timedelta(hours=5)
        print(f"Starting immediately. Will run until {end_time.strftime('%I:%M %p ET')}.")
    else:
        start_time = datetime(today.year, today.month, today.day, 12, 0, tzinfo=ET)
        end_time = datetime(today.year, today.month, today.day, 17, 0, tzinfo=ET)

        if now_et >= end_time:
            print("Past 5pm ET. Nothing to do.")
            return

        if now_et < start_time:
            wait = (start_time - now_et).total_seconds()
            print(f"Waiting until noon ET ({int(wait // 60)} minutes)...")
            print("(Your PC will stay awake.)")
            prevent_sleep()
            time.sleep(wait)

    print(f"\nLive updates every 5 minutes until {end_time.strftime('%I:%M %p ET')}.")
    print("Press Ctrl+C to stop early.\n")

    prevent_sleep()
    try:
        while datetime.now(ET) < end_time:
            run_update()
            next_run = datetime.now(ET) + timedelta(seconds=interval)
            if next_run >= end_time:
                break
            wait = (next_run - datetime.now(ET)).total_seconds()
            if wait > 0:
                next_str = next_run.strftime("%I:%M:%S %p")
                print(f"Next update at {next_str} ET...")
                time.sleep(wait)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        allow_sleep()
        print("Done. Sleep prevention removed.")


if __name__ == "__main__":
    main()
