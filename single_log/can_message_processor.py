import can
import struct
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ServoMessageResponse:
    command_id: int
    module_id: int
    timestamp: float
    current: int
    velocity: int
    position: int
    error: int

@dataclass
class CommandMessageResponse:
    command_id: int
    module_id: int
    timestamp: float
    value: int

class CANMessageProcessor:
    def __init__(self):
        self.command_responses: List[CommandMessageResponse] = []
        self.servo_responses: List[ServoMessageResponse] = []

    @staticmethod
    def parse_int32(data: bytes) -> int:
        return struct.unpack('<i', data)[0]
    
    @staticmethod
    def parse_uint16(data: bytes) -> int:
        return struct.unpack('<H', data)[0]
    
    def process_command_message(self, message: can.Message) -> Optional[CommandMessageResponse]:
        if len(message.data) < 4:
            return None
        command_id = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0x00FF
        value = self.parse_int32(message.data[:4])
        response = CommandMessageResponse(command_id, module_id, message.timestamp, value)
        self.command_responses.append(response)
        return response

    def process_servo_message(self, message: can.Message) -> Optional[ServoMessageResponse]:
        if len(message.data) != 16:
            return None
        command_id = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0x00FF
        current = self.parse_int32(message.data[0:4])
        velocity = self.parse_int32(message.data[4:8])
        position = self.parse_int32(message.data[8:12])
        error = self.parse_uint16(message.data[14:16])
        response = ServoMessageResponse(command_id, module_id, message.timestamp, current, velocity, position, error)
        self.servo_responses.append(response)
        return response

    def save_to_csv(self, command_file: str = 'command_responses.csv', servo_file: str = 'servo_responses.csv'):
        def process_responses(responses):
            data = [asdict(r) for r in responses]
            for item in data:
                item['command_id'] = f"0x{item['command_id']:X}"
            return data

        command_df = pd.DataFrame(process_responses(self.command_responses))
        servo_df = pd.DataFrame(process_responses(self.servo_responses))
        
        command_df.to_csv(command_file, index=False)
        servo_df.to_csv(servo_file, index=False)

    def clear_responses(self):
        self.command_responses.clear()
        self.servo_responses.clear()