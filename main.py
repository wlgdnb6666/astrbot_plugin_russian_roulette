import random
import time
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import *

@register("russian_roulette", "YourName", "俄罗斯转盘决斗插件", "1.0.0")
class RussianRoulettePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储运行中的游戏状态: {group_id: {a: challenger, b: target, turn: current_uid, bullets_fired: 0, status: 0-idle, 1-ready, 2-started}}
        self.games = {}

    def get_game(self, group_id):
        if group_id not in self.games:
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
        return self.games[group_id]

    async def update_score(self, user_id, is_win=True):
        key = f"win_{user_id}" if is_win else f"loss_{user_id}"
        current = await self.get_kv_data(key, 0)
        await self.put_kv_data(key, current + 1)

    @filter.command("俄罗斯转盘")
    async def challenge(self, event: AstrMessageEvent):
        """玩法：/俄罗斯转盘 @某人"""
        group_id = event.message_obj.group_id
        if not group_id:
            yield event.plain_result("请在群聊中使用此功能。")
            return

        game = self.get_game(group_id)
        if game["status"] != 0:
            yield event.plain_result("当前群聊已有正在进行的决斗或准备中。")
            return

        # 获取被挑战者
        mentions = [at.qq for at in event.message_obj.message if isinstance(at, At)]
        if not mentions:
            yield event.plain_result("请 @ 一位你想决斗的对象。")
            return
        
        target_qq = mentions[0]
        challenger_qq = event.get_sender_id()

        if target_qq == challenger_qq:
            yield event.plain_result("你不能挑战你自己。")
            return

        game.update({
            "status": 1,
            "a": challenger_qq,
            "b": target_qq,
            "bullets_fired": 0
        })
        
        yield event.chain_result([
            At(qq=target_qq),
            Plain(f" 用户 {event.get_sender_name()} 向你发起挑战！请输入 /接受决斗 开始，或者输入 /拒绝决斗。")
        ])

    @filter.command("接受决斗")
    async def accept(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        
        if game["status"] == 1 and event.get_sender_id() == game["b"]:
            game["status"] = 2
            game["turn"] = game["a"] # 挑战者先开枪
            yield event.plain_result(f"决斗开始！由挑战者先开枪。请双方轮流输入 /开枪")
        elif game["status"] == 1:
            yield event.plain_result("只有被挑战者才能接受决斗。")

    @filter.command("开枪")
    async def fire(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        game = self.get_game(group_id)
        curr_user = event.get_sender_id()

        if game["status"] != 2:
            return
        
        if curr_user != game["turn"]:
            yield event.plain_result("还没轮到你，请不要抢火。")
            return

        game["bullets_fired"] += 1
        fired_count = game["bullets_fired"]
        
        # 模仿源码逻辑
        is_dead = False
        if fired_count >= 6: # 理论上第6枪必响
            is_dead = True
        else:
            # 源码逻辑：q:$随机数 1-[6-%枪%]$，如果 q==1 则响枪
            chance = 6 - fired_count + 1
            if random.randint(1, chance) == 1:
                is_dead = True

        if is_dead:
            winner = game["b"] if curr_user == game["a"] else game["a"]
            loser = curr_user
            
            await self.update_score(winner, True)
            await self.update_score(loser, False)
            
            # 重置游戏
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
            
            yield event.plain_result(f"“砰！”枪响了，{event.get_sender_name()} 倒在了血泊中...\n恭喜胜利者！战绩已更新。")
        else:
            # 切换回合
            game["turn"] = game["b"] if curr_user == game["a"] else game["a"]
            next_name = "对方" # 简单处理
            yield event.plain_result(f"“咔咔...”是空枪。你捡回了一条命。轮到对方开枪了。 (当前已开 {fired_count} 枪)")

    @filter.command("我的战绩")
    async def my_stats(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        wins = await self.get_kv_data(f"win_{user_id}", 0)
        losses = await self.get_kv_data(f"loss_{user_id}", 0)
        yield event.plain_result(f"【俄罗斯转盘战绩】\n用户：{event.get_sender_name()}\n胜利：{wins} 次\n失败：{losses} 次")

    @filter.command("终止决斗")
    async def stop_game(self, event: AstrMessageEvent):
        group_id = event.message_obj.group_id
        if group_id in self.games:
            self.games[group_id] = {"status": 0, "bullets_fired": 0, "a": None, "b": None, "turn": None}
            yield event.plain_result("决斗已强制终止并清空状态。")
