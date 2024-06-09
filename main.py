import asyncio
import re
import time

import requests
from satori import WebsocketsInfo, LoginStatus, Event
from satori.client import Account, App

live_room_id = 26887365
channel_ids = ['667345317', '740243150']
live_room_url = f"https://live.bilibili.com/{live_room_id}"
running = False
live_status = False
last_stop_live_time = 0.0

# TODO 需要更新成自己的host和token。
app = App(WebsocketsInfo(host='127.0.0.1', port=5500, token="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"))

def check_need_push():
    global live_status, last_stop_live_time
    need_push = False
    url = f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={live_room_id}'
    data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()['data']
    now_live_status = data['live_status'] == 1
    if live_status and now_live_status:
        print(f"持续直播中{time.time()}")
    elif not live_status and not now_live_status:
        print(f"持续停播中{time.time()}")
    elif live_status and not now_live_status:
        last_stop_live_time = time.time()
        print("停播了")
    elif not live_status and now_live_status:
        print("开播了")
        if time.time() - last_stop_live_time > 60 * 30:
            need_push = True
            print("需要推送消息")
        else:
            print("不需要推送")
    live_status = now_live_status
    return need_push, data['title'], data['user_cover']


async def listen_blive(account: Account):
    while running:
        try:
            need_push, title, keyframe = check_need_push()
            if need_push:
                for channel_id in channel_ids:
                    await account.send_message(channel_id, f'<at type="all"/> 守一开播啦！！！\n今天的标题是: {title}<img src="{keyframe}"/>{live_room_url}')
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(5)
    print("程序停止了")


@app.lifecycle
async def on_state_change(account: Account, state: LoginStatus):
    global running
    running = state == LoginStatus.CONNECT
    if running:
        asyncio.ensure_future(listen_blive(account))


@app.register
async def on_message(account: Account, event: Event):
    if event.channel.id in channel_ids and event.user.id != account.self_id:
        if re.search("^[\\W_]*t[\\W_]*d[\\W_]*$", event.message.content.lower()) is not None:
            await account.message_delete(channel_id=event.channel.id, message_id=event.message.id)
            await account.send_message(event.channel.id, "不准td!")
            await account.guild_member_mute(guild_id=event.guild.id, user_id=event.user.id, duration=1000 * 10)
        if event.message.content == "禁言我一分钟!":
            await account.guild_member_mute(guild_id=event.guild.id, user_id=event.user.id, duration=1000 * 60)


app.run()
