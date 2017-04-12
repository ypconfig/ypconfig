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

oidre = re.compile('^([0-9.]+\.)+([0-9]+)$')
oidmatch = oidre.match(oid)

if not oidmatch:
    usage()

oidbase = oidmatch.group(1)
oididx = oidmatch.group(2)

if cmd == '-s':
    try:
        vtype = args[3]
        value = args[4]
    except:
        usage()

ip = IPRoute()
links = ip.get_links()

def snmp_print(iface):
    if iface.get_attr('IFLA_IFALIAS'):
        print(''.join([str(oidbase), str(iface['index'])]))
        print('string')
        print(iface.get_attr('IFLA_IFALIAS'))
    
if cmd == '-g':
    for l in links:
        if int(l['index']) == int(oididx):
            snmp_print(l)
elif cmd == '-n':
    lidx = 0
    for l in links:
        if int(l['index']) == int(oididx):
            try:
                nextidx = lidx+1
                nlink = links[nextidx]
                snmp_print(nlink)
            except KeyError:
                pass
        lidx+=1
elif cmd == '-s':
    ip.link('set', index=int(oididx), IFLA_IFALIAS=value)
    ip.close()
