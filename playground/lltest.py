#!/usr/bin/env python3


"""This script should be able to create a configfile from all the current (supported) interfaces"""
import sys
from socket import AF_INET
from pyroute2 import IPRoute
from pprint import pprint
from pyroute2 import IPDB
from tabulate import tabulate
from yaml import load, dump
from time import sleep

#from pyface import Iface, Vlan


ip = IPDB()
parent = ip.interfaces['eth1']
i = ip.interfaces['lltest']
i.remove()
ip.commit()

i = ip.create(kind='vlan', ifname='lltest', link=parent, vlan_id=1234, reuse=True)
i.up()
ip.commit()

print("Waiting for fe80 address")
i.wait_ip('fe80::', mask=64)
pprint(i)

i.add_ip('fc00::1:1:1:1/64')
ip.commit()

pprint(i['ipaddr'])
