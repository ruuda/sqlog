# Sqlog

Ingest Nginx logs into a SQLite database for easy querying.

    $ ./sqlog.py log.sqlite < access.log

    $ sqlite3 log.sqlite
    > select url, count(*) as n
    > from logs
    > group by url
    > order by n desc
    > limit 100

The `queries` directory contains a few interesting queries to run.
