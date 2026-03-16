# jan-web

雀魂の牌譜(JSON/TXT)をアップロードして、精算結果をWeb表示するアプリです。

## ローカル実行

```bash
uv venv
uv sync --group dev
uv run uvicorn web.app:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開いてください。

## Cloudflare Workers デプロイ

### 1. ログイン

```bash
npx wrangler login
```

### 2. 依存インストール（Workers 用）

```bash
uv sync --group dev
```

### 3. ローカル検証

```bash
uv run pywrangler dev
```

### 4. デプロイ

```bash
uv run pywrangler deploy
```

`wrangler.toml` の `name` を変更すると、Workers 側のサービス名を変えられます。

## ディレクトリ構成

- `web/`: FastAPI, テンプレート, CSS, Workersエントリーポイント
- `module/`: 既存の精算ロジック
- `wrangler.toml`: Cloudflare Workers 設定
