#!/usr/bin/env python3


"""This script should be able to create a configfile from all the current (supported) interfaces"""

from pyroute2 import IPDB

# from pyface import Iface, Vlan


with IPDB() as ip:
    #
    # Create bridge and add ports and addresses.
    #
    # Transaction will be started by `with` statement
    # and will be committed at the end of the block
    with ip.create(kind="bond", ifname="rhev") as i:
        i.add_port("eth1")
