import can
import time
from can_message_processor import CANMessageProcessor

# Configuration
# CAN settings
CAN_CHANNEL = 'can0'
CAN_BITRATE = 1_000_000  # 1Mbps
CAN_DATA_BITRATE = 5_000_000  # 5Mbps

# CAN message filter settings
COMMAND_ID_BASE = 0x200
CONTROL_RESPONSE_ID_BASE = 0x500
MODULE_ID_MASK = 0xFF

def setup_can_interface():
    try:
        filters = [
            {"can_id": COMMAND_ID_BASE, "can_mask": 0xFF00, "extended": False},
            {"can_id": CONTROL_RESPONSE_ID_BASE, "can_mask": 0xFF00, "extended": False}
        ]
        bus = can.interface.Bus(channel=CAN_CHANNEL,
                                interface='socketcan',
                                fd=True,
                                bitrate=CAN_BITRATE,
                                data_bitrate=CAN_DATA_BITRATE,
                                can_filters=filters)
        print(f"Successfully configured {CAN_CHANNEL} for CANFD")
        print(f"Bitrate: {CAN_BITRATE / 1_000_000}Mbps, Data Bitrate: {CAN_DATA_BITRATE / 1_000_000}Mbps")
        return bus
    except can.CanError as e:
        print(f"Error setting up CAN interface: {e}")
        return None

def main():
    bus = setup_can_interface()
    if bus is None:
        return

    processor = CANMessageProcessor()
    print(f"Started logging at {processor.start_time}")
    
    try:
        start_time = time.time()
        while time.time() - start_time < 60:  # Run for 60 seconds
            message = bus.recv(1.0)  # Wait up to 1 second for a message
            if message is None:
                continue
            
            command_id = message.arbitration_id & 0xFF00
            module_id = message.arbitration_id & MODULE_ID_MASK
            
            if command_id == COMMAND_ID_BASE:
                response = processor.process_command_message(message)
                if response:
                    print(f"Processed command message: Command ID=0x{response.command_id:X}, Module ID={response.module_id}, Value={response.value}")
            elif command_id == CONTROL_RESPONSE_ID_BASE:
                response = processor.process_servo_message(message)
                if response:
                    print(f"Processed servo message: Command ID=0x{response.command_id:X}, Module ID={response.module_id}, Position={response.position}")
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        try:
            processor.save_to_csv(output_dir='can_output')
            print(f"Data saved to CSV files in 'can_output' directory with timestamp {processor.start_time}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
        
        if bus:
            bus.shutdown()
            print("CAN bus shut down")

if __name__ == "__main__":
    main()