#!/usr/bin/env python3

import esi_load, sys

def main(args):
    esi_load.getRefreshToken()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
