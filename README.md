# jan-web

雀魂の牌譜(JSON/TXT)をアップロードして、精算結果をWeb表示するアプリです。

## ローカル実行

```bash
uv venv
uv sync --group dev
uv run uvicorn web.app:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開いてください。

## Cloud Run デプロイ（推奨）

### 1. 前提

- Google Cloud プロジェクト作成済み
- `gcloud` CLI インストール済み
- 課金有効化済み

### 2. 初期セットアップ

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 3. デプロイ

```bash
cd /Users/twemu/Program/jan-web
gcloud run deploy jan-web \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

完了後に表示される URL が公開エンドポイントです。

### 4. 再デプロイ

```bash
gcloud run deploy jan-web \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## 補足: Cloudflare Workers

Workers 用の設定ファイル (`wrangler.toml` など) は残していますが、  
FastAPI 構成では無料枠のサイズ制限に引っかかりやすいため、運用は Cloud Run を推奨します。

## ディレクトリ構成

- `web/`: FastAPI, テンプレート, CSS
- `module/`: 精算ロジック
- `Dockerfile`: Cloud Run 実行イメージ定義
