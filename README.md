# jan-web

雀魂の牌譜(JSON/TXT)をアップロードして、精算結果をWeb表示するアプリです。

## Cloudflare Workers（無料枠）で実行

```bash
uv venv
uv sync --group dev
uv run pywrangler dev
```

## Cloudflare Workers（無料枠）へデプロイ

```bash
npx wrangler login
rm -rf .venv-workers python_modules .wrangler
uv sync --group dev
uv run pywrangler deploy
```

無料枠サイズを意識して、Workers実行は `worker.py` の軽量ルートで動作します。

## ディレクトリ構成

- `worker.py`: Workers無料枠向け軽量エントリーポイント
- `worker_core/`: Workers向け軽量ロジック
- `web/`: FastAPI版コード（Workersデプロイ対象外）
- `module/`: 精算ロジック
