#---------
#---- PRINT INFORMATION ABOUT TRANSFER
# ---------
import math

# --- READ FILE , AND PRINT TRANSFER INFORMATION
# ---
# ----- FILENAME - PATH - FRAGMENT COUNT - FRAGMENT SIZE - LAST FRAGMENT SIZE
def print_transfer_info_file(file_in, file_name, path, fragment_size, file_size):
    packets_number = math.ceil(file_size / fragment_size)
    last_fragment_size = file_size % fragment_size
    string_to_send = file_in.read()
    print("File to send : " + file_name + "  " + str(file_size) + " B")
    print("File path: " + path)
    print("Fragment count: " + str(packets_number))
    print_fragment_info(len(string_to_send), fragment_size, last_fragment_size)
    return string_to_send, packets_number

# --- PRINT TRANSFER INFORMATION MESSAGE
# ---
# ----- MESSAGE ->   STRING_SENDING - SIZE  - FRAGMENT SIZE - LAST FRAGMENT SIZE
def print_transfer_info_message(string_to_send, fragment_size):
    string_size = len(string_to_send)
    packets_number = math.ceil(string_size / fragment_size)
    last_fragment_size = string_size % fragment_size
    print("String to send : " + string_to_send)
    print("String size : " + str(string_size) + " B")
    print_fragment_info(len(string_to_send), fragment_size, last_fragment_size)
    return packets_number

# ---
# --- PRINT FRAGMENT
def print_fragment_info(string_to_send_len, fragment_size, last_fragment_size):
    if string_to_send_len < fragment_size:
        print("Fragment size: " + str(string_to_send_len))
    else:
        print("Fragment size: " + str(fragment_size))
    if last_fragment_size > 0 and last_fragment_size != fragment_size:
        print("Last fragment size: " + str(string_to_send_len % fragment_size))

