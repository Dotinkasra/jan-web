# jan-web

雀魂の牌譜（JSON/TXT）をアップロードして、ご祝儀を含む精算結果を表示する Web ツールです。

## 現在の実行方式

- 本番デプロイは **Cloudflare Workers (JavaScript)** です。
- エントリーポイントは `wrangler.toml` の `main = "worker.js"` です。
- Workers 無料枠（3MiB 制限）に収めるため、配布サイズを最小化した構成になっています。

## 必要環境

- Node.js / npm（`npx wrangler` 実行用）
- `uv`（`pywrangler` 実行用）
- Python 3.12+（ローカル補助ツール実行用）

## ローカル開発（Workers）

```bash
uv venv
uv sync --group dev
uv run pywrangler dev
```

起動後、表示されたローカル URL にアクセスします。

## デプロイ（Cloudflare Workers）

初回のみ:

```bash
npx wrangler login
```

デプロイ:

```bash
uv run pywrangler deploy
```

## 実装上の補足

- `worker.js`
  - 本番用エントリーポイント（UI/SEO/免責表示/牌譜解析/レスポンス生成を含む）
  - `/favicon.ico` は `web/static/favicon.ico` を埋め込み配信
- `worker.py` / `worker_core/`
  - Python Workers 版の軽量経路（現状 `wrangler.toml` の main では未使用）
  - ロジック比較や移行検討のために保持
- `module/`
  - 牌譜解析および精算ロジック（Python 実装）
- `web/`
  - FastAPI ベースの旧実装（Cloudflare Workers の本番経路では未使用）

## 注意点

- Workers 無料枠サイズ制限を超える要因（不要な依存・仮想環境ファイル同梱）に注意してください。
- `wrangler.toml` の `main` を変更した場合、デプロイサイズと挙動が大きく変わる可能性があります。
