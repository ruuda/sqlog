select
  count(*) as n,
  vhost,
  url
from
  logs
where
  method = 'GET'
  and status = 200
  and url not like '%.woff'
  and url not like '%.woff2'
  and time_local > datetime('now', '-30 days')
group by
  vhost, url
order by
  n desc
limit
  100;
