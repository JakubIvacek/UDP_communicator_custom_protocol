
# Data transfer over udp with own SELECTIVE REPEAT ARQ implementation

# Imports
import binascii, time, socket, os
from header_to_json import retrieve_header
from create_send_packets import send_packet_data
from create_send_packets import send_info_packet_type_only
from globals import *
from print_transfer_information import print_transfer_info_file,  print_transfer_info_message

def data_receive(socket_your, address_port_sending, file_bool):
    try:
        # Initiate transfer information
        print("\nFile,Message   transfer started")
        print("Sending '2' = ACK ", "\n")
        socket_your.settimeout(120)
        send_info_packet_type_only(2, socket_your, address_port_sending) # Sent ACK
        while True:
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            if header.get("header_type") == 6 and data[header_size:].decode() != "":  # Data packet
                break
        # Receive transfer information
        start_time = time.time()
        if file_bool:
            file_name = data[header_size:]
            decoded_file_name = file_name.decode()
            print("First data packet arrived. Filename : ", decoded_file_name)
            data, _ = socket_your.recvfrom(1500)
            fragment_count = int(data[header_size:].decode())
        else:
            fragment_count = int(data[header_size:].decode())
        # MAIN SENDING LOOP
        parts, fragment_size = sender_selective_repeat_arq(fragment_count, socket_your, address_port_sending, file_bool)

        end_time = time.time()
        transfer_time = end_time - start_time
        if not file_bool:
            # Print information about message received
            message = "".join(parts)
            print_transfer_info_message(message, fragment_size)
        else:
            # Get path where to send, and save file
            decoded_file_name = "1" + decoded_file_name # FOR TESTING ADDING 1 TO NAME
            file_path = input("Enter path where to save C:/.../  or (yes) to receive in working directory: ")
            if file_path == "yes":
                path = decoded_file_name
            else:
                path = file_path + "\\" + decoded_file_name
            with open(path, 'wb') as file_write:
                for part in parts:
                    file_write.write(part)
            # Print information about the transfer
            file_size = os.path.getsize(path)
            file_write.close()
            file_in = open(path, 'rb')
            print_transfer_info_file(file_in, decoded_file_name, path, fragment_size, file_size)
            file_in.close()
        print(f"Data transfer completed in {transfer_time:.3f} seconds")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except ConnectionResetError:
        print(f"No connection on {address_port_sending}.")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")

# Main sending loop returns packets in right order and size of fragment
def sender_selective_repeat_arq(fragment_count, socket_your, address_port_sending, file_bool):
    parts = [None] * fragment_count
    received = [False] * fragment_count
    parts = [None] * fragment_count
    fragment_size = 0
    # --- MAIN LOOP
    while True:
        # --- RECEIVE PACKET
        packet, _ = socket_your.recvfrom(1500)
        header = retrieve_header(packet)
        crc = header.get("crc")
        data = packet[header_size:]
        seq_num = header.get("sequence_number")
        window_size = header.get("window_size")
        if fragment_size == 0: fragment_size = header.get("data_length")

        # --- CHECK CRC AND ACK OR NACK
        crc_check = binascii.crc_hqx(data, 0)
        if crc_check == crc:
            # --- RECEIVED CORRECT ACK SEND
            print("Packet : " + str(seq_num + 1) + "  received okay SENDING ACK:", address_port_sending)
            # STORE IN CORRECT ORDER PACKET
            if not received[seq_num]:
                if file_bool:
                    parts[seq_num] = data
                else:
                    parts[seq_num] = data.decode()
                received[seq_num] = True  # Mark the packet as received
                send_packet_data(2, socket_your, address_port_sending, 0,
                                 seq_num, window_size, 0, 0, "")
        else:
            # --- RECEIVED WRONG NACK SEND
            print("Packet : " + str(seq_num + 1) + "  received wrong SENDING NACK:", address_port_sending)
            send_packet_data(7, socket_your, address_port_sending, 0,
                             seq_num, window_size, 0, 0, "")
        if all(received):
            break
    print("File,Message received okay. \n")
    return parts, fragment_size