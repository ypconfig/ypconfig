# ypconfig

ypconfig is a Python (hence the Y instead of the I) tool to configure networking interfaces on a Linux machine. Goal is to be able to configure a machine using [Ansible](http://ansible.com) and be able to rollback if something goes wrong while configuring the interfaces.

This tool is made possible by [pyroute2](https://github.com/svinota/pyroute2) which enables us to communicate with the Linux Netlink interface.

# System Requirements

ypconfig supports Python >= 3.11 and has been tested on Debian 12.

# Configuration

ypconfig reads a YAML file (defaults to `/etc/ypconfig/ypconfig.yml`) and tries to configure the system accordingly. The config file should contain an array of interfaces, where each interface has the following options:

- description:
  Your own description, usually read via snmpd.
- addresses:
  An array of addresses with the syntax 'ipAddress/prefixLength'.
- vaddresses:
  Optional: an array of addresses that can be assigned on this interface, e.g. via VRRP. ypconfig will not add or remove these addresses.
- adminstate:
  The state of the interface. Options: `UP` or `DOWN`. Default: `UP`.
- mtu:
  The MTU of the interface. Default: `1500`.
- ratelimit:
  Either a single float-value where this value is the ratelimit in bit/s, or an `in` value and/or `out` value, to differentiate between incoming and outgoing ratelimits. Optionally, a unit can be added (KMG). [NOT YET IMPLEMENTED]
- slaves:
  An array with interfaces you want to bond into this interface.
- Optional type:
  The type of the interface:
  - `default`
  - `bond`
  - `slave`
  - `vlan`
  - `loopback`
- For vLAN interfaces, set the following options:
  - The value `vlanid` is the vLAN ID (integer).
  - The value `parent` is the name of the parent interface.
- For bond interfaces, set the following options:
  - `bond-mode`, the bond-mode you want to use. See [this documentation](https://www.kernel.org/doc/Documentation/networking/bonding.txt) for more information.
    - `balance-rr`
    - `active-backup`
    - `balance-xor`
    - `broadcast`
    - `802.3ad`
    - `balance-tlb`
    - `balance-alb`
  - miimon:
    The MII link monitoring frequency in milliseconds. Default: `100`.
  - lacp_rate:
    Only valid if mode is `802.3ad`. Can be `slow` or `fast`. Default: `slow`.

## Routes

There is a special 'interface' called `routes`. If the config file does not have a `routes` interface, ypconfig will not touch routes. If you do want ypconfig to handle routes, here's how:

```
routes:
  default:
  - 192.168.1.1
  - fd00::192:168:1:1
  172.16.0.0/24:
  - 192.168.2.1
  fd08::172:16:0:0/64
  - fd00::192:168:2:1
```

Although the routes use an array for nexthop, only one nexthop is currently supported.

# Usage

When installing ypconfig, a config file will be created for you in `/etc/ypconfig/ypconfig.yml`. This config file will contain your currently configured interfaces. Note that this config file will not be generated when a file with the same name already exists. You can generate a config file at any time using `ypconfig createconfig`.

ypconfig ships with a systemd unit, `ypconfig.service`. This one-shot service takes care of configuring your interfaces (as specified in the config file) on boot.

You can commit at any time by running `ypconfig commit`. This will rollback if it doesn't receive your confirmation within 60 seconds. This behaviour can be overridden by running with the `--confirm` flag, but you should probably not do that as it will not rollback when you may need it to. Note that running `--confirm` with a faulty config file will not commit. You can check your config file using `ypconfig configtest`.

All `ypconfig` commands take the argument `--cfg` which allows you to use a custom config file.

# Examples

## Example 1: One interface

This is a single, normal interface with no special options.

```
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
```

## Example 2: vLAN interface

A vLAN interface on `eth0`.

```
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
```

## Example 3: Multiple interfaces

Two interfaces: `eth0` with jumbo frames, and `eth1` with a ratelimit of 10 Mbit up and 100 Mbit down.

```
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
```

## Example 4: Bonded interface with two slaves

```
bond0:
  adminstate: UP
  mtu: 9000
  addresses:
  - 192.168.1.4/24
  - fd00::192:168:1:4/64
  slaves:
  - eth0
  - eth1
```

# Credits

ypconfig was originally written by Mark Schouten <mark@tuxis.nl> at Tuxis. It was open-sourced in June 2017.
