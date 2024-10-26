# Main script that initializes peer-to-peer communication
# Imports
import socket, threading, time
# Import modules
from header_to_json import retrieve_header
from communication_start import peer_to_peer_start
from create_send_packets import send_info_packet_type_only
from transfer_sender import data_send
from transfer_receive import data_receive

# Function to reset global control variables to initial states
def reset_global_variables():
    global keep_alive_running, user_input, on, switch, transfer, file, sender, transfer_file
    keep_alive_running = True
    user_input = ""
    on = True
    transfer = False
    switch = False
    file = False
    sender = False
    transfer_file = False

# Function to handle user input in a separate thread
def user_input_thread():
    global user_input
    while keep_alive_running:
        input_user = input("Enter : M for message send, F for file Send, E for Exit\n")
        user_input = input_user

# Keep-alive thread that maintains active connection by sending periodic "keep-alive" packets
# Also checks for incoming communication requests or exit signals
def keep_alive_thread(socket_your, address_port_sending):
    global keep_alive_running, on, switch, transfer, transfer_file
    count_no_signal = 0
    while keep_alive_running:
        socket_your.settimeout(60)
        try:
            send_info_packet_type_only(0, socket_your, address_port_sending)  # Send SYN packet (type 0)
            data, _ = socket_your.recvfrom(1500)
            type_header = retrieve_header(data).get("header_type")
            count_no_signal = 0

            # Check packet type received
            if type_header == 0:   # SYN response received
                print("KeepAlive from :", address_port_sending)
            elif type_header == 3:  # Message transfer request received
                transfer = True
                print("Sending message comm from :", address_port_sending)
                break
            elif type_header == 4:  # Exit signal received
                print("Exit received from :", address_port_sending)
                on = False
                break
            elif type_header == 5:  # File transfer request received
                transfer_file = True
                print("Sending file comm from :", address_port_sending)
                break
        except ConnectionResetError:
            count_no_signal += 1
            print(f"No connection by {address_port_sending}.")
        except socket.timeout:
            print("Timeout, no response KA. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred KA: {e}")
        if count_no_signal == 3:
            print("Exit 3 times no respond on KeepAlive.")
            on = False
        time.sleep(5)

# Functions to start and stop the keep-alive and user input threads
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

# Main loop to manage user inputs and control data transfer states
def main_loop(socket_your, address_port_sending):  # main loop
    global user_input, transfer, keep_alive_running, file, sender, on, transfer_file
    reset_global_variables()
    (keep_ali_thread, user_inp_thread) = start_threads(socket_your, address_port_sending)
    old_input = ""
    while True:
        if on is False:  # Exit condition
            print("Exit initiated. ")
            end_threads(user_inp_thread, keep_ali_thread)
            break
        if transfer_file or transfer: # Initiates file or message transfer
            print("File, Message Transfer initiated. ")
            file_bool = transfer_file
            end_threads(user_inp_thread, keep_ali_thread)
            if sender:
                data_send(socket_your, address_port_sending, file_bool)
            else:
                data_receive(socket_your, address_port_sending, file_bool)
            print("\nFile transfer stopped")
            reset_global_variables()
            keep_ali_thread, user_inp_thread = start_threads(socket_your, address_port_sending)

        user_input = user_input.lower()
        if old_input != user_input:
            if user_input == "e": # Exit
                on = False
                send_info_packet_type_only(4, socket_your, address_port_sending)
            elif user_input == "m": # Message transfer
                sender = True
                transfer = True
                send_info_packet_type_only(3, socket_your, address_port_sending)
            elif user_input == "f": # File transfer
                sender = True
                transfer_file = True
                send_info_packet_type_only(5, socket_your, address_port_sending)
        old_input = user_input
        time.sleep(1)
    socket_your.close()

# Main function to initiate peer-to-peer communication or exit
def main():
    running = True
    while running:
        reset_global_variables()
        user_input = input("Input : P for  PEER to PEER communication \n E for Exit \n").lower()
        if user_input == "p":
            socket_your, address_port_sending = peer_to_peer_start() # START COMMUNICATION
            main_loop(socket_your, address_port_sending) # START MAIN LOOP
        elif user_input == "e":
            running = False
        else:
            print("Wrong user input")

if __name__ == "__main__":
    main()
