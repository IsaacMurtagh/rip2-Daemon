"""
    Cosc364 RipV2 Daemon assignment
    Authors: itm20, ljm176
"""
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