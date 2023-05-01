import socket
import struct

def send_data_to_server(HOST = '127.0.0.1', SENDPORT =5055, RECIEVEPORT=5050):
    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Define the packet format
    PACKET_FORMAT = '!HHLLBBHHH{}s'
    message = b'This is a test message.'

    # Define the packet fields
    SEQ_NUMBER = 0
    ACK_NUMBER = 0
    DATA_OFFSET = 5
    FLAGS = 0b000010   # SYN flag set
    WINDOW_SIZE = 1024
    CHECKSUM = 0
    URG_POINTER = 0

    # Pack the SYN packet
    packet = struct.pack(PACKET_FORMAT.format(len(message)), 0, 0, SEQ_NUMBER, ACK_NUMBER,
                     (DATA_OFFSET << 4) + 0, FLAGS, WINDOW_SIZE, CHECKSUM, URG_POINTER, message)
    # Send the SYN packet to the server
    s.sendto(packet, (HOST, SENDPORT))
    # Wait for SYN-ACK packet from the server
    while True:
        packet, address = s.recvfrom(RECIEVEPORT)
        header = struct.unpack(PACKET_FORMAT, packet[:20])
        flags = header[5]

        if flags == 0b000010 | 0b100000:   # SYN-ACK received
            break

    # Send the ACK packet to the server
    SEQ_NUMBER += 1
    ACK_NUMBER = header[2] + 1
    FLAGS = 0b010000   # ACK flag set
    packet = struct.pack(PACKET_FORMAT, 0, 0, SEQ_NUMBER, ACK_NUMBER,
                         (DATA_OFFSET << 4) + 0, FLAGS, WINDOW_SIZE, CHECKSUM, URG_POINTER)
    s.sendto(packet, (HOST, SENDPORT))

    # Start sending data packets
    seq_number = SEQ_NUMBER
    ack_number = ACK_NUMBER
    window_size = WINDOW_SIZE
    data = b'Hello, server!'
    while len(data) > 0:
        # Pack the data packet
        SEQ_NUMBER = seq_number
        ACK_NUMBER = ack_number
        DATA_OFFSET = 5
        FLAGS = 0b000000   # No flags set
        WINDOW_SIZE = window_size
        CHECKSUM = 0
        URG_POINTER = 0
        packet = struct.pack(PACKET_FORMAT, 0, 0, SEQ_NUMBER, ACK_NUMBER,
                             (DATA_OFFSET << 4) + 0, FLAGS, WINDOW_SIZE, CHECKSUM, URG_POINTER) + data

        # Send the data packet to the server
        s.sendto(packet, (HOST, SENDPORT))

        # Wait for ACK packet from the server
        while True:
            packet, address = s.recvfrom(RECIEVEPORT)
            header = struct.unpack(PACKET_FORMAT, packet[:20])
            flags = header[5]

            if flags == 0b010000:   # ACK received
                ack_number = header[2] + 1
                window_size = header[6]
                break

        # Update sequence number and send the next data packet
        seq_number += len(data)
        data = b''

    # Close the connection
    FLAGS = 0b000001   # FIN flag set
    packet = struct.pack(PACKET_FORMAT, 0, 0, seq_number, ack_number,
                         (DATA_OFFSET << 4) + 0, FLAGS, WINDOW_SIZE, CHECKSUM, URG_POINTER)
    s.sendto(packet, (HOST, SENDPORT))
    s.close()

def receive_data_from_client(HOST='127.0.0.1', RECEIVE_PORT=5055, SEND_PORT=5050):
    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    s.bind((HOST, RECEIVE_PORT))

    # Define the packet format
    PACKET_FORMAT = '!HHLLBBHHH{}s'

    seq_number = 0
    ack_number = 0
    window_size = 1024

    while True:
        # Receive the data packet from the client
        packet, address = s.recvfrom(1024)

        # Unpack the packet header
        header = struct.unpack(PACKET_FORMAT.format(len(packet) - 20), packet[:20])
        flags = header[5]
        seq = header[2]
        data = packet[20:]

        # Check if FIN flag is set
        if flags & 0b000001:
            # Send ACK packet with FIN flag set
            ack_number = seq + len(data)
            packet = struct.pack(PACKET_FORMAT.format(0), 0, 0, seq_number, ack_number,
                                 (5 << 4) + 0, 0b000001, window_size, 0, 0)  # FIN flag set
            s.sendto(packet, (address[0], SEND_PORT))
            break

        # Send ACK packet to the client
        ack_number = seq + len(data)
        packet = struct.pack(PACKET_FORMAT.format(0), 0, 0, seq_number, ack_number,
                             (5 << 4) + 0, 0b010000, window_size, 0, 0)  # ACK flag set
        s.sendto(packet, (address[0], SEND_PORT))

        # Process the data
        print(data.decode())

    # Close the socket
    s.close()

def main():
    user_input = input("Enter 'c' to send data to server or 's' to receive data from client: ")
    if user_input == 'c':
        send_data_to_server()
        print('done')
    elif user_input == 's':
        receive_data_from_client()
        print('done')
    else:
        print("Invalid input, please enter 'c' or 's'.")


if __name__ == '__main__':
    main()
