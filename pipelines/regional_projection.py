"""国立社会保障・人口問題研究所「日本の地域別将来推計人口（令和5年推計）」を取得する。

結果表 suikei_kekka.xlsx（全国の都道府県・市区町村をまとめた 1 シート）を、
原典の行と列のまま CSV にする。見出しは 2 行（1 行目に 総数・男・女、2 行目に 計 と
5 歳階級）なので、列名を「総数/計」「男/0～4歳」のように 1 行にまとめる。
各行に元のファイルの sha256・シート名・行番号（source_sha256・source_sheet・source_row）を付ける。
値の加工（縦持ちへの変換、型付け、コードの変換）は dbt で行う。

取得したファイルの記録は source_file.parquet に書く。前回の記録と手元のファイルがあれば、
ETag・Last-Modified が変わっていないときはダウンロードをスキップする。

出力: data/ipss/{suikei_kekka.xlsx,source_file.parquet,population.csv}

データソース: 国立社会保障・人口問題研究所
https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/t-page.asp
"""

import csv
import io
import logging
from pathlib import Path

import duckdb
import openpyxl

from shared.fetch import fetch_file, replacing

logger = logging.getLogger("pipelines")

URL = "https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/3kekka/suikei_kekka.xlsx"
PAGE_URL = "https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/t-page.asp"
USER_AGENT = "dataset-ipss (+https://github.com/queria-io/dataset-ipss)"
OUTPUT_DIR = Path("data/ipss")


def label(value) -> str | None:
    return None if value is None else "".join(str(value).split())


def column_names(top: tuple, sub: tuple) -> list[str | None]:
    """2 行の見出しを 1 行の列名にする。見出しの無い列は None。"""

    def name(i: int) -> str | None:
        block = next((label(top[j]) for j in range(i, -1, -1) if top[j] is not None), None)
        if top[i] is None and sub[i] is None:
            return None
        return block if sub[i] is None else f"{block}/{label(sub[i])}"

    return [name(i) for i in range(len(top))]


def extract(sheet) -> tuple[list[str], list[tuple[int, list]]]:
    """列名と、(Excel の行番号, 値) の行を返す。"""
    rows = [tuple(r) for r in sheet.iter_rows(values_only=True)]
    head = next((i for i, r in enumerate(rows) if r and label(r[0]) == "コード"), None)
    if head is None:
        raise SystemExit("見出しの行（コード）が見つからない")
    names = column_names(rows[head], rows[head + 1])
    keep = [i for i, n in enumerate(names) if n is not None]
    body = [(n + 1, r) for n, r in enumerate(rows) if n >= head + 2 and any(c is not None for c in r)]
    return [names[i] for i in keep], [(n, [r[i] for i in keep]) for n, r in body]


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with replacing(path) as partial, partial.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def previous_source(path: Path) -> dict | None:
    """前回の source_file の行。無ければ None。"""
    if not path.exists():
        return None
    rows = duckdb.sql(f"SELECT * EXCLUDE (page_url) FROM read_parquet('{path}')").fetchall()
    columns = ["url", "sha256", "bytes", "media_type", "retrieved_at", "etag", "last_modified"]
    return dict(zip(columns, rows[0])) if rows else None


def write_source_file(path: Path, row: dict) -> None:
    columns = (
        "$url AS url, $page_url AS page_url, $sha256 AS sha256, $bytes::BIGINT AS bytes, $media_type AS media_type,"
        " $retrieved_at::TIMESTAMPTZ AS retrieved_at, $etag AS etag, $last_modified AS last_modified"
    )
    with replacing(path) as partial:
        duckdb.execute(
            f"COPY (SELECT {columns}) TO '{partial}' (FORMAT parquet)",
            {**row, "page_url": PAGE_URL, "retrieved_at": str(row["retrieved_at"])},
        )


def download_regional_projection(output_dir: Path = OUTPUT_DIR) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx, record = output_dir / "suikei_kekka.xlsx", output_dir / "source_file.parquet"
    logger.info("%s", URL)
    source = fetch_file(URL, xlsx, previous=previous_source(record), user_agent=USER_AGENT, timeout=120)
    book = openpyxl.load_workbook(io.BytesIO(xlsx.read_bytes()), read_only=True)
    try:
        sheet = book.worksheets[0]
        header, rows = extract(sheet)
        title = sheet.title
    finally:
        book.close()
    if not rows:
        raise SystemExit(f"{URL}: 1 行も取れなかった（Excel の形が変わった？）")
    write_source_file(record, source)
    write_csv(
        output_dir / "population.csv",
        [*header, "source_sha256", "source_sheet", "source_row"],
        [[*values, source["sha256"], title, n] for n, values in rows],
    )
    logger.info("  population: %d 行", len(rows))
    return len(rows)
