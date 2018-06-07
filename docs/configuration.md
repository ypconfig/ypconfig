ypconfig reads a yaml-file (defaults to /etc/ypconfig/ypconfig.yml) and tries to configure the system accordingly. The configfile has the following syntax:

An array of interfaces, where each interface has the following options:
- description:
  A description we can read via snmpd
- addresses:
  An array of addresses in the syntax address/prefixlen
- vaddresses:
  An optional array of addresses that can be assigned on this interface, e.g. via VRRP. ypconfig will not add or remove these addresses
- adminstate:
  The state of the interface, may be ```UP``` or ```DOWN```, defaults to ```UP```
- mtu:
  The MTU of the interface, defaults to ```1500```
- ratelimit:
  Or a single float-value where this value is the ratelimit in bit/s, or a ```in``` value and/or ```out``` value, to differentiate between incoming and outgoing ratelimits. Optionally a unit can be added (KMG). [NOT YET IMPLEMENTED]
- slaves:
  An array with interfaces you want to bond into this interface.
- Optional type:
  The type of the interface:
  - default
  - bond
  - slave
  - vlan
  - loopback
- For vlan interfaces, set the following options:
  - The value ```vlanid``` is an integer for the vlan id.
  - The value ```parent``` is the name of the parent interface
- For bond interfaces, set the following options:
  - bond-mode, the bond-mode you want to use. See (this documentation)[https://www.kernel.org/doc/Documentation/networking/bonding.txt] for more information.
    - balance-rr
    - active-backup
    - balance-xor
    - broadcast
    - 802.3ad
    - balance-tlb
    - balance-alb
  - miimon:
    The MII link monitoring frequency in milliseconds, defaults to ```100```
  - lacp_rate:
    Only valid if mode is ```802.3ad```. Can be ```slow``` or ```fast```, defaults to ```slow```.

ROUTES
======
There is a special 'interface' called ```routes```. If the configfile does not have a ```routes```, routes remain ***untouched***. If you do want ypconfig to handle routes, here's how:

    routes:
      default:
      - 192.168.1.1
      - fd00::192:168:1:1
      172.16.0.0/24:
      - 192.168.2.1
      fd08::172:16:0:0/64
      - fd00::192:168:2:1

Although the routes use an array for nexthop, only one nexthop is currently supported.

EXAMPLE 1
=========

A single interface, nothing fancy

    eth0:
      addresses:
      - 192.168.1.4/24
      - fd00::192:168:1:4/64
      adminstate: UP
      mtu: 1500
    lo:
      addresses:
      - 127.0.0.1/8
      - ::1/128
      mtu: 65536

EXAMPLE 2
=========

A vlan interface on eth0

    eth0:
      adminstate: UP
      mtu: 1500
    foobar:
      adminstate: UP
      addresses:
      - 192.168.1.4/24
      - fd00::192:168:1:4/64
      mtu: 1500
      vlanid: 200
      parent: eth0
    lo:
      addresses:
      - 127.0.0.1/8
      - ::1/128
      mtu: 65536


EXAMPLE 3
=========

Two interfaces, eth0 with jumbo frames and eth1 with a ratelimit of 10mbit up and 100mbit down

    eth0:
      adminstate: UP
      mtu: 9000
      addresses:
      - 192.168.1.4/24
      - fd00::192:168:1:4/64
    eth1:
      adminstate: UP
      mtu: 1500
      addresses:
      - 192.168.2.4/24
      - fd00::192:168:2:4/64
      ratelimit:
        up: 10M
        down: 100M
    lo:
      addresses:
      - 127.0.0.1/8
      - ::1/128
      mtu: 65536

EXAMPLE 4
=========

Create a bond-interface with two slaves

    bond0:
      adminstate: UP
      mtu: 9000
      addresses:
      - 192.168.1.4/24
      - fd00::192:168:1:4/64
      slaves:
      - eth0
      - eth1
