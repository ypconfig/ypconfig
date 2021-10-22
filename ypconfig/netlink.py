#!/usr/bin/env python3

from pyroute2 import IPRoute
from pyroute2 import IPDB
from socket import AF_INET, AF_INET6


def GetNow():
    ip = IPRoute()
    ret = {}

    for route in ip.get_routes() + ip.get_routes(family=AF_INET6):
        if route.get_attr('RTA_GATEWAY'):
            try:
                ret['routes']
            except KeyError:
                ret['routes'] = dict()

            if not route.get_attr('RTA_DST'):
                dst = 'default'
            else:
                dst = '/'.join([str(route.get_attr('RTA_DST')), str(route['dst_len'])])

            try:
                ret['routes'][dst]
            except KeyError:
                ret['routes'][dst] = list()

            ret['routes'][dst].append(route.get_attr('RTA_GATEWAY'))

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
                    this['bond-mode'] = bonddata.get_attr('IFLA_BOND_MODE')
                    ret[this['name']] = this
            except Exception as e:
                print(e)
                pass
        else:
            ret[this['name']] = this

    return ret

def Commit(cur, new):
    global ip

    skiproutes = False
    changed = False

    try:
        curroutes = cur['routes']
        crouteset = set(cur['routes'].keys())
    except KeyError:
        crouteset = set()

    try:
        newroutes = new['routes']
        nrouteset = set(new['routes'].keys())
    except KeyError:
        skiproutes = True
        print("No routes configured, skipping routeconfiguration")

    try:
        del(new['routes'])
    except:
        pass

    try:
        del(cur['routes'])
    except:
        pass

    curif = set(cur.keys())
    newif = set(new.keys())

    with IPDB(mode='implicit') as ip:
        curif = set(cur.keys())
        newif = set(new.keys())

        # These interfaces should be deleted
        for iface in curif.difference(newif):
            changed = True
            Delif(iface)

        # These interfaces need to be created
        toadd = list()
        for iface in newif.difference(curif):
            changed = True
            if new[iface]['type'] == 'bond':
                toadd.insert(0, iface)
            elif new[iface]['type'] == 'vlan':
                toadd.append(iface)

        for iface in toadd:
            changed = True
            if new[iface]['type'] == 'bond':
                Addbond(new[iface])
            elif new[iface]['type'] == 'vlan':
                Addvlan(new[iface])

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
                                Delslave(iface, slave)
                        elif v in ['vlanid', 'parent']:
                            Delif(iface)
                            Addvlan(new[iface])
                        elif v in ['bond-mode', 'miimon', 'lacp_rate']:
                            Delif(iface)
                            Addbond(new[iface])
                except KeyError as e:
                    print(f"{e} on {iface}")
                    pass
                except Exception as e:
                    raise e

        if not skiproutes:
            try:
                # These routes should be deleted
                for route in crouteset.difference(nrouteset):
                    changed = True
                    DelRoute(route)

                # These routes should be created
                for route in nrouteset.difference(crouteset):
                    changed = True
                    AddRoute(route, newroutes[route])

                # These routes should be checked
                for route in nrouteset.intersection(crouteset):
                    if curroutes[route] != newroutes[route]:
                        changed = True
                        ChangeRoute(route, newroutes[route])

            except Exception as e:
                raise e

        ip.commit()
        ip.release()

        return changed

def AddRoute(route, gws):
    print(f"Adding route for {route}/{gws}")
    global ip
    for d in gws:
        ip.routes.add(dst=route, gateway=d)
        ip.commit()

def DelRoute(route):
    print(f"Removing route for {route}")
    global ip
    ip.routes.remove(route)

def DefaultRoute(gws):
    global ip
    v6new = [ d for d in gws if ':' in d ]
    v4new = [ d for d in gws if '.' in d ]
    v6cur = list()
    v4cur = list()
    for r in ip.routes:
        if r['dst_len'] != 0:
            continue
        if r['family'] == 10:
            v6cur.append(r['gateway'])
        elif r['family'] == 2:
            v4cur.append(r['gateway'])

    if len(v6new) > len(v6cur):
        AddRoute('default', v6new)

    if len(v4new) > len(v4cur):
        AddRoute('default', v4new)

    for r in ip.routes:
        if r['dst_len'] != 0:
            continue
        if r['family'] == 10:
            if len(v6new) == 0:
                r.remove()
            elif len(v6new) == len(v6cur):
                if v6new[0] == v6cur[0]:
                    continue
                r.remove()
                ip.commit()
                AddRoute('default', v6new)
        elif r['family'] == 2:
            if len(v4new) == 0:
                r.remove()
            elif len(v4new) == len(v4cur):
                if v4new[0] == v4cur[0]:
                    continue
                r.remove()
                ip.commit()
                AddRoute('default', v4new)

def ChangeRoute(route, gws):
    print(f"Changing route for {route}")
    global ip
    if route == 'default':
        return DefaultRoute(gws)

    for d in gws:
        ip.routes[route].gateway = d

def Delif(iface):
    print(f"Removing interface {iface}")
    global ip
    i = ip.interfaces[iface]
    i.remove()
    ip.commit()

def Addvlan(vals):
    print(f"Creating vlan interface {vals['name']} on {vals['parent']} with id {vals['vlanid']}")
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
    print(f"Creating bond interface {vals['name']} with {str(vals)}")
    global ip
    iface = vals['name']
    i = ip.create(kind='bond', ifname=iface, bond_mode=vals['bond-mode'], bond_miimon=vals['miimon'], reuse=True)
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
    print(f"Adding interface {slave} as slave on {iface}")
    global ip
    Ifstate(slave, 'DOWN')
    i = ip.interfaces[iface]
    i.add_port(ip.interfaces[slave])
    ip.commit()

def Delslave(iface, slave):
    print(f"Removing interface {slave} as slave from {iface}")
    global ip
    i = ip.interfaces[iface]
    i.del_port(slave)
    ip.commit()

def Deladdr(iface, addr):
    print(f"Removing IP {addr} from {iface}")
    global ip
    i = ip.interfaces[iface]
    i.del_ip(addr)
    ip.commit()

def Addaddr(iface, addr):
    print(f"Adding IP {addr} to {iface}")
    global ip
    i = ip.interfaces[iface]
    i.add_ip(addr)
    ip.commit()

def Ifstate(iface, state):
    print(f"Setting state of interface {iface} to {state}")
    global ip
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
    print(f"Setting MTU of interface {iface} to {mtu}")
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
    print(f"Setting alias of interface {iface} to {alias}")
    global ip
    i = ip.interfaces[iface]
    if str(i['ifalias']) != str(alias):
        i['ifalias'] = alias
        # XXX We do not want this. But untill https://github.com/svinota/pyroute2/issues/349 is fixed, we need it.
        try:
            ip.commit()
        except:
            pass
