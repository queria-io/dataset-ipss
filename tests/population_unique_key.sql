-- 1行が1地域の1年の男女1区分の1階級
select city_code, year, sex_code, age_class, count(*) as n
from {{ ref('population') }}
group by all
having count(*) > 1
