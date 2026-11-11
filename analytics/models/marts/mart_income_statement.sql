with income as (
    select *
    from {{ ref('int_metric_facts') }}
    where statement = 'income'
),

pivoted as (
    select
        ticker,
        period_start,
        period_end,
        max(case when metric = 'revenue' then val end) as revenue,
        max(case when metric = 'interest_income' then val end) as interest_income,
        max(case when metric = 'interest_expense' then val end) as interest_expense,
        max(case when metric = 'noninterest_income' then val end) as noninterest_income,
        max(case when metric = 'net_interest_income' then val end) as net_interest_income,
        max(case when metric = 'cost_of_revenue' then val end) as cost_of_revenue,
        max(case when metric = 'gross_profit' then val end) as gross_profit,
        max(case when metric = 'operating_expenses' then val end) as operating_expenses,
        max(case when metric = 'research_and_development' then val end) as research_and_development,
        max(case when metric = 'selling_general_and_administrative' then val end) as selling_general_and_administrative,
        max(case when metric = 'operating_income' then val end) as operating_income,
        max(case when metric = 'income_before_tax' then val end) as income_before_tax,
        max(case when metric = 'income_tax_expense' then val end) as income_tax_expense,
        max(case when metric = 'net_income' then val end) as net_income,
        max(case when metric = 'eps_basic' then val end) as eps_basic,
        max(case when metric = 'eps_diluted' then val end) as eps_diluted,
        max(case when metric = 'weighted_avg_shares_diluted' then val end) as weighted_avg_shares_diluted,
        max(filed) as filed,
        max(fy) as fy
    from income
    group by ticker, period_start, period_end
),

typed as (
    select
        *,
        date_diff('day', period_start, period_end) as period_days,
        coalesce(revenue, noninterest_income + net_interest_income) as revenue_effective
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
