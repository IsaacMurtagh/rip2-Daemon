import sys
import Config_parser
sys.tracebacklimit=0

class RipDaemon:
    def __init__(self, configuration_filename):
        daemon_configuration = Config_parser.parse(configuration_filename)
        self.id = daemon_configuration['router-id']
        self.input_ports = daemon_configuration['input-ports']
        self.outputs = daemon_configuration['output-ports']

    def start(self):
        print(self.daemon_configuration)


def main():
    # if len(sys.argv) != 2:
    #     raise Exception
    # filename = sys.argv[1]
    filename = "configs.conf"

    daemon = RipDaemon(filename)
    daemon.start()


main()