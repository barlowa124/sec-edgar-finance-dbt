with source as (
    select * from {{ ref('sec_facts') }}
),

cleaned as (
    select
        cik,
        upper(ticker) as ticker,
        entity_name,
        taxonomy,
        concept,
        concept_label,
        unit,
        try_cast(fact_start as date) as period_start,
        try_cast(fact_end as date) as period_end,
        try_cast(val as double) as val,
        accn,
        try_cast(fy as integer) as fy,
        fp,
        form,
        try_cast(filed as date) as filed,
        frame,
        retrieved_at
    from source
    where concept is not null
      and fact_end is not null
      and val is not null
)

select * from cleaned
