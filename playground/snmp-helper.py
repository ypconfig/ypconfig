#!/usr/bin/env python3

"""This script is a helper for net-snmpd, to get ifaliases working"""
from pyroute2 import IPRoute
import sys, re

def usage():
    print("snmpd-helper.py (-g|-n) oid")
    print("snmpd-helper.py -s oid type value")
    sys.exit(1)

args = sys.argv

try:
    cmd = args[1]
    oid = args[2]
except:
    usage()

if cmd not in ['-s', '-g', '-n']:
    usage()

oidre = re.compile('^(\.1\.3\.6\.1\.2\.1\.31\.1\.1\.1\.18(\.?))([0-9]+)?$')
oidmatch = oidre.match(oid)

if not oidmatch:
    usage()

oidbase = '.1.3.6.1.2.1.31.1.1.1.18'
oididx = oidmatch.group(3) or 0

if cmd == '-s':
    try:
        vtype = args[3]
        value = args[4]
    except:
        usage()

ip = IPRoute()
links = {}
linklist = []

for l in ip.get_links():
    descr = l.get_attr('IFLA_IFALIAS') or l.get_attr('IFLA_IFNAME')
    links[l['index']] = descr

for idx in sorted(links.keys()):
    linklist.append({'index': idx, 'descr': links[idx] })

def get_next(idx):
    if idx == 0:
        return linklist[idx]

    try:
        for lidx, l in enumerate(linklist):
            if l['index'] == int(idx):
                return linklist[lidx+1]
    except IndexError:
        pass

    raise IndexError


def snmp_print(iface):
    print('.'.join([str(oidbase), str(iface['index'])]))
    print('string')
    print(iface['descr'])
    
if cmd == '-g':
    for l in linklist:
        if int(l['index']) == int(oididx):
            snmp_print(l)
elif cmd == '-n':
    try:
        i = get_next(oididx)
        snmp_print(i)
    except IndexError:
        pass
elif cmd == '-s':
    ip.link('set', index=int(oididx), IFLA_IFALIAS=value)
    ip.close()
