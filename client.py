#client file
import socket
import sys
import codecs

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
    sol = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP_address = socket.gethostbyname(socket.gethostname())
    port_num = 5000
    magic_cookie = "abcddcba"
    message_type = 3
    message_to_send = codecs.encode(magic_cookie + message_type + size, 'utf-8')
    sol.bind(IP_address, port_num)
    print("Our IP adress is: %s\nWe use a port number: %d", IP_address, port_num)
    sol.send(message_to_send)
    print("Client started, listening for offer requests...")
    sol.listen(1)
    (connection_socket, server_address) = sol.accept()    
    return connection_socket, server_address[0], server_address[1]
        
        
if __name__ == '__main__':
    #starting the client 
    size, TCP_num, UDP_num = start_up()
    connection_socket, server_adress, server_port = looking_for_a_server(size)