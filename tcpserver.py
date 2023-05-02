import socket
import hashlib
import logging

#get machine IP
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print(ip_address)
TIMEOUT = 0.5
logging.basicConfig(level=logging.ERROR)

def receive_packet(sock):
    """
    Receive a packet from the socket and return the sequence number, packet, checksum, and hash.
    """
    packet_data, addr = sock.recvfrom(1024)

    # Parse the TCP header fields
    source_port = int.from_bytes(packet_data[:2], byteorder='big')
    dest_port = int.from_bytes(packet_data[2:4], byteorder='big')
    seq_num = int.from_bytes(packet_data[4:8], byteorder='big')
    ack_num = int.from_bytes(packet_data[8:12], byteorder='big')
    data_offset_reserved_flags = int.from_bytes(packet_data[12:14], byteorder='big')
    window_size = int.from_bytes(packet_data[14:16], byteorder='big')
    checksum = int.from_bytes(packet_data[16:18], byteorder='big')
    urgent_pointer = int.from_bytes(packet_data[18:20], byteorder='big')

    # Extract the packet data
    packet = packet_data[20:].decode()

    # Compute the TCP checksum over the TCP header and data
    tcp_header = packet_data[:20]
    computed_checksum = compute_tcp_checksum(tcp_header + packet.encode(), addr[0], dest_port, source_port)

    # Verify the checksum
    if computed_checksum != checksum:
        logging.warning("Checksum mismatch: computed=%d, received=%d", computed_checksum, checksum)

    # Return the parsed fields and packet data
    return seq_num, packet, checksum, computed_checksum

def send_nak(seq_num, sock, addr):
    """
    Send a NAK message for the packet with the given sequence number to the specified address.
    """
    sock.sendto(str(seq_num).encode(), addr)
    logging.debug("Sent NAK for packet with sequence number: %s", seq_num)

def selective_repeat_receiver(outputfile, listening_port, address_for_acks, port_for_acks):
    """
    Receive packets using the selective repeat protocol with checksum and hash verification.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', listening_port))

        # Set up the sliding window parameters
        WINDOW_SIZE = 10
        buffer = []

        # Wait for a SYN message from the sender to initiate the handshake
        data, addr = sock.recvfrom(1024)
        if data == b"SYN":
            # Send a SYN-ACK message to the sender
            sock.sendto(b"SYN-ACK", addr)

            # Wait for an ACK message from the sender to complete the handshake and establish the connection
            data, addr = sock.recvfrom(1024)
            if data == b"ACK":
                remote_addr = addr[0]
                remote_port = int(addr[1])
                logging.info("Connected to remote address: %s remote port: %s", remote_addr, remote_port)

                expected_seq_num = 0
                received_packets = {} # Dictionary to keep track of received packets
                timers = {} # Dictionary to keep track of timers for each packet
                while True:
                    # Check if any timers have expired
                    for seq_num, timer in timers.items():
                        if time.time() > timer:
                            # Timer has expired, packet is lost, retransmit it
                            packet_data, addr = received_packets[seq_num]
                            sock.sendto(packet_data, addr)
                            timers[seq_num] = time.time() + TIMEOUT

                    sock.settimeout(TIMEOUT)
                    try:
                        seq_num, packet, packet_checksum, packet_hash = receive_packet(sock)
                        logging.debug("Received packet with sequence number: %s", seq_num)

                        # Verify the checksum and hash
                        if hashlib.sha256(packet.encode()).hexdigest() == packet_checksum and hashlib.md5(packet.encode()).hexdigest() == packet_hash:
                            if seq_num == expected_seq_num:
                                received_packets[seq_num] = packet
                                timers[seq_num] = time.time() + TIMEOUT
                                while expected_seq_num in received_packets:
                                    expected_seq_num += 1
                                # write the packet to the output file
                                with open(outputfile, 'a') as file:
                                    file.write(packet)
                                # Check if any packets in the buffer can now be sent
                                for seq_num, packet_data, addr in buffer:
                                    if seq_num in received_packets:
                                        buffer.remove((seq_num, packet_data, addr))
                                        # Send the packet to the receiver
                                        sock.sendto(packet_data, addr)
                                        timers[seq_num] = time.time() + TIMEOUT
                            else:
                                # Packet is out of sequence
                                if seq_num not in received_packets:
                                    received_packets[seq_num] = packet
                                    send_nak(seq_num, sock, addr)
                                    # Add packet to buffer for potential retransmission
                                    buffer.append((seq_num, packet_data, addr))
                                    timers[seq_num] = time.time() + TIMEOUT
                        else:
                            # Packet is corrupted
                            send_nak(seq_num, sock, addr)
                            # Add packet to buffer for potential retransmission
                            buffer.append((seq_num, packet_data, addr))
                            timers[seq_num] = time.time() + TIMEOUT
                        # Perform congestion control to reduce packet loss
                        if len(buffer) > WINDOW_SIZE:
                            # Send a NAK for all packets in the buffer
                            for seq_num, packet_data, addr in buffer:
                                send_nak(seq_num, sock, addr)
                            buffer = []

                    except socket.timeout:
                        logging.info("Timeout occurred while waiting for packet")
                        # Send a NAK for all expected packets in the window
                        for seq_num in range(expected_seq_num, expected_seq_num + WINDOW_SIZE):
                            if seq_num not in received_packets:
                                send_nak(seq_num, sock, addr)
                            # Restart timer for the first unacknowledged packet
                                timer = Timer(TIMEOUT_DURATION, handle_timeout, args=[expected_seq_num])
                                try:
                                    timer.start()
                                except:
                                    logging.debug("An error occurred while starting the timer")
    except Exception as e:
        logging.error("An error occurred: %s", e)
