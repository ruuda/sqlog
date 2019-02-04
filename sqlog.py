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

def create_table(conn: sqlite3.Connection) -> None:
  """
  Create the logs table if it does not exist.
  """
  conn.execute("""
    create table if not exists logs
    (
      remote_addr     text not null,
      time_local      text not null,
      method          text not null,
      url             text not null,
      protocol        text not null,
      status          int not null,
      body_bytes_sent int not null,
      referer         text null,
      user_agent      text not null,
      constraint unique_visit unique (remote_addr, time_local, method, url)
    );
  """)
  conn.execute("create index if not exists ix_time_local on logs (time_local);")
  conn.execute("create index if not exists ix_url        on logs (url);")
  conn.commit()


def main(fname: str) -> None:
  with sqlite3.connect(fname) as conn:
    create_table(conn)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(-1)

    main(sys.argv[1])
