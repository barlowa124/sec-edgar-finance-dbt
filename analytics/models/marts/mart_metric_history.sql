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
from {{ ref('int_metric_facts') }}
order by ticker, metric, period_end desc
