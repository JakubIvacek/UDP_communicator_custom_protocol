#---------
#---- P2P COMMUNICATION START FUNCTION
# ---------
#---- RETURNS --- YOUR_SOCKET , TUPLE_ADDRESS_HOST_OTHER
import socket
import time
from create_send_packets import send_info_packet_type_only
from header_to_json import retrieve_header

def peer_to_peer_start():  # P2P start
    print("peerToPeer Start")
    connected = False
    # SET USER INPUT
    port_your = input("Input port you are listening on: ")
    address_sending = input("Input ip you are sending to: ")
    port_sending = input("Input port you are sending to: ")
    # SET UP SOCKET
    socket_your = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_your.bind(("", int(port_your)))
    socket_your.settimeout(120)
    address_port_sending = (address_sending, int(port_sending))
    while not connected:
        try:
            # CONNECTION 3-WAY-HANDSHAKE
            # "0" = SYN  "1" = SYN-ACK   "2" = ACK
            send_info_packet_type_only(0, socket_your, address_port_sending)  # sent "0" = SYN
            #print("SYN SENT :", address_port_sending)
            data, _ = socket_your.recvfrom(1500)  # check if "1" = SYN-ACK received
            type_header = retrieve_header(data).get("header_type")
            if type_header == 0:
                print("SYN RECEIVED :", address_port_sending)
                send_info_packet_type_only(1, socket_your, address_port_sending)  # sent "1" = SYN-ACK
                #print("SYN-ACK SENT :", address_port_sending)
                data, _ = socket_your.recvfrom(1500)  # check if "1" = SYN-ACK received
                type_header = retrieve_header(data).get("header_type")
                if type_header == 1:
                    print("SYN-ACK RECEIVED :", address_port_sending)
                    send_info_packet_type_only(2, socket_your, address_port_sending)  # sent "2" = ACK
                    data, _ = socket_your.recvfrom(1500)  # check if "2" = SYN-ACK received
                    type_header = retrieve_header(data).get("header_type")
                    if type_header == 2:
                        print("ACK RECEIVED :", address_port_sending)
                        connected = True
                    else:
                        print("NO ACK RECEIVED ")
        except ConnectionResetError:
            print(f"No connection on {address_port_sending}.")
        except socket.timeout:
            print("Timeout, no response. Retrying...")
        except socket.gaierror as e:
            print(f"Error occurred: {e}")
        if not connected:
            time.sleep(5)
    print("Connected")
    return socket_your, address_port_sending