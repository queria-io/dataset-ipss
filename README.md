# dataset-ipss

国立社会保障・人口問題研究所（社人研）の将来推計人口を Queria のカタログ（[data.queria.io](https://data.queria.io/)）へ取り込むデータセットです。

## データ出典

[日本の地域別将来推計人口（令和5(2023)年推計）](https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/t-page.asp)の結果表のうち、
男女・年齢（5歳）階級別の推計結果（`3kekka/suikei_kekka.xlsx`、全都道府県・市区町村の1シート）を表にします。

| 原典 | テーブル |
| --- | --- |
| `3kekka/suikei_kekka.xlsx` | `regional_projection.population` |

社人研のコンテンツは[公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)に準拠した利用条件で提供されています（[サイトご利用にあたって](https://www.ipss.go.jp/site-ad/link/anlink.html)）。
使うときは出典として社人研の推計名を書き、Queria が加工したことを書いてください。

## 収録テーブル

| テーブル | 内容 | 行数 |
| --- | --- | ---: |
| `regional_projection.population` | 1行が1地域の1年の男女1区分の5歳階級1つ。2020〜2050年の5年ごと | 546,280 |

- 地域は都道府県・政令指定都市・政令指定都市の区と東京23区・市・町村の1,951。`area_level` で分かれる
- 福島県の浜通り13市町村は個別の推計が無く、「浜通り地域」（`city_code = 07999`）1行にまとまっている
- 2020年は国勢調査の実績値、2025年以降が推計値（`population_flag` が `A` と `E`）
- 男女計の行は無い。総人口指数や年齢3区分の割合などの再掲の列は取り込まない

```sql
-- 日野市の 65 歳以上人口の推移
SELECT year, sum(population) AS population_65_plus
FROM ipss.regional_projection.population
WHERE city_code = '13212' AND age_from >= 65
GROUP BY year
ORDER BY year;
```

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # queria sync -- python main.py
```

推計は5年ごとに出るので定期実行はしません。main への push と手動の実行（workflow_dispatch）で Sync が回ります。
