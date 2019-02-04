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
import typing

from typing import NamedTuple, Optional

class Row(NamedTuple):
  remote_addr: str
  time_local: str
  method: Optional[str]
  url: Optional[str]
  protocol: Optional[str]
  status: int
  body_bytes_sent: int
  referer: Optional[str]
  user_agent: Optional[str]


def parse_line(line: str) -> Row:
  # Parse the basic line.
  remote_addr, line = line.split(' - ', 1)
  remote_user, line = line.split(' [', 1)
  time_local_ugly, line = line.split('] ', 1)
  assert line[:1] == '"'
  # TODO: Can the request include escaped quotes?
  request, line = line[1:].split('" ', 1)
  status_str, line = line.split(' ', 1)
  body_bytes_str, line = line.split(' ', 1)
  assert line[:1] == '"'
  # TODO: Can the referer include escaped quotes?
  referer, line = line[1:].split('" "', 1)
  # TODO: Can the user agent include escaped quotes?
  user_agent, tail = line.split('"', 1)
  assert tail == '\n'

  # Split request in method, url, and protocol.
  # Sometimes the request contains utter garbage.
  method, url, protocol = None, None, None
  if request.count(' ') == 2:
    method, request = request.split(' ', 1)
    url, protocol = request.rsplit(' ', 1)

  # Nginx logs unknown things as a dash.
  referer = None if referer == '-' else referer
  user_agent = None if user_agent == '-' else user_agent

  # TODO: Parse time.
  time_local_iso8601 = time_local_ugly

  return Row(
    remote_addr,
    time_local_iso8601,
    method,
    url,
    protocol,
    int(status_str),
    int(body_bytes_str),
    referer,
    user_agent,
  )


def create_table(conn: sqlite3.Connection) -> None:
  """
  Create the logs table if it does not exist.
  """
  conn.execute("""
    create table if not exists logs
    (
      remote_addr     text not null,
      time_local      text not null,
      method          text null,
      url             text null,
      protocol        text null,
      status          int not null,
      body_bytes_sent int not null,
      referer         text null,
      user_agent      text null,
      constraint unique_visit unique (remote_addr, time_local, method, url)
        on conflict ignore
    );
  """)
  conn.execute("create index if not exists ix_time_local on logs (time_local);")
  conn.execute("create index if not exists ix_url        on logs (url);")


def insert_row(conn: sqlite3.Connection, row: Row) -> None:
  conn.execute("insert into logs values (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)


def main(fname: str) -> None:
  with sqlite3.connect(fname) as conn:
    create_table(conn)
    conn.commit()

    for line in sys.stdin:
      insert_row(conn, parse_line(line))

    conn.commit()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(-1)

    main(sys.argv[1])
