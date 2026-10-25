-- 政令指定都市を区で数えると、区・市・町村・浜通り地域の和が都道府県の値に一致する
with parts as (
    select left(city_code, 2) as prefecture_code, year, sex_code, age_class, sum(population) as population
    from {{ ref('population') }}
    where area_level in ('ward', 'city', 'town_village', 'region')
    group by all
)

select p.city_code, p.year, p.sex_code, p.age_class, p.population, parts.population as sum_of_parts
from {{ ref('population') }} as p
left join parts
    on left(p.city_code, 2) = parts.prefecture_code
    and p.year = parts.year and p.sex_code = parts.sex_code and p.age_class = parts.age_class
where p.area_level = 'prefecture'
  and parts.population is distinct from p.population
