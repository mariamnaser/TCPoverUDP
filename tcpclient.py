"""
/*******************************************************************************
 * Name          : tcpclient.py
 * Author        : Mariam Naser
 * Date          : April 25, 2023
 * Description   : TCP using UDP base
 ******************************************************************************/
"""
##Libraries
##Libraries
import socket
import sys
import logging


class sender:
    def __init__(self, input, address_of_udpl, port_number_of_udpl, windowsize, ack_port_number):
        logging.basicConfig(filename='udp_log.txt', level=logging.DEBUG)
        self.input = input
        self.recv_addr = (address_of_udpl, port_number_of_udpl)
        self.windowsize = windowsize
        self.ack_port = ack_port_number
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hostname=socket.gethostname()
        IPAddr=socket.gethostbyname(hostname)
        print("Your Computer Name is:"+hostname)
        print("Your Computer IP Address is:"+IPAddr)

    def start(self):
        # Establish connection with receiver
        print(address_of_udpl, int(port_number_of_udpl))
        if not self.establish_connection(self.remote_addr):
            logging.error('Could not establish connection')
            return

        # Start sending data
        self.send_data()

    def establish_connection(self, remote_addr):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('1')
        # Set timeout for receiving ACK
        udp_socket.settimeout(.5)

        # Send SYN packet to remote address
        syn_packet = b'SYN'
        try:
            udp_socket.sendto(syn_packet, remote_addr)
            print('sent')
            logging.debug(f'Sent SYN packet to {remote_addr}')
        except Exception as e:
            logging.error(f'Error sending SYN packet: {str(e)}')
            return False
        print('2')
        # Wait for SYN-ACK packet from remote address
        try:
            syn_ack_packet, remote_addr = udp_socket.recvfrom(1024)
            if syn_ack_packet == b'SYN-ACK':
                print('got reponse')
                logging.debug(f'Received SYN-ACK packet from {remote_addr}')
            else:
                logging.warning(f'Received unexpected packet from {remote_addr}: {syn_ack_packet}')
                return False
        except socket.timeout:
            logging.warning(f'Timeout waiting for SYN-ACK packet from {remote_addr}')
            return False
        except Exception as e:
            logging.error(f'Error receiving SYN-ACK packet: {str(e)}')
            return False

        # Send ACK packet to remote address
        ack_packet = b'ACK'
        try:
            udp_socket.sendto(ack_packet, remote_addr)
            logging.debug(f'Sent ACK packet to {remote_addr}')
            print('sent ack')
            return True
        except Exception as e:
            logging.error(f'Error sending ACK packet: {str(e)}')
            return False

#tcpclient file address_of_udpl port_number_of_udpl windowsize ack_port_number
#tcpclient input.txt address_of_udpl port_number_of_udpl windowsize ack_port_number

def main():
    args = sys.argv[1:]
    print (len(args))

    input = args[0]
    address_of_udpl = args[1]
    port_number_of_udpl = int(args[2])
    windowsize = int(args[3])
    ack_port_number = int(args[4])
    print(address_of_udpl, int(port_number_of_udpl))

    # create a new instance of sender
    client = sender(input, address_of_udpl, port_number_of_udpl, windowsize, ack_port_number)

    # initiate the handshake
    remote_addr = (address_of_udpl, ack_port_number)
    if not client.establish_connection(remote_addr):
        print('Connection establishment failed')
        return

    # call the start method to send the data
    client.start()


if __name__ == '__main__':
    main()
