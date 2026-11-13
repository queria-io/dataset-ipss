# 社人研 将来推計人口

国立社会保障・人口問題研究所（社人研）の「日本の地域別将来推計人口（令和5年推計）」を、SQL で集計できるテーブルにしたデータセットです。都道府県・市区町村（政令指定都市は区も）ごとの男女・5 歳階級別人口を、2020 年から 2050 年まで 5 年ごとに収録しています。

## 出典と利用条件

[日本の地域別将来推計人口（令和5(2023)年推計）](https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/t-page.asp)の結果表のうち、男女・年齢（5 歳）階級別の推計結果（`3kekka/suikei_kekka.xlsx`）を、1 行が 1 地域の 1 年の男女 1 区分の 5 歳階級 1 つの縦持ちに変換しています。

- 社人研のコンテンツは[公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)に準拠した利用条件で提供されています（[サイトご利用にあたって](https://www.ipss.go.jp/site-ad/link/anlink.html)）
- 使うときは出典として社人研の推計名を書き、Queria が加工したものであることを明記してください

## テーブル

| テーブル | 内容 |
| --- | --- |
| `regional_projection.population` | 1 行が 1 地域の 1 年の男女 1 区分の 5 歳階級 1 つ。2020〜2050 年の 5 年ごと |

## 使い方

日野市の 65 歳以上人口の推移:

```sql
SELECT year, sum(population) AS population_65_plus
FROM ipss.regional_projection.population
WHERE city_code = '13212' AND age_from >= 65
GROUP BY year
ORDER BY year;
```

男女計の行はありません。男女計は `sex` を問わず合計してください。

## 地域の区分

地域は 1,951 で、都道府県（47）・政令指定都市（20）・政令指定都市の区と東京 23 区（198）・それ以外の市（769）・町村（916）・浜通り地域（1）が `area_level` で分かれて同じ列に並びます。

- 日本全域をちょうど 1 回覆うのは、`area_level = 'prefecture'` だけ、または `area_level IN ('ward', 'city', 'town_village', 'region')` です。絞らずに合計すると重複して数えます
- 政令指定都市を市の単位で数えるときは、`'ward'` の代わりに `'designated_city'` と東京 23 区（`city_code` が 131 で始まる区）を使ってください
- 政令指定都市の区の行には、親の市のコードが `designated_city_code` に入ります。市の値は区の和に一致します

## 収録範囲の注意

- 2020 年は国勢調査の実績値、2025 年以降が推計値です（`population_flag` が `A` と `E`）。2020 年の年齢不詳は社人研が各階級に按分していて、階級の和は国勢調査の総人口に一致します
- 5 歳階級は 0~4歳 から 90~94歳 までと 95歳~ の 20 区分です。95歳~ は `age_to` が NULL です
- 福島県の浜通り 13 市町村（いわき市・相馬市・南相馬市・広野町・楢葉町・富岡町・川内村・大熊町・双葉町・浪江町・葛尾村・新地町・飯舘村）は個別の推計がなく、「浜通り地域」1 行（`city_code = '07999'`、`area_level = 'region'`）にまとまっています。07999 は社人研が付けたコードで団体コードではないため、`local_government_code` は NULL です
- 浜松市は 2024 年 1 月の区の再編（7 区 → 3 区）より前の 7 区で推計されています。再編後の 3 区の参考推計（`sankou1.xlsx`）は収録していません
- 地域コードは 2020 年 10 月 1 日時点のものです。`city_code`（5 桁）は e_stat の国勢調査のテーブルの地域コードと同じ体系です
- 総人口指数や年齢 3 区分の割合などの再掲の列は収録していません

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # fdl checkout → python main.py → fdl commit
```

推計は 5 年ごとに出るため、定期実行はしません。main への push と手動の実行（workflow_dispatch）で Sync が実行されます。
