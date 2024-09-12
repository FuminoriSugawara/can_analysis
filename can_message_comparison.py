
import sys
import time
import re
from collections import defaultdict

def compare_messages():
    control_count = defaultdict(int)
    motor_count = defaultdict(int)
    debug_count = defaultdict(int)
    current_second = int(time.time())
    next_print_time = current_second + 1

    # 正規表現パターンを定義
    control_pattern = re.compile(r'can0 (00[1-7]|20[1-7]|30[1-7]|40[1-7])')
    motor_pattern = re.compile(r'can0 (10[1-7]|50[1-7])')
    debug_pattern = re.compile(r'can0 700')

    print("-----------------------------------------------------------------------------------------------------------")
    print("Comparing control commands (001-007, 201-207, 301-307, 401-407), motor responses (101-107, 501-507), and debug output (700) messages.")
    print("Time (s) | Control (001-007, 201-207, 301-307, 401-407) | Motor (101-107, 501-507) | Debug (700) | Match?")
    print("-----------------------------------------------------------------------------------------------------------")

    try:
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                continue

            current_time = time.time()
            current_second = int(current_time)

            if control_pattern.search(line):
                control_count[current_second] += 1
            elif motor_pattern.search(line):
                motor_count[current_second] += 1
            elif debug_pattern.search(line):
                debug_count[current_second] += 1

            if current_second >= next_print_time:
                prev_second = current_second - 1
                control_msgs = control_count[prev_second]
                motor_msgs = motor_count[prev_second]
                debug_msgs = debug_count[prev_second]
                match = "Yes" if control_msgs == motor_msgs == debug_msgs else "No"

                print(f"{prev_second:<9} | {control_msgs:^27} | {motor_msgs:^25} | {debug_msgs:^11} | {match:^6}")

                # Clear old data
                if prev_second - 1 in control_count:
                    del control_count[prev_second - 1]
                    del motor_count[prev_second - 1]
                    del debug_count[prev_second - 1]

                next_print_time = current_second + 1

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

if __name__ == "__main__":
    compare_messages()