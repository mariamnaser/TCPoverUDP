import socket
import hashlib
import zlib
import time
import logging
import sys

logging.basicConfig(level=logging.DEBUG)
#get machine IP
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

def compute_tcp_checksum(data, src_addr, src_port, dst_port):
    pseudo_header = src_addr + socket.inet_aton(ip_address) + b'\x00' + socket.IPPROTO_TCP.to_bytes(1, byteorder='big') + len(data).to_bytes(2, byteorder='big')
    tcp_segment = src_port.to_bytes(2, byteorder='big') + dst_port.to_bytes(2, byteorder='big') + b'\x00\x00\x00\x00' + data
    segment_and_pseudo = pseudo_header + tcp_segment
    if len(segment_and_pseudo) % 2 != 0:
        segment_and_pseudo += b'\x00'
    s = sum(int.from_bytes(segment_and_pseudo[i:i+2], byteorder='big') for i in range(0, len(segment_and_pseudo), 2))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff

# Function to send a SYN message to the server to initiate the handshake
def send_syn(sock, server_ip, server_port):
    logging.debug("Sending SYN to %s:%d", server_ip, server_port)
    sock.sendto(b"SYN", (server_ip, server_port))

# Function to send an ACK message to complete the handshake and establish the connection
def send_ack(sock, addr):
    logging.debug("Sending ACK to %s:%d", addr[0], addr[1])
    sock.sendto(b"ACK", addr)

# Function to send a packet to the server
def send_packet(sock, seq_num, packet, remote_addr, remote_port, window_size):
    # Set the TCP header fields
    _, port = sock.getsockname()
    source_port = port # Use the local port passed as argument
    dest_port = remote_port # Use the remote port passed as argument
    seq_num = seq_num.to_bytes(4, byteorder='big')
    ack_num = b'\x00\x00\x00\x00' # Set to zero
    data_offset_reserved_flags = b'\x50\x00' # Data offset = 5, Reserved = 0, Flags = 0
    window_size = window_size.to_bytes(2, byteorder='big') # Convert window size to bytes
    checksum = b'\x00\x00' # Set to zero
    urgent_pointer = b'\x00\x00' # Set to zero

    # Concatenate the header and packet data
    tcp_header = source_port + dest_port + seq_num + ack_num + data_offset_reserved_flags + window_size + checksum + urgent_pointer
    data = tcp_header + packet

    # Compute the TCP checksum over the TCP header and data
    checksum = compute_tcp_checksum(data, remote_addr, source_port, dest_port)

    # Replace the checksum field in the header with the computed value
    checksum_bytes = checksum.to_bytes(2, byteorder='big')
    tcp_header = tcp_header[:16] + checksum_bytes + tcp_header[18:]

    # Send the packet to the remote address and port
    logging.debug("Sending packet %d to %s:%d", seq_num, remote_addr, remote_port)
    sock.sendto(data, (remote_addr, remote_port))

# Function to send a FIN message to signal the end of transmission

def send_fin(sock, remote_addr, remote_port):
    logging.debug("Sending FIN to %s:%d", remote_addr, remote_port)
    sock.sendto(b"FIN", (remote_addr, remote_port))
#another thing

def selective_repeat_sender(file_path, server_ip, server_port, window_size, ack_port):
    # Create a UDP socket and bind it to the local port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 0))

    # Set up the sliding window parameters
    TIMEOUT = 0.5 # Initial timeout in seconds
    THRESHOLD = 16 # Initial threshold value
    buffer = []

    # Send a SYN message to the server to initiate the handshake
    send_syn(sock, server_ip, server_port)

    # Wait for a SYN-ACK message from the server
    remote_addr = None
    remote_port = None
    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"SYN-ACK":
            # Send an ACK message to complete the handshake and establish the connection
            send_ack(sock, addr)
            remote_addr = addr[0]
            remote_port = int(addr[1])
            logging.info("Connected to remote address: %s remote port: %d", remote_addr, remote_port)
            break

    # Read the file and split it into packets
    packet_size = 1024
    with open(file_path, 'rb') as file:
        while True:
            packet = file.read(packet_size)
            if not packet:
                break
            seq_num = len(buffer)
            checksum, hash_val = compute_checksum_and_hash(packet)
            buffer.append((seq_num, packet, checksum, hash_val))

    # Send the packets in the buffer using the selective repeat protocol
    base = 0
    next_seq_num = 0
    packets_in_flight = {} # Dictionary to keep track of packets in flight
    last_ack_time = time.monotonic() # Record the time of the last received ACK
    while base < len(buffer):
        # Send packets up to the window size or until the end of the buffer
        while next_seq_num < base + window_size and next_seq_num < len(buffer):
            seq_num, packet, checksum, hash_val = buffer[next_seq_num]
            send_packet(sock, seq_num, packet, checksum, hash_val, remote_addr, remote_port)
            packets_in_flight[seq_num] = (packet, checksum, hash_val)
            next_seq_num += 1

        # Check for ACKs from the server
        try:
            data, addr = sock.recvfrom(1024)
        except socket.timeout:
            # Timeout occurred, retransmit all packets in flight
            logging.error("Timeout occurred, retransmitting packets")
            TIMEOUT *= 2
            THRESHOLD = max(THRESHOLD / 2, 1)
            for seq_num, packet_info in packets_in_flight.items():
                packet, checksum, hash_val = packet_info
                send_packet(sock, seq_num, packet, checksum, hash_val, remote_addr, remote_port)
            continue

        if addr[1] != ack_port:
            # Ignore packets from other ports
            continue

        if data == b"FIN":
            # Send a FIN request to signal the end of transmission
            send_fin(sock, remote_addr, remote_port)
            print("Sent FIN request to remote address:", remote_addr, "remote port:", remote_port)
            logging.info("Transmission complete")

def main():
    # Check if command-line arguments are correct
    if len(sys.argv) != 6:
        print(f"Usage: {sys.argv[0]} <inputfile> <remote_address> <remote_port> <window_size> <ack_port>")
        return

    inputfile = sys.argv[1]
    remote_address = sys.argv[2]
    remote_port = int(sys.argv[3])
    window_size = int(sys.argv[4])
    ack_port = float(sys.argv[5])

    # Call the selective_repeat_sender function with the provided arguments
    selective_repeat_sender(inputfile, remote_address, remote_port, window_size, ack_port)

if __name__ == "__main__":
    main()
