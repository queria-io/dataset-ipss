{# 日本の地域別将来推計人口（令和5年推計）の男女・5歳階級別人口。1行が1地域の1年の男女1区分の1階級。
   pipelines/regional_projection.py が suikei_kekka.xlsx から data/ipss/population.csv に書き出す。 #}

with source as (
    select *
    from read_csv('data/ipss/population.csv', header = true, all_varchar = true)
),

typed as (
    select
        code as city_code,
        case area_kind
            when 'a' then 'prefecture'
            when '0' then 'ward'
            when '1' then 'designated_city'
            when '2' then 'city'
            when '3' then 'town_village'
            when '9' then 'region'
        end as area_level,
        prefecture,
        nullif(city, '') as city_and_county,
        cast(year as integer) as year,
        case sex when 'male' then '1' when 'female' then '2' end as sex_code,
        case sex when 'male' then '男' when 'female' then '女' end as sex,
        age_class,
        cast(regexp_extract(age_class, '^([0-9]+)', 1) as integer) as age_from,
        cast(nullif(regexp_extract(age_class, '~([0-9]+)歳$', 1), '') as integer) as age_to,
        cast(population as integer) as population
    from source
),

designated_cities as (
    select distinct city_code
    from typed
    where area_level = 'designated_city'
),

-- 政令指定都市の区の親。区のコードは親の市のコードより大きく、同じ都道府県の次の政令指定都市より小さい
-- （横浜市 14100 の区は 14101〜14118、川崎市 14130 の区は 14131〜14137）
ward_parents as (
    select w.city_code, max(d.city_code) as designated_city_code
    from (select distinct city_code from typed where area_level = 'ward') as w
    join designated_cities as d
        on left(d.city_code, 2) = left(w.city_code, 2) and d.city_code < w.city_code
    group by w.city_code
)

select
    typed.city_code,
    -- 浜通り地域（07999）は団体コードではないので、検査数字を付けない
    case when area_level <> 'region' then {{ local_government_code('typed.city_code') }} end as local_government_code,
    area_level,
    ward_parents.designated_city_code,
    prefecture,
    city_and_county,
    year,
    sex_code,
    sex,
    age_class,
    age_from,
    age_to,
    population,
    -- 2020年は国勢調査の実績値、2025年以降が推計値
    case when year = 2020 then 'A' else 'E' end as population_flag
from typed
left join ward_parents using (city_code)
