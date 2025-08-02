import struct

default_frame_length = 8

def set_target_pressure(target_pressure : float, node_id : int) -> bytes:
    command = [0x11,0x05,0x07, node_id,]
    return bytes(command) + struct.pack('<f', target_pressure)

def get_data_from_frame(frame: bytes) -> tuple:
    # Atmosphere pressure sent to host
    print(frame.hex())
    if frame[0] == 0x08:
        return "AtmospherePressure", struct.unpack('<f', frame[1:5])[0]
    elif frame[0] == 0x09:
        return "SupplyPressure", struct.unpack('<f', frame[1:5])[0]
    elif frame[0] == 0x10:
        return "NodePressure", frame[1], struct.unpack('<f', frame[2:6])[0]
    
    
