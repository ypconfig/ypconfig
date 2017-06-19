#!/usr/bin/env python3

from pyroute2 import IPRoute
from pyroute2 import IPDB

def GetNow():
    ip = IPRoute()
    ret = {}

    for iface in ip.get_links():
        iname = iface.get_attr('IFLA_IFNAME')
        try:
            this = ret[iname]
        except KeyError:
            this = {}
            this['type'] = 'default'

        this['name'] = iface.get_attr('IFLA_IFNAME')
        if iface.get_attr('IFLA_IFALIAS'):
            this['description'] = iface.get_attr('IFLA_IFALIAS')
        else:
            this['description'] = this['name']

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

        if this['name'] == 'lo':
            this['type'] = 'loopback'
            this['adminstate'] = 'UP'


        if iface.get_attr('IFLA_LINKINFO'):
            try:
                linfo = iface.get_attr('IFLA_LINKINFO')
                if linfo.get_attr('IFLA_INFO_KIND') == 'vlan':
                    # Get the parents name
                    pname = ip.get_links(iface.get_attr('IFLA_LINK'))[0].get_attr('IFLA_IFNAME')
                    this['type'] = 'vlan'
                    this['parent'] = pname
                    this['vlanid'] = linfo.get_attr('IFLA_INFO_DATA').get_attr('IFLA_VLAN_ID')
                    ret[this['name']] = this
                elif linfo.get_attr('IFLA_INFO_SLAVE_KIND') == 'bond':
                    # Get the parents name
                    pname = ip.get_links(iface.get_attr('IFLA_MASTER'))[0].get_attr('IFLA_IFNAME')
                    try:
                        ret[pname]
                    except KeyError:
                        ret[pname] = {}

                    try:
                        ret[pname]['slaves']
                    except KeyError:
                        ret[pname]['slaves'] = []

                    ret[pname]['slaves'].append(this['name'])
                    this['type'] = 'slave'
                    ret[this['name']] = this
                elif linfo.get_attr('IFLA_INFO_KIND') == 'bond':
                    bonddata = linfo.get_attr('IFLA_INFO_DATA')
                    this['type'] = 'bond'
                    this['miimon'] = bonddata.get_attr('IFLA_BOND_MIIMON')
                    this['bond_mode'] = bonddata.get_attr('IFLA_BOND_MODE')
                    ret[this['name']] = this
            except Exception as e:
                print(e)
                pass
        else:
            ret[this['name']] = this

    return ret

def Commit(cur, new):
    global ip
    curif = set(cur.keys())
    newif = set(new.keys())

    changed = False
    with IPDB(mode='implicit') as ip:
        curif = set(cur.keys())
        newif = set(new.keys())

        # These interfaces should be deleted
        for iface in curif.difference(newif):
            changed = True
            Delif(iface)

        # These interfaces need to be created
        for iface in newif.difference(curif):
            changed = True
            if new[iface]['type'] == 'vlan':
                Addvlan(new[iface])
            elif new[iface]['type'] == 'bond':
                Addbond(new[iface])

        # Processes changes in remaining interfaces
        for iface in newif.intersection(curif):
            c = cur[iface]
            n = new[iface]

            for v in ['description', 'addresses', 'adminstate', 'mtu', 'ratelimit', 'slaves', 'vlanid', 'parent', 'bond-mode', 'miimon', 'lacp_rate']:
                try:
                    n[v]
                except KeyError:
                    if v == 'addresses':
                        n[v] = []
                    else:
                        n[v] = None
                try:
                    c[v]
                except KeyError:
                    if v == 'addresses':
                        c[v] = []
                    else:
                        c[v] = None

                if v == 'addresses':
                    vaddresses = []
                    try:
                        vaddresses += n['vaddresses']
                    except KeyError:
                        pass
                    try:
                        vaddresses += c['vaddresses']
                    except KeyError:
                        pass

                try:
                    if n[v] != c[v]:
                        if v != 'addresses':
                            changed = True
                        if v == 'adminstate':
                            Ifstate(iface, n[v])
                        elif v == 'mtu':
                            Ifmtu(iface, n[v])
                        elif v == 'description':
                            Ifalias(iface, n[v])
                        elif v == 'addresses':
                            for addr in set(n[v]).difference(set(c[v])):
                                if addr not in vaddresses:
                                    changed = True
                                    Addaddr(iface, addr)
                            for addr in set(c[v]).difference(set(n[v])):
                                if addr not in vaddresses:
                                    changed = True
                                    Deladdr(iface, addr)
                        elif v == 'slaves':
                            for slave in set(n[v]).difference(set(c[v])):
                                Addslave(iface, slave)
                            for slave in set(c[v]).difference(set(n[v])):
                                Removeslave(iface, slave)
                        elif v in ['vlanid', 'parent']:
                            Delif(iface)
                            Addvlan(new[iface])
                        elif v in ['bond-mode', 'miimon', 'lacp_rate']:
                            Delif(iface)
                            Addbond(new[iface])
                except KeyError as e:
                    print("%s on %s" % (e, iface))
                    pass
                except Exception as e:
                    raise e
        ip.commit()
        ip.release()

        return changed

def Delif(iface):
    print("Removing interface %s" % (iface))
    global ip
    i = ip.interfaces[iface]
    i.remove()
    ip.commit()

def Addvlan(vals):
    print("Creating vlan interface %s on %s with id %s" % (vals['name'], vals['parent'], vals['vlanid']))
    global ip
    iface = vals['name']
    Ifstate(vals['parent'], 'UP')

    parent = ip.interfaces[vals['parent']]

    i = ip.create(kind='vlan', ifname=iface, link=parent, vlan_id=vals['vlanid'], reuse=True)
    ip.commit()

    Ifstate(iface, vals['adminstate'])

    Ifmtu(iface, vals['mtu'])
    Ifalias(iface, vals['description'])
    try:
        vals['addresses']
        for addr in vals['addresses']:
            Addaddr(iface, addr)
    except KeyError:
        pass
    except Exception as e:
        raise e
    ip.commit()

def Addbond(vals):
    print("Creating bond interface %s with %s" % (vals['name'], str(vals)))
    global ip
    iface = vals['name']
    i = ip.create(kind='bond', ifname=iface, bond_mode=vals['bond_mode'], bond_miimon=vals['miimon'], reuse=True)
    for child in vals['slaves']:
        Ifmtu(child, vals['mtu'])
        Addslave(iface, child)
    Ifmtu(iface, vals['mtu'])
    Ifstate(iface, vals['adminstate'])
    Ifalias(iface, vals['description'])
    try:
        vals['addresses']
        for addr in vals['addresses']:
            Addaddr(vals['name'], addr)
    except KeyError:
        pass
    except Exception as e:
        raise e
    ip.commit()

def Addslave(iface, slave):
    print("Adding interface %s as slave on %s" % (slave, iface))
    global ip
    i = ip.interfaces[iface]
    i.add_port(ip.interfaces[slave])
    ip.commit()

def Delslave(iface, slave):
    print("Removing interface %s as slave from %s" % (slave, iface))
    global ip
    i = ip.interfaces[iface]
    i.del_port(ip.interfaces[slave])
    ip.commit()

def Deladdr(iface, addr):
    print("Removing IP %s from %s" % (addr, iface))
    global ip
    i = ip.interfaces[iface]
    i.del_ip(addr)
    ip.commit()

def Addaddr(iface, addr):
    print("Adding IP %s to %s" % (addr, iface))
    global ip
    i = ip.interfaces[iface]
    i.add_ip(addr)
    ip.commit()

def Ifstate(iface, state):
    print("Setting state of interface %s to %s" % (iface, state))
    global ip
    from pprint import pprint
    i = ip.interfaces[iface]
    if i['kind'] == 'vlan':
        p = ip.interfaces[i['link']]
        if p['operstate'] == 'DOWN' and state == 'UP':
            return
    if state == 'UP':
        i.up()
        ip.commit()
        i.wait_ip('fe80::', mask=64, timeout=5)
    if state == 'DOWN':
        i.down()
        ip.commit()

def Ifmtu(iface, mtu):
    print("Setting MTU of interface %s to %s" % (iface, mtu))
    global ip
    i = ip.interfaces[iface]
    if int(i['mtu']) != int(mtu):
        i['mtu'] = int(mtu)
        # XXX We do not want this. But untill https://github.com/svinota/pyroute2/issues/349 is fixed, we need it.
        try:
            ip.commit()
        except:
            pass

def Ifalias(iface, alias):
    print("Setting alias of interface %s to %s" % (iface, alias))
    global ip
    i = ip.interfaces[iface]
    if str(i['ifalias']) != str(alias):
        i['ifalias'] = alias
        # XXX We do not want this. But untill https://github.com/svinota/pyroute2/issues/349 is fixed, we need it.
        try:
            ip.commit()
        except:
            pass
