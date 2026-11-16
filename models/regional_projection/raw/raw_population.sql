{# 日本の地域別将来推計人口（令和5年推計）の結果表を、原典の行と列のまま読む。
   pipelines/regional_projection.py が suikei_kekka.xlsx を data/ipss/population.csv にする。 #}

select *
from read_csv('data/ipss/population.csv', header = true, all_varchar = true)
