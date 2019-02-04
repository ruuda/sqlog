#!/usr/bin/env python3
# Sqlog -- Ingest Nginx logs into SQLite.
# Copyright 2019 Ruud van Asseldonk.

"""
Sqlog: Ingest Nginx logs into SQLite for querying.

Usage:
    ./sqlog.py log.sqlite < access.log
"""

import sys
import sqlite3

def main(fname: str) -> None:
    conn = sqlite3.connect(fname)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(-1)

    main(sys.argv[1])
