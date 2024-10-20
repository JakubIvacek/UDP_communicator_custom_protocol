import binascii
import math
import os.path
import socket
import struct
import threading
import time
import struct

# --------------------------------   GLOBAL VARIABLES
# ip 172.28.128.1
keep_alive_running = True
user_input = ""
on = True
switch = False
transfer = False
file = False
transfer_file = False
sender = False
header_format = "BHHHHHH"
header_size = 14  # header format 13 + 1 padding


def reset_global_variables():  # RESET GLOBAL VARIABLES
    global keep_alive_running, user_input, on, switch, transfer, file, sender, transfer_file
    keep_alive_running = True
    user_input = ""
    on = True
    transfer = False
    switch = False
    file = False
    sender = False
    transfer_file = False


# --------------------------------   THREAD STUFF
# Thread for checking user input
def user_input_thread():
    global user_input
    while keep_alive_running:
        input_user = input("Enter : M for message send, F for file Send, E for Exit\n")
        user_input = input_user


def start_threads(socket_your, address_port):
    keep_ali_thread = threading.Thread(target=keep_alive_thread, args=(socket_your, address_port))
    keep_ali_thread.daemon = True
    keep_ali_thread.start()
    user_inp_thread = threading.Thread(target=user_input_thread)
    user_inp_thread.daemon = True
    user_inp_thread.start()
    return keep_ali_thread, user_inp_thread


def end_threads(user_inp_thread, keep_ali_thread):
    global keep_alive_running
    print("-- ENTER ANYTHING TO CONTINUE --")
    keep_alive_running = False
    keep_ali_thread.join()
    user_inp_thread.join()


# --------------------------------   HEADER CREATE/RETRIEVE
def create_header(head_type, sequence_number, acknowledgment_number, fragment_offset, window_size, data_length, crc):
    global header_format
    header = struct.pack(header_format, head_type, sequence_number, acknowledgment_number,
                         fragment_offset, window_size, data_length, crc)
    return header


def retrieve_header(packet):
    global header_format
    header = packet[:header_size]
    # Unpack the header to retrieve the values
    unpacked_data = struct.unpack(header_format, header)
    (header_type, sequence_number, acknowledgment_number, fragment_offset,
     window_size, data_length, crc) = unpacked_data
    return {
        'header_type': header_type,
        'sequence_number': sequence_number,
        'acknowledgment_number': acknowledgment_number,
        'fragment_offset': fragment_offset,
        'window_size': window_size,
        'data_length': data_length,
        'crc': crc,
    }


# --------------------------------   SENT PACKAGE STUFF
def send_packet_data(type_header, socket_your, address_port_sending, sequence_number, acknowledgment_number,
                     fragment_offset, window_size, data_length, crc, data):
    global header_format
    header = struct.pack(header_format, type_header, sequence_number, acknowledgment_number, fragment_offset,
                         window_size, data_length, crc)
    if isinstance(data, bytes):
        encoded_data = data
    else:
        encoded_data = data.encode()  # Convert string to bytes

    # Send the header and data together
    socket_your.sendto(header + encoded_data, address_port_sending)


def send_info_packet_type_only(type_header, socket_your, address_port_sending):
    global header_format
    header = struct.pack(header_format, type_header, 0, 0, 0, 0, 0, 0)
    socket_your.sendto(header, address_port_sending)  # send type info message


# --------------------------------   P2P COMMUNICATION START
def peer_to_peer_start():  # P2P start
    print("peerToPeer Start")
    connected = False
    while not connected:
        try:
            #SET USER INPUT
            port_your = input("Input port you are listening on: ")
            address_sending = input("Input ip you are sending to: ")
            port_sending = input("Input port you are sending to: ")
            start_connection = input("Want to Start connection? (Y/N): ").strip().lower()
            #SET UP SOCKET
            socket_your = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_your.bind(("", int(port_your)))
            socket_your.settimeout(120)
            address_port_sending = (address_sending, int(port_sending))
            if start_connection == "y":
                # INITIATE CONNECTION 3-WAY-HANDSHAKE
                # "0" = SYN  "1" = SYN-ACK   "2" = ACK
                send_info_packet_type_only(0, socket_your, address_port_sending)  # sent "0" = SYN
                print("SYN SENT :", address_port_sending)
                data, _ = socket_your.recvfrom(1500)  # check if "1" = SYN-ACK received
                type_header = retrieve_header(data).get("header_type")
                if type_header == 1:
                    print("SYN-ACK RECEIVED :", address_port_sending)
                    send_info_packet_type_only(2, socket_your, address_port_sending)  # Sent "2" = ACK
                    print("ACK SENT :", address_port_sending)
                    connected = True
                    print("CONNECTED .  \n")
                else:
                    print("Not connected try again SYN-ACK not received")
            elif start_connection == "n":
                # WAITING FOR CONNECTION 3-WAY-HANDSHAKE
                # "0" = SYN  "1" = SYN-ACK   "2" = ACK
                data, _ = socket_your.recvfrom(1500)  # check if "0" = SYN
                type_header = retrieve_header(data).get("header_type")
                if type_header == 0:
                    print("SYN RECEIVED :", address_port_sending)
                    send_info_packet_type_only(1, socket_your, address_port_sending)  #sent "1" = SYN-ACK
                    print("SYN-ACK SENT :", address_port_sending)
                    data, _ = socket_your.recvfrom(1500)  # check if "2" = ACK received
                    type_header = retrieve_header(data).get("header_type")
                    if type_header == 2:
                        print("ACK RECEIVED :", address_port_sending)
                        connected = True
                        print("CONNECTED . \n")
                    else:
                        print("Not connected try again ACK not received")
                else:
                    print("Not connected try again SYN-ACK not received")
        except socket.timeout:
            print("Timeout, no response. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred: {e}")
    main_loop(socket_your, address_port_sending)


# --------------------------------   MESSAGE TRANSFER RECEIVE/SEND
def receive_message(socket_your, address_port_sending):
    # Receive message
    try:
        print("\nMessage transfer started")
        print("Sending '2' = ACK ", "\n")
        socket_your.settimeout(60)
        send_info_packet_type_only(2, socket_your, address_port_sending)  # sent "2" = ACK
        while True:  # sometimes 0 from keepalive is received first so im waiting for 6 Data packet
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            if header.get("header_type") == 6:  # 6 = Data packet
                break
        only_data = data[header_size:]
        print("Message received :", only_data.decode(), "\n")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")


def send_message(socket_your, address_port_sending):
    # SEND MESSAGE
    try:
        print("\nMessage transfer started")
        socket_your.settimeout(120)
        print("WAITING FOR ACK :", address_port_sending)
        while True:  # sometimes 0 from keepalive is received first so im waiting for 2 ACK
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            #print(data)
            if header.get("header_type") == 2:  # 2 = Ack
                break
        if header.get("header_type") == 2:
            print("ACK RECEIVED :", address_port_sending, "\n")
            # sending message
            string_to_send = input("Enter message to SEND :")
            send_packet_data(6, socket_your, address_port_sending, 0, 0,
                             0, 0, 0, 0, string_to_send)
            print("Message sent : " + string_to_send, "\n")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")


# --------------------------------   FILE TRANSFER RECEIVE/SEND
def file_send(socket_your, address_port_sending, file_bool):
    global user_input
    file_name = ""
    string_to_send = ""
    try:
        print("\nFile\Message transfer started")
        socket_your.settimeout(120)
        print("WAITING FOR ACK :", address_port_sending)
        while True:  # sometimes 0 from keepalive is received first so im waiting for 2 ACK
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            #print(data)
            if header.get("header_type") == 2:  # 2 = Ack
                break
        print("ACK RECEIVED :", address_port_sending, "\n")
        # SET UP FILE , FRAGMENT
        file_name = input("Enter file name : ")
        path = input("Enter path where to find file C:/.../  or (yes) if in working directory: ")
        fragment_size = int(input("Enter fragment size : max 1458 :"))
        while 0 >= fragment_size or 1458 < fragment_size:
            fragment_size = int(input("Enter fragment size :  max 1458 :"))
        # READ FILE
        if path == "yes":
            path = file_name
        else:
            path = path + "\\" + file_name
        file_in = open(path, "rb")
        file_size = os.path.getsize(path)
        packets_number = math.ceil(file_size / fragment_size)
        last_fragment_size = file_size % fragment_size
        string_to_send = file_in.read()
        print("File to send : " + file_name + "  " + str(file_size) + " B")
        print("File path: " + path)
        print("Fragment count: " + str(packets_number))
        print("Fragment size: " + str(fragment_size))
        if last_fragment_size > 0 and last_fragment_size != fragment_size:
            print("Last fragment size: " + str(file_size % fragment_size))
        # SEPARATE FILE INTO FRAGMENTS
        parts = []
        while len(string_to_send) > 0:
            string_part = string_to_send[0:fragment_size]  # file already in bytes "rb"
            parts.append(string_part)
            string_to_send = string_to_send[fragment_size:]
        #SEND FILE NAME FIRST
        send_packet_data(6, socket_your, address_port_sending, 0, 0,
                         0, 0, 0, 0, file_name)
        #SEND FRAGMENT SIZE
        send_packet_data(6, socket_your, address_port_sending, 0, 0,
                         0, 0, 0, 0, str(len(parts)))
        #SEND LOOP
        i = 0
        while i < len(parts):
            string_part = parts[i]
            crc = binascii.crc_hqx(string_part, 0)
            send_packet_data(6, socket_your, address_port_sending, i, 0,
                             i, 0, 0, crc, string_part)
            packet, _ = socket_your.recvfrom(1500)
            type_header = retrieve_header(packet).get("header_type")
            if type_header == 2:  # ACK
                print("PACKET - " + str(i + 1) + " ACK RECEIVED arrived ok :", address_port_sending)
                i += 1
            elif type_header == 7:  # NACK
                print("PACKET - " + str(i + 1) + " NACK RECEIVED arrived wrong :", address_port_sending)

        print("File sent : " + file_name, "\n")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")


def file_receive(socket_your, address_port_sending):
    received_packets_count = 0
    full_string = []
    fragment_size = 0
    try:
        print("\nFile  transfer started")
        print("Sending '2' = ACK ", "\n")
        socket_your.settimeout(120)
        send_info_packet_type_only(2, socket_your, address_port_sending)  # sent "2" = ACK
        while True:  # sometimes 0 from keepalive is received first so im waiting for 6 Data packet
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            if header.get("header_type") == 6:  # 6 = Data packet
                break
        # RECEIVE FILE NAME
        file_name = data[header_size:]
        decoded_file_name = file_name.decode()
        print("First data packet arrived. Filename : ", decoded_file_name)
        # RECEIVE FRAGMENT COUNT
        data, _ = socket_your.recvfrom(1500)
        fragment_count = int(data[header_size:].decode())
        # RECEIVE MAIN LOOP
        i = 0
        parts = []
        while i < fragment_count:
            packet, _ = socket_your.recvfrom(1500)
            header = retrieve_header(packet)
            crc = header.get("crc")
            data = packet[header_size:]
            if fragment_size == 0:
                fragment_size = len(data)
            crc_check = binascii.crc_hqx(data, 0)
            if crc_check == crc:
                print("Packet : " + str(i + 1) + "  received okay SENDING ACK")
                i += 1
                parts.append(data)
                send_info_packet_type_only(2, socket_your, address_port_sending)
            else:
                print("Packet : " + str(i + 1) + "  received wrong SENDING NACK")
                send_info_packet_type_only(7, socket_your, address_port_sending)
        print("File received okay. \n")
        decoded_file_name = "1" + decoded_file_name
        file_path = input("Enter path where to save C:/.../  or (yes) to receive in working directory: ")
        if file_path == "yes":
            path = decoded_file_name
        else:
            path = file_path + "\\" + decoded_file_name

        with open(path, 'wb') as file_write:
            for part in parts:
                file_write.write(part)
        file_size = os.path.getsize(path)
        last_fragment_size = file_size % fragment_size
        print("File to send : " + decoded_file_name + "  " + str(file_size) + " B")
        print("File path: " + path)
        print("Fragment count: " + str(fragment_count))
        print("Fragment size: " + str(fragment_size))
        if last_fragment_size > 0 and last_fragment_size != fragment_size:
            print("Last fragment size: " + str(file_size % fragment_size))
        print(f"File saved {path}")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")


# --------------------------------   KEEPALIVE THREAD
def keep_alive_thread(socket_your, address_port_sending):
    global keep_alive_running, on, switch, transfer, transfer_file
    while keep_alive_running:
        socket_your.settimeout(60)
        try:
            send_info_packet_type_only(0, socket_your, address_port_sending)  # sent 0 = SYN
            data, _ = socket_your.recvfrom(1500)
            type_header = retrieve_header(data).get("header_type")
            # received 0 = SYN
            if type_header == 0:
                print("KeepAlive from :", address_port_sending)
            # SOMETHING ELSE RECEIVED
            elif type_header == 3:  # received 3 = Sending message
                transfer = True
                print("Sending message comm from :", address_port_sending)
                break
            elif type_header == 4:  # received 4 = Exit
                print("Exit received from :", address_port_sending)
                on = False
                break
            elif type_header == 5:  # received 5 = Sending file
                transfer_file = True
                print("Sending file comm from :", address_port_sending)
                break

        except socket.timeout:
            print("Timeout, no response KA. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred KA: {e}")

        time.sleep(5)


# --------------------------------   MAIN LOOP
def main_loop(socket_your, address_port_sending):  # main loop
    global user_input, transfer, keep_alive_running, file, sender, on, transfer_file
    reset_global_variables()
    (keep_ali_thread, user_inp_thread) = start_threads(socket_your, address_port_sending)
    old_input = ""
    while True:
        if on is False:  # When exit is initiated
            print("Exit initiated. ")
            end_threads(user_inp_thread, keep_ali_thread)
            break
        if transfer:  # When transfer is initiated
            print("Message Transfer initiated. ")
            end_threads(user_inp_thread, keep_ali_thread)
            if sender:
                send_message(socket_your, address_port_sending)
            else:
                receive_message(socket_your, address_port_sending)
            print("\nMessage transfer stopped")
            reset_global_variables()  # Start again threads
            keep_ali_thread, user_inp_thread = start_threads(socket_your, address_port_sending)
        if transfer_file:
            print("File Transfer initiated. ")
            end_threads(user_inp_thread, keep_ali_thread)
            if sender:
                file_send(socket_your, address_port_sending)
            else:
                file_receive(socket_your, address_port_sending)
            print("\nFile transfer stopped")
            reset_global_variables()  # Start again threads
            keep_ali_thread, user_inp_thread = start_threads(socket_your, address_port_sending)
        user_input = user_input.lower()
        if old_input != user_input:
            match user_input:
                case "e":
                    on = False
                    # sent "4" = exit to let other side know
                    send_info_packet_type_only(4, socket_your, address_port_sending)
                case "m":
                    sender = True
                    transfer = True
                    # sent "3" = message transfer to let other side know
                    send_info_packet_type_only(3, socket_your, address_port_sending)
                case "f":
                    sender = True
                    transfer_file = True
                    # sent "5" = message transfer to let other side know
                    send_info_packet_type_only(5, socket_your, address_port_sending)
        old_input = user_input
        time.sleep(1)
    socket_your.close()


# MAIN LOOP
def main():
    while True:
        reset_global_variables()
        # CHECK USER INPUT
        user_input = input("Input : P for  PEER to PEER communication \n E for Exit \n")
        user_input = user_input.lower()
        match user_input:
            case "p":
                peer_to_peer_start()
            case "e":
                break
            case _:
                print("Wrong user input")


if __name__ == "__main__":
    main()
