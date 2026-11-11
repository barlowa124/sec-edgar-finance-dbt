with income_fy as (
    select *
    from {{ ref('mart_income_statement') }}
    where period_type = 'FY'
),

ranked_income as (
    select
        *,
        row_number() over (partition by ticker order by period_end desc) as rn,
        lag(revenue_effective) over (partition by ticker order by period_end) as prior_revenue
    from income_fy
),

latest_income as (
    select *
    from ranked_income
    where rn = 1
),

balance_asof as (
    select
        b.*,
        i.period_end as income_period_end,
        row_number() over (
            partition by b.ticker
            order by b.period_end desc
        ) as rn
    from {{ ref('mart_balance_sheet') }} b
    join latest_income i
        on b.ticker = i.ticker
       and b.period_end <= i.period_end
),

latest_balance as (
    select *
    from balance_asof
    where rn = 1
),

cash_flow_asof as (
    select
        cf.*,
        i.period_end as income_period_end,
        row_number() over (
            partition by cf.ticker
            order by cf.period_end desc, cf.period_start desc
        ) as rn
    from {{ ref('mart_cash_flow') }} cf
    join latest_income i
        on cf.ticker = i.ticker
       and cf.period_type = 'FY'
       and cf.period_end <= i.period_end
),

latest_cash_flow as (
    select *
    from cash_flow_asof
    where rn = 1
),

joined as (
    select
        i.ticker,
        i.period_start,
        i.period_end,
        i.revenue_effective as revenue,
        i.revenue as revenue_reported,
        i.prior_revenue,
        i.net_income,
        i.operating_income,
        i.gross_profit,
        i.eps_basic,
        i.eps_diluted,
        i.weighted_avg_shares_diluted,
        i.interest_income,
        i.interest_expense,
        i.noninterest_income,
        i.net_interest_income,
        b.assets,
        b.liabilities,
        b.stockholders_equity,
        b.cash,
        b.accounts_receivable,
        b.inventory,
        b.ppe,
        b.goodwill,
        b.intangibles,
        b.long_term_debt,
        b.debt_current,
        b.accounts_payable,
        b.accrued_liabilities,
        b.deferred_revenue,
        b.shares_outstanding,
        cf.operating_cash_flow,
        cf.investing_cash_flow,
        cf.financing_cash_flow,
        cf.capex,
        cf.dividends_paid,
        cf.share_repurchases,
        cf.debt_issuance,
        cf.debt_repayment
    from latest_income i
    left join latest_balance b
        on i.ticker = b.ticker
    left join latest_cash_flow cf
        on i.ticker = cf.ticker
)

select
    ticker,
    period_start,
    period_end,
    revenue,
    revenue_reported,
    prior_revenue,
    case
        when prior_revenue is not null and prior_revenue <> 0
        then (revenue - prior_revenue) / prior_revenue
    end as revenue_growth_yoy,
    net_income,
    operating_income,
    gross_profit,
    eps_basic,
    eps_diluted,
    weighted_avg_shares_diluted,
    interest_income,
    interest_expense,
    noninterest_income,
    net_interest_income,
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
    operating_cash_flow,
    investing_cash_flow,
    financing_cash_flow,
    capex,
    dividends_paid,
    share_repurchases,
    debt_issuance,
    debt_repayment,
    operating_cash_flow - capex as fcf,
    net_income / nullif(revenue, 0) as net_margin,
    operating_income / nullif(revenue, 0) as operating_margin,
    gross_profit / nullif(revenue, 0) as gross_margin,
    case
        when stockholders_equity is not null and stockholders_equity > 0
        then net_income / stockholders_equity
    end as roe,
    case
        when stockholders_equity is not null and stockholders_equity > 0
        then (coalesce(long_term_debt, 0) + coalesce(debt_current, 0)) / stockholders_equity
    end as debt_to_equity,
    cash / nullif(assets, 0) as cash_to_assets,
    (operating_cash_flow - capex) / nullif(revenue, 0) as fcf_margin,
    capex / nullif(operating_cash_flow, 0) as capex_to_ocf,
    (case when revenue is null then 1 else 0 end)
        + (case when net_income is null then 1 else 0 end)
        + (case when assets is null then 1 else 0 end)
        + (case when stockholders_equity is null then 1 else 0 end)
        + (case when operating_cash_flow is null then 1 else 0 end) as missing_core_metrics
from joined
order by ticker
