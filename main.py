import json
from pathlib import Path

from aiocqhttp import CQHttp
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
import random
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

# 存储订阅点赞的用户ID的json文件
ZANWO_JSON_FILE = (
    Path("data/plugins_data/astrbot_plugin_zanwo") / "zanwo_subscribe.json"
)


@register(
    "astrbot_plugin_zanwo",
    "Futureppo",
    "发送 赞我 自动点赞",
    "1.0.0",
    "https://github.com/Futureppo/astrbot_plugin_zanwo",
)
class zanwo(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.max_attempts = 5  # 点赞轮数，每轮点赞10次

        self.success_responses: list[str] = config.get("success_responses", [])
        self.error_responses: list[str] = config.get("error_responses", [])

        self.subscribed_users: list[str] = []  # 订阅点赞的用户ID列表
        self._init_subscribed_users()

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

    async def _like(self, client: CQHttp, ids: list[str]) -> list[str]:
        """
        点赞的核心逻辑
        :param client: CQHttp客户端
        :param ids: 用户ID列表
        """
        replys: list[str] = []
        for id in ids:
            total_likes = 0
            for _ in range(self.max_attempts):
                try:
                    await client.send_like(user_id=int(id), times=10)  # 点赞10次
                    total_likes += 10
                except:  # noqa: E722
                    break
            reply = random.choice(
                self.success_responses if total_likes > 0 else self.error_responses
            )
            replys.append(reply)
        return replys

    async def _auto_like(self, client: CQHttp):
        """自动点赞"""
        await self._like(client, self.subscribed_users)

    @filter.regex(r"^赞我$")
    async def like_me(self, event: AiocqhttpMessageEvent):
        """给用户点赞"""
        sender_id = event.get_sender_id()
        client = event.bot
        result = await self._like(client, [sender_id])
        yield event.plain_result(result[0])
        # 触发自动点赞
        await self._auto_like(client)

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

    @filter.command("点赞列表")
    async def like_list(self, event: AiocqhttpMessageEvent):
        """查看订阅点赞的用户ID列表"""
        if not self.subscribed_users:
            yield event.plain_result("当前没有订阅点赞的用户哦~")
            return
        user_list = "\n".join(self.subscribed_users)
        yield event.plain_result(f"当前订阅点赞的用户ID列表：\n{user_list}")
