select
  count(*) as n,
  vhost,
  url,
  referer,
  user_agent
from
  logs
where
  method = 'GET'
  and status = 200
  and url like '%.woff'
  and time_local > datetime('now', '-180 days')
group by
  vhost, url, referer, user_agent
order by
  n desc
limit
  100;
