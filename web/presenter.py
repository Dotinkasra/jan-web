from module.data import User


def _yen(value: int) -> str:
    # return f"{value:,}円"
    return f"{value:,} G"


def _signed_yen(value: int) -> str:
    # return f"{value:+,}円"
    return f"{value:+,} G"


def _bonus_table(user: User) -> tuple[list[dict], int, int]:
    tsumo_target_count = user.tsumo_target_count

    ron_chip_aka = user.aka_dora
    ron_chip_ura = user.ura_dora
    ron_chip_ippatsu = user.ippatsu
    ron_chip_allstar = user.allstar * user.allstar_chip_rate
    ron_chip_yiman = user.yiman * user.yiman_chip_rate
    ron_chip_tobi = user.tobi_ron

    tumo_chip_aka = user.aka_dora_tumo * tsumo_target_count
    tumo_chip_ura = user.ura_dora_tumo * tsumo_target_count
    tumo_chip_ippatsu = user.ippatsu_tumo * tsumo_target_count
    tumo_chip_allstar = user.allstar_tumo * user.allstar_chip_rate * tsumo_target_count
    tumo_chip_yiman = user.yiman_tumo * user.yiman_tumo_chip_rate * tsumo_target_count
    tumo_chip_tobi = user.tobi_tumo

    chip_total_aka = ron_chip_aka + tumo_chip_aka
    chip_total_ura = ron_chip_ura + tumo_chip_ura
    chip_total_ippatsu = ron_chip_ippatsu + tumo_chip_ippatsu
    chip_total_allstar = ron_chip_allstar + tumo_chip_allstar
    chip_total_yiman = ron_chip_yiman + tumo_chip_yiman
    chip_total_tobi = ron_chip_tobi + tumo_chip_tobi

    chip_total = (
        chip_total_aka + chip_total_ura + chip_total_ippatsu + chip_total_allstar + chip_total_yiman + chip_total_tobi
    )
    chip_total_yen = chip_total * user.chip_yen_unit

    rows = [
        {
            "name": "赤ドラ",
            "ron": f"{user.aka_dora}回",
            "tsumo": f"{user.aka_dora_tumo}回",
            "chip": f"{chip_total_aka}枚",
        },
        {
            "name": "裏ドラ",
            "ron": f"{user.ura_dora}回",
            "tsumo": f"{user.ura_dora_tumo}回",
            "chip": f"{chip_total_ura}枚",
        },
        {
            "name": "一発",
            "ron": f"{user.ippatsu}回",
            "tsumo": f"{user.ippatsu_tumo}回",
            "chip": f"{chip_total_ippatsu}枚",
        },
        {
            "name": "オールスター",
            "ron": f"{user.allstar}回",
            "tsumo": f"{user.allstar_tumo}回",
            "chip": f"{chip_total_allstar}枚",
        },
        {"name": "役満", "ron": f"{user.yiman}回", "tsumo": f"{user.yiman_tumo}回", "chip": f"{chip_total_yiman}枚"},
        {"name": "飛ばし", "ron": f"{user.tobi_ron}回", "tsumo": f"{user.tobi_tumo}回", "chip": f"{chip_total_tobi}枚"},
        {"name": "合計チップ枚数", "ron": "", "tsumo": "", "chip": f"{chip_total}枚"},
        {"name": "合計金額", "ron": "", "tsumo": "", "chip": _yen(chip_total_yen)},
    ]
    return rows, chip_total, chip_total_yen


def _payment_details(user: User) -> tuple[list[dict], int]:
    rows = []
    total = 0

    for hule in user.transaction:
        chip_cnt = int(hule.yen / user.chip_yen_unit) if user.chip_yen_unit > 0 else 0
        rows.append(
            {
                "to": hule.to,
                "type": f"{hule.bonus.value}(ツモ)" if hule.zimo else f"{hule.bonus.value}(ロン)",
                "chip": f"{chip_cnt}枚",
                "yen": _yen(hule.yen),
            }
        )
        total += hule.yen

    if not rows:
        rows.append({"to": "なし", "type": "", "chip": "0枚", "yen": _yen(0)})

    return rows, total


def _opponent_summary(user: User) -> list[dict]:
    rows = []
    for row in user.opponent_summaries:
        rows.append(
            {
                "to": row.to,
                "score_yen": _signed_yen(row.score_yen),
                "receive_chip": f"{row.receive_chip:,}枚",
                "pay_chip": f"{row.pay_chip:,}枚",
                "total_yen": _signed_yen(row.total_yen),
                "score_negative": row.score_yen < 0,
                "total_negative": row.total_yen < 0,
            }
        )

    if not rows:
        rows.append(
            {
                "to": "なし",
                "score_yen": _yen(0),
                "receive_chip": "0枚",
                "pay_chip": "0枚",
                "total_yen": _yen(0),
                "score_negative": False,
                "total_negative": False,
            }
        )

    return rows


def _user_card(user: User) -> dict:
    bonus_rows, _, _ = _bonus_table(user)
    payment_rows, payment_total = _payment_details(user)
    opponent_rows = _opponent_summary(user)

    bonus_net = user.bonus_yen - payment_total
    total_result = user.score_yen + bonus_net
    return {
        "nickname": user.nickname,
        "point": f"{user.point:,}",
        "score": user.score,
        "score_negative": user.score < 0,
        "score_yen": _yen(user.score_yen),
        "bonus_yen": _yen(user.bonus_yen),
        "payment_yen": _yen(payment_total),
        "bonus_net_yen": _signed_yen(bonus_net),
        "result_yen": _signed_yen(total_result),
        "result_negative": total_result < 0,
        "bonus_rows": bonus_rows,
        "payment_rows": payment_rows,
        "opponent_rows": opponent_rows,
    }


def build_result_context(users: list[User]) -> dict:
    return {
        "users": [_user_card(user) for user in users],
    }
