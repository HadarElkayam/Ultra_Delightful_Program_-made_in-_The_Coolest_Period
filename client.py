#client file
import socket
import codecs
import threading
import time

def start_up():
    units_start = [' ', 'K', 'M', 'G']
    size = 0
    good_file_size_string = False
    good_protocol_number_string = False
    TCP_num = 0
    UDP_num = 0
    while (not good_file_size_string):
        file_size_string = input("Enter file size, in the following format: size units\n(Units are in up to units of gigabites, in one word: GB instead of Giga Byte\n")
        word_count = len(file_size_string.split())
        if word_count == 2:
            if not file_size_string[:file_size_string.find(' ')].isdigit():
                print("Invalid size")
            else:
                space_index = file_size_string.find('b')
                if space_index != -1:
                    if file_size_string[space_index - 1] in units_start:
                        size = 2 ** (-3 + 10 * units_start.index(file_size_string[space_index - 1]))
                        good_file_size_string = True
                    else:
                        print("Invalid unit")
                else:
                    space_index = file_size_string.find('B')
                    if space_index == -1 or file_size_string[space_index - 1] not in units_start:
                        print("Invalid unit")
                    else:
                        size = 2 ** (10 * units_start.index(file_size_string[space_index - 1]))
                        good_file_size_string = True
        else:
            print("Invalid number of arguments")
             
    while not good_protocol_number_string:
        tcp_and_udp_string = input("Enter the requested number of TCP and UDP connections, in the following format: number_of_TCP_connections number_of_UDP_connections\n")
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

def looking_for_a_server(port_num):
    server_recieved = False
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP_address = '127.0.0.1' #socket.gethostbyname(socket.gethostname())
    magic_cookie = "abcddcba"
    server_udp_port_num = 0
    server_tcp_port_num = 0
    connection_socket.bind((IP_address, port_num))
    print(f"Our IP adress is: {IP_address}\nWe use a port number: {port_num}")
    print("Client started, listening for offer requests...")
    while not server_recieved:
        (response, server_IP_address) = connection_socket.recvfrom(1024)
        if codecs.encode(response[0:4], 'hex').decode() != magic_cookie: 
            print("recieved an offer with the wrong cookie")
        elif int(codecs.encode(response[4:5], 'hex'), 16) != 2:
            print("recieved an offer with the wrong message type")
        else: #.
            server_udp_port_num = int(codecs.encode(response[5:7], 'hex'), 16)
            server_tcp_port_num = int(codecs.encode(response[7:9], 'hex'), 16)
            if server_udp_port_num > 6500 or server_udp_port_num < 0 or server_tcp_port_num > 6500 or server_tcp_port_num < 0:
                print("recieved an invalid port number")
            else:
                server_recieved = True
                print(f"Received offer from {server_IP_address[0]}")
 
    return connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address[0] 

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
    message_to_send = hex(size)[2:]
    if len(message_to_send) % 2 != 0:
        message_to_send = message_to_send.rjust(1 + len(message_to_send), '0')
    message_to_send = codecs.decode(message_to_send, 'hex') + b'\n'

    end = False
    while not end:
        try:
            start_time = time.time()
            print(f"Client waiting for TCP message from server, with IP {server_IP_address}...")
            connection_socket.connect((server_IP_address, server_tcp_port_num))
            connection_socket.settimeout(1)
            connection_socket.send(message_to_send)
            recieved_message = connection_socket.recv(size + 1)
            connection_socket.settimeout(None)
            end_time = time.time()
            if len(recieved_message) != size + 1:
                print(f"Client recived data from server with IP {server_IP_address} in TCP transfer number {transfer_num} in the wrong size, failed.")
                end = True
            else:
                transfer_time = end_time - start_time
                print(f"TCP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second")
                end = True
        except socket.timeout:
            print(f"In TCP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected")        
            end = True
    connection_socket.close()
    
def udp_connection(size, connection_socket, server_udp_port_num, port_num, server_IP_address, transfer_num, magic_cookie, IP_address):
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connection_socket.bind((IP_address, port_num))
    hex_size = hex(size)[2:]
    if len(hex_size) != 16:
        hex_size = hex_size.rjust(16, '0')
    message_to_send = codecs.decode(magic_cookie + "03" + hex_size, 'hex')
    connection_socket.sendto(message_to_send, (server_IP_address, server_udp_port_num))
    total_segments = 0
    current_segment = 0
    segment_counter = 0
    segment_len = 0
    end = False
    start_time = time.time()
    print(f"Client waiting for UDP transfer number {transfer_num} payloads from server, with IP {server_IP_address}...")
    try:
        connection_socket.sendto(message_to_send, (server_IP_address, server_udp_port_num))
        connection_socket.settimeout(1)
    except socket.timeout:
        print(f"In UDP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected or finished transfering")
        end = True
    while not end:
        try:
            (recieved_message, recieved_server_IP_address) = connection_socket.recvfrom(size)
            connection_socket.settimeout(None)
            if recieved_server_IP_address[0] == server_IP_address:
                if codecs.encode(recieved_message[0:4], 'hex').decode() != magic_cookie:
                    print(f"Client UDP transfer number {server_IP_address} recieved a payload with the wrong cookie from the server")
                elif int(codecs.encode(recieved_message[4:5], 'hex'), 16) != 4:
                    print(f"Client UDP transfer number {transfer_num} recieved wrong message type")
                else:
                    total_segments = int(codecs.encode(recieved_message[5:13], 'hex'), 16)
                    current_segment = int(codecs.encode(recieved_message[13:21], 'hex'), 16)
                    segment_counter = segment_counter + 1                    
                    segment_len = segment_len + len(recieved_message) - 20
                if current_segment == total_segments or segment_counter == total_segments:
                    end_time = time.time()
                    transfer_time = end_time - start_time
                    print(f"UDP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second, percentage of packets received successfully: {int(segment_counter/total_segments)*100}%")
                    end = True
        except socket.timeout:
            print(f"In UDP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected or finished transfering")
            end_time = time.time()
            transfer_time = end_time - start_time
            print(f"UDP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second, percentage of packets received successfully: {int(segment_counter/total_segments)}%")
    connection_socket.close()
    
    
        
if __name__ == '__main__':
    #starting the client
    port_num = 5005
    while True:
        size, TCP_num, UDP_num = start_up()
        connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address = looking_for_a_server(port_num)
        speed_test(size, TCP_num, UDP_num, connection_socket, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address, port_num + 3000)