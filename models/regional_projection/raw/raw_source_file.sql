{# 取得したファイルの記録。pipelines/regional_projection.py が data/ipss/source_file.parquet に書く。 #}

select *
from read_parquet('data/ipss/source_file.parquet')
