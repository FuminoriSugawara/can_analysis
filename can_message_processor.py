import can
import struct
import pandas as pd
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import os
from datetime import datetime

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
        self.command_responses: Dict[int, List[CommandMessageResponse]] = {}
        self.servo_responses: Dict[int, List[ServoMessageResponse]] = {}
        self.start_time: str = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        
        if module_id not in self.command_responses:
            self.command_responses[module_id] = []
        self.command_responses[module_id].append(response)
        
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
        
        if module_id not in self.servo_responses:
            self.servo_responses[module_id] = []
        self.servo_responses[module_id].append(response)
        
        return response

    def save_to_csv(self, output_dir: str = 'output'):
        os.makedirs(output_dir, exist_ok=True)

        def process_responses(responses):
            data = [asdict(r) for r in responses]
            for item in data:
                item['command_id'] = f"0x{item['command_id']:X}"
            return data

        # Save command responses
        for module_id, responses in self.command_responses.items():
            df = pd.DataFrame(process_responses(responses))
            filename = os.path.join(output_dir, f'{self.start_time}_command_{module_id}.csv')
            df.to_csv(filename, index=False)
            print(f"Saved command responses for module {module_id} to {filename}")

        # Save servo responses
        for module_id, responses in self.servo_responses.items():
            df = pd.DataFrame(process_responses(responses))
            filename = os.path.join(output_dir, f'{self.start_time}_servo_responses_{module_id}.csv')
            df.to_csv(filename, index=False)
            print(f"Saved servo responses for module {module_id} to {filename}")

    def clear_responses(self):
        self.command_responses.clear()
        self.servo_responses.clear()