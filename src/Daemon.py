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
        self.sending_table = {} # Table with router_id : socket() that packets sent on
        self.receiving_sockets = [] # list of socket()'s that packets sent received on

        self.initialise_routing_table()
        self.initialise_receiving_sockets()
        self.display_routing_table()
        pprint.pprint(self.sending_table)
        pprint.pprint(self.receiving_sockets)


    def initialise_receiving_sockets(self):
        """ For each input_port associated with daemon, create a socket
            and add it to the list of sockets that daemon is receiving on
        """
        for port in self.input_ports:
            self.receiving_sockets.append(self.create_socket(port))

    def initialise_routing_table(self):
        """ Take the initial information given from the configuration files and 
            populate the routing table and lookup reference table used to associate
            router-id's with socket  ports.
        """
        self.routing_table = []
        for output in self.outputs:
            router_id, metric = output["output_router"], output["output_metric"]
            self.add_table_entry(router_id, metric, router_id)
            self.sending_table[router_id] = self.create_socket(output["output_port"])
    
     
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
        s = socket.socket()
        s.bind((MY_IP_ADDRESS, port_number))
        return s

    def close_all_sockets(self):
        """ Loops through sending and receiving sockets, closing them
            this should be called just before the daemon terminates
        """
        for socket in self.sending_table.values():
            socket.close()
        for socket in self.receiving_sockets:
            socket.close()


def main():
    # if len(sys.argv) != 2:
    #     raise Exception
    # filename = sys.argv[1]
    filename = "src/configs.conf"

    daemon = RipDaemon(filename)
    # daemon.start()


main()