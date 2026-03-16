# jan-web

雀魂の牌譜(JSON/TXT)をアップロードして、精算結果をWeb表示するアプリです。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動

```bash
uvicorn web.app:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開いてください。

## ディレクトリ構成

- `web/`: FastAPI, テンプレート, CSS
- `module/`: 既存の精算ロジック
