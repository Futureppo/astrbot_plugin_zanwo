from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import aiohttp
import random
import json

positive_responses = [
    "给你点了捏",
    "赞送出去啦！",
    "为你点赞成功！",
    "点了，快查收吧！",
    "赞已送达，请注意查收~"
    ]
        
negative_responses = [
    "赞过啦！！",
    "已经给你点过赞啦！",
    "重复点赞可不行哦~",
    "之前就赞过了呢！"
    ]
        
error_responses = [
    "赞你的时候出错了",
    "哎呀，点赞失败了",
    "点赞好像没成功",
    ]

@register("astrbot_plugin_zanwo", "Futureppo", "发送 赞我 自动点赞", "1.0.0")
class zanwo(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    @filter.regex(r'^赞我$')
    async def like_me(self, event: AstrMessageEvent):
        '''当用户发送 "赞我" 时，对该用户进行尽可能多的点赞，最多50个'''
        sender_id = event.get_sender_id()
        total_likes = 0
        max_attempts = 6  
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://127.0.0.1:3000/send_like"  #127.0.0.1:3000是你的http服务地址，和NapCat的地址一致
                headers = {'Content-Type': 'application/json'}
                
                for attempt in range(max_attempts):
                    payload = json.dumps({"user_id": sender_id, "times": 10})
                    async with session.post(url, data=payload, headers=headers) as response:
                        response_json = await response.json()
                        print(response_json)
                        
                        if response_json['status'] == 'ok':
                            total_likes += 10
                        elif response_json['status'] == 'failed' and response_json['retcode'] == 200:
                            # 赞过啦，停止循环
                            break
                        else:
                            # 用户未开启点赞，点赞失败
                            yield event.plain_result(f"用户隐私设置未开启点赞，点赞失败")
                            return
                
                if total_likes > 0:
                    yield event.plain_result(random.choice(positive_responses))
                else:
                    yield event.plain_result(random.choice(negative_responses))
        except Exception as e:
            yield event.plain_result(random.choice(error_responses))
