import json

from module.data import Bonus, Hule, User


class Jansoul:
    RATE = 500

    def __init__(self, paifu: dict, samma: bool = False):
        self.paifu = paifu
        self.users = self._create_users(samma=samma)
        self._calc_bonus()

    def get_users(self):
        return self.users

    def _create_users(self, samma: bool) -> list[User]:
        """牌譜からユーザーを作成する

        Parameters
        ----------
        samma bool: サンマの場合はTrue, ヨンマの場合はFalse

        Returns
        -------
        list[User]: 取得したUserのリスト

        """
        users = []
        seats = [0, 1, 2] if samma else [0, 1, 2, 3]
        for u in self.paifu["head"]["accounts"]:
            user = User(seat=u["seat"], nickname=u["nickname"])
            seats.remove(u["seat"])
            users.append(user)
        if len(seats) > 0:
            for i, seat in enumerate(seats):
                users.append(User(seat=seat, nickname=f"CPU{i+1}"))

        point_dict = {result["seat"]: result["part_point_1"] for result in self.paifu["head"]["result"]["players"]}
        for user in users:
            user.point = point_dict[user.seat]

        return users

    def _get_user_with_seat(self, seat: int) -> User | None:
        """シート番号のUserを取得する

        Parameters
        ----------
        seat int: 取得したいシート番号

        Returns
        -------
        User: シート番号に着席しているUser

        """
        for u in self.users:
            if u.seat == seat:
                return u

    def _get_recordHule(self) -> list:
        """和了のデータを抽出する

        Returns
        -------
        list: 和了のデータ

        """
        filtered_actions = [
            action
            for action in self.paifu["data"]["data"]["actions"]
            if action["type"] == 1 and action["result"]["name"] == ".lq.RecordHule"
        ]
        return filtered_actions

    def _calc_bonus(self):
        def count_ippatsu(hule: dict) -> int:
            for fans in hule["fans"]:
                if fans["id"] == 30:
                    return fans["val"]
            return 0

        def count_aka_dora(hule: dict) -> int:
            for fans in hule["fans"]:
                if fans["id"] == 32:
                    return fans["val"]
            return 0

        def count_allstar(hule: dict) -> int:
            for fans in hule["fans"]:
                if fans["id"] == 32:
                    if fans["val"] == 3:
                        return 1
            return 0

        def count_yiman(hule: dict) -> int:
            if hule["yiman"]:
                return 1
            return 0

        def count_ura_dora(hule: dict) -> int:
            for fans in hule["fans"]:
                if fans["id"] == 33:
                    return fans["val"]
            return 0

        def fangchong_user(delta_scores: list[int]) -> User | None:
            for i, score in enumerate(delta_scores):
                if score < 0:
                    return self._get_user_with_seat(i)
            return None

        def tobi_users(scores: list[int]) -> list[User] | None:
            users = []
            for i, score in enumerate(scores):
                if score < 0:
                    users.append(self._get_user_with_seat(i))

            if len(users) == 0:
                return None

            return users

        def count(hule: dict, fangchong: User | None = None, tobi: list[User] | None = None):
            winner = self._get_user_with_seat(hule["seat"])
            ippatsu = count_ippatsu(hule)
            ura_dora = count_ura_dora(hule)
            aka_dora = count_aka_dora(hule)
            yiman = count_yiman(hule)
            allstar = count_allstar(hule)

            if winner is None:
                return

            # 祝儀役がなくてもトビが発生しているケースは処理を継続する
            if ippatsu + ura_dora + aka_dora + yiman + allstar == 0 and tobi is None:
                return

            if fangchong is None:  # ツモ
                winner.ippatsu_tumo += ippatsu
                winner.ura_dora_tumo += ura_dora
                winner.aka_dora_tumo += aka_dora
                winner.yiman_tumo += yiman
                winner.allstar_tumo += allstar

                for user in self.users:
                    if not user.seat == hule["seat"]:
                        if ippatsu > 0:
                            user.transaction.append(
                                Hule(to=winner.nickname, cnt=ippatsu, bonus=Bonus.ippatsu, zimo=True)
                            )
                        if ura_dora > 0:
                            user.transaction.append(
                                Hule(to=winner.nickname, cnt=ura_dora, bonus=Bonus.ura_dora, zimo=True)
                            )
                        if aka_dora > 0:
                            user.transaction.append(
                                Hule(to=winner.nickname, cnt=aka_dora, bonus=Bonus.aka_dora, zimo=True)
                            )
                        if yiman > 0:
                            user.transaction.append(Hule(to=winner.nickname, cnt=yiman, bonus=Bonus.yiman, zimo=True))
                        if allstar > 0:
                            user.transaction.append(
                                Hule(to=winner.nickname, cnt=allstar, bonus=Bonus.allstar, zimo=True)
                            )

            else:  # ロン
                winner.ippatsu += ippatsu
                winner.ura_dora += ura_dora
                winner.aka_dora += aka_dora
                winner.yiman += yiman
                winner.allstar += allstar
                if ippatsu > 0:
                    fangchong.transaction.append(Hule(to=winner.nickname, cnt=ippatsu, bonus=Bonus.ippatsu, zimo=False))
                if ura_dora > 0:
                    fangchong.transaction.append(
                        Hule(to=winner.nickname, cnt=ura_dora, bonus=Bonus.ura_dora, zimo=False)
                    )
                if aka_dora > 0:
                    fangchong.transaction.append(
                        Hule(to=winner.nickname, cnt=aka_dora, bonus=Bonus.aka_dora, zimo=False)
                    )
                if yiman > 0:
                    fangchong.transaction.append(Hule(to=winner.nickname, cnt=yiman, bonus=Bonus.yiman, zimo=False))
                if allstar > 0:
                    fangchong.transaction.append(Hule(to=winner.nickname, cnt=allstar, bonus=Bonus.allstar, zimo=False))

            if tobi is not None:
                if fangchong is None:  # ツモ: 飛んだプレイヤーから1枚ずつ
                    winner.tobi += len(tobi)
                    winner.tobi_tumo += len(tobi)
                    for user in tobi:
                        user.transaction.append(Hule(to=winner.nickname, cnt=1, bonus=Bonus.tobi, zimo=True))
                else:  # ロン: ロン対象者から1枚
                    winner.tobi += 1
                    winner.tobi_ron += 1
                    fangchong.transaction.append(Hule(to=winner.nickname, cnt=1, bonus=Bonus.tobi, zimo=False))

        recordHule = self._get_recordHule()
        for record in recordHule:
            for hule in record["result"]["data"]["hules"]:
                user = None if hule["zimo"] == True else fangchong_user(record["result"]["data"]["delta_scores"])
                tobi = tobi_users(record["result"]["data"]["scores"])
                count(hule, user, tobi)
