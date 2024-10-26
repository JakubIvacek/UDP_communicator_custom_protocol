# ---------  RETURN JSON HEADER FROM PACKET

# Imports
import struct
header_format = "BHHHHH"
header_size = 12  # header format 11 + 1 padding

def retrieve_header(packet):
    global header_format
    header = packet[:header_size]
    # Unpack the header to retrieve the values
    unpacked_data = struct.unpack(header_format, header)
    (header_type, sequence_number, acknowledgment_number, window_size, data_length, crc) = unpacked_data
    return {
        'header_type': header_type,
        'sequence_number': sequence_number,
        'acknowledgment_number': acknowledgment_number,
        'window_size': window_size,
        'data_length': data_length,
        'crc': crc,
    }