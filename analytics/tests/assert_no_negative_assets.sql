select
    ticker,
    period_end,
    assets
from {{ ref('mart_balance_sheet') }}
where assets < 0
