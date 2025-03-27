select
  count(*) as n,
  user_agent
from
  logs
where
  url not in ('/feed.xml', '/robots.txt')
  and status >= 200
  and status <  400
  and user_agent is not null
  and time_local > datetime('now', '-30 days')
group by
  user_agent
order by
  n desc
limit
  100;
