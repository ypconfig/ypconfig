#!/usr/bin/env python3

from pprint import pprint, pformat

class Iface(object):
    def __init__(self, nlinfo=None, cinfo=None):
        self.name = str()
        self.addresses = []
        self.mtu = 1500
        self.adminstate = 0

        if nlinfo:
            self.parse_nlinfo(nlinfo)
        elif cinfo:
            self.parse_config(cinfo)

    def setname(self, name):
        self.name = name

    def setmtu(self, mtu):
        self.mtu = mtu

    def setadminstate(self, adminstate):
        if not adminstate in ['UP', 'DOWN', 'UNKNOWN']:
            raise ValueError("Unknown value for adminstate: %s" % (adminstate))

        self.adminstate = adminstate

    def parse_nlinfo(self, nlinfo):
        self.setmtu(nlinfo.get_attr('IFLA_MTU'))
        self.setname(nlinfo.get_attr('IFLA_IFNAME'))
        self.setadminstate(nlinfo.get_attr('IFLA_OPERSTATE'))


    def __str__(self):
        return pformat(vars(self))

class Eth(Iface):
    def __init__(self, nlinfo=None, cinfo=None):
        super(self.__class__, self).__init__()
        del(self.vlans)
        self.vlanid = int()
        self.parent = int()

        if nlinfo:
            self.parse_nlinfo(nlinfo)
        elif cinfo:
            self.parse_config(cinfo)

    self.vlans = []
class Vlan(Iface):
    def __init__(self, nlinfo=None):
        super(self.__class__, self).__init__()
        del(self.vlans)
        self.vlanid = int()
        self.parent = int()

        if nlinfo:
            self.parse_nlinfo(nlinfo)
        elif cinfo:
            self.parse_config(cinfo)

    def parse_nlinfo(self, nlinfo):
        self.setmtu(nlinfo.get_attr('IFLA_MTU'))
        self.setname(nlinfo.get_attr('IFLA_IFNAME'))
        self.setadminstate(nlinfo.get_attr('IFLA_OPERSTATE'))

        self.setparent(nlinfo.get_attr(''))


