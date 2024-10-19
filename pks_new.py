import binascii
import math
import os.path
import socket
import struct
import threading
import time

# GLOBAL VARIABLES
# ip 172.28.128.1
keep_alive_running = True
user_input = ""
on = True
switch = False
transfer = False
file = False
sender = False

def reset_global_variables():  # RESET GLOBAL VARIABLES
    global keep_alive_running, user_input, on, switch, transfer, file, sender
    keep_alive_running = True
    user_input = ""
    on = True
    transfer = False
    switch = False
    file = False
    sender = False

# Thread for checking user input
def user_input_thread():
    global user_input
    while keep_alive_running:
        input_user = input("Enter : M for message send, F for file Send, E for Exit\n  :")
        user_input = input_user


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
                socket_your.sendto(str.encode("0"), address_port_sending) # sent "0" = SYN
                data, _ = socket_your.recvfrom(1500) # check if "1" = SYN-ACK received
                if data.decode() == "1":
                    print("SYN-ACK RECEIVED :", address_port_sending)
                    socket_your.sendto(str.encode("2"), address_port_sending) # Sent "2" = ACK
                    connected = True
                    print("Connected.")
                else:
                    print("Not connected try again SYN-ACK not received")
            elif start_connection == "n":
                # WAITING FOR CONNECTION 3-WAY-HANDSHAKE
                # "0" = SYN  "1" = SYN-ACK   "2" = ACK
                data, _ = socket_your.recvfrom(1500) # check if "0" = SYN
                if data.decode() == "0":
                    print("SYN RECEIVED :", address_port_sending)
                    socket_your.sendto(str.encode("1"), address_port_sending) #sent "1" = SYN-ACK
                    data, _ = socket_your.recvfrom(1500)  # check if "2" = ACK received
                    if data.decode() == "2":
                        print("ACK RECEIVED :", address_port_sending)
                        connected = True
                        print("Connected.")
                    else:
                        print("Not connected try again ACK not received")
                else:
                    print("Not connected try again SYN-ACK not received")
        except socket.timeout:
            print("Timeout, no response. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred: {e}")
    main_loop(socket_your, address_port_sending)


# Keep Alive Thread "0" = SYN AND "1" = SYN-ACK
def keep_alive_thread(socket_your, address_port_sending):
    global keep_alive_running, on, switch, transfer, file
    while keep_alive_running:
        socket_your.settimeout(60)
        try:
            socket_your.sendto(str.encode("0"), address_port_sending)  # sent "0" = SYN
            data, _ = socket_your.recvfrom(1500)
            if data.decode() == "0": # received "0" = SYN
                print("KeepAlive received SYN from :", address_port_sending)

            # SOMETHING ELSE RECEIVED

            elif data.decode() == "3":# received "3" = Sending message
                transfer = True
                keep_alive_running = False
                print("Sending message received from :", address_port_sending)
                break
            elif data.decode() == "4":# received "4" = Exit
                print("Exit received from :", address_port_sending)
                on = False
                break

        except socket.timeout:
            print("Timeout, no response KA. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred KA: {e}")


        time.sleep(5)

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
    print("PRESS F TO CONTINUE")
    keep_alive_running = False
    keep_ali_thread.join()
    user_inp_thread.join()

def receive_message(socket_your, address_port_sending):
    # Receive message
    try:
        print("Sending '2' = ACK ", "\n")
        socket_your.settimeout(60)
        socket_your.sendto(str.encode("2"), address_port_sending)  # sent "2" = ACK
        data, _ = socket_your.recvfrom(1500)
        print("Message received :", data, "\n")
    except socket.timeout:
        print("Timeout, no response. Retrying...")
    except socket.gaierror as e:
        print(f"Error occurred: {e}")

def send_message(socket_your, address_port_sending):
    # SEND MESSAGE
    global user_input
    old_input = user_input
    ack = False
    count = 0
    while not ack:
        try:
            socket_your.settimeout(60)
            data, _ = socket_your.recvfrom(1500)  # check if "2" = ACK received
            if data.decode() == "2":
                print("ACK RECEIVED :", address_port_sending, "\n")
                # sending message
                print("Enter message to SEND :")
                while old_input == user_input:
                    time.sleep(2)
                string_to_send = user_input
                socket_your.sendto(str.encode(string_to_send), address_port_sending)
                print("Message sent : " + string_to_send, "\n")
                ack = True
            count += 1
        except socket.timeout:
            print("Timeout, no response. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred: {e}")


def main_loop(socket_your, address_port_sending):  # main loop
    global user_input, transfer, keep_alive_running, file, sender, on
    reset_global_variables()
    (keep_ali_thread, user_inp_thread) = start_threads(socket_your, address_port_sending)
    while True:
        if on is False:  # When exit is initiated by other side exit
            print("Exit received from :", address_port_sending)
            end_threads(user_inp_thread, keep_ali_thread)
            break
        if transfer:
            print("\nFile/Message transfer started")
            # Turn off keep alive
            keep_alive_running = False
            keep_ali_thread.join()
            if sender:
                send_message(socket_your, address_port_sending)
            else:
                receive_message(socket_your, address_port_sending)
            # Start again
            reset_global_variables()
            print("\nFile/Message transfer stopped")
            keep_ali_thread, user_inp_thread = start_threads(socket_your, address_port_sending)
        user_input = user_input.lower()
        match user_input:
            case "e":
                on = False
                socket_your.sendto(str.encode("4"), address_port_sending) # sent "4" = exit
            case "m":
                sender = True
                transfer = True
                socket_your.sendto(str.encode("3"), address_port_sending) # sent "3" = message transfer
            case "f":
                x = 0
        time.sleep(2)
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