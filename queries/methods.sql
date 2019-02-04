select
  count(*) as n,
  method,
  protocol
from
  logs
group by
  method,
  protocol
order by
  n desc
limit
  100;
