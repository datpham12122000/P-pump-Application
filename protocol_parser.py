import struct

default_frame_length = 8

def set_target_pressure(target_pressure : float, node_id : int) -> bytes:
    command = [0x6,0x05,0x07, node_id,]
    return bytes(command) + struct.pack('<f', target_pressure)

def set_manual_mode_adjust(node_id,manual_mode:bool) -> bytes:
    command = [0x6,node_id,0x9 if manual_mode else 0xB,0x0,0x0,0x0,0x0,0x0]
    return bytes(command)

def set_valve(node_id: int , valve_status:int) -> bytes:
    command = [0x6,node_id,0xF,valve_status,0x00,0x00,0x00,0x00]
    return bytes(command)

def sending_type_command(node_id: int , sending_type:int,cycle:int) -> bytes:
    command = [0x6,node_id,0xD,sending_type,(cycle >> 8) & 0xFF,cycle & 0xFF,0x00,0x00]
    return bytes(command)

def get_data_from_frame(frame: bytes) -> tuple:
    # Atmosphere pressure sent to host
    print(frame.hex())
    if frame[0] == 0x08:
        return "AtmospherePressure", struct.unpack('<f', frame[1:5])[0]
    elif frame[0] == 0x09:
        return "SupplyPressure", struct.unpack('<f', frame[1:5])[0]
    elif frame[0] == 0x10:
        return "NodePressure", frame[1], struct.unpack('<f', frame[2:6])[0]
    elif frame[0] == 0x03:
        return "NodePressureInDevelopment", frame[1], struct.unpack('<f', frame[2:6])[0]
    elif frame[0] == 0x07:
        if frame[2] == 0x09:
            return "ManualModeEnter",frame[3]
        if frame[2] == 0x0B:
            return "ManualModeExit",frame[3]
        if frame[2] == 0x0F:
            return "ValveFeedback",frame[3]
    return "UnknownInformation",0,0
    
    
