import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import *

@register("russian_roulette", "青禾遇海", "俄罗斯转盘决斗插件", "1.2.1")
class RussianRoulettePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.games = {}
        
        # --- 整合青禾遇海提供的 100 条文案库 ---
        self.MISS_MESSAGES = [
            "☁️ “咔哒——” 死神在门外抽了根烟，决定再等等。",
            "☁️ 弹巢转了一圈，子弹在隔壁格子里打了个盹。",
            "☁️ 运气这东西，今天居然站在你这边。",
            "☁️ 枪响了？不，那只是你的心跳声。",
            "☁️ 上帝今天休假，撒旦也没上班。",
            "☁️ 这一发是空的，但你的冷汗是真的。",
            "☁️ 子弹说：下次一定。",
            "☁️ 你活下来了，虽然腿还在抖。",
            "☁️ 命运之轮停在了'再给你一次机会'。",
            "☁️ “咔”——这是世界上最动听的声音。",
            "☁️ 死神摆摆手：这一局不算。",
            "☁️ 弹巢里传来一声叹息，子弹失约了。",
            "☁️ 你赢了，虽然赢的方式有点狼狈。",
            "☁️ 枪管里吹出一缕青烟，像是嘲笑。",
            "☁️ 这一枪打在了空气上，空气没意见。",
            "☁️ 阎王爷翻了翻生死簿：名字写错了。",
            "☁️ 你刚才是不是尿裤子了？没关系，活着就好。",
            "☁️ 子弹在弹巢里迷路了。",
            "☁️ “咔”——命运给你发了一张续费卡。",
            "☁️ 这一发要是实的，你现在已经在排队喝汤了。",
            "☁️ 枪说：我开玩笑的。",
            "☁️ 你今天的幸运值居然还没用完。",
            "☁️ 死神打了个哈欠：再玩两轮。",
            "☁️ 弹巢转动时，子弹睡着了。",
            "☁️ 这一枪打出去的是寂寞。",
            "☁️ 你活下来了，但头发好像白了几根。",
            "☁️ “咔哒”——这是死神的恶作剧。",
            "☁️ 子弹今天不想上班。",
            "☁️ 你的命硬得连子弹都摇头。",
            "☁️ 这一发是空的，下一发可不一定。",
            "☁️ 枪管里传来一声轻笑。",
            "☁️ 你刚才闭眼了？睁开眼吧，还活着。",
            "☁️ 命运骰子掷出了'大赦'。",
            "☁️ 这一枪打在了虚无里，虚无没还手。",
            "☁️ 死神收了镰刀：今天 quota 满了。",
            "☁️ 弹巢里的子弹在倒数第二格停下了。",
            "☁️ 你闻到了火药味，但没看到光。",
            "☁️ “咔”——这是给你的警告，不是判决。",
            "☁️ 子弹在弹巢里翻了个身，继续睡。",
            "☁️ 这一枪要是响了，故事就到此为止了。",
            "☁️ 你的心跳声比枪声还大。",
            "☁️ 死神在门外看了看门牌号：走错了。",
            "☁️ 弹巢转到了'谢谢惠顾'。",
            "☁️ 这一发是空的，但你已经死过一次了。",
            "☁️ 枪说：再给你一次重新做人的机会。",
            "☁️ 你今天的命是借来的，记得还。",
            "☁️ “咔哒”——这是命运按下的暂停键。",
            "☁️ 子弹在弹巢里数着格子：一、二……还没轮到我。",
            "☁️ 你活下来了，虽然不知道是该哭还是该笑。",
            "☁️ 这一枪打在了昨天，昨天已经死了。"
        ]

        self.HIT_MESSAGES = [
            "💥 你的脑浆为这把手枪增添了新的涂装。",
            "💥 恭喜你，终于不用还花呗了。",
            "💥 这一枪，打断了你所有的Flag。",
            "💥 阎王要你三更死，你偏要两更来报到。",
            "💥 你的墓志铭可以写：死于自信。",
            "💥 这一发子弹等了你很久，它说 worth it。",
            "💥 你证明了'下次一定'有时候没有下次。",
            "💥 你的运气余额已清零，且无法充值。",
            "💥 这一枪很公平，毕竟你先动的手。",
            "💥 你终于成为了传说中的'一枪超人'。",
            "💥 命运的开枪从不提前通知。",
            "💥 你赌赢了九十九次，却输在了第一百次。",
            "💥 这声枪响，是你生命的最后一个标点。",
            "💥 轮盘停止转动时，你的心跳也停止了。",
            "💥 你以为是游戏，子弹却认真了。",
            "💥 这把手枪没有空枪，只有早到或迟到的子弹。",
            "💥 你的故事到此为止，没有续集。",
            "💥 死亡从不爽约，它只是喜欢迟到。",
            "💥 你扣下扳机的那一刻，结局已经写好。",
            "💥 硝烟散去，只剩一具不相信命运的尸体。",
            "💥 菜，就多练——可惜你没机会了。",
            "💥 这一枪，是系统给你的特别奖励。",
            "💥 你的复活币呢？哦，忘了这是硬核模式。",
            "💥 这一枪打出了暴击，可惜是你自己。",
            "💥 你刚才的表情很帅，现在更'帅'了。",
            "💥 恭喜解锁成就：自掘坟墓。",
            "💥 这一枪叫'晚安玛卡巴卡'，睡吧。",
            "💥 你的KDA从此定格，且分母+1。",
            "💥 这一枪是友情赠送，不用谢。",
            "💥 你刚才说'我不信邪'？邪说：'我来了。'",
            "💥 鲜血在地板上画出了最后一朵玫瑰。",
            "💥 你的灵魂比子弹更先离开了身体。",
            "💥 这声枪响，是为你奏响的安魂曲。",
            "💥 你倒在了自己编织的赌局里。",
            "💥 生命是一场豪赌，而你all in了命。",
            "💥 这把手枪吞掉了你所有的明天。",
            "💥 你的最后一秒，比想象中更安静。",
            "💥 硝烟是你留给世界的最后一句诗。",
            "💥 你赌的是运气，输的是余生。",
            "💥 这一枪，把'如果'变成了'没有如果'。",
            "💥 出局。",
            "💥 游戏结束，玩家一已断开连接。",
            "💥 确认击杀。",
            "💥 目标沉默。",
            "💥 生命体征：无。",
            "💥 你输了，字面意义上的。",
            "💥 这一枪没有回头路。",
            "💥 轮到你退场了。",
            "💥 子弹完成了它的使命。",
            "💥 这里多了一具不信邪的尸体。"
        ]

    def get_game(self, group_id):
        if group_id not in self.games:
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None, "mode": "normal"}
        return self.games[group_id]

    async def update_score(self, user_id, is_win=True):
        key = f"win_{user_id}" if is_win else f"loss_{user_id}"
        current = await self.get_kv_data(key, 0)
        await self.put_kv_data(key, current + 1)

    @filter.command("决斗")
    async def challenge(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        if not group_id:
            yield event.plain_result("❌ 请在群聊中使用此功能。")
            return

        game = self.get_game(group_id)
        if game["status"] != 0:
            yield event.plain_result("⚠️ 当前群聊已有正在进行的决斗。")
            return

        # 识别模式
        mode = "normal"
        if "双弹" in event.message_str: mode = "double"
        elif "自杀" in event.message_str: mode = "suicide"

        challenger_qq = str(event.get_sender_id())
        
        if mode == "suicide":
            game.update({"status": 2, "a": challenger_qq, "b": "SYSTEM", "turn": challenger_qq, "mode": "suicide", "bullets_fired": 0})
            yield event.plain_result("💀 你开启了【自杀模式】。没人会阻止你，请发送【/开枪】。")
            return

        mentions = [at.qq for at in event.message_obj.message if isinstance(at, At)]
        if not mentions:
            yield event.plain_result("❓ 请 @ 一位对手，或输入【/决斗 自杀】。")
            return
        
        target_qq = str(mentions[0])
        if target_qq == challenger_qq:
            yield event.plain_result("🤕 想自杀请使用【/决斗 自杀】。")
            return

        game.update({"status": 1, "a": challenger_qq, "b": target_qq, "bullets_fired": 0, "mode": mode})
        mode_desc = "【双弹模式】" if mode == "double" else "【普通模式】"
        yield event.chain_result([
            At(qq=target_qq),
            Plain(f" 用户 {event.get_sender_name()} 向你发起 {mode_desc} 决斗！\n回复【/接受决斗】或【/拒绝决斗】。")
        ])
        return

    @filter.command("接受决斗")
    async def accept(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        if game["status"] == 1 and str(event.get_sender_id()) == str(game["b"]):
            game["status"] = 2
            game["turn"] = game["a"]
            yield event.plain_result("🔫 决斗开始！请双方轮流发送【/开枪】。")
        return

    @filter.command("拒绝决斗")
    async def decline(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        if game["status"] == 1 and str(event.get_sender_id()) == str(game["b"]):
            self.games[group_id] = {"status": 0}
            yield event.plain_result("🏳️ 对方拒绝了你的挑战。")
        return

    @filter.command("认输")
    async def give_up(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        curr_user = str(event.get_sender_id())
        if game["status"] == 2 and curr_user in [game["a"], game["b"]]:
            winner_id = game["b"] if curr_user == game["a"] else game["a"]
            await self.update_score(winner_id, True)
            await self.update_score(curr_user, False)
            self.games[group_id] = {"status": 0}
            yield event.plain_result(f"🏳️ {event.get_sender_name()} 认输了，这并不丢人，只是活着比较重要。")
        return

    @filter.command("开枪")
    async def fire(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        curr_user = str(event.get_sender_id())

        if game["status"] != 2 or curr_user != str(game["turn"]): return

        game["bullets_fired"] += 1
        cnt = game["bullets_fired"]
        bullets_in_chamber = 2 if game["mode"] == "double" else 1
        
        # 概率计算
        remaining_slots = 7 - cnt
        current_prob = (bullets_in_chamber / remaining_slots * 100) if remaining_slots > 0 else 100.0
        
        is_dead = False
        if random.randint(1, remaining_slots + 1) <= bullets_in_chamber:
            is_dead = True

        if is_dead:
            if game["mode"] != "suicide":
                winner_id = game["b"] if curr_user == game["a"] else game["a"]
                await self.update_score(winner_id, True)
            await self.update_score(curr_user, False)
            self.games[group_id] = {"status": 0}
            yield event.plain_result(f"{random.choice(self.HIT_MESSAGES)}\n{event.get_sender_name()} 倒下了。")
        else:
            # 计算下一发的概率展示给用户
            next_slots = 7 - (cnt + 1)
            next_prob = (bullets_in_chamber / next_slots * 100) if next_slots > 0 else 100.0
            
            if game["mode"] != "suicide":
                game["turn"] = game["b"] if curr_user == game["a"] else game["a"]
            
            yield event.plain_result(f"{random.choice(self.MISS_MESSAGES)}\n(当前命中概率：{current_prob:.1f}% | 下一发：{next_prob:.1f}%)")
        return

    @filter.command("我的战绩")
    async def my_stats(self, event: AstrMessageEvent):
        uid = str(event.get_sender_id())
        w = await self.get_kv_data(f"win_{uid}", 0)
        l = await self.get_kv_data(f"loss_{uid}", 0)
        total = w + l
        rate = (w / total * 100) if total > 0 else 0
        yield event.plain_result(f"📊 【个人战绩】\n用户：{event.get_sender_name()}\n胜场：{w}\n败场：{l}\n胜率：{rate:.1f}%")
        return

    @filter.command("终止决斗")
    async def stop_game(self, event: AstrMessageEvent):
        self.games[event.message_obj.group_id] = {"status": 0}
        yield event.plain_result("🛑 决斗已重置。")
        return
