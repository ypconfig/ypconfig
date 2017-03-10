#!/usr/bin/env python3


"""This script should be able to create a configfile from all the current (supported) interfaces"""
import sys
from socket import AF_INET
from pyroute2 import IPRoute
from pprint import pprint
from pyroute2 import IPDB
from tabulate import tabulate
from yaml import load, dump

#from pyface import Iface, Vlan

linkstate = ['DOWN', 'UP']
ip = IPRoute()

ifaces = {}
for iface in ip.get_links():
    pprint(iface)
    this = {}
    iname = iface.get_attr('IFLA_IFNAME')
    addrs = []
    for addr in ip.get_addr(index=iface['index']):
        if addr.get_attr('IFA_ADDRESS').startswith('fe80:'):
            # We don't store link-locals
            continue
        fa = '/'.join([addr.get_attr('IFA_ADDRESS'), str(addr['prefixlen'])])
        addrs.append(fa)

    if len(addrs) > 0:
        this['addresses'] = addrs
    this['adminstate'] = iface.get_attr('IFLA_OPERSTATE')
    this['mtu'] = iface.get_attr('IFLA_MTU')

    if iface.get_attr('IFLA_LINKINFO'):
        try:
            linfo = iface.get_attr('IFLA_LINKINFO')
            if linfo.get_attr('IFLA_INFO_KIND') == 'vlan':
                # Get the parents name
                pname = ip.get_links(iface.get_attr('IFLA_LINK'))[0].get_attr('IFLA_IFNAME')
                try:
                    ifaces[pname]
                except KeyError:
                    ifaces[pname] = {}

                try:
                    ifaces[pname]['vlans']
                except KeyError:
                    ifaces[pname]['vlans'] = []

                this['name'] = iname
                this['vlanid'] = linfo.get_attr('IFLA_INFO_DATA').get_attr('IFLA_VLAN_ID')
                ifaces[pname]['vlans'].append(this)
        except Exception as e:
            print(e)
            pass
    else:
        ifaces[iname] = this

print(dump(ifaces,default_flow_style=False))

# #ip.link("add",
# #        ifname="v100",
# #        kind="vlan",
# #        link=ip.link_lookup(ifname="eth1")[0],
# #        vlan_id=100)

#     #pprint(iface)
#     ##print(iface.get_attr('IFLA_IFNAME'))
#     #print(iface.get_attr('IFLA_OPERSTATE'))
#     ##print(iface['index'])
#pprint(ip.get_addr(index=iface['index']))
