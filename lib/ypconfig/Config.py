#!/usr/bin/env python3

from yaml import load, dump
from sys import exit
from copy import deepcopy
import re, socket


def Get(cfg):
    try:
        f = open(cfg)
    except Exception as e:
        raise e

    try:
        document = load(f.read())
    except:
        raise ValueError("YAML Error in configuration")

    return document

def Validate(document):
    def ipv4(teststring):
        regex = re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/([1-9]|[12][0-9]|3[0-2])$')

        if regex.match(teststring):
            return teststring
        else:
            raise ValueError("This is not a valid IPv4 address: %s" % (teststring))

    def ipv6(teststring):
        if teststring.startswith('fe80:'):
            raise ValueError("Do not configure link-local addresses")

        try:
            if len(teststring.split('/')) == 2:
                socket.inet_pton(socket.AF_INET6, teststring.split('/')[0])
                if 128 >= int(teststring.split('/')[1]) > 0:
                    return teststring.lower()
        except:
            raise ValueError("This is not a valid IPv6 address: %s" % (teststring))

    def IP(ip):
        if ':' in ip:
            return ipv6(ip)
        else:
            return ipv4(ip)

    def Adminstate(state):
        if type(int()) == type(state):
            state = list(['DOWN', 'UP'])[state]

        if state.upper() in ['UP', 'DOWN', 'UNKNOWN']:
            return state.upper()
        else:
            raise ValueError("Adminstate must be UP or DOWN, not %s" % (state))

    def Mtu(mtu):
        if 65536 >= mtu > 1280:
            return mtu
        else:
            raise ValueError("Invalid value for MTU")

    def VlanId(vlanid):
        if 4096 >= vlanid > 0:
            return vlanid
        else:
            raise ValueError("Invalid value for vlanid")

    def Interface(iface, iname):
        ret = {}
        ret['name'] = iname
        if iname == 'lo':
            ret['type'] = 'loopback'
        else:
            ret['type'] = 'default'

        try:
            for address in iface['addresses']:
                try:
                    ret['addresses']
                except KeyError:
                    ret['addresses'] = []
                ret['addresses'].append(IP(address))
        except ValueError as e:
            raise e
        except (KeyError, TypeError):
            pass

        try:
            ret['adminstate'] = Adminstate(iface['adminstate'])
        except ValueError as e:
            raise e
        except KeyError:
            ret['adminstate'] = 'UP'

        try:
            ret['mtu'] = Mtu(iface['mtu'])
        except ValueError as e:
            raise e
        except KeyError:
            if iname == 'lo':
                ret['mtu'] = 65536
            else:
                ret['mtu'] = '1500'

        try:
            ret['vlanid'] = VlanId(iface['vlanid'])
        except ValueError as e:
            raise e
        except KeyError:
            pass

        try:
            if iface['vlans']:
                vlans = []
                for vlan in iface['vlans']:
                    vname = ''
                    try:
                        vname = vlan['name']
                    except KeyError:
                        vname = "%s.%s" % (iname, vlan['vlanid'])
                    vlan['type'] = 'vlan'
                    vlan = Interface(vlan, vname)
                    if int(vlan['mtu']) > int(ret['mtu']):
                        ret['mtu'] = vlan['mtu']
                    vlans.append(vlan)
                ret['vlans'] = vlans
        except ValueError as e:
            raise e
        except KeyError:
            pass

        try:
            if iface['slaves']:
                ret['type'] = 'bond'
                ret['slaves'] = iface['slaves']
        except KeyError:
            pass

        return ret

    # First, check if any weird values occur
    olddoc = deepcopy(document)
    for iface in olddoc.keys():
        document[iface] = Interface(document[iface], iface)

    # Then, check if interfaces used in bonds are actually unconfigured
    olddoc = deepcopy(document)
    for iface in olddoc.keys():
        if document[iface]['type'] == 'bond':
            for s in document[iface]['slaves']:
                try:
                    if document[s]['vlans']:
                        raise ValueError("Interface %s is used as a slave and has vlans configured" % (s))
                except ValueError as e:
                    raise e
                except KeyError:
                    pass

                try:
                    if document[s]['addresses']:
                        raise ValueError("Interface %s is used as a slave and has addresses configured" % (s))
                except ValueError as e:
                    raise e
                except KeyError:
                    pass

                try:
                    document[s]
                except KeyError:
                    document[s] = {}

                document[s]['mtu'] = document[iface]['mtu']
                document[s]['adminstate'] = 'UP'
                document[s]['name'] = s
                document[s]['type'] = 'slave'

    return document

