#client file
import socket
import codecs
import threading
import time

"""
This function is the "start up" state of the client 
We recieve from the client the file size and the number of TCP and UDP connections 

Returns:
    The file size
    The number of TCP connections the client wants
    The number of UDP connections the client wants
"""
def start_up():
    #initializing constants and return values
    units_start = [' ', 'K', 'M', 'G']
    size = 0
    good_file_size_string = False
    good_protocol_number_string = False
    TCP_num = 0
    UDP_num = 0
    #while we did not recieve valid arguments for file size
    #keep iterating
    while (not good_file_size_string):
        file_size_string = input("\033[92mEnter file size, in the following format: size units\n(Units are in up to units of gigabites, in one word: GB instead of Giga Byte\n")
        #there needs to be only two inputs
        #size and units
        word_count = len(file_size_string.split())
        if word_count == 2:
            #checking if the first argument is a number
            if not file_size_string[:file_size_string.find(' ')].isdigit():
                print("\033[91mInvalid size")
            else:
                #in this part we calculate the number of bytes requested to send
                #we have a different case for bytes and bits input
                #such as kilo bytes (KB) and kilo bits (Kb) 
                space_index = file_size_string.find('b')
                #if we use bits
                if space_index != -1:
                    #if the units are valid
                    #calculating file size in bytes
                    if file_size_string[space_index - 1] in units_start:
                        size = 2 ** (-3 + 10 * units_start.index(file_size_string[space_index - 1]))
                        good_file_size_string = True
                    else:
                        print("\033[91mInvalid unit")
                else:
                    space_index = file_size_string.find('B')
                    #if we use bytes
                    if space_index == -1 or file_size_string[space_index - 1] not in units_start:
                        print("\033[91mInvalid unit")
                    else:
                        #if the units are valid
                        #calculating file size in bytes
                        size = 2 ** (10 * units_start.index(file_size_string[space_index - 1]))
                        good_file_size_string = True
        #if there are more than two inputs
        else:
            print("\033[91mInvalid number of arguments")
        
    #while we did not recieve valid arguments for UDP and TCP transfer numbers
    #keep iterating     
    while not good_protocol_number_string:
        tcp_and_udp_string = input("\033[92mEnter the requested number of TCP and UDP connections, in the following format: number_of_TCP_connections number_of_UDP_connections\n")
        numbers = tcp_and_udp_string.split()
        #there needs to be only two numbers
        #one for UDP transfers and one for TCP transfers
        if len(numbers) != 2:
            print("\033[91mInvalid number of arguments")
        #checking if the inputs are valid numbers
        elif (not numbers[0].isdigit()) or (not numbers[1].isdigit()):
            print("\033[91mInvalid numbers")
        else:
            #inputs are valid numbers
            TCP_num = int(numbers[0])
            UDP_num = int(numbers[1])
            good_protocol_number_string = True
    print("\033[92mAll arguments are valid")
    return size, TCP_num, UDP_num

"""
This function is the "looking for a server" state of the client 
We initialize a socket and listening for for offers
Until we recieve a valid one

Args:
    client_offer_port_num: the number of the port that the client will recieve offers to
    magic_cookie: the cookie required for the messages
    offer_message_number: the number that we identify the offer message with

Returns:
    The number of the UDP port that the server will accept UDP transfers to
    The number of the TCP port that the server will accept TCP transfers to
    The IP address of the client
    The IP address of the server
    
"""
def looking_for_a_server(client_offer_port_num, magic_cookie, offer_message_number):
    server_recieved = False
    #initializing a socket to recieve offers from
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_IP_address = socket.gethostbyname(socket.gethostname())
    server_udp_port_num = 0
    server_tcp_port_num = 0
    #binding the socket to our IP and port number
    connection_socket.bind((client_IP_address, client_offer_port_num))
    print(f"\033[94mOur IP adress is: {client_IP_address}\nWe use a port number: {port_num}")
    
    print("\033[92mClient started, listening for offer requests...")
    #while we did not find a valid server to connect with us
    #keep iterating
    while not server_recieved:
        #recieving a message form a server
        (response, (server_IP_address, _)) = connection_socket.recvfrom(1024)
        
        #checking if the magic cokie is correct
        if codecs.encode(response[0:4], 'hex').decode() != magic_cookie: 
            print("\033[91mClient recieved an offer with the wrong cookie")
        #checking if this is an offer message
        elif int(codecs.encode(response[4:5], 'hex'), 16) != offer_message_number:
            print("\033[91mClient recieved an offer with the wrong message type")
            
        else: #.
            #recieving the server UDP and TCP port numbers to connect to
            server_udp_port_num = int(codecs.encode(response[5:7], 'hex'), 16)
            server_tcp_port_num = int(codecs.encode(response[7:9], 'hex'), 16)
            #checking if the server UDP and TCP port numbers to connect to are valid
            if server_udp_port_num > 6500 or server_udp_port_num < 0 or server_tcp_port_num > 6500 or server_tcp_port_num < 0:
                print(f"\033[91mClient recieved an invalid port number, from IP: {server_IP_address}")
            else:
                #found a valid server to connect to
                server_recieved = True
                print(f"\033[94mReceived offer from {server_IP_address}")
 
    return server_udp_port_num, server_tcp_port_num, client_IP_address, server_IP_address

"""
This function is the "speed test" state of the client 
We start a new thread for each TCP and UDP connection
To recieve data from

Args:
    size: The file size
    TCP_num: The number of TCP connections the client wants
    UDP_num: The number of UDP connections the client wants
    server_udp_port_num: The number of the UDP port that the server will accept UDP transfers to
    server_tcp_port_num: The number of the TCP port that the server will accept TCP transfers to
    client_IP_address: The IP address of the client
    server_IP_address: The IP address of the server
    port_num: The port number of our connection socket
    request_message_number: the number that we identify the request message with
    payload_message_number: the number that we identify the payload message with
    magic_cookie: the cookie required for the messages
"""

def speed_test(size, TCP_num, UDP_num, server_udp_port_num, server_tcp_port_num, client_IP_address, server_IP_address, client_port_num, request_message_number, payload_message_number, magic_cookie):
    threads = []
    
    #for every requested TCP transfer
    #starting a thread 
    #in which we will recieve data from the server in
    for i in range(TCP_num):
        thread = threading.Thread(target=tcp_connection, args=(size, server_tcp_port_num, client_port_num, client_IP_address, server_IP_address, i,))
        thread.start()
        threads.append(thread)
        client_port_num = client_port_num + 1
        
    #for every requested UDP transfer
    #starting a thread 
    #in which we will recieve data from the server in
    for i in range(UDP_num):
        thread = threading.Thread(target=udp_connection, args=(size, server_udp_port_num, client_port_num, server_IP_address, i, magic_cookie, client_IP_address, request_message_number, payload_message_number))
        thread.start()
        threads.append(thread)
        client_port_num = client_port_num + 1
    
    #waiting until all the threads will finish
    for thread in threads:
        thread.join()


"""
In this function we initialize a TCP socket 
Receiving data from the server in it by a TCP connection
And calculating the speed of the transfer 

Args:
    size: The file size
    port_num: The port number of our connection socket
    server_tcp_port_num: The number of the TCP port that the server will accept TCP transfers to
    client_IP_address: The IP address of the client
    server_IP_address: The IP address of the server
    trasnfer_num: The number of the TCP transfer out of the total TCP transfers that we have made
"""
def tcp_connection(size, server_tcp_port_num, port_num, client_IP_address, server_IP_address, transfer_num):
    #initializing a socket for the client to recieve data in through a TCP connection
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection_socket.bind((client_IP_address, port_num))

    #creating and decoding a message to send
    message_to_send = hex(size)[2:]
    #padding the message if neccesary
    if len(message_to_send) % 2 != 0:
        message_to_send = message_to_send.rjust(1 + len(message_to_send), '0')
    message_to_send = codecs.decode(message_to_send, 'hex') + b'\n'

    end = False
    while not end:
        try:
            #recored start time
            start_time = time.time()
            print(f"\033[92mClient waiting for TCP message from server, with IP {server_IP_address}...")
            #connecting to the server for TCP connection
            connection_socket.settimeout(1)
            connection_socket.connect((server_IP_address, server_tcp_port_num))
            connection_socket.settimeout(None)
            #setting a timeout, in case the server collapsed
            connection_socket.settimeout(1)
            #sending a size request to the server
            connection_socket.send(message_to_send)
            #recieveing a sum of data from the server
            recieved_message = connection_socket.recv(size + 1)
            connection_socket.settimeout(None)
            #record end time
            end_time = time.time()
            #if the message that we recieved has a wrong number of bytes
            #something went wrong
            if len(recieved_message) != size + 1:
                print(f"\033[91mvClient recived data from server with IP {server_IP_address} in TCP transfer number {transfer_num} in the wrong size, failed.")
                end = True
            else:
                #transfer succeed!
                transfer_time = end_time - start_time
                print(f"\033[92mTCP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second")
                end = True
        #timeout error handling
        except:
            print(f"\033[93mIn TCP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected")        
            end = True
    #closing our connection socket
    connection_socket.close()
    
"""
In this function we initialize a UDP socket 
Receiving data from the server in it by a UDP connection
And calculating the speed of the transfer 

Args:
    size: The file size
    server_udp_port_num: The number of the UDP port that the server will accept UDP transfers to
    port_num: The port number of our connection socket
    server_IP_address: The IP address of the server
    trasnfer_num: The number of the UDP transfer out of the total UDP transfers that we have made
    magic_cookie: the cookie required for the messages
    client_IP_address: The IP address of the client
    request_message_number: the number that we identify the request message with
    payload_message_number: the number that we identify the payload message with
"""
 
def udp_connection(size, server_udp_port_num, port_num, server_IP_address, transfer_num, magic_cookie, client_IP_address, request_message_number, payload_message_number):
    #initializing a socket for the client to recieve data in through a TCP connection
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connection_socket.bind((client_IP_address, port_num))
    hex_size = hex(size)[2:]
    #padding the message if neccesary
    if len(hex_size) != 16:
        hex_size = hex_size.rjust(16, '0')
    #creating a request message    
    message_to_send = codecs.decode(magic_cookie + "0" + str(request_message_number) + hex_size, 'hex')
    total_segments = 0
    current_segment = 0
    segment_counter = 0
    segment_len = 0
    end = False
    print(f"\033[94mClient waiting for UDP transfer number {transfer_num} payloads from server, with IP {server_IP_address}...")
    #recording start time
    start_time = time.time()
    try:
        #sending a request message to the server
        connection_socket.settimeout(1)
        connection_socket.sendto(message_to_send, (server_IP_address, server_udp_port_num))
        connection_socket.settimeout(None)
    #in case the server disconnected
    except socket.timeout:
        print(f"\033[93mIn UDP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected or finished transfering")
        end = True
    while not end:
        try:
            #recieving a payload message from the server
            connection_socket.settimeout(1)
            (recieved_message, recieved_server_IP_address) = connection_socket.recvfrom(size)
            connection_socket.settimeout(None)
            #if we have recieved a message to out port from the right server
            if recieved_server_IP_address[0] == server_IP_address:
                #checking if the magic cokie is correct
                if codecs.encode(recieved_message[0:4], 'hex').decode() != magic_cookie:
                    print(f"Client UDP transfer number {server_IP_address} recieved a payload with the wrong cookie from the server")
                #checking if this is a payload message
                elif int(codecs.encode(recieved_message[4:5], 'hex'), 16) != payload_message_number:
                    print(f"Client UDP transfer number {transfer_num} recieved wrong message type")
                
                else:
                    #correct message
                    #checking the segment numbers
                    total_segments = int(codecs.encode(recieved_message[5:13], 'hex'), 16)
                    current_segment = int(codecs.encode(recieved_message[13:21], 'hex'), 16)
                    segment_counter = segment_counter + 1
                    #calculating the total data size that we have recieved                    
                    segment_len = segment_len + len(recieved_message) - 21
                #finished the transfer!
                if current_segment == total_segments or segment_counter == total_segments:
                    end_time = time.time()
                    #calculating the total time
                    transfer_time = end_time - start_time
                    #if we did not recieve all the bytes
                    if segment_len < size:
                        print(f"\033[92mUDP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second, percentage of packets received successfully: {int(segment_counter/total_segments)*100}%")
                        print(f"\033[93mBut not all of the payloads had all of the required data, there are {size - segment_len} bytes that we did not recieve")
                    else:
                        print(f"\033[92mUDP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second, percentage of packets received successfully: {int(segment_counter/total_segments)*100}%")
                    end = True
                    
        #if the server disconnected
        except:
            print(f"\033[93mIn UDP transfer number {transfer_num}, server did not respond for a full second, assumes server has been disconnected or finished transfering")
            end_time = time.time()
            transfer_time = end_time - start_time
            print(f"\033[92mUDP transfer #{transfer_num} finished, total time: {transfer_time} seconds, total speed: {round(size/transfer_time, 2)} bits/second, percentage of packets received successfully: {int(segment_counter/total_segments)*100}%")
    #closing our socket
    connection_socket.close()
    
    
        
if __name__ == '__main__':
    #starting the client
    magic_cookie = "abcddcba"
    port_num = 5005
    offer_message_number = 2
    request_message_number = 3
    payload_message_number = 4

    #runs forever
    while True:
        #client goes into start up state
        size, TCP_num, UDP_num = start_up()
        #client gets out of start up state
        #client goes into looking for a server state
        server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address = looking_for_a_server(port_num, magic_cookie, offer_message_number)
        #client gets out of looking for a server state
        #client goes into speed test state
        speed_test(size, TCP_num, UDP_num, server_udp_port_num, server_tcp_port_num, IP_address, server_IP_address, port_num + 3000, request_message_number, payload_message_number, magic_cookie)