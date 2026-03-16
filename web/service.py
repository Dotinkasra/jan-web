from module.jan import Jan
from module.jansoul import Jansoul


def analyze_paifu(
    paifu_json: dict,
    samma: bool = False,
    rate: int = 50,
    chip: int = 500,
    uma_1: int = 10,
    uma_2: int = 20,
    oka_1: int = 25000,
    oka_2: int = 30000,
    all_star_chip: int = 5,
    yiman_tumo_chip: int = 5,
    yiman_chip: int = 10,
):
    jan = Jan(
        samma=samma,
        rate=rate,
        chip=chip,
        uma_1=uma_1,
        uma_2=uma_2,
        oka_1=oka_1,
        oka_2=oka_2,
        all_star_chip=all_star_chip,
        yiman_tumo_chip=yiman_tumo_chip,
        yiman_chip=yiman_chip,
    )

    jansoul = Jansoul(paifu=paifu_json, samma=samma)
    jan.users = sorted(jansoul.get_users(), key=lambda x: x.point, reverse=True)
    jan._count()
    return jan.users
