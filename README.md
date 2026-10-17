# jan-web

雀魂・一番街の牌譜（JSON/TXT）をアップロードして、ご祝儀を含む精算結果を表示する Web ツールです。

## 対応する牌譜

- 本番の JavaScript Workers 版は、雀魂と一番街の四人打ち牌譜を自動判定します。複数ファイルで両形式を混在できます。
- 一番街は `handRecord` と対局終了イベント（`eventType: 6`）を含むJSONに対応します。イベントの `data` はオブジェクト・JSON文字列のどちらでも読み込めます。
- 一番街のプレイヤーIDを席番号に対応づけ、最終持ち点・和了・役情報を既存の雀魂用入力形式に変換します。祝儀、ウマ、オカ、金額の計算は既存処理を共用します。
- 一発・赤ドラ・裏ドラ・役満を祝儀の対象にします。複合役満、オールスター、トビの扱いも既存の雀魂用処理に従います。
- 一番街の役IDは [RiichiCity-to-Tenhou-Log-Parser の対応表](https://github.com/cht33/RiichiCity-to-Tenhou-Log-Parser/blob/main/convert.py) を参照しています。
- Pythonの旧実装・補助経路は引き続き雀魂用です。

検証（Node.jsの標準テストランナー、追加依存なし）:

```bash
node --test tests/paifu.test.mjs
```

個人情報を含まない合成牌譜で、一発・役満・トビ・ダブロン・流局などのケースを検証します。雀魂の計算結果はGitのHEAD版との比較も行います。

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
