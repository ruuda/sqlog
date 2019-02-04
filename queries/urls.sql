select
  count(*) as n,
  url
from
  logs
where
  method = 'GET'
  and status = 200
  and url not like '%.woff'
  and url not like '%.woff2'
group by
  url
order by
  n desc
limit
  100;
