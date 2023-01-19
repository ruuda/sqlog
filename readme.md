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

-----------

The `data_dir` directory can be used to store multiple *.log* files. 

    $ cp /var/log/nginx/access* ./data_dir    # Copy all access* files from default dir 
    
The `data_dir/log_unzipper.sh` can be used if you have gzipped logs;
use the `--archive-zips` flag to delete the .gz files:

    $ cd data_dir                        # go into data_dir directory
    $ ./log_unzipper.sh                  # unzip all files
    $ ./log_unzipper.sh --archive-zips   # unzip + delete zips afterwards
 
The `ingest_access_logs.sh` bash script will loop through all `*.log*`
files in the data_dir folder and ingest them into the log.sqlite db:

    $ ./ingest_access_logs.sh
