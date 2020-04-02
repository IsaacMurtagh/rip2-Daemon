# rip-assignment

## Setup to run Daemons
for each daemon:

RUNNING PRESET DAEMONS
    1. Open a new terminal window
    2. Download xterm, a program for running a new terminal inside a shell
        - For mac and linux "sudo apt install xterm"
    3. Change directory to rip-assignment/test
    4. execute command "./run_top_x1.sh"
        - This will run all daemons in the config for topology1x1

RUNNING INDIVIDUAL DAEMONS
    1. Open a new terminal window
    2. Change directory to rip-assignment/src
    3. execute command "python3 Daemon.py ../configs/topology1x1/router1.conf"
        - This is useful for killing and reinstating daemons.