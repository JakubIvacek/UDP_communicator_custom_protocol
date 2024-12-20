# Data transfer over udp with own SELECTIVE REPEAT ARQ implementation

# Imports
import binascii, random, socket, os
from time import sleep
import time

from header_to_json import retrieve_header
from print_transfer_information import print_transfer_info_file, print_transfer_info_message
from create_send_packets import send_packet_data
from globals import *

def data_send(socket_your, address_port_sending, file_bool):
    global user_input, max_fragment_size
    file_name = ""
    string_to_send = ""
    count_no_signal = 0
    send_successfully = False
    while count_no_signal < 3 and not send_successfully:
        try:
            # Initiate transfer information
            print("\nFile,Message transfer started")
            socket_your.settimeout(120)
            print("WAITING FOR ACK :", address_port_sending)
            while True:
                data, _ = socket_your.recvfrom(1500)
                header = retrieve_header(data)
                if header.get("header_type") == 2:  # 2 = Ack
                    break
            print("ACK RECEIVED :", address_port_sending, "\n")

            # Get User input
            if file_bool:
                while True:
                    try:
                        file_name = input("Enter file name : ")
                        path = input("Enter path where to find file C:/.../  or (yes) if in working directory: ")
                        if path == "yes":
                            path = file_name
                        else:
                            path = path + "\\" + file_name
                        file_in = open(path, "rb")
                        file_size = os.path.getsize(path)
                        break
                    except FileNotFoundError:
                        print(f"Error: The file '{path}' was not found.")
            else:
                string_to_send = input("Enter message to send : ")
            fragment_size = int(input("Enter fragment size : max 1464 :"))
            while 0 >= fragment_size or max_fragment_size < fragment_size:
                fragment_size = int(input("Enter fragment size :  max 1464 :"))
            mistake = input("Enter 1 if u want bad packet receive : ")

            # Print transfer information
            if file_bool:
                string_to_send, packets_number = print_transfer_info_file(file_in, file_name, path, fragment_size, file_size)
                file_in.close()
            else:
                packets_number = print_transfer_info_message(string_to_send, fragment_size)

            # separate data into fragments
            parts = []
            while len(string_to_send) > 0:
                if file_bool:
                    string_part = string_to_send[0:fragment_size]  # file already in bytes "rb"
                else:
                    string_part = string_to_send[0:fragment_size]
                    string_part = str.encode(string_part)  # message get part and encode
                string_to_send = string_to_send[fragment_size:]
                parts.append(string_part)

            # Send filename, fragment_count
            if file_bool:
                send_packet_data(6, socket_your, address_port_sending,  0,
                                 0, 0, file_name)
            send_packet_data(6, socket_your, address_port_sending, 0,
                             0, 0, str(len(parts)))
            # MAIN SENDING LOOP
            sender_selective_repeat_arq(parts, packets_number, mistake, socket_your, address_port_sending)
            send_successfully = True
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
    if send_successfully:
        print("Data send successfully.")


def sender_selective_repeat_arq(parts, packets_number, mistake, socket_your, address_port_sending):
    # ---  MAIN ARQ LOOP SEND - SELECTIVE REPEAT
    error = 0
    window_size = 15
    window_start = 0
    ack_check = [False] * packets_number
    window_end = min(window_size - 1, len(parts) - 1)
    currently_not_ack = 0
    sq_num = 0
    count_no_signal = 0

    packet_timers = {i: None for i in range(packets_number)}
    timeout_threshold = 2.0
    while count_no_signal < 3 and not all(ack_check):
        try:
            current_time = time.time()
            while True:
                # --- IF WINDOW NOT FILLED SEND PACKET OR NOT ENOUGH LEFT TO FILL THE WINDOW
                if (currently_not_ack < window_size or window_end < len(parts)) and not sq_num >= len(parts):
                    string_part = parts[sq_num]
                    crc = binascii.crc_hqx(string_part, 0)
                    # -- IF MISTAKE ON 7% CHANCE TO SEND BAD PACKET MAX 50 ERRORS
                    if mistake == "1" and error <= 50:
                        if random.random() < 0.07:
                            crc += 1
                            error += 1
                    send_packet_data(6, socket_your, address_port_sending, sq_num, len(string_part), crc, string_part)
                    currently_not_ack += 1
                    sq_num += 1
                #check if some packets timeout if yes send again
                for packet_num in range(window_start, min(window_start + window_size, packets_number)):
                    if not ack_check[packet_num]:
                        if packet_timers[packet_num] and (current_time - packet_timers[packet_num] > timeout_threshold):
                            print(f"Timeout for packet {packet_num + 1}, retransmitting...")
                            string_part = parts[packet_num]
                            crc = binascii.crc_hqx(string_part, 0)
                            send_packet_data(6, socket_your, address_port_sending, packet_num, len(string_part), crc,
                                             string_part)
                            # Restart the timer
                            packet_timers[packet_num] = current_time
                # --- IF WINDOW FILLED RECEIVED PACKETS OR LESS PACKETS
                if currently_not_ack >= window_size or window_end >= len(parts) or len(parts) < window_size:
                    packet, _ = socket_your.recvfrom(1500)
                    header = retrieve_header(packet)
                    type_header = header.get("header_type")
                    ack_num = header.get("packet_number")
                    # --- ACK RECEIVED
                    if type_header == 2:
                        print(f"PACKET {ack_num + 1} - ACK RECEIVED, arrived correct:", address_port_sending)
                        window_start += 1
                        window_end += 1
                        currently_not_ack -= 1
                        ack_check[ack_num] = True
                        packet_timers[ack_num] = None
                    # --- NACK RECEIVED
                    elif type_header == 7:
                        print(f"PACKET {ack_num + 1} - NACK RECEIVED, arrived wrong:", address_port_sending)
                        # --- RETRANSMIT THE LOST PACKET
                        string_part = parts[ack_num]
                        crc = binascii.crc_hqx(string_part, 0)
                        send_packet_data(6, socket_your, address_port_sending, ack_num, len(string_part), crc, string_part)
                        packet_timers[ack_num] = current_time
                # --- CHECK IF ALL PACKETS ACKED
                if all(ack_check):
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
    if all(ack_check):
        print("All packets send OKAY")