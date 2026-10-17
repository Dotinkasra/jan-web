import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';
import test from 'node:test';

function load(source) {
  const context = vm.createContext({ Response, URL });
  vm.runInContext(source.replace('export default {', 'const worker = {') +
    '\nthis.api = { worker, analyzePaifu, analyzeFromPayload, ' +
    (source.includes('function normalizePaifu(') ? 'normalizePaifu' : '') + ' };', context);
  return context.api;
}
const current = load(readFileSync(new URL('../worker.js', import.meta.url), 'utf8'));
// Entirely synthetic records: no private replay file or player identifiers.
const players = Array.from({ length: 4 }, (_, position) => ({
  userId: position + 1, position, nickname: `Player ${position + 1}`,
}));
const definitions = [
  [0, 4, 3, [49, 51]], [1, 4, null, [50]], [0, 3, 1, [51]],
  [0, 1, 3, [49]], [1, 2, null, [50]], [0, 4, 1, [49]],
];
const finalPoints = [13500, 23300, 17700, 45500];
const sample = {
  playerCount: 4,
  handRecord: definitions.map(([end_type, winner, loser, fans], index) => ({
    players: structuredClone(players),
    handEventRecord: [{
      eventType: 5, startTime: 1700000000000 + index * 1000,
      data: {
        end_type,
        win_info: [{ user_id: winner, fang_info: fans.map(fang_type => ({ fang_type, fang_num: 1 })) }],
        user_profit: players.map(player => ({
          user_id: player.userId, user_point: 25000,
          point_profit: player.userId === winner ? (end_type === 1 ? 3000 : 1000)
            : (end_type === 1 || player.userId === loser ? -1000 : 0),
        })),
      },
    }, ...(index === 5 ? [{ eventType: 6, data: {
      user_data: players.map((player, i) => ({ user_id: player.userId, point_num: finalPoints[i] })),
    } }] : [])],
  })),
};
const plain = (value) => JSON.parse(JSON.stringify(value));
const settings = { rate: 50, chip: 500, uma_1: 10, uma_2: 20, oka_1: 25000,
  oka_2: 30000, all_star_chip: 5, yiman_tumo_chip: 5, yiman_chip: 10 };

test('sample final points and bonus transfers', () => {
  const users = current.analyzePaifu(sample, settings);
  assert.deepEqual(plain(users.map(u => [u.nickname, u.point, u.chip])), [
    ['Player 4', 45500, 3], ['Player 2', 23300, 0],
    ['Player 3', 17700, 1], ['Player 1', 13500, 1],
  ]);
  assert.equal(users.reduce((sum, u) => sum + u.point, 0), 100000);
  assert.equal(users.reduce((sum, u) => sum + u.transaction.reduce((s, t) => s + t.cnt, 0), 0), 5);
  const normalized = current.normalizePaifu(sample);
  assert.equal(normalized.head.start_time, 1700000000);
  assert.equal(normalized.data.data.actions.length, 6);
});

test('Mahjong Soul calculation matches the pre-change implementation', () => {
  const baseline = load(execFileSync('git', ['show', 'HEAD:worker.js'], { encoding: 'utf8' }));
  const paifu = plain(current.normalizePaifu(sample));
  // Include bonus types absent from the sample in the regression check.
  paifu.data.data.actions[1].result.data.hules[0].fans = [
    { id: 30, val: 1 }, { id: 32, val: 3 }, { id: 33, val: 2 },
  ];
  paifu.data.data.actions[1].result.data.hules[0].yiman = true;
  assert.equal(current.normalizePaifu(paifu), paifu);
  assert.deepEqual(plain(current.analyzePaifu(paifu, settings)), plain(baseline.analyzePaifu(paifu, settings)));
});

test('ippatsu, all-star, multiple yakuman and tsumo bankruptcy use existing rules', () => {
  const paifu = structuredClone(sample);
  const end = paifu.handRecord[0].handEventRecord.find(e => e.eventType === 5);
  end.data.end_type = 1;
  end.data.win_info[0].fang_info = [
    { fang_type: 2, fang_num: 1 }, { fang_type: 49, fang_num: 3 },
    { fang_type: 51, fang_num: 2 }, { fang_type: 38, fang_num: 13 },
    { fang_type: 45, fang_num: 13 },
  ];
  end.data.user_profit[0].user_point = -100;
  end.data.user_profit[0].point_profit = -25100;
  paifu.handRecord = [{ ...paifu.handRecord[0], handEventRecord: [end,
    paifu.handRecord.at(-1).handEventRecord.find(e => e.eventType === 6)] }];
  const winner = current.analyzePaifu(paifu, settings).find(u => u.nickname === 'Player 4');
  assert.deepEqual(plain([winner.ippatsu_tumo, winner.aka_dora_tumo, winner.ura_dora_tumo,
    winner.allstar_tumo, winner.yiman_tumo, winner.tobi, winner.chip]), [1, 3, 2, 1, 1, 1, 49]);
});

test('double ron shares the discarder and draws award no bonuses', () => {
  const paifu = structuredClone(sample);
  const end = paifu.handRecord[0].handEventRecord.find(e => e.eventType === 5);
  const second = structuredClone(end.data.win_info[0]);
  second.user_id = paifu.handRecord[0].players[0].userId;
  end.data.win_info.push(second);
  end.data.user_profit[0].point_profit = 5200;
  const normalized = current.normalizePaifu(paifu);
  assert.equal(normalized.data.data.actions[0].result.data.hules.length, 2);
  assert.doesNotThrow(() => current.analyzePaifu(paifu, settings));
  end.data.win_info = [];
  end.data.end_type = 7;
  assert.equal(current.normalizePaifu(paifu).data.data.actions.length, 5);
});

test('draws with tenpai entries or null win_info do not count as wins', async () => {
  for (const winInfo of [
    players.slice(0, 3).map(player => ({ user_id: player.userId, fang_info: null })),
    null,
  ]) {
    const paifu = structuredClone(sample);
    const end = paifu.handRecord[0].handEventRecord.find(e => e.eventType === 5);
    end.data.end_type = 7;
    end.data.win_info = winInfo;
    const expected = structuredClone(paifu);
    expected.handRecord[0].handEventRecord.find(e => e.eventType === 5).data.win_info = [];
    assert.equal(current.normalizePaifu(paifu).data.data.actions.length, 5);
    assert.deepEqual(plain(current.analyzePaifu(paifu, settings)), plain(current.analyzePaifu(expected, settings)));
    const response = await current.worker.fetch(new Request('https://example.test/analyze-json', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paifu_json: paifu, ...settings }),
    }));
    assert.equal(response.status, 200);
  }
});

test('string event data and unordered players/profits are supported', () => {
  const paifu = structuredClone(sample);
  for (const hand of paifu.handRecord) {
    hand.players.reverse();
    for (const event of hand.handEventRecord) {
      event.data.user_profit?.reverse();
      event.data = JSON.stringify(event.data);
    }
  }
  assert.deepEqual(plain(current.analyzePaifu(paifu, settings)), plain(current.analyzePaifu(sample, settings)));
});

test('incomplete, three-player and malformed records fail clearly', () => {
  const paifu = structuredClone(sample);
  paifu.playerCount = 3;
  assert.throws(() => current.normalizePaifu(paifu), /四人打ち/);
  paifu.playerCount = 4;
  const last = paifu.handRecord.at(-1).handEventRecord;
  const final = last.pop();
  assert.throws(() => current.normalizePaifu(paifu), /最終結果/);
  last.push(final);
  final.data.user_data[0].user_id = -1;
  assert.throws(() => current.normalizePaifu(paifu), /点数情報/);
});

test('HTTP endpoint accepts Riichi City and mixed-format batches', async () => {
  for (const list of [[sample], [sample, plain(current.normalizePaifu(sample))]]) {
    const response = await current.worker.fetch(new Request('https://example.test/analyze-json', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paifu_json_list: list, ...settings }),
    }));
    assert.equal(response.status, 200);
    const html = await response.text();
    assert.match(html, /45,500/);
    assert.match(html, /Player 4/);
  }
});
