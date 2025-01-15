#server_file
import socket
import codecs
import threading

"""
In this function we are broadcasting offers to the clients
Every second we send a new broadcast offer message

Args:
    server_IP_address: The IP address of the server
    broadcast_port_num: The port number that we send the broadcasts to
    server_udp_port_num: The number of the UDP port that the server will accept UDP transfers to
    server_tcp_port_num: The number of the TCP port that the server will accept TCP transfers to
    magic_cookie: the cookie required for the messages
    offer_message_number: the number that we identify the offer message with
"""

def send_offers(server_IP_address, broadcast_port_num, server_udp_port_num, server_tcp_port_num, magic_cookie, offer_message_number):
    offer_counter = 0
    #initializing a socket for broadcasting
    offer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    offer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #creating a message to send
    message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("0" + str(offer_message_number), 'hex') + codecs.decode(hex(server_udp_port_num)[2:], 'hex') + codecs.decode(hex(server_tcp_port_num)[2:], 'hex')
    print(f"\033[92mServer started, listening on IP address {server_IP_address}")
    #broadcasting forever
    while True:
        try:
            #every second there will be a timeout, since this socket is not getting any messages to it
            #then it will bradcast the message again
            offer_socket.settimeout(1)
            offer_counter = offer_counter + 1
            #sending the broadcast message
            offer_socket.sendto(message_to_send, ('255.255.255.255', broadcast_port_num)) #port_num))
            offer_socket.settimeout(None)
        except socket.timeout:
            if offer_counter % 10 == 0:
                #printing interesting statistic
                print(f"\033[94mServer boradcasted offers {offer_counter} times")

"""
In this function we recive requests for UDP connections from the clients
And then, creating and starting a thread to transfer them the requested data to

Args:
    udp_socket: The socket that the server will recieve UDP requests from clients to
    magic_cookie: the cookie required for the messages
    server_udp_port_num: The number of the UDP port that the server will accept UDP transfers to
    server_IP_address: The IP address of the server
    request_message_number: the number that we identify the request message with
    payload_message_number: the number that we identify the payload message with
"""

def udp_connections(udp_socket, magic_cookie, server_udp_port_number, server_IP_address, request_message_number, payload_message_number):
    threads = []
    transfer_num = 0
    #recieving connections forever
    while True:
        #recieving a udp request from a client
        (recievedmessage, (client_IP_address, client_udp_port_number)) = udp_socket.recvfrom(1024)
        #checking if this is the correct cookie
        if codecs.encode(recievedmessage[0:4], 'hex').decode() != magic_cookie: 
            print(f"\033[91mServer recieved a request with the wrong cookie, from IP: {client_IP_address}")
        #checking if this is a request message
        elif int(codecs.encode(recievedmessage[4:5], 'hex'), 16) != request_message_number:
            print(f"\033[91mServer recieved a request with the wrong message type, from IP: {client_IP_address}")
            
        #valid message
        else:
            file_size = int(codecs.encode(recievedmessage[5:13], 'hex'), 16)
            print(f"\033[92mServer received a request from {client_IP_address}")
            #creating a thread to start transfering data over a UDP connection
            thread = threading.Thread(target=udp_connection, args=(file_size, magic_cookie, server_IP_address, client_IP_address, client_udp_port_number, server_udp_port_number, transfer_num, payload_message_number, ))
            #starting the thread
            thread.start()
            threads.append(thread)
            transfer_num = transfer_num + 1
            server_udp_port_number = server_udp_port_number + 1

"""
In this function we recive requests for TCP connections from the clients
And then, creating and starting a thread to transfer them the requested data to

Args:
    tcp_socket: The socket that the server will recieve TCP requests from clients to
"""
  
def tcp_connections(tcp_socket):
    threads = []
    transfer_num = 0
    #recieving connections forever
    while True:
        tcp_socket.listen(1000)
        #connecting to a TCP client socket
        specific_tcp_socket, (client_IP_address, client_port_nume) = tcp_socket.accept()
        #receiving a message from this socket
        recievedmessage = specific_tcp_socket.recv(1024)
        file_size = int(codecs.encode(recievedmessage[:-1], 'hex'), 16)
        print(f"\033[92mServer received a request from client with IP: {client_IP_address}, and port number: {client_port_nume}")
        #creating a thread to start transfering data over a TCP connection
        thread = threading.Thread(target=tcp_connection, args=(file_size, client_IP_address, specific_tcp_socket, transfer_num, ))
        #starting the thread
        thread.start()
        threads.append(thread)

"""
In this function we initialize a UDP socket 
Sending data in segments to the client by it using a UDP connection

Args:
    file_size: The requested file size by the client
    magic_cookie: the cookie required for the messages
    server_IP_address: The IP address of the server
    client_IP_address: The IP address of the client
    client_port_num: The port number of the client socket that we will send data to
    server_udp_port_num: The number of the UDP port that the server will accept UDP transfers to
    trasnfer_num: The number of the UDP transfer out of the total UDP transfers that we have made
    payload_message_number: the number that we identify the payload message with
"""

def udp_connection(file_size, magic_cookie, server_IP_address, client_IP_address, client_port_number, server_udp_port_number, transfer_num, payload_message_number):
    #calculating the number of segments to send
    #changes depending on the data size requested by the client
    total_segments = max(22, int(file_size/(2 ** 26.75) + 10))
    segment_counter = 0
    segment_size = int(file_size/total_segments)
    #initializing a UDP soxket to send the data with
    server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_udp_socket.bind((server_IP_address, server_udp_port_number))
    #while there is still data to be sent
    #keep iterating
    while segment_counter < total_segments:
        #creating a payload message header to send 
        message_to_send = codecs.decode(magic_cookie, 'hex') + codecs.decode("0" + str(payload_message_number), 'hex') + codecs.decode(hex(total_segments)[2:].rjust(16, '0'), 'hex') + codecs.decode(hex(segment_counter)[2:].rjust(16 , '0'), 'hex')
        #adding the data
        message_to_send = message_to_send + b'\a' * segment_size
        #adding missing data in the last segment
        if segment_counter + 1 == total_segments:
            message_to_send = message_to_send + b'\a' * int(file_size%segment_size)
        #sending the message
        server_udp_socket.sendto(message_to_send, (client_IP_address, client_port_number))
        segment_counter = segment_counter + 1
        #printing interesting statistic
        if segment_counter % 10 == 0:
            print(f"\033[94mServer already sent {segment_counter} payloads in UDP transfer #{transfer_num} to client with IP: {client_IP_address}")
    #closing the socket
    server_udp_socket.close()

"""
In this function we initialize a TCP socket 
Sending data to the client by it using a TCP connection

Args:
    file_size: The requested file size by the client
    client_IP_address: The IP address of the client
    server_tcp_socket: The socket that we will send the client the data with, using a TCP connection
    trasnfer_num: The number of the UDP transfer out of the total UDP transfers that we have made
"""
       
def tcp_connection(file_size, client_IP_address, server_tcp_socket, transfer_num):
    #creating the message to send
    message_to_send = b'\a' * file_size
    #adding the '\n' charachter and sending the data
    server_tcp_socket.send(message_to_send + b'\n')
    print(f"\033[92mServer sent required data, in size: {file_size} over a TCP #{transfer_num} connection for client with IP: {client_IP_address}")
    #closing the socket
    server_tcp_socket.close()


if __name__ == '__main__':
    magic_cookie = "abcddcba"
    port_num = 5005
    server_udp_port_num = 6001
    server_tcp_port_num = 6002
    offer_message_number = 2
    request_message_number = 3
    payload_message_number = 4
    IP_address = socket.gethostbyname(socket.gethostname())
    #creating sockets for recieving udp and tcp requests from clients
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    udp_socket.bind((IP_address, server_udp_port_num))
    tcp_socket.bind((IP_address, server_tcp_port_num))
    print(f"\033[94mOur IP adress is: {IP_address}\nWe use a port number: {port_num}")
    #creating threads
    offer_thread = threading.Thread(target=send_offers, args=(IP_address, port_num, server_udp_port_num, server_tcp_port_num, magic_cookie, offer_message_number, ))
    udp_connections_thread = threading.Thread(target=udp_connections, args=(udp_socket, magic_cookie, server_udp_port_num + 1000, IP_address, request_message_number, payload_message_number))
    tcp_connections_thread = threading.Thread(target=tcp_connections, args=(tcp_socket, ))
    #starting threads
    offer_thread.start()
    udp_connections_thread.start()
    tcp_connections_thread.start()
