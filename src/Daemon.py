import sys
import Config_parser
import pprint
import socket
import time
from random import randint
# sys.tracebacklimit=0

MY_IP_ADDRESS = "127.0.0.1"
BUFF_SIZE = 4096

TIMEOUT_RATIO = 1
FLOOD_TIMER = 30
GARBAGE_TIMER = 180

class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        input_ports = daemon_configuration['input-ports']
        
        self.lookup = daemon_configuration['outputs']
        self.id = daemon_configuration['router-id']
        self.input_sockets = {} # port : socket() of daemon
        self.routing_table = {} # destination_router: dict of entries
        self.updated = False # Used to notify daemon if it needs to send a triggered update

        self.initialise_input_sockets(input_ports)
        pprint.pprint(self.lookup)
        self.display_routing_table()

    def initialise_input_sockets(self, input_ports):
        """ For each input_port associated with daemon, create a socket and add 
            it to the list of sockets that daemon is receiving and trasmitting on
        """
        for port in input_ports:
            self.input_sockets[port]= self.create_socket(port)
    
     
    def add_table_entry(self, dest, metric, next_hop, timer=0, flag=False):
        """ Adds an entry to the routing table 
            dest = destination router
            metric = hop count to dest
            next = the router to forward to, to reach dest
            timer = how long since there has been an update for this entry
            flag = False when has not been changed, true when has been
        """
        self.routing_table[dest] = {
            "dest": dest, 
            "metric": metric, 
            "next": next_hop, 
            "timer":timer,
            "flag": flag
            }


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
            try:
                socket.close()
            except Exception:
                pass


    def run(self):
        """ Runs the RIPv2 Daemon """
        flood_time = time.time()
        garbadge_time = time.time()
        print(f'----- RIP Daemon {self.id} running... ----')
        while True:
            if (self.is_flood_time(flood_time)):
                print("-- Periodic Update --")
                self.send_routing_table()
                flood_time = time.time()
                # self.display_routing_table()
            
            if (self.is_garbage_time(garbadge_time)):
                garbadge_time = time.time()

            self.handle_incoming_traffic()
            if (self.updated):
                print("-- Triggered Update --")
                self.updated = False
                self.send_routing_table()
                self.display_routing_table()
            

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
        print("- Sending routing table -")
        for router_id in self.lookup:
            port_number = self.lookup[router_id]['output_port']
            try:
                s = socket.socket()
                s.connect((MY_IP_ADDRESS, port_number))
                data = self.generate_datagram()
                s.send(data)
                s.close()
                print(f"Connected to: Router {router_id}")
            except Exception as e:
                if (e.errno == 111): # Connection refused, no interface on given port
                    print(f"Could not connect to: Router {router_id}")
                else:
                    raise e

    
    def generate_datagram(self):
        """ Generates the RIP datagram, can have at most 25 entries, therefore
            a list of all the datgram generated is returned.
        """
        # --- INCOMPLETE ---
        # Must implemenent splitting datagrams when more than 25 entries.
        header = bytearray(4)
        header[0] = 2 # Command: Response
        header[1] = 2 # Version: RIPv2
        header[2] = 0xFF00 & self.id # Split 16 bit router id
        header[3] = 0x00FF & self.id

        for row in self.routing_table.values():
            entry = bytearray(20)
            entry[6] = 0xFF00 & row['dest']
            entry[7] = 0x00FF & row['dest']
            entry[19] = row['metric']
            header += entry

        return header


    def handle_incoming_traffic(self):
        """ Checks all of the daemon sockets and accepts any new connection,
            will then read the buffer on that socket, and determines if any updates 
            on the routing table.

            Is not blocking, so if there is not already a request on the socket, it throws
            an exception BlockingIOError which can be ignored.
        """
        for my_port, my_socket in self.input_sockets.items():
            try:
                neighbour_socket, address = my_socket.accept()
                data = self.recieve_data(neighbour_socket)
                neighbour_table, neighbour_id = self.parse_update_message(data)
                self.update_routing_table(neighbour_table, neighbour_id)
                neighbour_socket.close()
            except BlockingIOError:
                pass # No messages on socket
            except ValueError:
                print(f"Malformed packet received on port {my_port}")
                neighbour_socket.close()
            except IndexError:
                print("index error")
        
    
    def parse_update_message(self, data):
        """ Takes a response packet it has received, does error checking and returns 
            a dict of parsed information and the id of the router that sent the message.
            {next: ..., dest: ..., metric: ...}
        """
        command = data[0]
        version = data[1]
        router_id = (data[2] << 8) | data[3]
        if (command != 2 and version != 2):
            raise ValueError

        table = []
        for i in range(4, len(data), 20):
            dest = (data[i + 6] << 8) + data[i + 7]
            metric = data[i + 19]
            table.append({'next': router_id, "dest": dest, "metric": metric})

        return table, router_id

    
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


    def update_routing_table(self, neighbour_table, neighbour_id):
        """ Takes a list of dictionary's as a paramater and uses the information 
            to determine the best routes, by comparing it to it's own routing table.

            When it receives information about a neighbour, it can used the predefined configurations
            to add an entry, self.lookup,  for its directly attached neighbours configs.

            Sets updated to true if there has been changes for triggered update
        """
        if self.routing_table.get(neighbour_id) is None:
            self.updated = True
        self.add_table_entry(neighbour_id, self.lookup[neighbour_id]['output_metric'], neighbour_id)

        for entry in neighbour_table:
            my_entry = self.routing_table.get(entry['dest'])
            calculated_metric = self.routing_table[entry['next']]['metric'] + entry['metric']

            if entry['dest'] == self.id:
                continue # Ignore routes to self
            elif (my_entry is None): # No entry for that destination
                if calculated_metric < 16:
                    self.add_table_entry(entry['dest'], calculated_metric, entry['next']) # add entry
                    self.updated = True
            else:
                if my_entry['next'] == entry['next']:
                    self.add_table_entry(entry['dest'], calculated_metric, entry['next'])
                elif calculated_metric < my_entry['metric']:
                    self.add_table_entry(entry['dest'], calculated_metric, entry['next'])
                    self.updated = True


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