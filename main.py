import binascii
import math
import os.path
import socket
import struct
import threading
import time

# ip 172.28.128.1
keep_alive_running = True
user_input = ""
on = True
switch = False
file_transfer = False
file = False


# --------------------------------- THREAD STUFF
# Start loops , messages just for printing info diff for server client
def startThreads(socket_in_use, address, client):
    if client:
        messages = [" Client loop Enter : E for Exit , S for Switch , M for message send, F for file Send \n", "Client KeepAlive from Server arrived conn. on", "Exit received from Server shutting down", "Switch received from Server switching"]
    else:
        messages = ["Server input Enter: E for Exit, S for Switch\n", "Server KeepAlive from Client arrived conn. on", "Exit received from Client shutting down", "Switch received from Client switching"]
    keep_alive_thread = threading.Thread(target=KeepAlive, args=(socket_in_use, address, messages, client))
    keep_alive_thread.daemon = True
    user_input_thread = threading.Thread(target=UserInputThread, args=(messages[0],))
    user_input_thread.daemon = True
    user_input_thread.start()
    keep_alive_thread.start()
    return keep_alive_thread, user_input_thread


# Thread for checking user input
def UserInputThread(message):
    global user_input
    while keep_alive_running:
        input_user = input(message)
        user_input = input_user


# Keep Alive Thread
# GETS 0 data == KEEPALIVE PACKET , 1 data == SIGNAL TO SHUT DOWN, 2 data == SWITCH SIGNAL
def KeepAlive(socket_in_use, address, messages, client):
    global keep_alive_running, on, switch, file_transfer, file
    while keep_alive_running:
        try:
            socket_in_use.settimeout(60)
            #   KEEP ALIVE
            if client:                      # IF CLIENT SEND KEEP ALIVE
                socket_in_use.sendto("0".encode(), address)
            data = socket_in_use.recv(1500)  # Data receive
            if str(data.decode()) == "0":  # KEEP ALIVE
                print(messages[1])
                if not client:             # IF SERVER SEND BACK ACK
                    socket_in_use.sendto("0".encode(), address)

            # OTHER SIGNALS TO TURN OFF KEEPALIVE and set
            # GLOBAL variables BEFORE SENDING , SWITCHING , EXITING

            elif str(data.decode()) == "1":  # "1" EXIT RECEIVED
                on = False
                print(messages[2])
                socket_in_use.sendto(str.encode("1"), address)  # SEND BACK "1" EXIT ACK
                break
            elif str(data.decode()) == "2":  # "2" SWITCH RECEIVED
                on = False
                switch = True
                print(messages[3])
                socket_in_use.sendto(str.encode("2"), address)  # SEND BACK "2" SWITCH ACK
                break
            elif str(data.decode()) == "3" or str(data.decode()) == "4":  # "3" "4" FILE TRANSFER RECEIVED
                file_transfer = True
                keep_alive_running = False
                print("File transfer start received sending back ack")
                if str(data.decode()) == "4":   # "4" FILE TRANSFER , "3" MESSAGE
                    file = True
                socket_in_use.sendto(str.encode(str(data.decode())), address)  # SEND BACK ACK "3" "4"
                break
        except (socket.timeout, socket.gaierror) as e:
            on = False
            print("Socket error in KeepAlive OR timeout " + str(e))
            return
        time.sleep(5)


# ---------------------------------------- LOGIN SERVER , CLIENT
def loginServer():  # Server Start and Initial Connection
    print("Login SERVER")
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enter port
    port_server = input("Input port: ")
    socket_server.bind(("", int(port_server)))
    # check connection
    connected = False
    while not connected:
        try:
            data, address_client = socket_server.recvfrom(1500)
            if data.decode() == "1":
                socket_server.sendto(str.encode("0"), address_client)  # send back connected (ack)
                print("Connected to address :", address_client)
                connected = True
        except (socket.timeout, socket.gaierror) as e:
            print("Not connected try again" + e)
    serverLoop(socket_server, address_client)


def loginClient():  # Client Start and Initial Connection to server
    print("Login CLIENT")
    connected = False
    while not connected:
        try:
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Enter port and ip of server
            address_server = input("Input ip of server : ")
            port_server = input("Input port of server: ")
            address_port_server = (address_server, int(port_server))
            # try to connect to server
            socket_client.sendto(str.encode("1"), address_port_server)
            socket_client.settimeout(40)
            # if  0 received (ack) connected
            data, address = socket_client.recvfrom(1500)
            if data.decode() == "0":
                print("Connected to address:", address_port_server)
                connected = True
            else:
                print("Not connected try again")
        except (socket.timeout, socket.gaierror) as e:
            print("Not connected try again" + e)
    clientLoop(socket_client, address_port_server)


#  ----------------------------- MAIN LOOP SERVER , CLIENT
def serverLoop(socket_server, address_client):  # Server main loop
    global user_input, file_transfer, keep_alive_running, file
    reset_global_variables()
    keep_alive_thread, user_input_thread = startThreads(socket_server, address_client, False)
    while True:
        if on is False:  # When exit is initiated by other side exit
            end_threads(keep_alive_thread, user_input_thread)
            break
        if file_transfer:
            print("File transfer started")
            # Turn off keep alive
            keep_alive_running = False
            keep_alive_thread.join()
            fileTransferReceive(socket_server, address_client, file)  # DO FILE TRANSFER
            # Start keep alive again
            reset_global_variables()
            print("File received")
            keep_alive_thread, user_input_thread = startThreads(socket_server, address_client, False)
        user_input_match = user_input.lower()
        match user_input_match:
            case 'e':
                if send_info(socket_server, address_client, ["Send info to other Client about shutting down", "Received ack from Client shutting down"], "1"):
                    return  # socket error
            case 's':
                if send_info(socket_server, address_client, ["Send info to other Client about switching", "Received ack from Client switching"], "2"):
                    return  # socket error
        time.sleep(2)
    socket_server.close()
    if switch:
        user_input = ""
        loginClient()


def clientLoop(socket_client, address_port_server):  # Client main loop
    global user_input
    reset_global_variables()
    keep_alive_thread, user_input_thread = startThreads(socket_client, address_port_server, True)
    while True:
        if on is False:  # When exit is initiated by other side exit
            end_threads(keep_alive_thread, user_input_thread)
            break
        user_input_match = user_input.lower()
        match user_input_match:
            case "e":
                if send_info(socket_client, address_port_server,["Send info to Server about shutting down", "Received ack from Server shutting down"], "1"):
                    return  # socket error
            case "s":
                if send_info(socket_client, address_port_server, ["Send info to Server about switching", "Received ack from Server switching"], "2"):
                    return  # socket error
            case "m":
                # TURN OFF KEEPALIVE FIRST
                if send_info(socket_client, address_port_server, ["Send info to Server file transfer start", "Received ack from Server start transfer"], "3"):
                    return  # socket error
                # Do file transfer and start back keep alive after finishing
                keep_alive_thread, user_input_thread = startFileTransfer(socket_client, address_port_server, keep_alive_thread, user_input_thread,  False)
            case "f":
                # TURN OFF KEEPALIVE FIRST
                if send_info(socket_client, address_port_server, ["Send info to Server file transfer start", "Received ack from Server start transfer"], "4"):
                    return  # socket error
                # Do file transfer and start back keep alive after finishing
                keep_alive_thread, user_input_thread = startFileTransfer(socket_client, address_port_server, keep_alive_thread, user_input_thread, True)
        time.sleep(2)
    socket_client.close()
    if switch:
        user_input = ""
        loginServer()


# end threads when exiting called before exiting main loop
def end_threads(keep_alive_thread, user_input_thread):
    global keep_alive_running, switch, file_transfer, file
    keep_alive_running = False
    keep_alive_thread.join()
    if file_transfer:
        print("PRESS F TO CONTINUE")
    elif not switch:
        print("PRESS E TO EXIT")
    else:
        print("PRESS S TO SWITCH")
    user_input_thread.join()


def send_info(socket_in_use, address, messages,data):
    global keep_alive_running, on, switch, file_transfer
    try:
        keep_alive_running = False
        socket_in_use.sendto(str.encode(data), address)
        print(messages[0])
        data_user = socket_in_use.recv(1500)
        if data_user.decode() == data:
            if data == "1":
                on = False
            elif data == "2":
                on = False
                switch = True
            elif data == "3":
                file_transfer = True
        print(messages[1])
    except (socket.timeout, socket.gaierror) as e:
        print("Error while sending info to KEEPALIVE after user input")
        return True
    return False


def reset_global_variables():  # RESET GLOBAL VARIABLES
    global keep_alive_running, user_input, on, switch, file_transfer, file
    keep_alive_running = True
    user_input = ""
    on = True
    file_transfer = False
    switch = False
    file = False


# Start file Transfer end keep alive before and start back up after transfer
def startFileTransfer(socket_in_use, address, keep_alive_thread, input_thread,  file_):
    global file_transfer
    file_transfer = True
    end_threads(keep_alive_thread, input_thread) # end threads
    fileTransferSend(socket_in_use, address, file_)  # do the file transfer
    reset_global_variables()
    print("File transfer done")
    return startThreads(socket_in_use, address, True)   # Start threads again


def fileTransferSend(socket_in_use, address, file_type):
    global user_input
    file_name = ""
    string_to_send = ""
    string_part = ""
    error = 0
    if file_type:
        file_name = input("Enter file name : ")
    else:
        string_to_send = input("Enter message to send : ")
    fragment_size = int(input("Enter fragment size : max 1470 :"))
    while 0 >= fragment_size or 1470 < fragment_size:
        fragment_size = int(input("Enter fragment size :  max 1470 :"))
    mistake = input("Enter 1 if u want bad packet receive : ")
    if file_type:
        file_in = open(file_name, "rb")
        file_size = os.path.getsize(file_name)
        print("File to send : " + file_name + str(file_size) + " B")
        packets_number = math.ceil(file_size / fragment_size)
        string_to_send = file_in.read()
    else:
        packets_number = math.ceil(len(string_to_send) / fragment_size)
    # SEND START PACKETS NUM
    socket_in_use.sendto(str(packets_number).encode(), address)
    # SEND FILE NAME
    socket_in_use.sendto(file_name.encode(), address)
    # separate string and get parts
    parts = []
    while len(string_to_send) > 0:
        if file_type:
            string_part = string_to_send[0:fragment_size]  # file already in bytes "rb"
        else:
            string_part = string_to_send[0:fragment_size]
            string_part = str.encode(string_to_send)  # message get part and encode
        parts.append(string_part)
        string_to_send = string_to_send[fragment_size:]
    # send loop
    i = 0
    while i < len(parts):
        #    GET PART OF THE STRING TO SEND
        string_part = parts[i]
        # crc
        crc = binascii.crc_hqx(string_part, 0)
        if mistake == "1" and error == 0:
            crc += 1
            error += 1
        header = struct.pack("H", crc)
        # wait for response
        try:
            socket_in_use.settimeout(10.0)
            socket_in_use.sendto(header + string_part, address)  # send data
            data = socket_in_use.recv(1500)
            data = data.decode()
            if data == "2":  # ACK RECEIVED DATA OK
                print("Packet : " + str(i + 1) + " arrived ok")
                i += 1
                continue
            elif data == "3":  # DATA ARRIVED WRONG SENDING AGAIN
                print("Packet : " + str(i + 1) + " arrived wrong sending again")
                continue
        except (socket.timeout, socket.gaierror) as e:
            print(e)
            print("Something went wrong")
            return


def fileTransferReceive(socket_in_use, address, file_type):
    received_packets_count = 0
    full_string = []
    fragment_size = 0
    # receive packets num
    data = socket_in_use.recv(1500)
    packets_to_arrive = int(data.decode())
    # receive file name
    data = socket_in_use.recv(1500)
    file_name = data.decode()
    while received_packets_count < packets_to_arrive:
        try:
            socket_in_use.settimeout(10)
            data = socket_in_use.recv(1500)
            crc = struct.unpack("H", data[0:2])
            if fragment_size == 0:
                fragment_size = len(data)
            crc_check = binascii.crc_hqx(data[2:], 0)
            if crc[0] == crc_check:  # RECEIVED OKAY APPEND FRAGMENT
                print("Packet : " + str(received_packets_count + 1) + " received ok")
                received_packets_count += 1
                if file_type:
                    full_string.append(data[2:])
                else:
                    full_string.append(data[2:].decode())
                socket_in_use.sendto(str.encode("2"), address)
            else:  # ELSE SEND SEND AGAIN FRAGMENT
                print("Packet : " + str(received_packets_count + 1) + "  wrong receive")
                socket_in_use.sendto(str.encode("3"), address)
        except (socket.timeout, socket.gaierror) as e:
            print(e)
            print("Something went wrong")
            return
    # OUTPUT THE FILE , MESSAGE
    if not file_type:
        print("Message sent : " + "".join(full_string))
    else:
        global user_input
        user_input = ""
        while user_input == "":
            print("Enter file path where to store (C:/../../)  /or 1 if in working dir : ")
            time.sleep(5)
        x = ""
        if user_input == "1":
            file_output = open(file_name, "wb")
        else:
            file_output = open(os.path.join(user_input, file_name), "wb")
        user_input = ""
        for fragment in full_string:
            file_output.write(fragment)
        print("File written")
        print("Path : " + str(os.path.join(user_input, file_name)))
        print("Fragments : " + str(packets_to_arrive) + " Fragment size :" + str(fragment_size - 2))
        file_output.close()




# MAIN LOOP
def main():
    while True:
        reset_global_variables()
        # CHECK USER INPUT
        user_input = input("Input : C for Client \n S for Server \n E for Exit \n")
        user_input = user_input.lower()
        match user_input:
            case "c":
                loginClient()
            case "s":
                loginServer()
            case "e":
                break
            case _:
                print("Wrong user input")


if __name__ == "__main__":
    main()