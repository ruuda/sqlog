select
  count(*) as n,
  referer
from
  logs
where
  method = 'GET'
  and status = 200
  and url not like '%.woff'
  and url not like '%.woff2'
  and referer is not null
group by
  referer
order by
  n desc
limit
  100;
