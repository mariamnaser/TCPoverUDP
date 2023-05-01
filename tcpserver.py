"""
/*******************************************************************************
 * Name          : tcpEmulator.py
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
import socket
import sys
import logging

class Receiver:
    def __init__(self, outputfile, listening_port, address_for_acks, port_for_acks):
        logging.basicConfig(filename='udp_log.txt', level=logging.DEBUG)
        self.stdout = outputfile
        self.listening_port = listening_port
        self.address_for_acks = address_for_acks
        self.port_for_acks = port_for_acks
        self.is_listening = False
        hostname=socket.gethostname()
        self.IPAddr=socket.gethostbyname(hostname)
        print("Your Computer Name is:"+hostname)
        #print("Your Computer IP Address is:"+IPAddr)
    def listen_for_connections(self):
        """
        Listens for incoming connection requests.
        """
        print('here')
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((self.IPAddr, self.listening_port))

        while True:
            # Wait for SYN packet from remote address
            try:
                syn_packet, remote_addr = udp_socket.recvfrom(1024)
                print(syn_packet)
                if syn_packet == b'SYN':
                    print(syn_packet)
                    logging.debug(f'Received SYN packet from {remote_addr}')

                    # Send SYN-ACK packet to remote address
                    syn_ack_packet = b'SYN-ACK'
                    print(syn_ack_packet)
                    udp_socket.sendto(syn_ack_packet, remote_addr)
                    logging.debug(f'Sent SYN-ACK packet to {remote_addr}')

                    # Wait for ACK packet from remote address
                    ack_packet, remote_addr = udp_socket.recvfrom(1024)
                    if ack_packet == b'ACK':
                        logging.debug(f'Received ACK packet from {remote_addr}')

                        # Start data transfer
                        self.transfer_data(udp_socket, remote_addr)

                    else:
                        logging.warning(f'Received unexpected packet from {remote_addr}: {ack_packet}')

                else:
                    logging.warning(f'Received unexpected packet from {remote_addr}: {syn_packet}')

            except socket.timeout:
                logging.warning(f'Timeout waiting for SYN packet')
            except Exception as e:
                logging.error(f'Error during connection setup: {str(e)}')

    def transfer_data(self, udp_socket, remote_addr):
        """
        Transfers data between the remote address and the local client.
        """
        # TODO: Implement data transfer
        pass

    def start(self):
        """
        Starts the receiver to listen for incoming connections.
        """
        self.is_listening = True
        print('initiated')
        self.listen_for_connections()

    def stop(self):
        """
        Stops the receiver from listening for incoming connections.
        """
        self.is_listening = False

#tcpserver file listening_port address_for_acks port_for_acks
#tcpserver output.txt 5050 127.0.0.1 5055
def main():
    args = sys.argv[1:]
    print (len(args))
    print(args)
    outputfile = args[0]
    listening_port = int (args[1])
    address_for_acks = args[2]
    port_for_acks = int (args[3])

    # Create the TCP client
    client = Receiver(outputfile, listening_port, address_for_acks, port_for_acks)

    # Start the TCP client
    client.start()

if __name__ == '__main__':
    main()
