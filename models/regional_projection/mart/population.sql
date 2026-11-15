{# 日本の地域別将来推計人口（令和5年推計）の男女・5歳階級別人口。1行が1地域の1年の男女1区分の1階級。
   総数は男と女の和なので、男と女の 5 歳階級の列だけを縦持ちにする。 #}

with long as (
    unpivot (
        select city_code, area_level, prefecture, city_and_county, year, source_sha256, source_sheet, source_row, columns('^(男|女)/[0-9]')
        from {{ ref('stg_population') }}
    )
    on columns('^(男|女)/[0-9]')
    into name label value population
),

typed as (
    select
        city_code,
        area_level,
        prefecture,
        city_and_county,
        year,
        case split_part(label, '/', 1) when '男' then '1' when '女' then '2' end as sex_code,
        split_part(label, '/', 1) as sex,
        replace(split_part(label, '/', 2), '～', '~') as age_class,
        population,
        source_sha256,
        source_sheet,
        source_row
    from long
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
    cast(regexp_extract(age_class, '^([0-9]+)', 1) as integer) as age_from,
    cast(nullif(regexp_extract(age_class, '~([0-9]+)歳$', 1), '') as integer) as age_to,
    population,
    -- 2020年は国勢調査の実績値、2025年以降が推計値
    case when year = 2020 then 'A' else 'E' end as population_flag,
    source_sha256,
    source_sheet,
    source_row
from typed
left join ward_parents using (city_code)
