import sys
import Config_parser
import pprint
import socket
sys.tracebacklimit=0

MY_IP_ADDRESS = "127.0.0.1"

class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        self.id = daemon_configuration['router-id']
        self.input_ports = daemon_configuration['input-ports']
        self.outputs = daemon_configuration['outputs']
        self.input_sockets = {} # port : socket() of daemon
        self.lookup = {} # Table of router_id : port

        self.initialise_routing_table()
        self.initialise_input_sockets()
        self.display_routing_table()
        pprint.pprint(self.input_sockets)


    def initialise_input_sockets(self):
        """ For each input_port associated with daemon, create a socket and add 
            it to the list of sockets that daemon is receiving and trasmitting on
        """
        for port in self.input_ports:
            self.input_sockets[port]= self.create_socket(port)


    def initialise_routing_table(self):
        """ Take the initial information given from the configuration files and 
            populate the routing table and lookup reference table used to associate
            router-id's with socket  ports.
        """
        self.routing_table = []
        for output in self.outputs:
            router_id, metric = output["output_router"], output["output_metric"]
            self.add_table_entry(router_id, metric, router_id)
            self.lookup[router_id] = output["output_port"]
    
     
    def add_table_entry(self, dest, metric, next_hop, timer=0):
        """ Adds an entry to the routing table """
        self.routing_table.append({
            "dest": dest, 
            "metric": metric, 
            "next": next_hop, 
            "timer":timer
            })

    def display_routing_table(self):
        pprint.pprint(self.routing_table)

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
        while True:
            if (self.is_flood_time()):
                self.send_routing_table()
            
            if (self.is_flood_time()):
                pass # Check routing table to see if expired routes

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


    def is_flood_time(self):
        """ Checks if the timer for unscolicated messages has expired """
        return False


    def is_garbage_time(self):
        """ Checks if timer for garbadge collection """
        return False

    
    def send_routing_table(self):
        """ Sends the routing table to all output ports """
        pass


    def handle_incoming_traffic(self):
        """ Checks all of the daemon sockets and accepts any new connection,
            will then readthe buffer on that socket, and determine any updates 
            on the routing table.
        """
        for my_port, my_socket in self.input_sockets.items():
            try:
                neighbour_socket, address = my_socket.accept()

                print(address)
            except BlockingIOError:
                print(f"port: {my_port}")
        

def main():
    # if len(sys.argv) != 2:
    #     raise Exception
    # filename = sys.argv[1]
    filename = "src/configs.conf"
    try:
        daemon = RipDaemon(filename)
        daemon.run()
    except KeyboardInterrupt:
        print("Daemon session ended, all sockets closed")
        daemon.close_all_sockets()



main()