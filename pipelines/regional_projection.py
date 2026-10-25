"""国立社会保障・人口問題研究所「日本の地域別将来推計人口（令和5年推計）」を取り出す。

結果表 suikei_kekka.xlsx（全国の都道府県・市区町村をまとめた 1 シート）を、
1 行 = 1 地域 × 1 年 × 男女 × 5 歳階級の CSV にする。

原典の行は 1 地域 × 1 年で、列に 総数・男・女 のそれぞれ 計 と 5 歳階級 20 区分が並ぶ。
総数は男と女の和なので男と女だけを残し、取り出すときに 男 + 女 = 総数、
5 歳階級の和 = 計 になっていることを確かめる。

出力: data/ipss/population.csv

データソース: 国立社会保障・人口問題研究所
https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/t-page.asp
"""

import csv
import io
import logging
import re
import unicodedata
from pathlib import Path

import openpyxl

from shared.fetch import fetch, replacing

logger = logging.getLogger("pipelines")

URL = "https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/3kekka/suikei_kekka.xlsx"
USER_AGENT = "dataset-ipss (+https://github.com/queria-io/dataset-ipss)"
OUTPUT_DIR = Path("data/ipss")

# 見出しの 1 行目に 総数・男・女 が、2 行目に 計 と 5 歳階級が並ぶ
SEXES = {"男": "male", "女": "female"}
FIELDS = ["code", "area_kind", "prefecture", "city", "year", "sex", "age_class", "population"]


def normalize(value) -> str:
    return unicodedata.normalize("NFKC", "" if value is None else str(value)).strip()


def header_columns(top: tuple, sub: tuple) -> dict[str, dict[str, int]]:
    """{'総数' | '男' | '女': {'計' | '0~4歳' | ...: 列番号}}。"""
    starts = [(i, normalize(c)) for i, c in enumerate(top) if normalize(c) in ("総数", *SEXES)]

    def block(i: int) -> dict[str, int]:
        labels = []
        for j in range(i, len(sub)):
            label = normalize(sub[j])
            if not label or (labels and label == "計"):
                break
            labels.append((label, j))
        return dict(labels)

    return {name: block(i) for i, name in starts}


def extract(sheet) -> list[dict]:
    rows = [tuple(r) for r in sheet.iter_rows(values_only=True)]
    head = next((i for i, r in enumerate(rows) if r and normalize(r[0]) == "コード"), None)
    if head is None:
        raise SystemExit("見出しの行（コード）が見つからない")
    columns = header_columns(rows[head], rows[head + 1])
    ages = [a for a in columns["総数"] if a != "計"]
    if len(ages) != 20 or any(columns[s].keys() != columns["総数"].keys() for s in SEXES):
        raise SystemExit(f"見出しの形が想定と違う: {columns}")

    def one(row) -> list[dict]:
        value = {s: {a: row[j] for a, j in columns[s].items()} for s in ("総数", *SEXES)}
        for a in columns["総数"]:
            if value["総数"][a] != sum(value[s][a] for s in SEXES):
                raise SystemExit(f"{row[:5]} {a}: 男 + 女 が総数に合わない")
        for s in value:
            if value[s]["計"] != sum(value[s][a] for a in ages):
                raise SystemExit(f"{row[:5]} {s}: 5 歳階級の和が計に合わない")
        year = re.fullmatch(r"(\d{4})年", normalize(row[4]))
        if year is None:
            raise SystemExit(f"{row[:5]}: 年の形が想定と違う")
        base = {
            "code": f"{int(row[0]):05d}",
            "area_kind": normalize(row[1]),
            "prefecture": normalize(row[2]),
            "city": normalize(row[3]),
            "year": year.group(1),
        }
        return [
            {**base, "sex": SEXES[s], "age_class": a, "population": value[s][a]}
            for s in SEXES
            for a in ages
        ]

    return [r for row in rows[head + 2:] if row[0] is not None for r in one(row)]


def write_csv(path: Path, rows: list[dict]) -> None:
    with replacing(path) as partial, partial.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def download_regional_projection(output_dir: Path = OUTPUT_DIR) -> int:
    logger.info("%s", URL)
    content = fetch(URL, user_agent=USER_AGENT, timeout=120)
    book = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    try:
        rows = extract(book.worksheets[0])
    finally:
        book.close()
    if not rows:
        raise SystemExit(f"{URL}: 1 行も取れなかった（Excel の形が変わった？）")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "population.csv", rows)
    logger.info("  population: %d 行", len(rows))
    return len(rows)
