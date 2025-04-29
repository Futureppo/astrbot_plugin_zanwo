import random
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from aiocqhttp import CQHttp
import aiocqhttp
from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.filter.permission import PermissionType

# 存储订阅点赞的用户ID的json文件
ZANWO_JSON_FILE = (
    Path("data/plugins_data/astrbot_plugin_zanwo") / "zanwo_subscribe.json"
)

success_responses = [
    "👍{total_likes}"
    "赞了赞了",
    "点赞成功！",
    "给你点了{total_likes}个赞",
    "赞送出去啦！一共{total_likes}个哦！",
    "为你点赞成功！总共{total_likes}个！",
    "点了{total_likes}个，快查收吧！",
    "赞已送达，请注意查收~ 一共{total_likes}个！",
    "给你点了{total_likes}个赞，记得回赞我哟！"
    "赞了{total_likes}次，看看收到没？"
    "点了{total_likes}赞，没收到可能是我被风控了",
]

limit_responses = [
    "今天给你的赞已达上限",
    "赞了那么多还不够吗？",
    "别太贪心哟~",
    "今天赞过啦！",
    "今天已经赞过啦~",
    "已经赞过啦~",
    "还想要赞？不给了！",
    "已经赞过啦，别再点啦！",
]


@register(
    "astrbot_plugin_zanwo",
    "Futureppo",
    "发送 赞我 自动点赞",
    "1.0.7",
    "https://github.com/Futureppo/astrbot_plugin_zanwo",
)
class zanwo(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.success_responses: list[str] = success_responses

        # 群聊白名单
        self.enable_white_list_groups: bool = config.get(
            "enable_white_list_groups", False
        )
        self.white_list_groups: list[str] = config.get("white_list_groups", [])

        self.subscribed_users: list[str] = []  # 订阅点赞的用户ID列表
        self._init_subscribed_users()
        self.today_liked: dict[str, Any] = {
            "date": None,
            "status": False,
        }  # 存储今日点赞状态（每次重启bot就会被刷新，后续考虑改为持久化存储）

    def _init_subscribed_users(self):
        """初始化订阅点赞的用户ID列表"""
        if ZANWO_JSON_FILE.exists():
            with open(ZANWO_JSON_FILE, "r", encoding="utf-8") as f:
                try:
                    self.subscribed_users = json.load(f)
                except json.JSONDecodeError:
                    self.subscribed_users = []
        else:
            ZANWO_JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
            ZANWO_JSON_FILE.touch()
            with open(ZANWO_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(self.subscribed_users, f)

    def _save_subscribed_users(self):
        """同步订阅点赞的用户ID列表到JSON文件"""
        with open(ZANWO_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(self.subscribed_users, f)

    async def _like(self, client: CQHttp, ids: list[str]) -> str:
        """
        点赞的核心逻辑
        :param client: CQHttp客户端
        :param ids: 用户ID列表
        """
        for id in ids:
            total_likes = 0
            for _ in range(5):
                try:
                    await client.send_like(user_id=int(id), times=10)  # 点赞10次
                    total_likes += 10
                except aiocqhttp.exceptions.ActionFailed as e:
                    error_message = str(e)
                    if "已达" in error_message:
                        error_reply = random.choice(limit_responses)
                    elif "权限" in error_message:
                        error_reply = "你设了权限不许陌生人赞你"
                    else:
                        error_reply = "不知道啥原因赞不了你"
                    break
            if total_likes > 0:
                reply = random.choice(self.success_responses).format(total_likes=total_likes)
            else:
                reply = error_reply

        return reply

    @filter.regex(r"^赞我$")
    async def like_me(self, event: AiocqhttpMessageEvent):
        """给用户点赞"""
        # 获取群组id
        group_id = event.get_group_id()

        # 检查群组id是否在白名单中, 若没填写白名单则不检查
        if self.enable_white_list_groups and len(self.white_list_groups) != 0:
            # 检查群组id是否在白名单中
            if not self.check_group_id(group_id):
                logger.info(f"群组 {group_id} 不在白名单中")
                return
        sender_id = event.get_sender_id()
        client = event.bot
        result = await self._like(client, [sender_id])
        yield event.plain_result(result)

        # 触发自动点赞
        if (
            self.today_liked["date"] is None
            or self.today_liked["date"] != datetime.now().date()
        ):
            if not self.today_liked["status"]:
                await self._like(client, self.subscribed_users)
                self.today_liked["status"] = True
                self.today_liked["date"] = datetime.now().date()

    @filter.command("订阅点赞")
    async def subscribe_like(self, event: AiocqhttpMessageEvent):
        """订阅点赞"""
        sender_id = event.get_sender_id()
        if sender_id in self.subscribed_users:
            yield event.plain_result("你已经订阅点赞了哦~")
            return
        self.subscribed_users.append(sender_id)
        self._save_subscribed_users()
        yield event.plain_result("订阅成功！我将每天自动给你点赞~")

    @filter.command("取消订阅点赞")
    async def unsubscribe_like(self, event: AiocqhttpMessageEvent):
        """取消订阅点赞"""
        sender_id = event.get_sender_id()
        if sender_id not in self.subscribed_users:
            yield event.plain_result("你还没有订阅点赞哦~")
            return
        self.subscribed_users.remove(sender_id)
        self._save_subscribed_users()
        yield event.plain_result("取消订阅成功！我将不再自动给你点赞~")

    @filter.command("订阅点赞列表")
    async def like_list(self, event: AiocqhttpMessageEvent):
        """查看订阅点赞的用户ID列表"""

        if not self.subscribed_users:
            yield event.plain_result("当前没有订阅点赞的用户哦~")
            return
        users_str = "\n".join(self.subscribed_users).strip()
        yield event.plain_result(f"当前订阅点赞的用户ID列表：\n{users_str}")

    def check_group_id(self, group_id: str) -> bool:
        """检查群号是否在白名单中

        Args:
            group_id (str): 群号

        Returns:
            bool: 是否在白名单中
        """
        if group_id in self.white_list_groups:
            return True
        return False

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("谁赞了bot")
    async def get_profile_like(self, event: AiocqhttpMessageEvent):
        """获取bot自身点赞列表"""
        client = event.bot
        data = await client.get_profile_like()
        reply = ""
        user_infos = data.get("favoriteInfo", {}).get("userInfos", [])
        for user in user_infos:
            if (
                "nick" in user
                and user["nick"]
                and "count" in user
                and user["count"] > 0
            ):
                reply += f"\n【{user['nick']}】赞了我{user['count']}次"
        if not reply:
            reply = "暂无有效的点赞信息"
        url = await self.text_to_image(reply)
        yield event.image_result(url)
