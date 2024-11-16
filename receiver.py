
# Data receive over udp with own SELECTIVE REPEAT ARQ implementation

# Imports
import binascii, time, socket, os
from anyio import sleep

from header_to_json import retrieve_header
from create_send_packets import send_packet_data
from create_send_packets import send_info_packet_type_only
from globals import *
from print_transfer_information import print_transfer_info_file,  print_transfer_info_message

def data_receive(socket_your, address_port_sending, file_bool):
    count_no_signal = 0
    received_successfully = False
    while count_no_signal < 3 and not received_successfully:
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
            # MAIN RECEIVING LOOP
            parts, fragment_size = receiver_selective_repeat_arq(fragment_count, socket_your, address_port_sending, file_bool)

            end_time = time.time()
            transfer_time = end_time - start_time
            if not file_bool:
                # Print information about message received
                message = "".join(parts)
                print_transfer_info_message(message, fragment_size)
            else:
                # Get path where to send, and save file
                decoded_file_name = "1" + decoded_file_name # FOR TESTING ADDING 1 TO NAME
                while True:
                    file_path = input("Enter path where to save C:/.../  or (yes) to receive in working directory: ")
                    # Check if the user chose the working directory
                    if file_path.lower() == "yes":
                        break
                    # Check if dir exists
                    elif os.path.exists(os.path.dirname(file_path)):
                        break
                    else:
                        print("Invalid path. Please enter a valid directory path or 'yes' to use the working directory.")
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
            received_successfully = True
            print(f"Data transfer completed in {transfer_time:.3f} seconds")
        except socket.timeout:
            print("Timeout, no response. Retrying...")
        except ConnectionResetError:
            count_no_signal += 1
            print(f"No connection on {address_port_sending}.")
            sleep(5)
        except socket.gaierror as e:
            print(f"Error occurred: {e}")
    if count_no_signal == 3:
        print("Exit 3 times no respond Turning off")
    if received_successfully:
        print("Exit File transfer end")

# Main sending loop returns packets in right order and size of fragment
def receiver_selective_repeat_arq(fragment_count, socket_your, address_port_sending, file_bool):
    parts = [None] * fragment_count
    received = [False] * fragment_count
    parts = [None] * fragment_count
    fragment_size = 0
    count_no_signal = 0
    window_size = 29
    # --- MAIN LOOP
    while count_no_signal < 3 and not all(received):
        try:
            while True:
                # --- RECEIVE PACKET
                packet, _ = socket_your.recvfrom(1500)
                header = retrieve_header(packet)
                crc = header.get("crc")
                data = packet[header_size:]
                seq_num = header.get("packet_number")
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
                        send_packet_data(2, socket_your, address_port_sending, seq_num, 0, crc, "")
                else:
                    # --- RECEIVED WRONG NACK SEND
                    print("Packet : " + str(seq_num + 1) + "  received wrong SENDING NACK:", address_port_sending)
                    send_packet_data(7, socket_your, address_port_sending, seq_num, 0, crc, "")
                if all(received):
                    break
        except ConnectionResetError:
            count_no_signal += 1
            print(f"No connection by {address_port_sending}.")
            sleep(5)
        except socket.timeout:
            print("Timeout, no response KA. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred KA: {e}")
    if count_no_signal == 3:
        print("Exit 3 times no respond Turning off")
    if all(received):
        print("All packets received OKAY")
    return parts, fragment_size