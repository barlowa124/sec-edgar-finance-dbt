select
    ticker,
    count(*) as row_count
from {{ ref('mart_financial_screen') }}
group by ticker
having count(*) > 1
