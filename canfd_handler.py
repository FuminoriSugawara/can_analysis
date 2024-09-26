import can
import time

def setup_can_interface(channel='can0', bitrate=1000000, data_bitrate=5000000):
    """
    Setup the CAN interface for CANFD.
    
    :param channel: The CAN interface name
    :param bitrate: The CAN arbitration bitrate
    :param data_bitrate: The CAN FD data bitrate
    :return: Configured CAN bus object
    """
    try:
        bus = can.interface.Bus(channel=channel, 
                                interface='socketcan',
                                fd=True,
                                bitrate=bitrate,
                                data_bitrate=data_bitrate)
        print(f"Successfully configured {channel} for CANFD")
        return bus
    except can.CanError as e:
        print(f"Error setting up CAN interface: {e}")
        return None

def send_canfd_message(bus, arbitration_id, data):
    """
    Send a CANFD message.
    
    :param bus: The CAN bus object
    :param arbitration_id: The CAN arbitration ID
    :param data: The data to send (up to 64 bytes for CANFD)
    """
    message = can.Message(arbitration_id=arbitration_id, 
                          data=data,
                          is_extended_id=False,
                          is_fd=True)
    try:
        bus.send(message)
        print(f"Message sent on {bus.channel_info}")
    except can.CanError as e:
        print(f"Error sending message: {e}")

def receive_canfd_messages(bus, timeout=1.0):
    """
    Receive CANFD messages.
    
    :param bus: The CAN bus object
    :param timeout: Time to wait for a message
    """
    print(f"Listening for messages on {bus.channel_info}")
    while True:
        message = bus.recv(timeout)
        if message is None:
            print("No message received")
        else:
            print(f"Received message: {message}")
            # Check if it's a CANFD message
            if message.is_fd:
                print("This is a CANFD message")
            print(f"Arbitration ID: {message.arbitration_id}")
            print(f"DLC: {message.dlc}")
            print(f"Data: {message.data}")
            print("----")

if __name__ == "__main__":
    # Setup the CAN interface
    canfd_bus = setup_can_interface()
    
    if canfd_bus:
        # Example: Send a CANFD message
        # send_canfd_message(canfd_bus, arbitration_id=0x123, data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88] * 8)  # 64 bytes of data
        
        # Start receiving messages
        receive_canfd_messages(canfd_bus)