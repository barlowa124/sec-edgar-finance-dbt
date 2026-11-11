with balance as (
    select *
    from {{ ref('int_metric_facts') }}
    where statement = 'balance'
),

pivoted as (
    select
        ticker,
        period_end,
        max(case when metric = 'assets' then val end) as assets,
        max(case when metric = 'liabilities' then val end) as liabilities,
        max(case when metric = 'stockholders_equity' then val end) as stockholders_equity,
        max(case when metric = 'cash' then val end) as cash,
        max(case when metric = 'accounts_receivable' then val end) as accounts_receivable,
        max(case when metric = 'inventory' then val end) as inventory,
        max(case when metric = 'ppe' then val end) as ppe,
        max(case when metric = 'goodwill' then val end) as goodwill,
        max(case when metric = 'intangibles' then val end) as intangibles,
        max(case when metric = 'long_term_debt' then val end) as long_term_debt,
        max(case when metric = 'debt_current' then val end) as debt_current,
        max(case when metric = 'accounts_payable' then val end) as accounts_payable,
        max(case when metric = 'accrued_liabilities' then val end) as accrued_liabilities,
        max(case when metric = 'deferred_revenue' then val end) as deferred_revenue,
        max(case when metric = 'shares_outstanding' then val end) as shares_outstanding,
        max(filed) as filed,
        max(fy) as fy
    from balance
    group by ticker, period_end
)

select
    ticker,
    period_end,
    'instant' as period_type,
    assets,
    liabilities,
    stockholders_equity,
    cash,
    accounts_receivable,
    inventory,
    ppe,
    goodwill,
    intangibles,
    long_term_debt,
    debt_current,
    accounts_payable,
    accrued_liabilities,
    deferred_revenue,
    shares_outstanding,
    filed,
    fy
from pivoted
