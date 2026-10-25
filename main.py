"""社人研（国立社会保障・人口問題研究所）データパイプライン。

1. regional_projection: 日本の地域別将来推計人口（令和5年推計）の結果表を CSV にする
2. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.regional_projection import download_regional_projection

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/2: regional_projection (日本の地域別将来推計人口)")
    download_regional_projection()

    logger.info("2/2: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
