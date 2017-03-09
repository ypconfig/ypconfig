ypconfig reads a yaml-file (defaults to /etc/ypconfig/interfaces.yml) and tries to configure the system accordingly. The configfile has the following syntax:

An array of interfaces, where each interface has the following options:
- description:
  A description we can read via snmpd
- addresses:
  An array of addresses in the syntax address/prefixlen
- adminstate:
  The state of the interface, may be ```UP``` or ```DOWN```, defaults to ```UP```
- mtu:
  The MTU of the interface, defaults to ```1500```
- vlans:
  An array of dictionaries like interfaces, but with the following exceptions:
  - We do not (yet) support Q-in-Q, so ```vlans``` is not accepted
  - The value ```vlanid``` is an integer for the vlan id.
  - The value ```name``` is the name of the interface, defaults to ```parent.vlanid```
- ratelimit:
  Or a single float-value where this value is the ratelimit in bit/s, or a ```in``` value and/or ```out``` value, to differentiate between incoming and outgoing ratelimits. Optionally a unit can be added (KMG).
- slaves:
  An array with interfaces you want to bond into this interface.


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
      vlans:
      - adminstate: UP
        addresses:
        - 192.168.1.4/24
        - fd00::192:168:1:4/64
        mtu: 1500
        name: foobar
        vlanid: 200
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