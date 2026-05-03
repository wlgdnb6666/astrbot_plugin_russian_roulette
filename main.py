import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import *

@register("russian_roulette", "YourName", "俄罗斯转盘决斗插件", "1.1.1")
class RussianRoulettePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储运行中的游戏状态: {group_id: {a: 挑战者ID, b: 被挑战者ID, turn: 当前回合ID, bullets_fired: 已开枪数, status: 0-空闲, 1-准备, 2-进行中}}
        self.games = {}

    def get_game(self, group_id):
        if group_id not in self.games:
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
        return self.games[group_id]

    async def update_score(self, user_id, is_win=True):
        """更新 KV 存储中的胜负记录"""
        key = f"win_{user_id}" if is_win else f"loss_{user_id}"
        current = await self.get_kv_data(key, 0)
        await self.put_kv_data(key, current + 1)

    @filter.command("俄罗斯转盘")
    async def challenge(self, event: AstrMessageEvent):
        """发起挑战: /俄罗斯转盘 @某人"""
        group_id = event.message_obj.group_id
        if not group_id:
            yield event.plain_result("❌ 请在群聊中使用此功能。")
            return

        game = self.get_game(group_id)
        if game["status"] != 0:
            yield event.plain_result("⚠️ 当前群聊已有正在进行的决斗。")
            return

        # 获取被挑战者 (At 组件)
        mentions = [at.qq for at in event.message_obj.message if isinstance(at, At)]
        if not mentions:
            yield event.plain_result("❓ 请 @ 一位你想挑战的对象。")
            return
        
        # 统一转为字符串处理，防止 int 与 str 匹配失败
        target_qq = str(mentions[0])
        challenger_qq = str(event.get_sender_id())

        if target_qq == challenger_qq:
            yield event.plain_result("🤕 你不能挑战你自己。")
            return

        game.update({
            "status": 1,
            "a": challenger_qq,
            "b": target_qq,
            "bullets_fired": 0
        })
        
        yield event.chain_result([
            At(qq=target_qq),
            Plain(f" 用户 {event.get_sender_name()} 向你发起挑战！\n回复【/接受决斗】开始，或回复【/拒绝决斗】。")
        ])

    @filter.command("接受决斗")
    async def accept(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        sender_id = str(event.get_sender_id())
        
        # 校验：状态为准备中，且发送者是被挑战者
        if game["status"] == 1 and sender_id == str(game["b"]):
            game["status"] = 2
            game["turn"] = game["a"] # 挑战者先开枪
            yield event.plain_result("🔫 决斗开始！由挑战者先开枪。请双方轮流发送【/开枪】")
        elif game["status"] == 1:
            yield event.plain_result("🚫 只有被挑战者才能接受决斗。")

    @filter.command("拒绝决斗")
    async def decline(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        sender_id = str(event.get_sender_id())

        if game["status"] == 1 and sender_id == str(game["b"]):
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
            yield event.plain_result("🏳️ 对方拒绝了你的挑战，决斗取消。")

    @filter.command("开枪")
    async def fire(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        curr_user = str(event.get_sender_id())

        if game["status"] != 2: return
        if curr_user != str(game["turn"]):
            yield event.plain_result("💢 还没到你的回合，不要抢火！")
            return

        game["bullets_fired"] += 1
        fired_count = game["bullets_fired"]
        
        is_dead = False
        if fired_count >= 6: # 第6枪必响
            is_dead = True
        else:
            # 模拟 QRSpeed 逻辑：q:$随机数 1-[6-%枪%]$
            # 随着已开枪数增加，范围缩小，概率变大
            chance_range = 6 - (fired_count - 1)
            if random.randint(1, chance_range) == 1:
                is_dead = True

        if is_dead:
            winner = str(game["b"]) if curr_user == str(game["a"]) else str(game["a"])
            loser = curr_user
            await self.update_score(winner, True)
            await self.update_score(loser, False)
            
            # 清空该群游戏状态
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
            yield event.plain_result(f"💥 “砰！”枪响了...\n{event.get_sender_name()} 倒在了血泊中。决斗结束！")
        else:
            # 切换回合
            game["turn"] = game["b"] if curr_user == str(game["a"]) else game["a"]
            yield event.plain_result(f"☁️ “咔嚓...”是空枪。你捡回一条命。轮到对方了。\n(当前已试探 {fired_count}/6 次)")

    @filter.command("我的战绩")
    async def my_stats(self, event: AstrMessageEvent):
        user_id = str(event.get_sender_id())
        wins = await self.get_kv_data(f"win_{user_id}", 0)
        losses = await self.get_kv_data(f"loss_{user_id}", 0)
        total = wins + losses
        rate = (wins / total * 100) if total > 0 else 0
        yield event.plain_result(f"📊 【转盘战绩】\n用户：{event.get_sender_name()}\n胜场：{wins}\n败场：{losses}\n胜率：{rate:.1f}%")

    @filter.command("终止决斗")
    async def stop_game(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        if group_id in self.games:
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
            yield event.plain_result("🛑 决斗已重置。")
