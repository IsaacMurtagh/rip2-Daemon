"""
    Cosc364 RipV2 Daemon assignment
    Authors: itm20, ljm176

    Config_parser.py, MyExceptions.py and Daemon.py have been concatenated into one .py file,
    Original code is dependant on sperates modules.
"""

# -----------------------
# --- MyExceptions.py ---
# -----------------------

class ParserError(ValueError):
    pass

# ------------------------
# --- Config_parser.py ---
# ------------------------

import sys
from MyExceptions import ParserError
sys.tracebacklimit=0

MAX_PORT = 64000
MIN_PORT = 1024

MAX_METRIC = 15
MIN_METRIC = 1

MAX_ROUTER_ID = 64000
MIN_ROUTER_ID = 1

MAX_TIME_RATIO = 10
MIN_TIME_RATIO = 1


def validate_router_id(router_id):
    """ example return: 4 """

    # Check that router ID is in expected range
    if not router_id.isdigit():
        raise ParserError(f"router-id must be a digit: {router_id}")
    if not (MIN_ROUTER_ID <= int(router_id) <= MAX_ROUTER_ID):
        raise ParserError(f"router-id must be in range {MIN_ROUTER_ID}-{MAX_ROUTER_ID}"
                          f"(inclusive): {router_id}")

    return int(router_id)


def validate_time_ratio(time_ratio):
    """ returns int of value """
    if not time_ratio.isdigit():
        raise ParserError(f"time-ratio must be a digit: {time_ratio}")
    if not (MIN_TIME_RATIO <= int(time_ratio) <= MAX_TIME_RATIO):
        raise ParserError(f"time-ratio must be in range {MIN_TIME_RATIO}-{MAX_TIME_RATIO}"
                          f"(inclusive): {time_ratio}")

    return int(time_ratio)


def validate_input_ports(input_ports):
    """ example return: [2652, 5004, 2023] """

    # Check ports are all integers
    ports = input_ports.split(",")
    ports_list = []
    for port in ports:
        if not port.isdigit():
            raise ParserError(f"input-port must be a digit: {port}")
        else:
            ports_list.append(int(port))

    # Check ports are in expected range
    for port in ports_list:
        if not (MIN_PORT <= port <= MAX_PORT):
            raise ParserError(f"input-port must be in range {MIN_PORT}-{MAX_PORT}"
                              f"(inclusive): {port}")

    # Check that all ports are unqiue
    if len(ports_list) != len(set(ports_list)):
        raise ParserError(f"All values in input-ports must be unique")

    return ports_list


def validate_outputs(outputs, input_ports):
    """ example return: {2: {"output_port": 9080,
                             "output_metric" = 3,
                             "output_router" = 2}}
    """

    outputs_dict = {}
    split_outputs = outputs.split(",")

    for out in split_outputs:

        # check that out is in form "port-metric-id"
        split_out = out.split("-")
        if len(split_out) != 3:
            raise ParserError(f"All values in ouputs must be in form port-metric-id: {out}")

        for element in split_out:
            # Check that each element can be converted to an int
            if not element.isdigit():
                raise ParserError(f"All elements in port-metric-id must be integers: {out}")
        port, metric, router_id = [int(ele) for ele in split_out]

        # Check port is in range
        if not (MIN_PORT <= port <= MAX_PORT):
            raise ParserError(f"outputs: all ports must be in range"
                              f"{MIN_PORT}-{MAX_PORT}(inclusive): {out}")

        # Check metric is in range
        if not (MIN_METRIC <= metric <= MAX_METRIC):
            raise ParserError(f"outputs: all metrics must be in range "
                              f"{MIN_METRIC}-{MAX_METRIC} (inclusive): {out}")

        # Check router is in range
        if not (MIN_ROUTER_ID <= router_id <= MAX_ROUTER_ID):
            raise ParserError(f"outputs: all router-ids must be in range "
                              f"{MIN_ROUTER_ID}-{MAX_ROUTER_ID} (inclusive): {out}")
        
        # Create dict and add it to the list of outputs
        output = {
            "output_port": port,
            "output_metric": metric,
            "output_router": router_id 
        }

        outputs_dict[router_id] = output

    # Check there is no duplicate output ports
    uniq_output_ports = set([ele["output_port"] for ele in outputs_dict.values()])
    if len(outputs_dict) != len(uniq_output_ports):
        raise ParserError(f"All port values in outputs must be unique")

    # Check that output ports unique from input ports
    if len(uniq_output_ports.intersection(set(input_ports))) != 0:
        raise ParserError(f"All port values in output ports must be unique from input ports")

    return outputs_dict


def parse_lines(lines):
    configurations = {'router-id': [],
                      'input-ports': [],
                      'outputs': [],
                      'time-ratio': []}

    for line in lines:
        if line.startswith("#"):
            continue  # Comment line
        if len(line) == 0:
            continue  # Blank line
        
        # Check that line is in the form "[token] [values]"
        split_line = line.split(" ")
        if len(split_line) == 2:
            token, values = split_line
        else:
            raise ParserError(f"Lines must all conform to form [token] [values]:"
                              f"\n{line}")
        
        # Check that the token is an expected key
        if token in configurations:
            configurations[token].append(values.strip())
        else:
            raise ParserError(f"{token} is not an expected token, possible tokens: "
                              f"{', '.join(configurations.keys())}") 
    
    return configurations


def mutate_configs(configuration):
    """ Raises Exception if configurations not in the correct format """
    if len(configuration['time-ratio']) == 0:
        configuration['time-ratio'].append('1')

    router_id = configuration['router-id'][0]
    input_ports = configuration['input-ports'][0]
    outputs = configuration['outputs'][0]
    time_ratio = configuration['time-ratio'][0]

    # Check that there is only one entry for each token
    for token, value in configuration.items():
        if len(value) != 1:
            raise ParserError(f"Multiple lines for token: {token}")
    
    configuration['router-id'] = validate_router_id(router_id)
    configuration['input-ports'] = validate_input_ports(input_ports)
    configuration['outputs'] = validate_outputs(outputs, input_ports)
    configuration['time-ratio'] = validate_time_ratio(time_ratio)


def parse(filename):
    """ Parses a configuration file into a predefined structure.
        If the file is mal-formed then an exception is raised.

        file format (lines in any order)
        * means required
        
        *router-id [1-64000] (e.g: 1)
        *input-ports [1024-64000,...] (e.g: 3033,2922)
        *outputs [[port_number-hop_count(1-15)-route_id],..] (e.g: 2000-2-10,2921-4-11)

        Return: dictionary
        {
            'router-id': 1,
            'input-ports': [1001, 1002]
            'outputs': {2: {"output_port": 9080,
                           "output_metric" = 3,
                           "output_router" = 2}}
        }
    """
    file = open(filename, "r")
    lines = file.readlines()
    file.close()

    configuration = parse_lines(lines)
    mutate_configs(configuration)

    return configuration

# -----------------
# --- Daemon.py ---
# -----------------

import sys
import Config_parser
import pprint
import socket
import time
from random import randint
from copy import deepcopy

MY_IP_ADDRESS = "127.0.0.1"
BUFF_SIZE = 4096

FLOOD_TIMER = 30
DISPLAY_TABLE_TIMER = 10
ROUTE_TIMEOUT = 180
GARBAGE_TIMEOUT = 120


class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        input_ports = daemon_configuration['input-ports']
        self.timeout_ratio = daemon_configuration['time-ratio']
        
        self.start_time = time.time()
        self.lookup = daemon_configuration['outputs']
        self.id = daemon_configuration['router-id']
        self.input_sockets = {} # port : socket() of daemon
        self.routing_table = {} # destination_router: dict of entries
        self.updated = False # Used to notify daemon if it needs to send a triggered update

        self.initialise_input_sockets(input_ports)
        print("Parsed Config File")
        pprint.pprint(daemon_configuration)

        print("\nLookup Table")
        pprint.pprint(self.lookup)


    def initialise_input_sockets(self, input_ports):
        """ For each input_port associated with daemon, create a socket and add 
            it to the list of sockets that daemon is receiving and trasmitting on
        """
        for port in input_ports:
            self.input_sockets[port]= self.create_socket(port)


    def running_time(self):
        """ Returns string min:second of how long program has been running """
        since_inception = int(time.time() - self.start_time)
        return f"[{since_inception // 60}:{since_inception % 60:02}]"


    def display_routing_table(self):
        """ Displays the routing table in a readable format, with timers in seconds """
        cpy_routing_table = deepcopy(self.routing_table)
        current_time = time.time()
        for entry in cpy_routing_table.values():
            entry['timer'] = f"{current_time - entry['timer']:.0f}s"

        print(f"{self.running_time()} --- R{self.id} ROUTING TABLE ---")
        pprint.pprint(cpy_routing_table)
        print("---------------------\n")


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


    def run(self, run_time=None):
        """ Runs the RIPv2 Daemon.
            Run time can be set to an integer in seconds to determine how long the daemon will run.
            The purpose of this is primarly for testing purposes, to break the loop once time is up
        """
        flood_time = time.time() + ((FLOOD_TIMER + randint(-5, 5)) / self.timeout_ratio)
        display_time = time.time() + (DISPLAY_TABLE_TIMER / self.timeout_ratio)

        print(f'---- RIP Daemon {self.id} running at {self.timeout_ratio}x speed... ----')
        while True:
            time.sleep(0.1) # Used to slow the program and stop it eating too much resources
            self.handle_incoming_traffic()
            self.check_route_timers()

            # Triggered update if periodic update is not soon
            if self.updated and not (time.time() + (5 / self.timeout_ratio) >= flood_time): 
                print(f"{self.running_time()} -- Triggered Update --")
                self.send_routing_table(triggered=True)

            if (time.time() >= flood_time): # Periodic Update
                print(f"{self.running_time()} -- Periodic Update --")
                flood_time = time.time() + ((FLOOD_TIMER + randint(-5, 5)) / self.timeout_ratio)
                self.send_routing_table()

            if(time.time() >= display_time): # Print the current state of routing table
                display_time = time.time() + (DISPLAY_TABLE_TIMER / self.timeout_ratio)
                self.display_routing_table()

            #if run_time was configured, check if break should occur.
            if run_time is not None and run_time + self.start_time <= time.time():
                break;


    def add_table_entry(self, dest, metric, next_hop, flag=True):
        """ Adds an entry to the routing table 
            dest = destination router
            metric = hop count to dest
            next = the router to forward to, to reach dest
            timer = how long since there has been an update for this entry
            flag = False when has not been changed, true when has been
        """
        if (flag):
            self.updated = True
        self.routing_table[dest] = {
            "dest": dest, 
            "metric": metric, 
            "next": next_hop, 
            "timer":time.time(),
            "flag": flag
            }


    def check_route_timers(self):
        """ checks the forwarding table for expired routes.
            If a route  is not a metric fo 16 and lapses 180 seconds, that route
            should be marked as changed, a metric of 16 is applied and the timer is reset.

            If a route is a metric of 16, it can be assumed that the timer associated with it
            is the garbadge timeout, once that reaches 120 seconds it is deleted from the table.
            It is only left there, to inform other routes of the unreachable path.
        """
        for id in list(self.routing_table):
            entry = self.routing_table[id]
            if entry['metric'] == 16: # Check for garbage collection
                if time.time() >= entry['timer'] + (GARBAGE_TIMEOUT / self.timeout_ratio):
                    print(f"{self.running_time()} Deleting router {id} from table")
                    del self.routing_table[id]
            else: # Check for expired timer
                if time.time() >= entry['timer'] + (ROUTE_TIMEOUT / self.timeout_ratio):
                    print(f"{self.running_time()} Setting router {id} as unreachable")
                    self.add_table_entry(entry['dest'], 16, entry['next'], True)


    def send_routing_table(self, triggered=False):
        """ Sends the routing table on all output ports which prints out successful and 
            unsuccessful connections. 
        """
        for router_id in self.lookup:
            port_number = self.lookup[router_id]['output_port']
            try:
                s = socket.socket()
                s.connect((MY_IP_ADDRESS, port_number))
                data = self.generate_datagram(router_id, triggered)
                s.send(data)
                s.close()
                print(f"CONNECTION: Router {router_id}")
            except Exception as e:
                # Connection refused, no interface on given port
                print(f"CONNECTION FAILED: Router {router_id}")
        print()
        self.reset_route_flags()

    
    def generate_datagram(self, neighbour_id, triggered):
        """ Generates the RIP datagram.
            If it is a triggered update, then send only those which have flag set true

            Split horizons: Don't send routing entries about destinations to those
            who are the next hop.
        """
        header = bytearray(4)
        header[0] = 2 # Command: Response
        header[1] = 2 # Version: RIPv2
        header[2] = 0xFF00 & self.id # Split 16 bit router id
        header[3] = 0x00FF & self.id

        for row in self.routing_table.values():
            if not triggered or row['flag'] is True: # Only send changed rows
                if row['next'] != neighbour_id: # Split horizons
                    entry = bytearray(20)
                    entry[6] = 0xFF00 & row['dest']
                    entry[7] = 0x00FF & row['dest']
                    entry[19] = row['metric']
                    header += entry
        return header


    def reset_route_flags(self):
        """ Resets all the flags in routing table to false. This is only to be called
            after the routing table has been sent to all neighbours.
        """
        for entry in self.routing_table.values():
            entry['flag'] = False
        self.updated = False


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
                data = self.receive_data(neighbour_socket)
                neighbour_table, neighbour_id = self.parse_update_message(data)
                print(f"{self.running_time()} Received from router {neighbour_id}")
                pprint.pprint(neighbour_table, indent=5)
                print()
                self.update_routing_table(neighbour_table, neighbour_id)
                neighbour_socket.close()
            except BlockingIOError:
                pass # No messages on socket
            except ValueError:
                print(f"Malformed packet received by router {neighbour_id}")
                neighbour_socket.close()
            except IndexError:
                print(f"Malformed packet received by router {neighbour_id}")
                neighbour_socket.close()

        
    def parse_update_message(self, data):
        """ Takes a response packet it has received, does error checking and returns 
            a list of dicts of information.
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

    
    def receive_data(self, s):
        """ Receive data that has been put onto socket s """
        data = b''
        s.settimeout(0.1)
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

            Sets updated to true if there has been changes and a triggered update is required
        """
        if self.routing_table.get(neighbour_id) is None:
            self.add_table_entry(neighbour_id, self.lookup[neighbour_id]['output_metric'], neighbour_id, True)
        else:
            self.add_table_entry(neighbour_id, self.lookup[neighbour_id]['output_metric'], neighbour_id, False)

        for entry in neighbour_table:
            my_entry = self.routing_table.get(entry['dest'])
            calculated_metric = min(self.routing_table[entry['next']]['metric'] + entry['metric'], 16)

            if entry['dest'] == self.id:
                continue # Ignore routes to self

            elif (my_entry is None): # No entry for that destination
                if calculated_metric < 16:
                    self.add_table_entry(entry['dest'], calculated_metric, entry['next'], True) # add entry

            else:
                if calculated_metric == 16 and my_entry['metric'] == 16: # Ignore update of known unreachable route
                    continue

                elif calculated_metric < my_entry['metric']: # New best route
                    self.add_table_entry(entry['dest'], calculated_metric, entry['next'], True)

                elif my_entry['next'] == entry['next']: # Update by used route
                    if my_entry['metric'] != calculated_metric: # Route is now worse
                        self.add_table_entry(entry['dest'], calculated_metric, entry['next'], True)

                    else:
                        self.add_table_entry(entry['dest'], calculated_metric, entry['next'], False)


def main():
    if len(sys.argv) != 2:
        raise Exception
    filename = sys.argv[1]
    try:
        daemon = RipDaemon(filename)
        id = daemon.id
        daemon.run()
    except KeyboardInterrupt:
        print(f"Daemon session {id} ended, all sockets closed")
    finally:
        try:
            daemon.close_all_sockets()
        except Exception:
            pass


if __name__ == "__main__":
    main()