select
    ticker,
    period_start,
    period_end,
    count(*) as row_count
from {{ ref('mart_income_statement') }}
group by ticker, period_start, period_end
having count(*) > 1
