with cash_flow as (
    select *
    from {{ ref('int_metric_facts') }}
    where statement = 'cash_flow'
),

pivoted as (
    select
        ticker,
        period_start,
        period_end,
        max(case when metric = 'operating_cash_flow' then val end) as operating_cash_flow,
        max(case when metric = 'investing_cash_flow' then val end) as investing_cash_flow,
        max(case when metric = 'financing_cash_flow' then val end) as financing_cash_flow,
        max(case when metric = 'capex' then val end) as capex,
        max(case when metric = 'dividends_paid' then val end) as dividends_paid,
        max(case when metric = 'share_repurchases' then val end) as share_repurchases,
        max(case when metric = 'debt_issuance' then val end) as debt_issuance,
        max(case when metric = 'debt_repayment' then val end) as debt_repayment,
        max(filed) as filed,
        max(fy) as fy
    from cash_flow
    group by ticker, period_start, period_end
),

typed as (
    select
        *,
        date_diff('day', period_start, period_end) as period_days
    from pivoted
)

select
    *,
    case
        when period_days >= 300 then 'FY'
        when period_days between 60 and 120 then 'Q'
        else 'other'
    end as period_type
from typed
