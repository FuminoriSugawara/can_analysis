import can
import struct
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict, deque
import threading
import signal
import time
import colorsys

# Configuration
CAN_CHANNEL = 'can0'
CAN_BITRATE = 1_000_000  # 1Mbps
CAN_DATA_BITRATE = 5_000_000  # 5Mbps
TIME_WINDOW = 10  # Time window to display (in seconds)
ANGLE_CONVERSION_FACTOR = 10000  # Factor to convert raw value to angle
COMMAND_ID_RANGE_START = 0x201  # Hexadecimal 201
COMMAND_ID_RANGE_END = 0x2FF  # Hexadecimal 2FF
POSITION_ID_RANGE_START = 0x101  # Hexadecimal 101
POSITION_ID_RANGE_END = 0x1FF  # Hexadecimal 1FF
Y_AXIS_MIN = -90  # Minimum angle for Y-axis
Y_AXIS_MAX = 90   # Maximum angle for Y-axis
UPDATE_INTERVAL = 50  # Milliseconds between plot updates
MAX_DATA_POINTS = 1000  # Maximum number of data points to store (100 per second for 10 seconds)
NUM_SUBPLOTS = 7  # Number of subplots to display

def setup_can_interface():
    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL,
                                interface='socketcan',
                                fd=True,
                                bitrate=CAN_BITRATE,
                                data_bitrate=CAN_DATA_BITRATE)
        print(f"Successfully configured {CAN_CHANNEL} for CANFD")
        print(f"Bitrate: {CAN_BITRATE / 1_000_000}Mbps, Data Bitrate: {CAN_DATA_BITRATE / 1_000_000}Mbps")
        return bus
    except can.CanError as e:
        print(f"Error setting up CAN interface: {e}")
        return None

def parse_int32(data):
    return struct.unpack('<i', data)[0]  # Assuming little-endian

def value_to_angle(value):
    return value / ANGLE_CONVERSION_FACTOR

def generate_complementary_colors(n):
    hsv_colors = [(i / n, 0.8, 0.9) for i in range(n)]
    rgb_colors = [colorsys.hsv_to_rgb(*hsv) for hsv in hsv_colors]
    complementary_colors = [colorsys.hsv_to_rgb((h + 0.5) % 1, s, v) for h, s, v in hsv_colors]
    return list(zip(rgb_colors, complementary_colors))

class CANPlotter:
    def __init__(self):
        self.data = defaultdict(lambda: {'timestamps': deque(maxlen=MAX_DATA_POINTS), 
                                         'angles': deque(maxlen=MAX_DATA_POINTS)})
        self.start_time = None
        self.last_position = {}  # Store the last position for each ID
        self.latest_timestamp = 0  # Store the latest timestamp from CAN messages

        # Generate complementary colors for each ID pair
        num_pairs = COMMAND_ID_RANGE_END - COMMAND_ID_RANGE_START + 1
        self.color_pairs = generate_complementary_colors(num_pairs)

        # Set up the plot
        self.fig, self.axes = plt.subplots(NUM_SUBPLOTS, 1, figsize=(12, 4*NUM_SUBPLOTS), sharex=True)
        self.fig.suptitle(f'Real-time Angle Values')
        self.scatters = defaultdict(dict)

        for i, ax in enumerate(self.axes):
            ax.set_ylabel(f'Angle (degrees)\nID {i+1}')
            ax.set_ylim(Y_AXIS_MIN, Y_AXIS_MAX)
            ax.grid(True)

            command_id = COMMAND_ID_RANGE_START + i
            position_id = POSITION_ID_RANGE_START + i

            self.scatters[command_id] = ax.scatter([], [], facecolors='none', edgecolors='red', marker='o', s=20, label=f'Command 0x{command_id:X}')
            self.scatters[position_id] = ax.scatter([], [], facecolors='none', edgecolors='blue', marker='s', s=20, label=f'Position 0x{position_id:X}')
            ax.legend(loc='upper left')

        self.axes[-1].set_xlabel('Time (s)')

        self.data_lock = threading.Lock()
        self.running = True
        self.animation = None

    def update_plot(self, frame):
        with self.data_lock:
            if not any(self.data.values()):
                return []
            
            updated_scatters = []
            for i in range(NUM_SUBPLOTS):
                command_id = COMMAND_ID_RANGE_START + i
                position_id = POSITION_ID_RANGE_START + i

                for id in [command_id, position_id]:
                    if id in self.data:
                        visible_data = [(t - self.latest_timestamp, a) for t, a in zip(self.data[id]['timestamps'], self.data[id]['angles']) if t > self.latest_timestamp - TIME_WINDOW]
                        if visible_data:
                            timestamps, angles = zip(*visible_data)
                            self.scatters[id].set_offsets(list(zip(timestamps, angles)))
                            updated_scatters.append(self.scatters[id])
                        else:
                            self.scatters[id].set_offsets([])

            for ax in self.axes:
                ax.set_xlim(-TIME_WINDOW, 0)

            return updated_scatters

    def receive_can_messages(self, bus):
        while self.running:
            try:
                message = bus.recv(0.1)  # Non-blocking receive with timeout
                if message:
                    current_time = time.time()
                    if self.start_time is None:
                        self.start_time = current_time

                    relative_time = current_time - self.start_time
                    self.latest_timestamp = relative_time  # Update the latest timestamp
                    
                    if COMMAND_ID_RANGE_START <= message.arbitration_id <= COMMAND_ID_RANGE_END:
                        raw_value = parse_int32(message.data)
                        angle = value_to_angle(raw_value)
                        
                        with self.data_lock:
                            self.data[message.arbitration_id]['timestamps'].append(relative_time)
                            self.data[message.arbitration_id]['angles'].append(angle)
                        
                        position_id = message.arbitration_id - COMMAND_ID_RANGE_START + POSITION_ID_RANGE_START
                        position_angle = self.last_position.get(position_id, 0)
                    
                    elif POSITION_ID_RANGE_START <= message.arbitration_id <= POSITION_ID_RANGE_END and len(message.data) >= 5:
                        if message.data[1] == 0x14:
                            if (message.arbitration_id == 0x107):
                                print(f"Received message: {message}")

                            raw_value = parse_int32(message.data[2:6])
                            angle = value_to_angle(raw_value)
                            
                            with self.data_lock:
                                self.data[message.arbitration_id]['timestamps'].append(relative_time)
                                self.data[message.arbitration_id]['angles'].append(angle)
                            
                            self.last_position[message.arbitration_id] = angle
                            command_id = message.arbitration_id - POSITION_ID_RANGE_START + COMMAND_ID_RANGE_START
                            command_angle = self.data[command_id]['angles'][-1] if self.data[command_id]['angles'] else 0
            
            except can.CanError:
                if self.running:
                    print("Error receiving CAN message")

    def run(self, bus):
        receive_thread = threading.Thread(target=self.receive_can_messages, args=(bus,))
        receive_thread.start()

        self.animation = FuncAnimation(self.fig, self.update_plot, interval=UPDATE_INTERVAL, blit=True)
        plt.show()

        self.running = False
        receive_thread.join()

    def stop(self):
        self.running = False
        if self.animation:
            self.animation.event_source.stop()
        plt.close('all')

def signal_handler(signum, frame):
    print("\nCtrl+C pressed. Stopping the program...")
    if 'plotter' in globals():
        plotter.stop()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    canfd_bus = setup_can_interface()
    if canfd_bus:
        plotter = CANPlotter()
        try:
            plotter.run(canfd_bus)
        except KeyboardInterrupt:
            pass
        finally:
            plotter.stop()
            canfd_bus.shutdown()
    print("Program exited.")