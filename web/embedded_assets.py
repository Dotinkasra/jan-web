INDEX_TEMPLATE = """<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>雀魂 牌譜リザルト</title>
    <link rel="stylesheet" href="/static/style.css" />
    <link rel="icon" href="/favicon.ico" />
  </head>
  <body>
    <main class="container">
      <h1>雀魂 牌譜リザルト</h1>
      <p class="lead">牌譜JSONをアップロードして精算結果を表示します。</p>

      {% if error %}
      <div class="error">{{ error }}</div>
      {% endif %}

      <form action="/analyze" method="post" enctype="multipart/form-data" class="form-area" id="analyze-form">
        <div class="form-grid">
          <div class="form-row cols-3">
            <label>牌譜ファイル
              <input type="file" name="paifu_file" accept=".json,.txt" required />
            </label>

            <label>レート
              <input type="number" name="rate" value="50" required />
            </label>

            <label>チップ金額
              <input type="number" name="chip" value="500" required />
            </label>
          </div>

          <div class="form-row cols-2">
            <label>ウマ1
              <input type="number" name="uma_1" value="10" required />
            </label>

            <label>ウマ2
              <input type="number" name="uma_2" value="20" required />
            </label>
          </div>

          <div class="form-row cols-2">
            <label>初期点
              <input type="number" name="oka_1" value="25000" required />
            </label>

            <label>オカ
              <input type="number" name="oka_2" value="30000" required />
            </label>
          </div>

          <div class="form-row cols-3">
            <label>オールスターチップ倍率
              <input type="number" name="all_star_chip" value="5" required />
            </label>

            <label>役満ツモチップ倍率
              <input type="number" name="yiman_tumo_chip" value="5" required />
            </label>

            <label>役満ロンチップ倍率
              <input type="number" name="yiman_chip" value="10" required />
            </label>
          </div>
        </div>
        <button type="submit" class="submit-wide">結果を表示</button>
      </form>
    </main>
    <script>
      const form = document.getElementById("analyze-form");
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const fileInput = form.querySelector('input[name="paifu_file"]');
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
          alert("牌譜ファイルを選択してください。");
          return;
        }

        try {
          const text = await file.text();
          const paifuJson = JSON.parse(text);
          const payload = {
            paifu_json: paifuJson,
            rate: form.rate.value,
            chip: form.chip.value,
            uma_1: form.uma_1.value,
            uma_2: form.uma_2.value,
            oka_1: form.oka_1.value,
            oka_2: form.oka_2.value,
            all_star_chip: form.all_star_chip.value,
            yiman_tumo_chip: form.yiman_tumo_chip.value,
            yiman_chip: form.yiman_chip.value,
          };

          const response = await fetch("/analyze-json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const html = await response.text();
          document.open();
          document.write(html);
          document.close();
        } catch (error) {
          alert(`牌譜の送信に失敗しました: ${error}`);
        }
      });
    </script>
  </body>
</html>
"""


RESULT_TEMPLATE = """<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>精算結果</title>
    <link rel="stylesheet" href="/static/style.css" />
    <link rel="icon" href="/favicon.ico" />
  </head>
  <body>
    <main class="container">
      <header class="header-row">
        <h1>精算結果</h1>
        <a href="/" class="button-link">別の牌譜を読み込む</a>
      </header>

      <details class="settings-card settings-toggle" open>
        <summary class="settings-summary">
          <h2>現在の設定</h2>
          <span class="summary-hint" aria-hidden="true"></span>
        </summary>
        <div class="settings-grid">
          <div class="settings-row cols-3">
            <div><span>レート</span><strong>{{ settings.rate }}</strong></div>
            <div><span>チップ金額</span><strong>{{ settings.chip }}</strong></div>
            <div><span>ウマ</span><strong>{{ settings.uma_1 }}-{{ settings.uma_2 }}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>初期点</span><strong>{{ settings.oka_1 }}</strong></div>
            <div><span>オカ</span><strong>{{ settings.oka_2 }}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>オールスターチップ倍率</span><strong>{{ settings.all_star_chip }}</strong></div>
            <div><span>役満ツモチップ倍率</span><strong>{{ settings.yiman_tumo_chip }}</strong></div>
            <div><span>役満ロンチップ倍率</span><strong>{{ settings.yiman_chip }}</strong></div>
          </div>
        </div>
      </details>

      <div class="toggle-toolbar">
        <button type="button" id="expand-all">全部開く</button>
        <button type="button" id="collapse-all">全部閉じる</button>
      </div>

      {% for user in users %}
      <details class="card user-card" data-user-card>
        <summary class="user-summary">
          <div>
            <h2>{{ user.nickname }}</h2>
            <p class="summary-line">
              最終得点: {{ user.point }} ( <span class="{{ 'negative' if user.score_negative else 'positive' }}">{{ user.score }}</span> )
            </p>
          </div>
          <span class="summary-hint" aria-hidden="true"></span>
        </summary>

        <div class="card-content">
          <h3>総合得点</h3>
          <table>
            <thead>
              <tr>
                <th>得点</th>
                <th>祝儀収益</th>
                <th>祝儀支払</th>
                <th>結果</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{{ user.score_yen }}</td>
                <td>{{ user.bonus_yen }}</td>
                <td class="negative">-{{ user.payment_yen }}</td>
                <td class="{{ 'negative' if user.result_negative else 'positive' }}">{{ user.result_yen }}</td>
              </tr>
            </tbody>
          </table>

          <h3>祝儀明細</h3>
          <table>
            <thead>
              <tr>
                <th>種類</th>
                <th>ロン</th>
                <th>ツモ</th>
                <th>チップ枚数</th>
              </tr>
            </thead>
            <tbody>
              {% for row in user.bonus_rows %}
              <tr>
                <td>{{ row.name }}</td>
                <td>{{ row.ron }}</td>
                <td>{{ row.tsumo }}</td>
                <td>{{ row.chip }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>

          <h3>支払い明細</h3>
          <table>
            <thead>
              <tr>
                <th>振込先</th>
                <th>内容</th>
                <th>チップ枚数</th>
                <th>金額</th>
              </tr>
            </thead>
            <tbody>
              {% for row in user.payment_rows %}
              <tr>
                <td>{{ row.to }}</td>
                <td>{{ row.type }}</td>
                <td>{{ row.chip }}</td>
                <td>{{ row.yen }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>

          <h3>支払い集計（相手別）</h3>
          <table>
            <thead>
              <tr>
                <th>相手</th>
                <th>得点精算</th>
                <th>受け取りチップ</th>
                <th>支払いチップ</th>
                <th>合計金額</th>
              </tr>
            </thead>
            <tbody>
              {% for row in user.opponent_rows %}
              <tr>
                <td>{{ row.to }}</td>
                <td class="{{ 'negative' if row.score_negative else 'positive' }}">{{ row.score_yen }}</td>
                <td>{{ row.receive_chip }}</td>
                <td>{{ row.pay_chip }}</td>
                <td class="{{ 'negative' if row.total_negative else 'positive' }}">{{ row.total_yen }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </details>
      {% endfor %}
    </main>
    <script>
      const cards = document.querySelectorAll("[data-user-card]");
      document.getElementById("expand-all").addEventListener("click", () => {
        cards.forEach((card) => {
          card.open = true;
        });
      });
      document.getElementById("collapse-all").addEventListener("click", () => {
        cards.forEach((card) => {
          card.open = false;
        });
      });
    </script>
  </body>
</html>
"""


STYLE_CSS = """:root {
  --bg: #f6f8fb;
  --card: #ffffff;
  --line: #d5dce8;
  --text: #243247;
  --subtext: #5a6a82;
  --positive: #1f7a45;
  --negative: #b83232;
  --accent: #2f6feb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: linear-gradient(140deg, #eef4ff, #f7fbff 55%, #f0f4ff);
  color: var(--text);
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 16px 32px;
}

h1, h2, h3 {
  margin: 0 0 12px;
}

.lead {
  margin-top: 8px;
  color: var(--subtext);
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.button-link,
button {
  border: none;
  background: var(--accent);
  color: #fff;
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.toggle-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  gap: 14px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px;
}

.form-row {
  display: grid;
  gap: 12px;
}

.form-row.cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-row.cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.form-grid label {
  display: grid;
  gap: 6px;
  color: var(--subtext);
}

.form-grid input[type="number"],
.form-grid input[type="file"] {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--line);
  font-size: 14px;
}

.form-area {
  display: grid;
  gap: 18px;
}

.submit-wide {
  display: block;
  justify-self: stretch;
  width: 100%;
  min-height: 44px;
}

@media (max-width: 760px) {
  .form-row.cols-2,
  .form-row.cols-3 {
    grid-template-columns: 1fr;
  }
}

.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.user-summary {
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.user-summary::-webkit-details-marker {
  display: none;
}

.summary-hint::before {
  content: "開く";
  color: var(--subtext);
  font-size: 13px;
}

.user-card[open] .summary-hint::before {
  content: "閉じる";
}

.card-content {
  padding-top: 8px;
}

.summary-line {
  color: var(--subtext);
  margin-top: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
  background: #fff;
}

th, td {
  border: 1px solid var(--line);
  padding: 8px;
  text-align: left;
  font-size: 14px;
}

th {
  background: #edf3ff;
}

.positive {
  color: var(--positive);
}

.negative {
  color: var(--negative);
}

.error {
  color: #fff;
  background: #cc3b3b;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
}

.settings-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.settings-summary {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.settings-summary::-webkit-details-marker {
  display: none;
}

.settings-grid {
  display: grid;
  gap: 10px;
  margin-top: 8px;
}

.settings-row {
  display: grid;
  gap: 10px 14px;
}

.settings-row.cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.settings-row.cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.settings-grid .settings-row > div {
  display: grid;
  gap: 4px;
}

.settings-grid span {
  color: var(--subtext);
  font-size: 12px;
}

.settings-grid strong {
  font-size: 15px;
}

@media (max-width: 760px) {
  .settings-row.cols-2,
  .settings-row.cols-3 {
    grid-template-columns: 1fr;
  }
}
"""
