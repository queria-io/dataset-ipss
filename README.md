# dataset-ipss

Queria のデータセット `ipss`（国立社会保障・人口問題研究所 将来推計人口）のリポジトリです。データセットの説明は [docs/index.md](docs/index.md) にあります。

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # fdl checkout → python main.py → fdl commit
```

推計は 5 年ごとに出るため、定期実行はしません。main への push と手動の実行（workflow_dispatch）で Sync が実行されます。

この行は Apply の確認用です。
