{# 結果表の行に型を付け、地域の列を改名する。人口の列は「総数/計」「男/0～4歳」の名前のまま整数にする。
   2020年は国勢調査の実績値、2025年以降が推計値。 #}

select
    lpad(trim("コード"), 5, '0') as city_code,
    case trim("市などの別")
        when 'a' then 'prefecture'
        when '0' then 'ward'
        when '1' then 'designated_city'
        when '2' then 'city'
        when '3' then 'town_village'
        when '9' then 'region'
    end as area_level,
    trim("都道府県") as prefecture,
    nullif(trim("市区町村"), '') as city_and_county,
    cast(regexp_extract(trim("年"), '^([0-9]{4})年$', 1) as integer) as year,
    cast(columns('^(総数|男|女)/') as integer)
from {{ ref('raw_population') }}
