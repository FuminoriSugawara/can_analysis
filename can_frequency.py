import sys
import time
from collections import deque

def calculate_average_interval():
    intervals = deque()
    last_timestamp = None
    current_second = int(time.time())
    next_print_time = current_second + 1

    print("Calculating average CAN bus message interval using system time. Press Ctrl+C to stop.")
    print("Time (s) | Avg Interval (ms)")
    print("----------------------------")

    try:
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                continue

            current_time = time.time()
            current_second = int(current_time)
            
            if last_timestamp is not None:
                interval = (current_time - last_timestamp) * 1000  # Convert to milliseconds
                intervals.append(interval)
            
            if current_second >= next_print_time:
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"{current_second-1:<9} | {avg_interval:>14.3f}")
                else:
                    print(f"{current_second-1:<9} | {'N/A':>14}")
                
                intervals.clear()
                next_print_time = current_second + 1
            
            last_timestamp = current_time
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

if __name__ == "__main__":
    calculate_average_interval()