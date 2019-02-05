#!/usr/bin/env python3

# Sqlog -- Ingest Nginx logs into SQLite.
# Copyright 2019 Ruud van Asseldonk.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# A copy of the License has been included in the root of the repository.

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
    referer_opt, line = line[1:].split('" "', 1)
    # TODO: Can the user agent include escaped quotes?
    user_agent_opt, tail = line.split('"', 1)
    assert tail == '\n'

    # Split request in method, url, and protocol.
    # Sometimes the request contains utter garbage.
    method, url, protocol = None, None, None
    if request.count(' ') == 2:
        method, request = request.split(' ', 1)
        url, protocol = request.rsplit(' ', 1)

    # Nginx logs unknown things as a dash.
    referer = None if referer_opt == '-' else referer_opt
    user_agent = None if user_agent_opt == '-' else user_agent_opt

    # Parse the time format "dd/mmm/yyyy:HH:MM:SS +ZZZZ".
    assert len(time_local_ugly) == 26
    day = time_local_ugly[:2]
    assert time_local_ugly[2] == '/'
    monthname = time_local_ugly[3:6]
    assert time_local_ugly[6] == '/'
    year = time_local_ugly[7:11]
    assert time_local_ugly[11] == ':'
    hour = time_local_ugly[12:14]
    assert time_local_ugly[14] == ':'
    minute = time_local_ugly[15:17]
    assert time_local_ugly[17] == ':'
    second = time_local_ugly[18:20]
    assert time_local_ugly[20] == ' '
    offset_sign_and_hours = time_local_ugly[21:24]
    offset_minutes = time_local_ugly[24:26]

    offset = f'{offset_sign_and_hours}:{offset_minutes}'
    month = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    }[monthname]

    # Format the time as almost ISO 8601. Only leave off the T and just use a
    # space. Nobody likes the T. And SQLite is fine either way.
    time_local = f'{year}-{month}-{day} {hour}:{minute}:{second}{offset}'

    return Row(
        remote_addr,
        time_local,
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
    conn.execute("create index if not exists ix_time on logs (time_local);")
    conn.execute("create index if not exists ix_url  on logs (url);")


def insert_row(conn: sqlite3.Connection, row: Row) -> int:
    r = conn.execute("insert into logs values (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    return r.rowcount


def main(fname: str) -> None:
    with sqlite3.connect(fname) as conn:
        create_table(conn)
        conn.commit()

        rows_inserted = 0
        for line in sys.stdin:
            rows_inserted += insert_row(conn, parse_line(line))

            if rows_inserted % 100 == 0:
                print(f'\rInserted {rows_inserted} rows.', end='', flush=True)

        conn.commit()
        print(f'\rInserted {rows_inserted} rows.')

        conn.execute("analyze")
        conn.commit()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(-1)

    main(sys.argv[1])
