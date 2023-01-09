# Sqlog

Ingest Nginx logs into a SQLite database for easy querying.

    $ ./sqlog.py --format COMBINED log.sqlite < access.log

    $ sqlite3 log.sqlite
    > select url, count(*) as n
    > from logs
    > group by url
    > order by n desc
    > limit 100

The `queries` directory contains a few interesting queries to run. Use for
example like so:

    $ sqlite3 -header log.sqlite < queries/urls_30d.sql \
      | column --table --separator '|' \
      | less --chop-long-lines

(Sqlite also has `-column`, but it truncates values in combination with
`-header`.)
