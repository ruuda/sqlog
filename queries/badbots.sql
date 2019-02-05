select
  count(*) as n,
  remote_addr,
  sum(body_bytes_sent) as body_bytes_wasted
from
  logs
where
  -- My site is a static site, there is no PHP anywhere.
  -- Any requests for urls containing "PHP" are malware.
  url like '%php%'
  and status <> 200
group by
  remote_addr
order by
  n desc
limit
  100;
