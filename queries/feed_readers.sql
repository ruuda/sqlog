select
  count(*) / 90 as requests_per_day,
  remote_addr,
  max(user_agent)
from
  logs
where
  url = '/feed.xml'
  and status >= 200
  and status <  400
  and user_agent is not null
  and time_local > datetime('now', '-90 days')
group by
  remote_addr
order by
  requests_per_day desc
limit
  10;
