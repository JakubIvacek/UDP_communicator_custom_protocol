# --------------------------------
# --------------------------------   DATA TRANSFER RECEIVER WITH
# --------------------------------   SELECTIVE REPEAT ARQ

# ---- IMPORTS
import binascii, time, socket, os
from header_to_json import retrieve_header
from create_send_packets import send_packet_data
from create_send_packets import send_info_packet_type_only
from globals import *

def data_receive(socket_your, address_port_sending, file_bool):
    try:
        #--- INITIATE THE TRANSFER
        print("\nFile,Message   transfer started")
        print("Sending '2' = ACK ", "\n")
        socket_your.settimeout(120)
        send_info_packet_type_only(2, socket_your, address_port_sending)  # sent "2" = ACK
        while True:  # sometimes 0 from keepalive is received first so im waiting for 6 Data packet
            data, _ = socket_your.recvfrom(1500)
            header = retrieve_header(data)
            if header.get("header_type") == 6 and data[header_size:].decode() != "":  # 6 = Data packet
                break
        #--- RECEIVE TRANSFER INFORMATION
        start_time = time.time()
        if file_bool:
            # RECEIVE FILE NAME
            file_name = data[header_size:]
            decoded_file_name = file_name.decode()
            print("First data packet arrived. Filename : ", decoded_file_name)
            # RECEIVE FRAGMENT COUNT
            data, _ = socket_your.recvfrom(1500)
            fragment_count = int(data[header_size:].decode())
        else:
            # RECEIVE FRAGMENT COUNT ONLY IF MESSAGE SENT NOT FILE
            fragment_count = int(data[header_size:].decode())


        #---  DATA RECEIVE SELECTIVE REPEAT ARQ
        parts = [None] * fragment_count
        received = [False] * fragment_count
        parts = [None] * fragment_count
        fragment_size = 0
        #--- MAIN LOOP
        while True:
            #--- RECEIVE PACKET
            packet, _ = socket_your.recvfrom(1500)
            header = retrieve_header(packet)
            crc = header.get("crc")
            data = packet[header_size:]
            seq_num = header.get("sequence_number")
            window_size = header.get("window_size")
            if fragment_size == 0: fragment_size = header.get("data_length")

            #--- CHECK CRC AND ACK OR NACK
            crc_check = binascii.crc_hqx(data, 0)
            if crc_check == crc:
                #--- RECEIVED CORRECT ACK SEND
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
                #--- RECEIVED WRONG NACK SEND
                print("Packet : " + str(seq_num + 1) + "  received wrong SENDING NACK:", address_port_sending)
                send_packet_data(7, socket_your, address_port_sending, 0,
                                 seq_num,  window_size, 0, 0, "")
            if all(received):
                break
        print("File,Message received okay. \n")

        #---  PRINT INFORMATION ABOUT THE TRANSFER
        end_time = time.time()
        transfer_time = end_time - start_time
        if not file_bool:
            #---  IF MESSAGE PRINT INFORMATION
            message = "".join(parts)
            message_size = len(message.encode('utf-8'))
            print("Message received alright : " + message)
            print("Message size: " + str(message_size) + " B")
        else:
            #---  IF FILE PRINT INFORMATION AND SAVE THE FILE
            decoded_file_name = "1" + decoded_file_name # FOR TESTING ADDING 1 TO NAME
            file_path = input("Enter path where to save C:/.../  or (yes) to receive in working directory: ")
            #--- SAVE FILE
            if file_path == "yes":
                path = decoded_file_name
            else:
                path = file_path + "\\" + decoded_file_name
            with open(path, 'wb') as file_write:
                for part in parts:
                    file_write.write(part)
            file_size = os.path.getsize(path)
            last_fragment_size = file_size % fragment_size
            #--- PRINT INFORMATION
            print("File to send : " + decoded_file_name + "  " + str(file_size) + " B")
            print("File path: " + path)
            print("Fragment count: " + str(fragment_count))
            if file_size < fragment_size:
                print("Fragment size: " + str(file_size))
            else:
                print("Fragment size: " + str(fragment_size))
            if last_fragment_size > 0 and last_fragment_size != fragment_size:
                print("Last fragment size: " + str(file_size % fragment_size))
            print(f"File received: saved {path}")
        print(f"Data transfer completed in {transfer_time:.3f} seconds")
    # --- CATCH ERRORS
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except ConnectionResetError:
        print(f"No connection on {address_port_sending}.")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")
