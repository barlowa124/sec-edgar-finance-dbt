with mapped as (
    select
        f.cik,
        f.ticker,
        f.entity_name,
        f.taxonomy,
        f.concept,
        f.concept_label,
        f.unit,
        f.period_start,
        f.period_end,
        f.val,
        f.accn,
        f.fy,
        f.fp,
        f.form,
        f.filed,
        f.frame,
        f.retrieved_at,
        m.metric,
        m.statement,
        m.unit_kind,
        m.priority as concept_priority
    from {{ ref('stg_sec_facts') }} f
    inner join {{ ref('concept_map') }} m
        on f.concept = m.concept
    where
        (
            (m.unit_kind = 'usd' and f.unit = 'USD')
            or (m.unit_kind = 'usd_per_share' and f.unit ilike '%/shares')
            or (m.unit_kind = 'shares' and f.unit ilike '%shares')
        )
        and (m.statement = 'balance' or f.period_start is not null)
),

ranked as (
    select
        *,
        row_number() over (
            partition by ticker, metric, period_start, period_end
            order by
                concept_priority asc,
                coalesce(filed, date '1900-01-01') desc,
                case
                    when form in ('10-K', '20-F', '40-F') then 1
                    when form = '10-Q' then 2
                    when form = '8-K' then 3
                    else 4
                end asc,
                coalesce(accn, '') desc
        ) as rn
    from mapped
)

select
    ticker,
    metric,
    statement,
    unit_kind,
    period_start,
    period_end,
    val,
    form,
    filed,
    accn,
    concept,
    concept_label,
    concept_priority,
    fy,
    fp,
    frame,
    retrieved_at
from ranked
where rn = 1
