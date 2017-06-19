ypconfig
========

ypconfig is a Python (hence the Y instead of the I) tool to configure networking interfaces on a Linux machine. Goal is to be able to configure a machine using [Ansible](http://ansible.com) and be able to rollback if something goes wrong while configuring the interfaces.

This tool is made possible by [pyroute2](https://github.com/svinota/pyroute2), which enables us to communicate with Linux' Netlink interface.


Credits
=======

ypconfig is originally written by Mark Schouten <mark@tuxis.nl>, Tuxis Internet Engineering and shared with the community in June 2017!
