import sys
import Config_parser
import pprint
sys.tracebacklimit=0

class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        self.id = daemon_configuration['router-id']
        self.input_ports = daemon_configuration['input-ports']
        self.outputs = daemon_configuration['outputs']
        self.initialise_routing_table()
        self.display_routing_table()


    def initialise_routing_table(self):
        """ Take the initial information given from the configuration files and 
            populate the routing table and lookup reference table used to associate
            router-id's with socket ports.
        """
        self.routing_table = []
        self.lookup = []
        for output in self.outputs:
            router_id, metric = output["output_router"], output["output_metric"]
            self.add_table_entry(router_id, metric, router_id)
            self.lookup.append({router_id: output["output_port"]})
    
     
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


def main():
    # if len(sys.argv) != 2:
    #     raise Exception
    # filename = sys.argv[1]
    filename = "src/configs.conf"

    daemon = RipDaemon(filename)
    # daemon.start()


main()