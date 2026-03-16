function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#x27;");
}

function toInt(payload, key, defaultValue) {
  const raw = payload?.[key];
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) ? n : defaultValue;
}

function formatInt(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function yen(value) {
  return `${formatInt(value)} G`;
}

function signedYen(value) {
  const sign = value >= 0 ? "+" : "-";
  return `${sign}${formatInt(Math.abs(value))} G`;
}

const STYLE_CSS = `
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
`;

function layout(title, body) {
  return (
    "<!doctype html><html lang='ja'><head><meta charset='UTF-8'/>" +
    "<meta name='viewport' content='width=device-width, initial-scale=1.0'/>" +
    `<title>${title}</title><link rel='stylesheet' href='/static/style.css'/>` +
    "<link rel='icon' href='/favicon.ico'/></head><body>" +
    `${body}</body></html>`
  );
}

function indexHtml(error = "") {
  const errorBlock = error ? `<div class='error'>${escapeHtml(error)}</div>` : "";
  const body = `
    <main class="container">
      <h1>雀魂 牌譜リザルト</h1>
      <p class="lead">牌譜JSONをアップロードして精算結果を表示します。</p>
      ${errorBlock}
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
    form.addEventListener("submit",async(e)=>{
      e.preventDefault();
      const file=(form.querySelector('input[name="paifu_file"]').files||[])[0];
      if(!file){alert("牌譜ファイルを選択してください。");return;}
      try{
        const payload={
          paifu_json:JSON.parse(await file.text()),
          rate:form.rate.value,chip:form.chip.value,uma_1:form.uma_1.value,uma_2:form.uma_2.value,
          oka_1:form.oka_1.value,oka_2:form.oka_2.value,all_star_chip:form.all_star_chip.value,
          yiman_tumo_chip:form.yiman_tumo_chip.value,yiman_chip:form.yiman_chip.value
        };
        const res=await fetch("/analyze-json",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
        const html=await res.text();document.open();document.write(html);document.close();
      }catch(err){alert("牌譜の送信に失敗しました: " + err);}
    });
    </script>
    `;
  return layout("雀魂 牌譜リザルト", body);
}

function tr(cells) {
  return `<tr>${cells.join("")}</tr>`;
}

function bonusName(bonus) {
  switch (bonus) {
    case "aka_dora":
      return "赤ドラ";
    case "ura_dora":
      return "裏ドラ";
    case "ippatsu":
      return "一発";
    case "yiman":
      return "役満";
    case "allstar":
      return "オールスター";
    case "tobi":
      return "トビ";
    default:
      return bonus;
  }
}

function makeUser(seat, nickname) {
  return {
    seat,
    nickname,
    point: 0,
    score: 0,
    score_yen: 0,
    bonus_yen: 0,
    tobi: 0,
    tobi_ron: 0,
    tobi_tumo: 0,
    ura_dora: 0,
    aka_dora: 0,
    ippatsu: 0,
    allstar: 0,
    yiman: 0,
    ura_dora_tumo: 0,
    aka_dora_tumo: 0,
    ippatsu_tumo: 0,
    allstar_tumo: 0,
    yiman_tumo: 0,
    chip: 0,
    chip_yen_unit: 500,
    tsumo_target_count: 3,
    allstar_chip_rate: 5,
    yiman_tumo_chip_rate: 5,
    yiman_chip_rate: 10,
    transaction: [],
    score_transaction: [],
    bonus_summary_transaction: [],
    score_summary_transaction: [],
    opponent_summaries: [],
  };
}

function createUsers(paifu, samma) {
  const users = [];
  const seats = samma ? [0, 1, 2] : [0, 1, 2, 3];

  for (const account of paifu.head.accounts) {
    users.push(makeUser(account.seat, account.nickname));
    const idx = seats.indexOf(account.seat);
    if (idx >= 0) {
      seats.splice(idx, 1);
    }
  }

  for (let i = 0; i < seats.length; i += 1) {
    users.push(makeUser(seats[i], `CPU${i + 1}`));
  }

  const pointMap = new Map();
  for (const player of paifu.head.result.players) {
    pointMap.set(player.seat, player.part_point_1);
  }

  for (const user of users) {
    user.point = pointMap.get(user.seat) ?? 0;
  }

  return users;
}

function getUserBySeat(users, seat) {
  return users.find((u) => u.seat === seat) ?? null;
}

function getRecordHule(paifu) {
  return paifu.data.data.actions.filter(
    (action) => action.type === 1 && action.result && action.result.name === ".lq.RecordHule",
  );
}

function calcBonus(paifu, users) {
  function countIppatsu(hule) {
    for (const fan of hule.fans) {
      if (fan.id === 30) return fan.val;
    }
    return 0;
  }

  function countAkaDora(hule) {
    for (const fan of hule.fans) {
      if (fan.id === 32) return fan.val;
    }
    return 0;
  }

  function countAllstar(hule) {
    for (const fan of hule.fans) {
      if (fan.id === 32 && fan.val === 3) return 1;
    }
    return 0;
  }

  function countYiman(hule) {
    return hule.yiman ? 1 : 0;
  }

  function countUraDora(hule) {
    for (const fan of hule.fans) {
      if (fan.id === 33) return fan.val;
    }
    return 0;
  }

  function fangchongUser(deltaScores) {
    for (let i = 0; i < deltaScores.length; i += 1) {
      if (deltaScores[i] < 0) return getUserBySeat(users, i);
    }
    return null;
  }

  function tobiUsers(scores) {
    const out = [];
    for (let i = 0; i < scores.length; i += 1) {
      if (scores[i] < 0) {
        const user = getUserBySeat(users, i);
        if (user) out.push(user);
      }
    }
    return out.length > 0 ? out : null;
  }

  function count(hule, fangchong, tobi) {
    const winner = getUserBySeat(users, hule.seat);
    if (!winner) return;

    const ippatsu = countIppatsu(hule);
    const uraDora = countUraDora(hule);
    const akaDora = countAkaDora(hule);
    const yiman = countYiman(hule);
    const allstar = countAllstar(hule);

    if (ippatsu + uraDora + akaDora + yiman + allstar === 0 && !tobi) {
      return;
    }

    if (!fangchong) {
      winner.ippatsu_tumo += ippatsu;
      winner.ura_dora_tumo += uraDora;
      winner.aka_dora_tumo += akaDora;
      winner.yiman_tumo += yiman;
      winner.allstar_tumo += allstar;

      for (const user of users) {
        if (user.seat === hule.seat) continue;
        if (ippatsu > 0) user.transaction.push({ to: winner.nickname, cnt: ippatsu, bonus: "ippatsu", zimo: true, yen: 0 });
        if (uraDora > 0) user.transaction.push({ to: winner.nickname, cnt: uraDora, bonus: "ura_dora", zimo: true, yen: 0 });
        if (akaDora > 0) user.transaction.push({ to: winner.nickname, cnt: akaDora, bonus: "aka_dora", zimo: true, yen: 0 });
        if (yiman > 0) user.transaction.push({ to: winner.nickname, cnt: yiman, bonus: "yiman", zimo: true, yen: 0 });
        if (allstar > 0) user.transaction.push({ to: winner.nickname, cnt: allstar, bonus: "allstar", zimo: true, yen: 0 });
      }
    } else {
      winner.ippatsu += ippatsu;
      winner.ura_dora += uraDora;
      winner.aka_dora += akaDora;
      winner.yiman += yiman;
      winner.allstar += allstar;

      if (ippatsu > 0) fangchong.transaction.push({ to: winner.nickname, cnt: ippatsu, bonus: "ippatsu", zimo: false, yen: 0 });
      if (uraDora > 0) fangchong.transaction.push({ to: winner.nickname, cnt: uraDora, bonus: "ura_dora", zimo: false, yen: 0 });
      if (akaDora > 0) fangchong.transaction.push({ to: winner.nickname, cnt: akaDora, bonus: "aka_dora", zimo: false, yen: 0 });
      if (yiman > 0) fangchong.transaction.push({ to: winner.nickname, cnt: yiman, bonus: "yiman", zimo: false, yen: 0 });
      if (allstar > 0) fangchong.transaction.push({ to: winner.nickname, cnt: allstar, bonus: "allstar", zimo: false, yen: 0 });
    }

    if (tobi) {
      if (!fangchong) {
        winner.tobi += tobi.length;
        winner.tobi_tumo += tobi.length;
        for (const user of tobi) {
          user.transaction.push({ to: winner.nickname, cnt: 1, bonus: "tobi", zimo: true, yen: 0 });
        }
      } else {
        winner.tobi += 1;
        winner.tobi_ron += 1;
        fangchong.transaction.push({ to: winner.nickname, cnt: 1, bonus: "tobi", zimo: false, yen: 0 });
      }
    }
  }

  for (const record of getRecordHule(paifu)) {
    for (const hule of record.result.data.hules) {
      const fangchong = hule.zimo === true ? null : fangchongUser(record.result.data.delta_scores);
      const tobi = tobiUsers(record.result.data.scores);
      count(hule, fangchong, tobi);
    }
  }
}

function countChip(user, samma, allstarChip, yimanTumoChip, yimanChip) {
  const membersCount = samma ? 2 : 3;
  let chipSum = user.ura_dora + user.aka_dora + user.ippatsu;
  chipSum += user.allstar * allstarChip;
  chipSum += user.yiman * yimanChip;

  chipSum += (user.ura_dora_tumo + user.aka_dora_tumo + user.ippatsu_tumo) * membersCount;
  chipSum += user.allstar_tumo * allstarChip * membersCount;
  chipSum += user.yiman_tumo * yimanTumoChip * membersCount;
  chipSum += user.tobi;

  return chipSum;
}

function countScoreTransactions(users) {
  const rankIndex = new Map(users.map((user, idx) => [user, idx]));
  const debtors = users.filter((u) => u.score_yen < 0).sort((a, b) => rankIndex.get(b) - rankIndex.get(a));
  const creditors = users.filter((u) => u.score_yen > 0).sort((a, b) => rankIndex.get(a) - rankIndex.get(b));
  const creditorRemaining = new Map(creditors.map((u) => [u, u.score_yen]));

  for (const debtor of debtors) {
    debtor.score_transaction = [];
    let remain = -debtor.score_yen;

    for (const creditor of creditors) {
      if (remain <= 0) break;

      const cRemain = creditorRemaining.get(creditor) ?? 0;
      if (cRemain <= 0) continue;

      const pay = Math.min(remain, cRemain);
      debtor.score_transaction.push({ to: creditor.nickname, yen: pay });
      remain -= pay;
      creditorRemaining.set(creditor, cRemain - pay);
    }
  }
}

function buildNetPaymentSummary(users) {
  const userByNickname = new Map(users.map((u) => [u.nickname, u]));

  function netPairwise(rawMap) {
    const netMap = new Map(rawMap);

    for (let i = 0; i < users.length; i += 1) {
      for (let j = i + 1; j < users.length; j += 1) {
        const a = users[i];
        const b = users[j];
        const aMap = new Map(netMap.get(a));
        const bMap = new Map(netMap.get(b));

        const aToB = aMap.get(b) ?? 0;
        const bToA = bMap.get(a) ?? 0;

        if (aToB >= bToA) {
          const remain = aToB - bToA;
          if (remain > 0) aMap.set(b, remain);
          else aMap.delete(b);
          bMap.delete(a);
        } else {
          const remain = bToA - aToB;
          if (remain > 0) bMap.set(a, remain);
          else bMap.delete(a);
          aMap.delete(b);
        }

        netMap.set(a, aMap);
        netMap.set(b, bMap);
      }
    }

    return netMap;
  }

  const rawBonusMap = new Map(users.map((u) => [u, new Map()]));
  const rawScoreMap = new Map(users.map((u) => [u, new Map()]));

  for (const user of users) {
    const bonus = new Map(rawBonusMap.get(user));
    for (const t of user.transaction) {
      const toUser = userByNickname.get(t.to);
      if (!toUser) continue;
      bonus.set(toUser, (bonus.get(toUser) ?? 0) + t.yen);
    }
    rawBonusMap.set(user, bonus);

    const score = new Map(rawScoreMap.get(user));
    for (const s of user.score_transaction) {
      const toUser = userByNickname.get(s.to);
      if (!toUser) continue;
      score.set(toUser, (score.get(toUser) ?? 0) + s.yen);
    }
    rawScoreMap.set(user, score);
  }

  const bonusNetMap = netPairwise(rawBonusMap);
  const scoreNetMap = netPairwise(rawScoreMap);

  for (const user of users) {
    user.bonus_summary_transaction = [];
    for (const [toUser, amount] of bonusNetMap.get(user)) {
      if (amount > 0) user.bonus_summary_transaction.push({ to: toUser.nickname, yen: amount });
    }

    user.score_summary_transaction = [];
    for (const [toUser, amount] of scoreNetMap.get(user)) {
      if (amount > 0) user.score_summary_transaction.push({ to: toUser.nickname, yen: amount });
    }
  }
}

function buildOpponentSummaries(users, chipUnit) {
  const userByNickname = new Map(users.map((u) => [u.nickname, u]));
  const summaryMap = new Map();

  for (const user of users) {
    const map = new Map();
    for (const opp of users) {
      if (opp.nickname === user.nickname) continue;
      map.set(opp.nickname, {
        to: opp.nickname,
        score_yen: 0,
        receive_chip: 0,
        pay_chip: 0,
        total_yen: 0,
      });
    }
    summaryMap.set(user.nickname, map);
  }

  for (const payer of users) {
    const payerName = payer.nickname;

    for (const s of payer.score_transaction) {
      const payee = userByNickname.get(s.to);
      if (!payee) continue;
      const payeeName = payee.nickname;
      summaryMap.get(payerName).get(payeeName).score_yen -= s.yen;
      summaryMap.get(payeeName).get(payerName).score_yen += s.yen;
    }

    for (const t of payer.transaction) {
      const payee = userByNickname.get(t.to);
      if (!payee) continue;
      const payeeName = payee.nickname;
      const chipCnt = chipUnit > 0 ? Math.trunc(t.yen / chipUnit) : 0;
      summaryMap.get(payerName).get(payeeName).pay_chip += chipCnt;
      summaryMap.get(payeeName).get(payerName).receive_chip += chipCnt;
    }
  }

  for (const user of users) {
    const rows = [];
    for (const opp of users) {
      if (opp.nickname === user.nickname) continue;
      const row = summaryMap.get(user.nickname).get(opp.nickname);
      row.total_yen = row.score_yen + (row.receive_chip - row.pay_chip) * chipUnit;
      rows.push(row);
    }
    user.opponent_summaries = rows;
  }
}

function analyzePaifu(paifuJson, settings) {
  const samma = false;
  const users = createUsers(paifuJson, samma);
  calcBonus(paifuJson, users);
  users.sort((a, b) => b.point - a.point);

  const {
    rate,
    chip,
    uma_1: uma1,
    uma_2: uma2,
    oka_1: oka1,
    oka_2: oka2,
    all_star_chip: allStarChip,
    yiman_tumo_chip: yimanTumoChip,
    yiman_chip: yimanChip,
  } = settings;

  for (let i = 0; i < users.length; i += 1) {
    const user = users[i];
    let totalPoint = (user.point - oka2) / 1000;

    if (i === 0) {
      totalPoint += uma2;
      totalPoint += ((oka2 - oka1) * 4) / 1000;
    } else if (i === 1) {
      totalPoint += uma1;
    } else if (i === 2) {
      totalPoint -= uma1;
    } else if (i === 3) {
      totalPoint -= uma2;
    }

    user.score = totalPoint;
    user.chip = countChip(user, samma, allStarChip, yimanTumoChip, yimanChip);
    user.bonus_yen = user.chip * chip;
    user.score_yen = Math.round(user.score * rate);
    user.chip_yen_unit = chip;
    user.tsumo_target_count = samma ? 2 : 3;
    user.allstar_chip_rate = allStarChip;
    user.yiman_tumo_chip_rate = yimanTumoChip;
    user.yiman_chip_rate = yimanChip;

    for (const t of user.transaction) {
      let v = 0;
      if (t.bonus === "ippatsu" || t.bonus === "ura_dora" || t.bonus === "aka_dora") {
        v += chip * t.cnt;
      } else if (t.bonus === "allstar") {
        v += chip * t.cnt * allStarChip;
      } else if (t.bonus === "yiman") {
        v += chip * t.cnt * (t.zimo ? yimanTumoChip : yimanChip);
      } else if (t.bonus === "tobi") {
        v += chip;
      }
      t.yen = v;
    }
  }

  countScoreTransactions(users);
  buildNetPaymentSummary(users);
  buildOpponentSummaries(users, chip);
  return users;
}

function bonusTable(user) {
  const tsumoTargetCount = user.tsumo_target_count;

  const ronChipAka = user.aka_dora;
  const ronChipUra = user.ura_dora;
  const ronChipIppatsu = user.ippatsu;
  const ronChipAllstar = user.allstar * user.allstar_chip_rate;
  const ronChipYiman = user.yiman * user.yiman_chip_rate;
  const ronChipTobi = user.tobi_ron;

  const tsumoChipAka = user.aka_dora_tumo * tsumoTargetCount;
  const tsumoChipUra = user.ura_dora_tumo * tsumoTargetCount;
  const tsumoChipIppatsu = user.ippatsu_tumo * tsumoTargetCount;
  const tsumoChipAllstar = user.allstar_tumo * user.allstar_chip_rate * tsumoTargetCount;
  const tsumoChipYiman = user.yiman_tumo * user.yiman_tumo_chip_rate * tsumoTargetCount;
  const tsumoChipTobi = user.tobi_tumo;

  const chipTotalAka = ronChipAka + tsumoChipAka;
  const chipTotalUra = ronChipUra + tsumoChipUra;
  const chipTotalIppatsu = ronChipIppatsu + tsumoChipIppatsu;
  const chipTotalAllstar = ronChipAllstar + tsumoChipAllstar;
  const chipTotalYiman = ronChipYiman + tsumoChipYiman;
  const chipTotalTobi = ronChipTobi + tsumoChipTobi;

  const chipTotal = chipTotalAka + chipTotalUra + chipTotalIppatsu + chipTotalAllstar + chipTotalYiman + chipTotalTobi;
  const chipTotalYen = chipTotal * user.chip_yen_unit;

  return [
    { name: "赤ドラ", ron: `${user.aka_dora}回`, tsumo: `${user.aka_dora_tumo}回`, chip: `${chipTotalAka}枚` },
    { name: "裏ドラ", ron: `${user.ura_dora}回`, tsumo: `${user.ura_dora_tumo}回`, chip: `${chipTotalUra}枚` },
    { name: "一発", ron: `${user.ippatsu}回`, tsumo: `${user.ippatsu_tumo}回`, chip: `${chipTotalIppatsu}枚` },
    { name: "オールスター", ron: `${user.allstar}回`, tsumo: `${user.allstar_tumo}回`, chip: `${chipTotalAllstar}枚` },
    { name: "役満", ron: `${user.yiman}回`, tsumo: `${user.yiman_tumo}回`, chip: `${chipTotalYiman}枚` },
    { name: "飛ばし", ron: `${user.tobi_ron}回`, tsumo: `${user.tobi_tumo}回`, chip: `${chipTotalTobi}枚` },
    { name: "合計チップ枚数", ron: "", tsumo: "", chip: `${chipTotal}枚` },
    { name: "合計金額", ron: "", tsumo: "", chip: yen(chipTotalYen) },
  ];
}

function paymentDetails(user) {
  const rows = [];
  let total = 0;

  for (const hule of user.transaction) {
    const chipCnt = user.chip_yen_unit > 0 ? Math.trunc(hule.yen / user.chip_yen_unit) : 0;
    rows.push({
      to: hule.to,
      type: hule.zimo ? `${bonusName(hule.bonus)}(ツモ)` : `${bonusName(hule.bonus)}(ロン)`,
      chip: `${chipCnt}枚`,
      yen: yen(hule.yen),
    });
    total += hule.yen;
  }

  if (rows.length === 0) {
    rows.push({ to: "なし", type: "", chip: "0枚", yen: yen(0) });
  }

  return [rows, total];
}

function opponentSummary(user) {
  if (!user.opponent_summaries || user.opponent_summaries.length === 0) {
    return [{
      to: "なし",
      score_yen: yen(0),
      receive_chip: "0枚",
      pay_chip: "0枚",
      total_yen: yen(0),
      score_negative: false,
      total_negative: false,
    }];
  }

  return user.opponent_summaries.map((row) => ({
    to: row.to,
    score_yen: signedYen(row.score_yen),
    receive_chip: `${formatInt(row.receive_chip)}枚`,
    pay_chip: `${formatInt(row.pay_chip)}枚`,
    total_yen: signedYen(row.total_yen),
    score_negative: row.score_yen < 0,
    total_negative: row.total_yen < 0,
  }));
}

function buildResultContext(users) {
  return {
    users: users.map((user) => {
      const bonusRows = bonusTable(user);
      const [paymentRows, paymentTotal] = paymentDetails(user);
      const opponentRows = opponentSummary(user);
      const bonusNet = user.bonus_yen - paymentTotal;
      const totalResult = user.score_yen + bonusNet;
      return {
        nickname: user.nickname,
        point: formatInt(user.point),
        score: user.score,
        score_negative: user.score < 0,
        score_yen: yen(user.score_yen),
        bonus_yen: yen(user.bonus_yen),
        payment_yen: yen(paymentTotal),
        bonus_net_yen: signedYen(bonusNet),
        result_yen: signedYen(totalResult),
        result_negative: totalResult < 0,
        bonus_rows: bonusRows,
        payment_rows: paymentRows,
        opponent_rows: opponentRows,
      };
    }),
  };
}

function resultHtml(context, settings) {
  const usersHtml = context.users.map((user) => {
    const bonusRows = user.bonus_rows
      .map((row) => tr([
        `<td>${escapeHtml(row.name)}</td>`,
        `<td>${escapeHtml(row.ron)}</td>`,
        `<td>${escapeHtml(row.tsumo)}</td>`,
        `<td>${escapeHtml(row.chip)}</td>`,
      ]))
      .join("");

    const paymentRows = user.payment_rows
      .map((row) => tr([
        `<td>${escapeHtml(row.to)}</td>`,
        `<td>${escapeHtml(row.type)}</td>`,
        `<td>${escapeHtml(row.chip)}</td>`,
        `<td>${escapeHtml(row.yen)}</td>`,
      ]))
      .join("");

    const opponentRows = user.opponent_rows
      .map((row) => tr([
        `<td>${escapeHtml(row.to)}</td>`,
        `<td class='${row.score_negative ? "negative" : "positive"}'>${escapeHtml(row.score_yen)}</td>`,
        `<td>${escapeHtml(row.receive_chip)}</td>`,
        `<td>${escapeHtml(row.pay_chip)}</td>`,
        `<td class='${row.total_negative ? "negative" : "positive"}'>${escapeHtml(row.total_yen)}</td>`,
      ]))
      .join("");

    return `
      <details class="card user-card">
        <summary class="user-summary">
          <div>
            <h2>${escapeHtml(user.nickname)}</h2>
            <p>最終得点: ${escapeHtml(String(user.point))} (<span class="${user.score_negative ? "negative" : "positive"}">${escapeHtml(String(user.score))}</span>)</p>
          </div>
          <span class="summary-hint"></span>
        </summary>
        <h3>総合得点</h3>
        <table><thead><tr><th>得点</th><th>祝儀収益</th><th>祝儀支払</th><th>結果</th></tr></thead>
          <tbody>${tr([
            `<td>${escapeHtml(user.score_yen)}</td>`,
            `<td>${escapeHtml(user.bonus_yen)}</td>`,
            `<td class='negative'>-${escapeHtml(user.payment_yen)}</td>`,
            `<td class='${user.result_negative ? "negative" : "positive"}'>${escapeHtml(user.result_yen)}</td>`,
          ])}</tbody>
        </table>
        <h3>祝儀明細</h3>
        <table><thead><tr><th>種類</th><th>ロン</th><th>ツモ</th><th>チップ枚数</th></tr></thead><tbody>${bonusRows}</tbody></table>
        <h3>支払い明細</h3>
        <table><thead><tr><th>振込先</th><th>内容</th><th>チップ枚数</th><th>金額</th></tr></thead><tbody>${paymentRows}</tbody></table>
        <h3>支払い集計（相手別）</h3>
        <table><thead><tr><th>相手</th><th>得点精算</th><th>受け取りチップ</th><th>支払いチップ</th><th>合計金額</th></tr></thead><tbody>${opponentRows}</tbody></table>
      </details>
      `;
  }).join("");

  const body = `
    <main class="container">
      <header class="header-row"><h1>精算結果</h1><a href="/" class="button-link">別の牌譜を読み込む</a></header>
      <details class="settings-card" open>
        <summary class="settings-summary"><h2>現在の設定</h2><span class="summary-hint"></span></summary>
        <div class="settings-grid">
          <div class="settings-row cols-3">
            <div><span>レート</span><strong>${settings.rate}</strong></div>
            <div><span>チップ金額</span><strong>${settings.chip}</strong></div>
            <div><span>ウマ</span><strong>${settings.uma_1}-${settings.uma_2}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>初期点</span><strong>${settings.oka_1}</strong></div>
            <div><span>オカ</span><strong>${settings.oka_2}</strong></div>
          </div>
          <div class="settings-row cols-3">
            <div><span>オールスターチップ倍率</span><strong>${settings.all_star_chip}</strong></div>
            <div><span>役満ツモチップ倍率</span><strong>${settings.yiman_tumo_chip}</strong></div>
            <div><span>役満ロンチップ倍率</span><strong>${settings.yiman_chip}</strong></div>
          </div>
        </div>
      </details>
      <div class="toggle-toolbar"><button type="button" id="expand-all">全部開く</button><button type="button" id="collapse-all">全部閉じる</button></div>
      ${usersHtml}
    </main>
    <script>
      const cards=document.querySelectorAll(".user-card");
      document.getElementById("expand-all").addEventListener("click",()=>cards.forEach(c=>c.open=true));
      document.getElementById("collapse-all").addEventListener("click",()=>cards.forEach(c=>c.open=false));
    </script>
    `;
  return layout("精算結果", body);
}

function analyzeFromPayload(payload) {
  const settings = {
    rate: toInt(payload, "rate", 50),
    chip: toInt(payload, "chip", 500),
    uma_1: toInt(payload, "uma_1", 10),
    uma_2: toInt(payload, "uma_2", 20),
    oka_1: toInt(payload, "oka_1", 25000),
    oka_2: toInt(payload, "oka_2", 30000),
    all_star_chip: toInt(payload, "all_star_chip", 5),
    yiman_tumo_chip: toInt(payload, "yiman_tumo_chip", 5),
    yiman_chip: toInt(payload, "yiman_chip", 10),
  };

  const users = analyzePaifu(payload.paifu_json, settings);
  return [buildResultContext(users), settings];
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/static/style.css") {
      return new Response(STYLE_CSS, { headers: { "content-type": "text/css; charset=utf-8" } });
    }

    if (path === "/favicon.ico") {
      const faviconSvg =
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>" +
        "<rect width='64' height='64' rx='12' fill='#2f6feb'/>" +
        "<text x='50%' y='53%' dominant-baseline='middle' text-anchor='middle' font-size='34' fill='white'>麻</text></svg>";
      return new Response(faviconSvg, { headers: { "content-type": "image/svg+xml; charset=utf-8" } });
    }

    if (request.method === "GET" && path === "/") {
      return new Response(indexHtml(), { headers: { "content-type": "text/html; charset=utf-8" } });
    }

    if (request.method === "POST" && path === "/analyze-json") {
      try {
        const payload = await request.json();
        const [context, settings] = analyzeFromPayload(payload);
        return new Response(resultHtml(context, settings), { headers: { "content-type": "text/html; charset=utf-8" } });
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return new Response(indexHtml(`精算処理に失敗しました: ${message}`), {
          status: 400,
          headers: { "content-type": "text/html; charset=utf-8" },
        });
      }
    }

    return new Response("Not Found", { status: 404 });
  },
};
