-- This query ultimately selects pairs of urls, where a visitor first visited
-- the first url, and then later, after a few seconds, visited the second url.
-- It makes some attempts at excluding bots.

create temporary table
  visits
as
select
  *
from
  logs
where
  method = 'GET'
  and status = 200
  and url not like '%.woff'
  and url not like '%.woff2'
  and url not like '%.png'
  and url not like '%.jpg'
  and url not like '%.svg'
  and url not in ('/feed.xml', '/robots.txt', '/favicon.png')
  and user_agent not like '%bot%'
;

create index ix_addr_time on visits (remote_addr, datetime(time_local));
analyze visits;

select
  count(*) as n,
  v0.url as from_url,
  v1.url as to_url
from
  visits as v0,
  visits as v1
where
  v0.remote_addr = v1.remote_addr
  and v0.url <> v1.url
  -- Count the second hit only if it was at least 15 seconds after the first
  -- one. If they are too close, they might be part of the same page load. But
  -- on a slow connection, things could take time. 15 seconds feel like a good
  -- middle ground, my site *should* load in less than a few seconds even on a
  -- slow connection. Also, capture only the same "session", which I define as
  -- two hours.
  and datetime(v0.time_local, '+15 seconds') < datetime(v1.time_local)
  and datetime(v0.time_local, '+2 hours') > datetime(v1.time_local)
  -- Select only two consecutive visits, do not allow intermediate visits vm
  -- between v0 and v1.
  and not exists
  (
    select
      *
    from
      visits as vm
    where
      vm.remote_addr = v0.remote_addr
      and datetime(v0.time_local) < datetime(vm.time_local)
      and datetime(vm.time_local) < datetime(v1.time_local)
  )
group by
  from_url, to_url
order by
  n desc
limit
  100;

drop table visits;
