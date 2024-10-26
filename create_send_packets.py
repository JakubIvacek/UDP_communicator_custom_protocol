# ---------  PACKETS SENT FUNCTIONS

import struct
header_format = "BHHHHH"

# ---- SEND PACKET WITH DATA
def send_packet_data(type_header, socket_your, address_port_sending, sequence_number, acknowledgment_number,
                     window_size, data_length, crc, data):
    global header_format
    header = struct.pack(header_format, type_header, sequence_number, acknowledgment_number, window_size, data_length, crc)
    if isinstance(data, bytes):
        encoded_data = data
    else:
        encoded_data = data.encode()  # Convert string to bytes

    # Send the header and data together
    socket_your.sendto(header + encoded_data, address_port_sending)

# ---- SEND ONLY INFORMATION PACKET WITHOUT DATA
def send_info_packet_type_only(type_header, socket_your, address_port_sending):
    global header_format
    header = struct.pack(header_format, type_header, 0, 0, 0, 0, 0)
    socket_your.sendto(header, address_port_sending)  # send type info message