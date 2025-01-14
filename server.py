#server_file
import socket
import codecs
import threading
import time

def send_offers(IP_address, port_num, server_udp_port_num, server_tcp_port_num):
    offer_counter = 0
    magic_cookie = "abcddcba"
    offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    offer_socket.bind((IP_address, port_num))
    message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("02", 'hex') + codecs.decode(hex(server_udp_port_num)[2:], 'hex') + codecs.decode(hex(server_tcp_port_num)[2:], 'hex')
    print(f"Server started, listening on IP address {IP_address}")
    while True:
        try:
            offer_socket.settimeout(1)
            offer_counter = offer_counter + 1
            offer_socket.sendto(message_to_send, ('255.255.255.255', port_num))
            offer_socket.settimeout(None)
        except socket.timeout:
            if offer_counter % 10 == 0:
                print(f"Server boradcasted offers {offer_counter} times")

def udp_connections(udp_socket, magic_cookie, port_number, server_IP_address):
    threads = []
    while True:
        (recievedmessage, address) = udp_socket.recvfrom(1024)
        if codecs.encode(recievedmessage[0:4], 'hex').decode() != magic_cookie: 
            print(f"Server recieved a request with the wrong cookie, from IP: {address[0]}")
        elif int(codecs.encode(recievedmessage[4:5], 'hex'), 16) != 3:
            print(f"Server recieved a request with the wrong message type, from IP: {address[0]}")
        else: #.
            file_size = int(codecs.encode(recievedmessage[5:13], 'hex'), 16)
            print(f"Server received a request from {address[0]}")
            thread = threading.Thread(target=udp_connection, args=(file_size, magic_cookie, server_IP_address, address[0], address[1], port_number, ))
            thread.start()
            threads.append(thread)
            port_number = port_number + 1
        
def tcp_connections(tcp_socket, port_number, server_IP_address):
    threads = []
    while True:
        tcp_socket.listen(1000)
        specific_tcp_socket, (client_IP_address, client_port_nume) = tcp_socket.accept()
        recievedmessage = specific_tcp_socket.recv(1024)
        file_size = int(str(recievedmessage.decode())[:-1])
        print(f"Server received a request from client with IP: {client_IP_address}, and port number: {client_port_nume}")
        thread = threading.Thread(target=tcp_connection, args=(file_size, port_number, server_IP_address, client_IP_address, client_port_nume,))
        thread.start()
        threads.append(thread)
        port_number = port_number + 1

def udp_connection(file_size, magic_cookie, server_IP_address, client_IP_address, client_port_number, port_number):
    total_segments = max(22, int(file_size/(2 ** 26.75) + 10))
    segment_counter = 0
    segment_size = file_size/total_segments
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_IP_address, port_number))
    while segment_counter < total_segments:
        message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("04", 'hex') + codecs.decode(str(total_segments).ljust(16 - len(str(total_segments)), '00'), 'hex') + codecs.decode(str(segment_counter).ljust(16 - len(str(segment_counter)), '00'), 'hex')
        message_to_send = message_to_send + codecs.decode("".rjust(segment_size, 'aa'), 'hex')
        udp_socket.sendto(message_to_send, (client_IP_address, client_port_number))
        segment_counter = segment_counter + 1
        if segment_counter % 10 == 0:
            print(f"Server already sent {segment_counter} payloads to client with IP: {client_IP_address}")
        
def tcp_connection(file_size, port_number, server_IP_address, client_IP_address, client_port_number):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((server_IP_address, port_number))
    message_to_send = ''.ljust(file_size, 'aa') + '\n'
    tcp_socket.sendto(codecs.decode(message_to_send, 'hex'), (client_IP_address, client_port_number))


if __name__ == '__main__':
    magic_cookie = "abcddcba"
    port_num = 6000
    server_udp_port_num = 6001
    server_tcp_port_num = 6002
    IP_address = socket.gethostbyname(socket.gethostname())
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    udp_socket.bind((IP_address, server_udp_port_num))
    tcp_socket.bind((IP_address, server_tcp_port_num))
    print(f"Our IP adress is: {IP_address}\nWe use a port number: {port_num}")
    offer_thread = threading.Thread(target=send_offers, args=(IP_address, port_num, server_udp_port_num, server_tcp_port_num,))
    udp_connections_thread = threading.Thread(target=udp_connections, args=(udp_socket, magic_cookie, server_udp_port_num + 1000, IP_address))
    tcp_connections_thread = threading.Thread(target=tcp_connections, args=(tcp_socket, server_udp_port_num + 2000, IP_address))
    offer_thread.start()
    time.sleep(1)
    udp_connections_thread.start()
    tcp_connections_thread.start()

