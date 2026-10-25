-- 政令指定都市の値は、その区の和に一致する
with wards as (
    select designated_city_code, year, sex_code, age_class, sum(population) as population
    from {{ ref('population') }}
    where area_level = 'ward'
    group by all
)

select c.city_code, c.year, c.sex_code, c.age_class, c.population, wards.population as sum_of_wards
from {{ ref('population') }} as c
left join wards
    on c.city_code = wards.designated_city_code
    and c.year = wards.year and c.sex_code = wards.sex_code and c.age_class = wards.age_class
where c.area_level = 'designated_city'
  and wards.population is distinct from c.population
