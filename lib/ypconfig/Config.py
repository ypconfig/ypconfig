#!/usr/bin/env python3

from yaml import safe_load, dump, YAMLError
from sys import exit
from copy import deepcopy
import re, socket


def Get(cfg):
    try:
        f = open(cfg)
    except Exception as e:
        raise e

    try:
        document = safe_load(f.read())
    except YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            raise ValueError("YAML Error in configuration; Error on line %s, position %s)" \
                % (mark.line+1, mark.column+1))
    except:
        raise ValueError("YAML Error in configuration")

    return document

def Set(cfg, configdict):
    try:
        f = open(cfg, 'w')
    except Exception as e:
        raise e

    try:
        document = dump(configdict, default_flow_style=False)
        f.write(document)
    except Exception as e:
        raise e

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

        if state.upper() in ['UP', 'DOWN', 'UNKNOWN', 'LOWERLAYERDOWN']:
            return state.upper()
        else:
            raise ValueError("Adminstate must be UP or DOWN, not %s" % (state))

    def Ifname(teststring):
        regex = re.compile('^[-_a-z0-9]{2,15}$')

        if regex.match(teststring):
            return teststring
        else:
            raise ValueError("Invalid interfacename: %s" % (teststring))

    def Mtu(mtu):
        if 65536 >= int(mtu) > 128:
            return int(mtu)
        else:
            raise ValueError("Invalid value for MTU")

    def VlanId(vlanid):
        if 4096 >= vlanid > 0:
            return vlanid
        else:
            raise ValueError("Invalid value for vlanid")

    def MiiMon(miimon):
        if 10000 >= miimon >= 0:
            return miimon
        else:
            raise ValueError("Invalid value for miimon")

    def BondMode(bmode):
        modes = ['balance-rr','active-backup','balance-xor','broadcast','802.3ad','balance-tlb','balance-alb']

        try:
            if type(int()) == type(bmode):
                bmode = modes[bmode]
        except:
            raise ValueError("Invalid value for bond-mode")

        if bmode in modes:
            return modes.index(bmode)
        else:
            raise ValueError("Invalid value for bond-mode")

    def LacpRate(rate):
        if rate.lower() in ['slow', 'fast']:
            return rate.lower()
        else:
            raise ValueError("Invalid value for lacp_rate")

    def Interface(iface, iname):
        known_fields = [ 'vaddresses', 'description', 'name', 'addresses', 'adminstate', 'mtu', 'ratelimit', 'slaves', 'type', 'vlanid', 'parent', 'bond-mode', 'miimon', 'lacp_rate', 'autoconfigure' ]
        for f in iface.keys():
            if f not in known_fields:
                raise ValueError("Invalid field in config for interface %s: %s" % (iname, f))

        ret = {}
        ret['name'] = Ifname(iname)
        if iname == 'lo':
            ret['type'] = 'loopback'
        else:
            ret['type'] = 'default'

        try:
            ret['description'] = iface['description']
        except KeyError:
            ret['description'] = ret['name']

        try:
            if iface['vaddresses']:
                if type(iface['vaddresses']) != list:
                    raise ValueError("vaddresses should be an array")
            for address in iface['vaddresses']:
                try:
                    ret['vaddresses']
                except KeyError:
                    ret['vaddresses'] = []
                ret['vaddresses'].append(IP(address))
            ret['vaddresses'].sort()
        except ValueError as e:
            raise e
        except (KeyError, TypeError):
            pass

        try:
            if iface['addresses']:
                if type(iface['addresses']) != list:
                    raise ValueError("Addresses should be an array")
            for address in iface['addresses']:
                try:
                    ret['addresses']
                except KeyError:
                    ret['addresses'] = []
                ret['addresses'].append(IP(address))
            ret['addresses'].sort()
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
                ret['mtu'] = Mtu(65536)
            else:
                ret['mtu'] = Mtu(1500)

        try:
            ret['vlanid'] = VlanId(iface['vlanid'])
            ret['type'] = 'vlan'
            ret['parent'] = iface['parent']
        except ValueError as e:
            raise e
        except KeyError:
            pass

        try:
            if iface['slaves']:
                ret['type'] = 'bond'
                if type(iface['slaves']) != list:
                    raise ValueError("Slaves should be an array")
                ret['slaves'] = iface['slaves']
        except ValueError as e:
            raise e
        except KeyError:
            pass

        if ret['type'] == 'bond':
            try:
                ret['bond_mode'] = BondMode(iface['bond-mode'])
            except ValueError as e:
                raise e
            except KeyError:
                ret['bond_mode'] = 0

            try:
                if iface['miimon']:
                    ret['miimon'] = MiiMon(iface['miimon'])
            except ValueError as e:
                raise
            except KeyError:
                ret['miimon'] = 100

            if ret['bond_mode'] == '802.3ad':
                try:
                    ret['lacp_rate'] = LacpRate(iface['lacp_rate'])
                except ValueError as e:
                    raise e
                except KeyError:
                    ret['lacp_rate'] = 'slow'
        return ret

    # First, check if any weird values occur
    olddoc = deepcopy(document)
    for iface in olddoc.keys():
        if not document[iface]:
            raise ValueError("Empty interface configuration for %s" % (iface))
        document[iface] = Interface(document[iface], iface)

    # Then, check if interfaces used in bonds are actually unconfigured
    olddoc = deepcopy(document)
    for iface in olddoc.keys():
        if document[iface]['type'] == 'bond':
            for s in document[iface]['slaves']:
                try:
                    for t in document.keys():
                        try:
                            if document[t]['parent'] == s:
                                raise ValueError("Interface %s is used as a slave and has vlans configured" % (s))
                        except KeyError:
                            pass
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
                document[s]['name'] = s
                document[s]['type'] = 'slave'

    return document

