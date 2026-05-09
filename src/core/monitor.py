import time
import os
import re

LOG_FILE = "tokflare.log"

def analyze_logs():
    if not os.path.exists(LOG_FILE):
        print("Waiting for log file...")
        return

    print("--- TokFlare Live Monitoring Panel ---")
    print("Press Ctrl+C to stop (if running in foreground)")
    
    with open(LOG_FILE, "r") as f:
        # Go to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            
            # Simple Analysis
            if "ERROR" in line:
                print(f"🚨 ERROR: {line.strip()}")
            elif "New user registered" in line:
                user_id = re.search(r"registered: (\d+)", line)
                print(f"👤 NEW USER: {user_id.group(1) if user_id else 'Unknown'}")
            elif "Received update" in line:
                # Silently log interactions for summary
                pass
            elif "INFO" in line:
                print(f"ℹ️ {line.strip()}")

if __name__ == "__main__":
    try:
        analyze_logs()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
