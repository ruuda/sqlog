#!/usr/bin/env python3

# Sqlog -- Ingest Nginx logs into SQLite.
# Copyright 2019 Ruud van Asseldonk.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# A copy of the License has been included in the root of the repository.

"""
Sqlog: Ingest Nginx logs into SQLite for querying.

Usage:
  ./sqlog.py --format <format> log.sqlite < access.log

Options:
  --format COMBINED   Use default Nginx log format
  --format VCOMBINED  Use Nginx log format with "<vhost>: " prefix
"""

import sys
import sqlite3
import typing

from typing import NamedTuple, Optional


class Row(NamedTuple):
    vhost: Optional[str]
    remote_addr: str
    time_local: str
    method: Optional[str]
    url: Optional[str]
    protocol: Optional[str]
    status: int
    body_bytes_sent: int
    referer: Optional[str]
    user_agent: Optional[str]


def parse_line(format: str, line: str) -> Row:
    vhost: Optional[str] = None

    if format == "VCOMBINED":
        vhost, line = line.split(': ', 1)

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
    time_local = f'{year}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}{offset}'

    return Row(
        vhost,
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
        vhost           text null,
        remote_addr     text not null,
        time_local      text not null,
        method          text null,
        url             text null,
        protocol        text null,
        status          int not null,
        body_bytes_sent int not null,
        referer         text null,
        user_agent      text null
    );
    """)
    # Create a unique index, so that we can import the same logs multiple times,
    # without creating duplicates. Unfortunately, if the log format has only
    # second-granularity timestamps, then we cannot record a client repeating
    # the same request within one second.
    conn.execute("""
    create unique index if not exists ix_unique_visit on logs
    (
        -- Note that we put the time first, so we can query efficiently on time
        -- ranges.
        time_local,
        -- Null values do not count towards uniqueness, so index on a non-null
        -- value to ensure that we never insert log lines twice.
        ifnull(vhost, ''),
        remote_addr,
        ifnull(method, ''),
        ifnull(url, '')
    )
    """)
    conn.execute("create index if not exists ix_url on logs (url);")


def insert_row(conn: sqlite3.Connection, row: Row) -> int:
    try:
        r = conn.execute("insert into logs values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
        return r.rowcount
    except sqlite3.IntegrityError:
        return 0


def main(format: str, fname: str) -> None:
    with sqlite3.connect(fname) as conn:
        create_table(conn)
        conn.commit()

        n_inserted = 0
        n_ingested = 0

        for line in sys.stdin:
            inserted_count = insert_row(conn, parse_line(format, line))
            n_inserted += inserted_count
            n_ingested += 1

            if n_ingested % 200 == 0:
                print(
                    f'\rRead {n_ingested} lines, inserted {n_inserted}.',
                    end='',
                    flush=True
                )

        conn.commit()
        print(f'\rRead {n_ingested} lines, inserted {n_inserted}.')

        conn.execute('analyze')
        conn.commit()

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(-1)

    assert sys.argv[1] == "--format"
    assert sys.argv[2] in ("COMBINED", "VCOMBINED")

    main(sys.argv[2], sys.argv[3])
