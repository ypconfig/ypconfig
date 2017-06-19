#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Usage:
  ypconfig configtest [options]
  ypconfig createconfig [options]
  ypconfig commit [--confirm] [options]

Options:
  -h, --help            Show this help
  -v, --verbose         Be more verbose
  --confirm             Do not ask for confirmation [default: False]
  --cfg=<configfile>    Location of the configfile [default: /etc/ypconfig/ypconfig.yml]
"""

import sys, os, select
sys.path.insert(0, os.path.join(os.getcwd(), 'lib'))

from ypconfig import config, netlink
from docopt import docopt
from schema import Schema, And, Or, Use, SchemaError, Optional
from pprint import pprint
from pyroute2 import IPRoute
from time import time

def rollback(cfg):
    cur = config.Validate(netlink.GetNow())
    new = config.Get(cfg)
    netlink.Commit(cur, new)
    print("Rolled back to %s" % (cfg))
    sys.exit(1)

def main():
    args = docopt(__doc__)

    schema = Schema({
        '--help': bool,
        '--verbose': bool,
        '--cfg': str,
        '--confirm': bool,
        'commit': bool,
        'configtest': bool,
        'createconfig': bool
    })

    try:
        args = schema.validate(args)
    except SchemaError as e:
        sys.exit(e)

    if not args['createconfig']:
        try:
            cfgdoc = config.Get(args['--cfg'])
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

    if args['configtest']:
        try:
            cfg = config.Validate(cfgdoc)
        except Exception as e:
            print("Errors in configuration:\n - %s" % (e))
            sys.exit(1)
        else:
            print("Configuration is ok!")
    elif args['createconfig']:
        cfg = netlink.GetNow()
        cfg = config.Validate(cfg)
        config.Set(args['--cfg'], cfg)
    elif args['commit']:
        cur = config.Validate(netlink.GetNow())
        cfgfile = '_'.join(['ypconfig', 'backup', str(time())])
        rollbackcfg = os.path.join('/tmp', cfgfile)
        config.Set(rollbackcfg, cur)
        try:
            new = config.Validate(cfgdoc)
        except ValueError as e:
            print("Errors in configuration:\n - %s" % (e))
            sys.exit(1)

        changed = False
        try:
            changed = netlink.Commit(cur, new)
        except Exception as e:
            print("We had an error confirming this new configuration:\n - '%s" % (e))
            print("Rolling back")
            rollback(rollbackcfg)

        if not changed:
            print("Nothing changed")
            sys.exit(0)

        if not args['--confirm']:
            print("New configuration commited. Type 'confirm' to confirm, we will rollback in 60 seconds otherwise.")
            try:
                i, o, e = select.select( [sys.stdin], [], [], 60 )

                if i and sys.stdin.readline().strip() == 'confirm':
                    sys.exit(0)
                else:
                    rollback(rollbackcfg)
            except KeyboardInterrupt:
                rollback(rollbackcfg)

if __name__ == "__main__":
    main()
