P2P Communication Protocol
Initialization of Peer-to-Peer Communication
The peer_to_peer_start() function initiates communication by specifying:

Port
Target User Port
Target User IP Address
To avoid connection conflicts, one user is designated to initiate the first connection, ensuring they connect to a user who is ready to receive the request.

Three-Way Handshake
The protocol establishes a connection through a three-way handshake with the following sequence:

SYN (0): The initiating user sends a "0" SYN packet.
SYN-ACK (1): Upon receiving SYN, the receiving user responds with a "1" SYN-ACK packet.
ACK (2): The initiator confirms receipt by replying with a "2" ACK packet.
Once the connection is successfully established, the main_loop() function activates, launching two threads: 1. keepAlive and 2. userInput.

In main_loop(), the system monitors userInput, triggering further actions that send signals to keepAlive. When keepAlive receives a signal, it also relays it to the other user, updating global variables to manage connection state or data transfer, thereby pausing keepAlive and userInput threads. Once data transfer (message or file) is complete, these threads automatically resume.

Header Design
Field	Size
Type	1 B
SN	2 B
AN	2 B
WS	2 B
DL	2 B
CRC	2 B
Total	12 B
Type Definitions (1 Byte):
0000 (0): SYN
0001 (1): SYN-ACK
0010 (2): ACK
0011 (3): Message Transfer
0100 (4): Exit Application
0101 (5): File Transfer
0110 (6): Data Packet
0111 (7): NACK
Additional fields:

SN: Sequence Number (2 Bytes)
AN: Acknowledgment Number (2 Bytes)
WS: Window Size (2 Bytes)
DL: Data Length (2 Bytes)
CRC-16: Checksum (2 Bytes)
The full header size is 40 Bytes (12B + 8B UDP + 20B IP Header), with a maximum fragment size of 1460 Bytes.

Checksum Method
CRC-16 is used as the checksum. This method uses a polynomial as a divisor, accessible to both sides for verification. For instance, the polynomial x^3 + x^2 + 1 generates 1011 To calculate the checksum: The sender appends k -1 zeros to the data (e.g., 15 zeros for CRC-16).
It divides the data by the polynomial key using XOR.
The remainder is appended to the data.
The receiver performs XOR division on the received data. If the remainder is zero, data integrity is verified.

ARQ Method
The Selective Repeat (SR) protocol, a sliding window protocol that improves upon Go-Back-N, is implemented with the following fields:

SN: Sequence Number
AN: Acknowledgment Number
WS: Window Size
While transmitting, the sender keeps a sliding window of n = window size packets. If an ACK is received, the window slides forward. If a NACK is received, only the specified packet is resent, unlike Go-Back-N, where the entire window would be resent. This continues until all packets are acknowledged or successfully received. Packets are reassembled on the receiver side based on their sequence numbers.

Connection Maintenance
The connection is maintained through the KeepAlive thread, which sends periodic signals to sustain the connection and detects control messages for initiating data transfers or closing connections. During data transmission, KeepAlive temporarily halts and resumes once transfer completes. If the other user fails to respond to three consecutive keep-alive signals, the connection closes automatically.

Control Signals:

0 (SYN KeepAlive)
3 (Message Transfer)
4 (Exit)
5 (File Transfer)
