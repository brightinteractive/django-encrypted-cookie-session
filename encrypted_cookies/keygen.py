# -*- coding: utf-8 -*-
# (c) 2015 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import optparse
import sys

from  cryptography.fernet import Fernet


def main(stdout=sys.stdout, argv=sys.argv[1:]):
    p = optparse.OptionParser(
        usage='%prog [options]\n\n'
              'Generates a suitable value to put in '
              'your ENCRYPTED_COOKIE_KEYS=[...] setting.')
    (options, args) = p.parse_args(argv)
    stdout.write(Fernet.generate_key())


if __name__ == '__main__':
    main()
