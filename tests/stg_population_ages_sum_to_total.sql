-- 5 歳階級の和が計に一致する（総数・男・女のそれぞれで）
with long as (
    unpivot (select city_code, year, columns('^(総数|男|女)/') from {{ ref('stg_population') }})
    on columns('^(総数|男|女)/')
    into name label value population
)

select city_code, year, split_part(label, '/', 1) as sex,
    sum(population) filter (where label like '%/計') as total,
    sum(population) filter (where label not like '%/計') as sum_of_ages
from long
group by all
having total is distinct from sum_of_ages
