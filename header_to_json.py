# ---------  RETURN JSON HEADER FROM PACKET

# Imports
import struct
header_format = "BHHH"
header_size = 8  # header format 7 + 1 padding

def retrieve_header(packet):
    global header_format
    header = packet[:header_size]
    # Unpack the header to retrieve the values
    unpacked_data = struct.unpack(header_format, header)
    (header_type, packet_number, data_length, crc) = unpacked_data
    return {
        'header_type': header_type,
        'packet_number': packet_number,
        'data_length': data_length,
        'crc': crc,
    }