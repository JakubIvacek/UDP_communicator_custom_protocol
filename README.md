# P2P Communication Protocol

## Run
To run the P2P Communication Protocol, execute the following command in your terminal:

```bash
python main.py
```

## Initialization of Peer-to-Peer Communication
The `peer_to_peer_start()` function initiates communication by specifying the following parameters:
- **Port**: The port number to be used for communication.
- **Target User Port**: The port number of the user being connected to.
- **Target User IP Address**: The IP address of the target user.

To prevent connection conflicts, one user is designated to initiate the first connection, ensuring they connect to a user who is ready to receive requests.

## Three-Way Handshake

The protocol establishes a connection through a three-way handshake, following this sequence:

1. **SYN (0)**: The initiating user sends a "0" SYN packet.
2. **SYN-ACK (1)**: The receiving user responds with a "1" SYN-ACK packet upon receiving the SYN.
3. **ACK (2)**: The initiator confirms receipt by sending a "2" ACK packet.

Once the connection is successfully established, the `main_loop()` function is activated, launching two threads:
1. **keepAlive**
2. **userInput**

Within `main_loop()`, the system monitors `userInput`, triggering actions that send signals to the `keepAlive` thread. When `keepAlive` receives a signal, it relays it to the other user and updates global variables to manage connection state or data transfer, pausing both the `keepAlive` and `userInput` threads. Once data transfer (either a message or file) is complete, these threads automatically resume.

## Header Design

The protocol header is structured as follows:

| Field       | Size   |
|-------------|--------|
| Type        | 1 B    |
| SN          | 2 B    |
| AN          | 2 B    |
| WS          | 2 B    |
| DL          | 2 B    |
| CRC         | 2 B    |
| **Total**   | **12 B** |

### Type Definitions (1 Byte)

- `0000 (0)`: SYN
- `0001 (1)`: SYN-ACK
- `0010 (2)`: ACK
- `0011 (3)`: Message Transfer
- `0100 (4)`: Exit Application
- `0101 (5)`: File Transfer
- `0110 (6)`: Data Packet
- `0111 (7)`: NACK

### Additional Fields

- **SN**: Sequence Number (2 Bytes)
- **AN**: Acknowledgment Number (2 Bytes)
- **WS**: Window Size (2 Bytes)
- **DL**: Data Length (2 Bytes)
- **CRC-16**: Checksum (2 Bytes)

The total header size is 40 Bytes (12B + 8B UDP + 20B IP Header), with a maximum fragment size of 1460 Bytes.

## Checksum Method

The checksum is calculated using **CRC-16**. This method uses a polynomial as a divisor, which both parties can access for verification. For example, the polynomial \( x^3 + x^2 + 1 \) generates the key `1011`. The checksum calculation involves the following steps:

1. The sender appends \( k-1 \) zeros to the data (e.g., 15 zeros for CRC-16).
2. The sender performs modulo-2 division of the data by the polynomial key using XOR.
3. The remainder is appended to the data.

The receiver then performs the same XOR division on the received data. If the remainder is zero, data integrity is confirmed.

## ARQ Method

The **Selective Repeat (SR)** protocol, an enhancement of the Go-Back-N protocol, is implemented using the following fields:

- **SN**: Sequence Number
- **AN**: Acknowledgment Number
- **WS**: Window Size

During transmission, the sender maintains a sliding window of `n = window size` packets. If an ACK is received, the window slides forward. If a NACK is received, only the specified packet is resent, unlike Go-Back-N, where the entire window would be resent. This process continues until all packets are acknowledged or received correctly. Packets are reassembled on the receiver side based on their sequence numbers.

## Connection Maintenance

Connection stability is managed by the **KeepAlive** thread, which sends periodic signals to maintain the connection and detects control messages for initiating data transfers or closing connections. During data transmission, the `KeepAlive` thread is temporarily halted and resumes once the transfer is complete. If the other user fails to respond to three consecutive keep-alive signals, the connection is automatically closed.

### Control Signals

- `0`: SYN KeepAlive
- `3`: Message Transfer
- `4`: Exit
- `5`: File Transfer

