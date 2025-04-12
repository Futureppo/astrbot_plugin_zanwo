
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
import random
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

positive_responses = [
    "给你点了捏",
    "赞送出去啦！",
    "为你点赞成功！",
    "点了，快查收吧！",
    "赞已送达，请注意查收~",
]

negative_responses = [
    "赞过啦！！",
    "已经给你点过赞啦！",
    "重复点赞可不行哦~",
    "之前就赞过了呢！",
]

error_responses = [
    "赞你的时候出错了",
    "哎呀，点赞失败了",
    "点赞好像没成功",
]


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
        self.positive_responses: list[str] = config.get(
            "positive_responses", positive_responses
        )  # 点赞成功的回复
        self.error_responses: list[str] = config.get(
            "error_responses", error_responses
        )  # 点赞失败的回复


    @filter.regex(r"^赞我$")
    async def like_me(self, event: AiocqhttpMessageEvent):
        """当用户发送 "赞我" 时，对该用户进行尽可能多的点赞，最多50个"""
        sender_id = event.get_sender_id()
        total_likes = 0
        max_attempts = 5
        client = event.bot
        for _ in range(max_attempts):
            try:
                await client.send_like(user_id=int(sender_id), times=10)  # 点赞10次
                total_likes += 10
            except:  # noqa: E722
                break

        reply = random.choice(
            self.positive_responses if total_likes > 0 else self.error_responses
        )
        yield event.plain_result(reply)
