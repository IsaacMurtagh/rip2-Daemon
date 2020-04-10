"""
    Cosc364 RipV2 Daemon assignment
    Authors: itm20, ljm176
"""
from Daemon import RipDaemon
import pytest
import threading

RUN_TIME = 15

# This test runs the daemon in a multithread and then after a given run_time
# Returns the daemons with their converged routing tables.
# Note: the run time must be long enough that tables reach a converged state


@pytest.fixture(scope='session', autouse=True)
def DaemonTopology1x1():
    """ Runs a test on the dameon topology1x1 for each router and 
        asserts that the converged routing tables are as expcted
    """
    path_prefix = "../configs/topology1x3/"
    threads = []
    daemons = {}
    for n in range(1, 8):
        daemons[n] = RipDaemon(f"{path_prefix}router-{n}.conf")

    for id, d in daemons.items():
        t = threading.Thread(target=d.run, args=[RUN_TIME])
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    for d in daemons.values():
        d.display_routing_table()

    return daemons


def compare_tables(actual_table, expected_table):
    """ Compares the routing tables and checks that they converged as expcted """
    for dest in expected_table:
        actual_entry = actual_table.get(dest)
        expected_entry = expected_table[dest]
        assert(actual_entry.get('dest') == expected_entry['dest'])
        assert(actual_entry.get('metric') == expected_entry['metric'])
        assert(actual_entry.get('next') in expected_entry['next'])


def test_router1(DaemonTopology1x1):
    router_id = 1
    expected_table = {
        2: {'dest':2, 'metric':1, 'next':[2]},
        3: {'dest':3, 'metric':4, 'next':[2]},
        4: {'dest':4, 'metric':8, 'next':[2, 6]},
        5: {'dest':5, 'metric':6, 'next':[6]},
        6: {'dest':6, 'metric':5, 'next':[6]},
        7: {'dest':7, 'metric':8, 'next':[7]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


def test_router2(DaemonTopology1x1):
    router_id = 2
    expected_table = {
        1: {'dest':1, 'metric':1, 'next':[1]},
        3: {'dest':3, 'metric':3, 'next':[3]},
        4: {'dest':4, 'metric':7, 'next':[3]},
        5: {'dest':5, 'metric':7, 'next':[1]},
        6: {'dest':6, 'metric':6, 'next':[1]},
        7: {'dest':7, 'metric':9, 'next':[1]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


def test_router3(DaemonTopology1x1):
    router_id = 3
    expected_table = {
        1: {'dest':1, 'metric':4, 'next':[2]},
        2: {'dest':2, 'metric':3, 'next':[2]},
        4: {'dest':4, 'metric':4, 'next':[4]},
        5: {'dest':5, 'metric':6, 'next':[4]},
        6: {'dest':6, 'metric':7, 'next':[4]},
        7: {'dest':7, 'metric':10, 'next':[4]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)
    

def test_router4(DaemonTopology1x1):
    router_id = 4
    expected_table = {
        1: {'dest':1, 'metric':8, 'next':[3, 5]},
        2: {'dest':2, 'metric':7, 'next':[3]},
        3: {'dest':3, 'metric':4, 'next':[3]},
        5: {'dest':5, 'metric':2, 'next':[5]},
        6: {'dest':6, 'metric':3, 'next':[5]},
        7: {'dest':7, 'metric':6, 'next':[7]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


def test_router5(DaemonTopology1x1):
    router_id = 5
    expected_table = {
        1: {'dest':1, 'metric':6, 'next':[6]},
        2: {'dest':2, 'metric':7, 'next':[6, 4]},
        3: {'dest':3, 'metric':6, 'next':[4]},
        4: {'dest':4, 'metric':2, 'next':[4]},
        6: {'dest':6, 'metric':1, 'next':[6]},
        7: {'dest':7, 'metric':8, 'next':[4]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


def test_router6(DaemonTopology1x1):
    router_id = 6
    expected_table = {
        1: {'dest':1, 'metric':5, 'next':[1]},
        2: {'dest':2, 'metric':6, 'next':[1]},
        3: {'dest':3, 'metric':7, 'next':[5]},
        4: {'dest':4, 'metric':3, 'next':[5]},
        5: {'dest':5, 'metric':1, 'next':[5]},
        7: {'dest':7, 'metric':9, 'next':[5]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


def test_router7(DaemonTopology1x1):
    router_id = 7
    expected_table = {
        1: {'dest':1, 'metric':8, 'next':[1]},
        2: {'dest':2, 'metric':9, 'next':[1]},
        3: {'dest':3, 'metric':10, 'next':[4]},
        4: {'dest':4, 'metric':6, 'next':[4]},
        5: {'dest':5, 'metric':8, 'next':[4]},
        6: {'dest':6, 'metric':9, 'next':[4]},
    }
    actual_table = DaemonTopology1x1[router_id].routing_table
    compare_tables(actual_table, expected_table)


