-- 地域・年・男女ごとに 5 歳階級が 20 区分そろい、年と地域の区分が読めている
select city_code, year, sex_code, count(*) as n
from {{ ref('population') }}
group by all
having count(*) <> 20 or year is null or any_value(area_level) is null
