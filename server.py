#server_file
import socket
import codecs
import threading

def send_offers(IP_address, port_num, server_udp_port_num, server_tcp_port_num):
    offer_counter = 0
    magic_cookie = "abcddcba"
    offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("02", 'hex') + codecs.decode(hex(server_udp_port_num)[2:], 'hex') + codecs.decode(hex(server_tcp_port_num)[2:], 'hex')
    print(f"Server started, listening on IP address {IP_address}")
    while True:
        try:
            offer_socket.settimeout(1)
            offer_counter = offer_counter + 1
            offer_socket.sendto(message_to_send, ('127.0.0.1', port_num)) #port_num))
            offer_socket.settimeout(None)
        except socket.timeout:
            if offer_counter % 10 == 0:
                print(f"Server boradcasted offers {offer_counter} times")

def udp_connections(udp_socket, magic_cookie, port_number, server_IP_address):
    addresses = []
    threads = []
    transfer_num = 0 
    while True:
        (recievedmessage, address) = udp_socket.recvfrom(1024)
        if codecs.encode(recievedmessage[0:4], 'hex').decode() != magic_cookie: 
            print(f"Server recieved a request with the wrong cookie, from IP: {address[0]}")
        elif int(codecs.encode(recievedmessage[4:5], 'hex'), 16) != 3:
            print(f"Server recieved a request with the wrong message type, from IP: {address[0]}")
        elif address not in addresses: #.
            file_size = int(codecs.encode(recievedmessage[5:13], 'hex'), 16)
            print(f"Server received a request from {address[0]}")
            thread = threading.Thread(target=udp_connection, args=(file_size, magic_cookie, server_IP_address, address[0], address[1], port_number, transfer_num, ))
            thread.start()
            threads.append(thread)
            port_number = port_number + 1
            addresses.append(address)
        
def tcp_connections(tcp_socket):
    threads = []
    transfer_num = 0
    while True:
        tcp_socket.listen(1000)
        specific_tcp_socket, (client_IP_address, client_port_nume) = tcp_socket.accept()
        recievedmessage = specific_tcp_socket.recv(1024)
        file_size = int(codecs.encode(recievedmessage[:-1], 'hex'), 16)
        print(f"Server received a request from client with IP: {client_IP_address}, and port number: {client_port_nume}")
        thread = threading.Thread(target=tcp_connection, args=(file_size, client_IP_address, specific_tcp_socket, transfer_num, ))
        thread.start()
        threads.append(thread)

def udp_connection(file_size, magic_cookie, server_IP_address, client_IP_address, client_port_number, port_number, transfer_num):
    total_segments = max(22, int(file_size/(2 ** 26.75) + 10))
    segment_counter = 0
    segment_size = int(file_size/total_segments)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_IP_address, port_number))
    while segment_counter < total_segments:
        message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("04", 'hex') + codecs.decode(hex(total_segments)[2:].rjust(16, '0'), 'hex') + codecs.decode(hex(segment_counter)[2:].rjust(16 , '0'), 'hex')
        message_to_send = message_to_send + codecs.decode("".rjust(segment_size*2, 'a'), 'hex')
        udp_socket.sendto(message_to_send, (client_IP_address, client_port_number))
        segment_counter = segment_counter + 1
        if segment_counter % 10 == 0:
            print(f"Server already sent {segment_counter} payloads in UDP transfer #{transfer_num} to client with IP: {client_IP_address}")
        
def tcp_connection(file_size, client_IP_address, tcp_socket, transfer_num):
    message_to_send = ''.ljust(int(file_size*2), 'a')
    tcp_socket.send(codecs.decode(message_to_send, 'hex') + b'\n')
    print(f"Server sent required data, in size: {file_size} over a TCP #{transfer_num} connection for client with IP: {client_IP_address}")


if __name__ == '__main__':
    magic_cookie = "abcddcba"
    port_num = 5005
    server_udp_port_num = 6001
    server_tcp_port_num = 6002
    IP_address = '0.0.0.0' # socket.gethostbyname(socket.gethostname())
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    udp_socket.bind((IP_address, server_udp_port_num))
    tcp_socket.bind((IP_address, server_tcp_port_num))
    print(f"Our IP adress is: {IP_address}\nWe use a port number: {port_num}")
    offer_thread = threading.Thread(target=send_offers, args=(IP_address, port_num, server_udp_port_num, server_tcp_port_num,))
    udp_connections_thread = threading.Thread(target=udp_connections, args=(udp_socket, magic_cookie, server_udp_port_num + 1000, IP_address,))
    tcp_connections_thread = threading.Thread(target=tcp_connections, args=(tcp_socket, ))
    offer_thread.start()
    udp_connections_thread.start()
    tcp_connections_thread.start()
