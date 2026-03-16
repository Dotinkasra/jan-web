from html import escape
from workers import Response, WorkerEntrypoint

from worker_core.presenter import build_result_context
from worker_core.service import analyze_paifu


STYLE_CSS = """
body{margin:0;background:linear-gradient(140deg,#eef4ff,#f7fbff 55%,#f0f4ff);color:#243247;font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif}
*{box-sizing:border-box}.container{max-width:1000px;margin:0 auto;padding:24px 16px 32px}
h1,h2,h3{margin:0 0 12px}.lead{margin-top:8px;color:#5a6a82}
.header-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:20px}
.button-link,button{border:none;background:#2f6feb;color:#fff;text-decoration:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-size:14px}
.toggle-toolbar{display:flex;gap:10px;margin-bottom:16px}
.form-grid{display:grid;gap:14px;background:#fff;border:1px solid #d5dce8;border-radius:12px;padding:16px}
.form-row{display:grid;gap:12px}.form-row.cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.form-row.cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.form-grid label{display:grid;gap:6px;color:#5a6a82}.form-grid input{width:100%;padding:8px 10px;border-radius:8px;border:1px solid #d5dce8;font-size:14px}
.form-area{display:grid;gap:18px}.submit-wide{display:block;justify-self:stretch;width:100%;min-height:44px}
.card,.settings-card{background:#fff;border:1px solid #d5dce8;border-radius:12px;padding:16px;margin-bottom:16px}
.user-summary,.settings-summary{list-style:none;display:flex;justify-content:space-between;gap:12px;cursor:pointer}
.user-summary::-webkit-details-marker,.settings-summary::-webkit-details-marker{display:none}
.summary-hint::before{content:"開く";color:#5a6a82;font-size:13px}.user-card[open] .summary-hint::before,.settings-card[open] .summary-hint::before{content:"閉じる"}
.settings-grid{display:grid;gap:10px;margin-top:8px}.settings-row{display:grid;gap:10px 14px}.settings-row.cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.settings-row.cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.settings-grid .settings-row > div{display:grid;gap:4px}.settings-grid span{color:#5a6a82;font-size:12px}
table{width:100%;border-collapse:collapse;margin-bottom:12px;background:#fff}th,td{border:1px solid #d5dce8;padding:8px;text-align:left;font-size:14px}th{background:#edf3ff}
.positive{color:#1f7a45}.negative{color:#b83232}.error{color:#fff;background:#cc3b3b;border-radius:8px;padding:10px 12px;margin-bottom:14px}
@media (max-width:760px){.form-row.cols-2,.form-row.cols-3,.settings-row.cols-2,.settings-row.cols-3{grid-template-columns:1fr}}
"""


def _int(payload: dict, key: str, default: int) -> int:
    try:
        return int(payload.get(key, default))
    except Exception:
        return default


def _layout(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang='ja'><head><meta charset='UTF-8'/>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'/>"
        f"<title>{title}</title><link rel='stylesheet' href='/static/style.css'/>"
        "<link rel='icon' href='/favicon.ico'/></head><body>"
        f"{body}</body></html>"
    )


def _index_html(error: str = "") -> str:
    error_block = f"<div class='error'>{escape(error)}</div>" if error else ""
    body = f"""
    <main class="container">
      <h1>雀魂 牌譜リザルト</h1>
      <p class="lead">牌譜JSONをアップロードして精算結果を表示します。</p>
      {error_block}
      <form class="form-area" id="analyze-form">
        <div class="form-grid">
          <div class="form-row cols-3">
            <label>牌譜ファイル<input type="file" name="paifu_file" accept=".json,.txt" required /></label>
            <label>レート<input type="number" name="rate" value="50" required /></label>
            <label>チップ金額<input type="number" name="chip" value="500" required /></label>
          </div>
          <div class="form-row cols-2">
            <label>ウマ1<input type="number" name="uma_1" value="10" required /></label>
            <label>ウマ2<input type="number" name="uma_2" value="20" required /></label>
          </div>
          <div class="form-row cols-2">
            <label>初期点<input type="number" name="oka_1" value="25000" required /></label>
            <label>オカ<input type="number" name="oka_2" value="30000" required /></label>
          </div>
          <div class="form-row cols-3">
            <label>オールスターチップ倍率<input type="number" name="all_star_chip" value="5" required /></label>
            <label>役満ツモチップ倍率<input type="number" name="yiman_tumo_chip" value="5" required /></label>
            <label>役満ロンチップ倍率<input type="number" name="yiman_chip" value="10" required /></label>
          </div>
        </div>
        <button type="submit" class="submit-wide">結果を表示</button>
      </form>
    </main>
    <script>
    const form=document.getElementById("analyze-form");
    form.addEventListener("submit",async(e)=>{{
      e.preventDefault();
      const file=(form.querySelector('input[name="paifu_file"]').files||[])[0];
      if(!file){{alert("牌譜ファイルを選択してください。");return;}}
      try{{
        const payload={{
          paifu_json:JSON.parse(await file.text()),
          rate:form.rate.value,chip:form.chip.value,uma_1:form.uma_1.value,uma_2:form.uma_2.value,
          oka_1:form.oka_1.value,oka_2:form.oka_2.value,all_star_chip:form.all_star_chip.value,
          yiman_tumo_chip:form.yiman_tumo_chip.value,yiman_chip:form.yiman_chip.value
        }};
        const res=await fetch("/analyze-json",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(payload)}});
        const html=await res.text();document.open();document.write(html);document.close();
      }}catch(err){{alert(`牌譜の送信に失敗しました: ${{err}}`);}}
    }});
    </script>
    """
    return _layout("雀魂 牌譜リザルト", body)


def _tr(cells: list[str]) -> str:
    return "<tr>" + "".join(cells) + "</tr>"


def _result_html(context: dict, settings: dict) -> str:
    users_html = []
    for user in context["users"]:
        bonus_rows = "".join(
            _tr(
                [
                    f"<td>{escape(row['name'])}</td>",
                    f"<td>{escape(row['ron'])}</td>",
                    f"<td>{escape(row['tsumo'])}</td>",
                    f"<td>{escape(row['chip'])}</td>",
                ]
            )
            for row in user["bonus_rows"]
        )
        payment_rows = "".join(
            _tr(
                [
                    f"<td>{escape(row['to'])}</td>",
                    f"<td>{escape(row['type'])}</td>",
                    f"<td>{escape(row['chip'])}</td>",
                    f"<td>{escape(row['yen'])}</td>",
                ]
            )
            for row in user["payment_rows"]
        )
        opponent_rows = "".join(
            _tr(
                [
                    f"<td>{escape(row['to'])}</td>",
                    f"<td class='{'negative' if row['score_negative'] else 'positive'}'>{escape(row['score_yen'])}</td>",
                    f"<td>{escape(row['receive_chip'])}</td>",
                    f"<td>{escape(row['pay_chip'])}</td>",
                    f"<td class='{'negative' if row['total_negative'] else 'positive'}'>{escape(row['total_yen'])}</td>",
                ]
            )
            for row in user["opponent_rows"]
        )
        users_html.append(
            f"""
            <details class="card user-card">
              <summary class="user-summary">
                <div>
                  <h2>{escape(str(user["nickname"]))}</h2>
                  <p>最終得点: {escape(str(user["point"]))} (<span class="{'negative' if user['score_negative'] else 'positive'}">{escape(str(user["score"]))}</span>)</p>
                </div>
                <span class="summary-hint"></span>
              </summary>
              <h3>総合得点</h3>
              <table><thead><tr><th>得点</th><th>祝儀収益</th><th>祝儀支払</th><th>結果</th></tr></thead>
                <tbody>{_tr([f"<td>{escape(user['score_yen'])}</td>", f"<td>{escape(user['bonus_yen'])}</td>", f"<td class='negative'>-{escape(user['payment_yen'])}</td>", f"<td class='{'negative' if user['result_negative'] else 'positive'}'>{escape(user['result_yen'])}</td>"])}</tbody>
              </table>
              <h3>祝儀明細</h3>
              <table><thead><tr><th>種類</th><th>ロン</th><th>ツモ</th><th>チップ枚数</th></tr></thead><tbody>{bonus_rows}</tbody></table>
              <h3>支払い明細</h3>
              <table><thead><tr><th>振込先</th><th>内容</th><th>チップ枚数</th><th>金額</th></tr></thead><tbody>{payment_rows}</tbody></table>
              <h3>支払い集計（相手別）</h3>
              <table><thead><tr><th>相手</th><th>得点精算</th><th>受け取りチップ</th><th>支払いチップ</th><th>合計金額</th></tr></thead><tbody>{opponent_rows}</tbody></table>
            </details>
            """
        )

    body = f"""
    <main class="container">
      <header class="header-row"><h1>精算結果</h1><a href="/" class="button-link">別の牌譜を読み込む</a></header>
      <details class="settings-card" open>
        <summary class="settings-summary"><h2>現在の設定</h2><span class="summary-hint"></span></summary>
        <div class="settings-grid">
          <div class="settings-row cols-3">
            <div><span>レート</span><strong>{settings["rate"]}</strong></div>
            <div><span>チップ金額</span><strong>{settings["chip"]}</strong></div>
            <div><span>ウマ</span><strong>{settings["uma_1"]}-{settings["uma_2"]}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>初期点</span><strong>{settings["oka_1"]}</strong></div>
            <div><span>オカ</span><strong>{settings["oka_2"]}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>オールスターチップ倍率</span><strong>{settings["all_star_chip"]}</strong></div>
            <div><span>役満ツモチップ倍率</span><strong>{settings["yiman_tumo_chip"]}</strong></div>
            <div><span>役満ロンチップ倍率</span><strong>{settings["yiman_chip"]}</strong></div>
          </div>
        </div>
      </details>
      <div class="toggle-toolbar"><button type="button" id="expand-all">全部開く</button><button type="button" id="collapse-all">全部閉じる</button></div>
      {''.join(users_html)}
    </main>
    <script>
      const cards=document.querySelectorAll(".user-card");
      document.getElementById("expand-all").addEventListener("click",()=>cards.forEach(c=>c.open=true));
      document.getElementById("collapse-all").addEventListener("click",()=>cards.forEach(c=>c.open=false));
    </script>
    """
    return _layout("精算結果", body)


def _analyze_from_payload(payload: dict) -> tuple[dict, dict]:
    settings = {
        "rate": _int(payload, "rate", 50),
        "chip": _int(payload, "chip", 500),
        "uma_1": _int(payload, "uma_1", 10),
        "uma_2": _int(payload, "uma_2", 20),
        "oka_1": _int(payload, "oka_1", 25000),
        "oka_2": _int(payload, "oka_2", 30000),
        "all_star_chip": _int(payload, "all_star_chip", 5),
        "yiman_tumo_chip": _int(payload, "yiman_tumo_chip", 5),
        "yiman_chip": _int(payload, "yiman_chip", 10),
    }
    users = analyze_paifu(
        paifu_json=payload["paifu_json"],
        samma=False,
        rate=settings["rate"],
        chip=settings["chip"],
        uma_1=settings["uma_1"],
        uma_2=settings["uma_2"],
        oka_1=settings["oka_1"],
        oka_2=settings["oka_2"],
        all_star_chip=settings["all_star_chip"],
        yiman_tumo_chip=settings["yiman_tumo_chip"],
        yiman_chip=settings["yiman_chip"],
    )
    return build_result_context(users), settings


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("?", 1)[0]
        path = path[path.find("/", path.find("//") + 2) :]

        if path == "/static/style.css":
            return Response(STYLE_CSS, headers={"content-type": "text/css; charset=utf-8"})
        if path == "/favicon.ico":
            favicon_svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
                "<rect width='64' height='64' rx='12' fill='#2f6feb'/>"
                "<text x='50%' y='53%' dominant-baseline='middle' text-anchor='middle' "
                "font-size='34' fill='white'>麻</text></svg>"
            )
            return Response(favicon_svg, headers={"content-type": "image/svg+xml; charset=utf-8"})
        if request.method == "GET" and path == "/":
            return Response(_index_html(), headers={"content-type": "text/html; charset=utf-8"})
        if request.method == "POST" and path == "/analyze-json":
            try:
                payload = await request.json()
                context, settings = _analyze_from_payload(payload)
                return Response(
                    _result_html(context, settings),
                    headers={"content-type": "text/html; charset=utf-8"},
                )
            except Exception as exc:
                return Response(
                    _index_html(f"精算処理に失敗しました: {exc}"),
                    status=400,
                    headers={"content-type": "text/html; charset=utf-8"},
                )
        return Response("Not Found", status=404)
