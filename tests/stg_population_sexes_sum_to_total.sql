-- 男 + 女 が総数に一致する（計と 5 歳階級のそれぞれで）
with long as (
    unpivot (select city_code, year, columns('^(総数|男|女)/') from {{ ref('stg_population') }})
    on columns('^(総数|男|女)/')
    into name label value population
)

select city_code, year, split_part(label, '/', 2) as age_class,
    sum(population) filter (where label like '総数/%') as total,
    sum(population) filter (where label not like '総数/%') as male_and_female
from long
group by all
having total is distinct from male_and_female
