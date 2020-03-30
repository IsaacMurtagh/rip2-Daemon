import sys
import Config_parser
import pprint
import socket
import time
from random import randint
# sys.tracebacklimit=0

MY_IP_ADDRESS = "127.0.0.1"
BUFF_SIZE = 4096

TIMEOUT_RATIO = 6
FLOOD_TIMER = 30
GARBAGE_TIMER = 180

class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        input_ports = daemon_configuration['input-ports']
        outputs = daemon_configuration['outputs']

        self.id = daemon_configuration['router-id']
        self.input_sockets = {} # port : socket() of daemon
        self.lookup = {} # Table of router_id : port
        self.routing_table = [] # Used to determine routes and for response messages

        self.initialise_routing_table(outputs)
        self.initialise_input_sockets(input_ports)
        self.display_routing_table()

    def initialise_input_sockets(self, input_ports):
        """ For each input_port associated with daemon, create a socket and add 
            it to the list of sockets that daemon is receiving and trasmitting on
        """
        for port in input_ports:
            self.input_sockets[port]= self.create_socket(port)


    def initialise_routing_table(self, outputs):
        """ Take the initial information given from the configuration files and 
            populate the routing table and lookup reference table used to associate
            router-id's with socket  ports.
        """
        for output in outputs:
            router_id, metric = output["output_router"], output["output_metric"]
            self.add_table_entry(router_id, metric, router_id)
            self.lookup[router_id] = output["output_port"]
    
     
    def add_table_entry(self, dest, metric, next_hop, timer=0, flag=False):
        """ Adds an entry to the routing table 
            dest = destination router
            metric = hop count to dest
            next = the router to forward to, to reach dest
            timer = how long since there has been an update for this entry
            flag = False when has not been changed, true when has been
        """
        self.routing_table.append({
            "dest": dest, 
            "metric": metric, 
            "next": next_hop, 
            "timer":timer,
            "flag": flag
            })

    def display_routing_table(self):
        print("--- ROUTING TABLE ---")
        pprint.pprint(self.routing_table)
        print("---------------------")

    def create_socket(self, port_number):
        """ Creates a socket and returns it for a given port number """
        try:
            s = socket.socket()
            s.bind((MY_IP_ADDRESS, port_number))
            s.setblocking(False);
            s.listen()
            return s
        except Exception:
            print(f"Socket creation failed on port {port_number}")


    def close_all_sockets(self):
        """ Loops through sending and receiving sockets, closing them
            this should be called just before the daemon terminates
        """
        for _, socket in self.input_sockets.items():
            socket.close()
            

    def run(self):
        """ Runs the RIPv2 Daemon """
        flood_time = time.time()
        garbadge_time = time.time()

        while True:
            if (self.is_flood_time(flood_time)):
                self.send_routing_table()
                flood_time = time.time()
            
            if (self.is_garbage_time(garbadge_time)):
                garbadge_time = time.time()

            self.handle_incoming_traffic()


    def check_socket(self, s):
        """ Checks if any data avaliable on the socket to be read, if there is
            then take that information and do something with it
        """
        for socket in self.receiving_sockets:
            socket.settimeout(2)
            try:
                output_socket, address = socket.accept()
                port = address[1]
                self.sending_table[lookup[port]] = output_socket
            except socket.timeout:
                print("Socket did not accept")


    def is_flood_time(self, flood_time):
        """ Checks if the timer for unscolicated messages has expired.
            How often to send a message is calculated by the recommended time
            +/- a random value to avoid synchronisation, divided by the ratio 
            for testing purposes.
        """
        timeout = ((FLOOD_TIMER + randint(-5, 5)) / TIMEOUT_RATIO)
        return (time.time() - flood_time) >= timeout 


    def is_garbage_time(self, garbage_time):
        """ Checks if timer for garbage collection has expired.
            How often to send a message is calculated by the recommended time
            +/- a random value to avoid synchronisation, divided by the ratio 
            for testing purposes.
        """
        timeout = ((GARBAGE_TIMER + randint(-5, 5)) / TIMEOUT_RATIO)
        return (time.time() - garbage_time) >= timeout 

    
    def send_routing_table(self):
        """ Sends the routing table to all output ports """
        print("Sending routing table")
        for router_id, port_number in self.lookup.items():
            try:
                s = socket.socket()
                s.connect((MY_IP_ADDRESS, port_number))
                s.send(bytearray(str(self.id).encode())) # Currently just sends router ID
                s.close()
            except Exception as e:
                if (e.errno == 111): # Connection refused, no interface on given port
                    print(f"Could not connect to {port_number}")


    def handle_incoming_traffic(self):
        """ Checks all of the daemon sockets and accepts any new connection,
            will then read the buffer on that socket, and determine any updates 
            on the routing table.

            Is not blocking, so if there is not already a request on the socket, it throws
            an exception BlockingIOError which can be ignored.
        """
        for my_port, my_socket in self.input_sockets.items():
            try:
                neighbour_socket, address = my_socket.accept()
                print(self.recieve_data(neighbour_socket))
                neighbour_socket.close()
            except BlockingIOError:
                pass
        
    
    def recieve_data(self, s):
        """ Receive data that has been put onto socket s """
        data = b''
        s.settimeout(0.2)
        while True:
            try:
                part = s.recv(BUFF_SIZE)
            except socket.timeout:
                print("timeout occured")
            data += part
            if len(part) < BUFF_SIZE:
                break
        return bytearray(data)

def main():
    if len(sys.argv) != 2:
        raise Exception
    filename = sys.argv[1]
    # filename = "src/configs.conf"
    try:
        daemon = RipDaemon(filename)
        daemon.run()
    except KeyboardInterrupt:
        print("Daemon session ended, all sockets closed")
    finally:
        try:
            daemon.close_all_sockets()
        except Exception:
            pass

main()