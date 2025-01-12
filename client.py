#client file
import socket
import sys
import codecs
import ipaddress
import threading
import time
import multiprocessing

def start_up():
    units_start = [' ', 'K', 'M', 'G']
    size = 0
    good_file_size_string = False
    good_protocol_number_string = False
    TCP_num = 0
    UDP_num = 0
    while (not good_file_size_string):
        file_size_string = input("Enter file size, in the following format: size units\n(Units are in up to units of gigabites, in one word: GB instead of Giga Byte")
        word_count = len(file_size_string.split())
        if word_count != 2:
            if not file_size_string[file_size_string.find(' '):].isdigit():
                print("Invalid size")
            space_index = file_size_string.find('b')
            if space_index != -1:
                if file_size_string[space_index - 1] in units_start:
                    size = 2 ** (10 * units_start.index(file_size_string[space_index - 1]))
                    good_file_size_string = True
                else:
                    print("Invalid unit")
            else:
                space_index = file_size_string.find('B')
                if space_index == -1 or file_size_string[space_index - 1] not in units_start:
                    print("Invalid unit")
                else:
                    size = 2 ** (3 + 10 * units_start.index(file_size_string[space_index - 1]))
                    good_file_size_string = True
        else:
            print("Invalid number of arguments")
             
    while not good_protocol_number_string:
        tcp_and_udp_string = input("Enter the requested number of TCP and UDP connections, in the following format: number_of_TCP_connections number_of_UDP_connections")
        numbers = tcp_and_udp_string.split()
        if len(numbers) != 2:
            print("Invalid number of arguments")
        elif (not numbers[0].isdigit()) or (not numbers[1].isdigit()):
            print("Invalid numbers")
        else:
            TCP_num = int(numbers[0])
            UDP_num = int(numbers[1])
            good_protocol_number_string = True
    print("All arguments are valid")
    return size, TCP_num, UDP_num

def looking_for_a_server(size):
    server_recieved = False
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP_address = socket.gethostbyname(socket.gethostname())
    magic_cookie = "abcddcba"
    port_num = 5000
    server_udp_port_num = 0
    server_tcp_port_num = 0
    connection_socket.bind((IP_address, port_num))
    print("Our IP adress is: %s\nWe use a port number: %d", IP_address, port_num)
    connection_socket.listen(1000)
    print("Client started, listening for offer requests...")
    while not server_recieved:
        (response, server_IP_address) = connection_socket.recvfrom(1024)
        if response[0:8].decode() != magic_cookie: 
            print("recieved an offer with the wrong cookie")
        elif int(response[8:9].decode()) != 4:
            print("recieved an offer with the wrong message type")
        else: #.
            server_udp_port_num = int(response[9:11].decode())
            server_tcp_port_num = int(response[11:13].decode())
            if server_udp_port_num > 6500 or server_udp_port_num < 0 or server_tcp_port_num > 6500 or server_tcp_port_num < 0:
                print("recieved an invalid port number")
            else:
                server_recieved = True
                print("Received offer from %s", server_IP_address)
 
    return connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address 

def speed_test(size, TCP_num, UDP_num, connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address, port_num):
    threads = []
    magic_cookie = "abcddcba"
    
    for i in range(TCP_num):
        thread = threading.Thread(target=tcp_connection, args=(size, server_tcp_port_num, port_num, IP_address, server_IP_address, i,))
        thread.start()
        threads.append(thread)
        port_num = port_num + 1
        
    for i in range(UDP_num):
        thread = threading.Thread(target=udp_connection, args=(size, connection_socket, server_udp_port_num, port_num, server_IP_address, i, magic_cookie, IP_address,))
        thread.start()
        threads.append(thread)
        port_num = port_num + 1
    
    for thread in threads:
        thread.join()

def tcp_connection(size, server_tcp_port_num, port_num, IP_address, server_IP_address, transfer_num):
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection_socket.bind((IP_address, port_num))
    message_to_send = str(size) + "\n"
    message_to_send = message_to_send.encode("utf-8")

    right_size = False
    while not right_size:
        try:
            connection_socket.settimeout(1)
            start_time = time.time()
            connection_socket.sendto(message_to_send, (server_IP_address, server_tcp_port_num))
            print("Client waiting for TCP message from server, with IP %s...", server_IP_address)
            recieved_message = connection_socket.recv(size + 1)
            connection_socket.settimeout(None)
            end_time = time.time()
            if len(recieved_message) != size + 1:
                print("Client recived data from server with IP %s in TCP transfer number %d in the wrong size, tries again...", server_IP_address, transfer_num)
            else:
                transfer_time = end_time - start_time
                print("TCP transfer #%d finished, total time: %d seconds, total speed: %.2f bits/second", transfer_num, transfer_time, size/transfer_time)
                right_size = True
        except socket.timeout:
            print("In TCP transfer number %d, server did not respond for a full second, assumes server has been disconnected", transfer_num)        
            right_size = True
    connection_socket.close()
    
def udp_connection(size, connection_socket, server_udp_port_num, port_num, server_IP_address, transfer_num, magic_cookie, IP_address):
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connection_socket.bind((IP_address, port_num))
    message_to_send = str(size) + "\n"
    message_to_send = message_to_send.encode("utf-8")
    message_to_send = codecs.encode(magic_cookie + 3 + size, 'utf-8')
    connection_socket.sendto(message_to_send, (server_IP_address, server_udp_port_num))
    total_segments = 0
    current_segment = 0
    segment_counter = 0
    end = False
    start_time = time.time()
    while not end:
        try:
            connection_socket.settimeout(1)
            connection_socket.sendto(message_to_send, (server_IP_address, server_tcp_port_num))
            print("Client waiting for UDP transfer number %d payload from server, with IP %s...", transfer_num, server_IP_address)
            (recieved_message, recieved_server_IP_address) = connection_socket.recvfrom(size)
            connection_socket.settimeout(None)
            if recieved_server_IP_address == server_IP_address:
                recieved_message = recieved_message.decode("utf-8")
                if recieved_message[0:8].decode() != magic_cookie:
                    print("Client UDP transfer number %d recieved a payload with the wrong cookie from the server", transfer_num)
                elif int(recieved_message[8:9].decode()) != 4:
                    print("Client UDP transfer number %d recieved wrong message type", transfer_num)
                else:
                    total_segments = int(recieved_message[9:17].decode())
                    current_segment = int(recieved_message[17:25].decode())
                    segment_counter = segment_counter + 1                    
                if current_segment == total_segments and segment_counter == total_segments:
                    end_time = time.time()
                    transfer_time = end_time - start_time
                    print("UDP transfer #%d finished, total time: %d seconds, total speed: %.2f bits/second, percentage of packets received successfully: %d", transfer_num, transfer_time, size/transfer_time, segment_counter/total_segments)
                    end = True
        except socket.timeout:
            print("In UDP transfer number %d, server did not respond for a full second, assumes server has been disconnected or finished transfering", transfer_num)
            end_time = time.time()
            transfer_time = end_time - start_time
            print("UDP transfer #%d finished, total time: %d seconds, total speed: %.2f bits/second, percentage of packets received successfully: %d", transfer_num, transfer_time, size/transfer_time, segment_counter/total_segments)
    connection_socket.close()
    
    
        
if __name__ == '__main__':
    #starting the client
    port_num = 5000 
    while True:
        size, TCP_num, UDP_num = start_up()
        connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address = looking_for_a_server(size, port_num)
        speed_test(size, TCP_num, UDP_num, connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address, port_num + 1)