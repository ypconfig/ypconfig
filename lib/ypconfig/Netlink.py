#!/usr/bin/env python3

from pyroute2 import IPRoute
from pyroute2 import IPDB

def GetNow():
    ip = IPRoute()
    ret = {}

    for iface in ip.get_links():
        this = {}
        this['type'] = 'default'
        this['name'] = iface.get_attr('IFLA_IFNAME')
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
                        ret[pname]
                    except KeyError:
                        ret[pname] = {}

                    try:
                        ret[pname]['vlans']
                    except KeyError:
                        ret[pname]['vlans'] = []

                    
                    this['type'] = 'vlan'
                    this['vlanid'] = linfo.get_attr('IFLA_INFO_DATA').get_attr('IFLA_VLAN_ID')
                    ret[pname]['vlans'].append(this)
            except Exception as e:
                print(e)
                pass
        else:
            ret[this['name']] = this

    return ret
