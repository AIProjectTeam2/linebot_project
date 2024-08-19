from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from .models import MedicalRecord
import mysql.connector
import json
import feedparser
from django.conf import settings

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        sydrom = data.get('sydrom')
        email = data.get('email')

        try:
            cursor.execute(
                "INSERT INTO users (username, sydrom, email) VALUES (%s, %s, %s)",
                (username, sydrom, email)
            )
            db.commit()
            return JsonResponse({'message': '用戶資料登錄成功'})
        except mysql.connector.Error as err:
            return JsonResponse({'error': str(err)})

    return HttpResponseBadRequest()
    
@csrf_exempt
def callback(request):
    if request.method == "POST":
        signature = request.META.get('HTTP_X_LINE_SIGNATURE')
        body = request.body.decode('utf-8')

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseBadRequest()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in handler.parser.parse(body, signature):
            if isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    res_text = event.message.text
                    user_id = event.source.user_id

                    if res_text == '@註冊會員':
                        form_text = (
                            "請提供您的資訊，格式如下：\n"
                            "你的名字: \n"
                            "症狀:   \n"
                            "你的信箱: "
                        )
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=form_text))
                    elif res_text.startswith("你的名字:"):
                        try:
                            # 提取註冊信息
                            user_info = {}

                            # 使用換行符分隔每一段信息
                            parts = res_text.splitlines()

                            for part in parts:
                                if ':' in part:
                                    key, value = part.split(':', 1)
                                    user_info[key.strip()] = value.strip()

                            if '你的名字' in user_info and '症狀' in user_info and '你的信箱' in user_info:
                                username = user_info['你的名字']
                                sydrom = user_info['症狀']
                                email = user_info['你的信箱']

                                # 檢查並保存資料
                                cursor.execute(
                                    "INSERT INTO users (username, sydrom, email) VALUES (%s, %s, %s)",
                                    (username, sydrom, email)
                                )
                                db.commit()
                                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="您的資料已成功儲存！"))
                            else:
                                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請提供正確的格式：\n你的名字: 路人丙\n症狀: 腿軟\n你的信箱: a123456@gmail.com"))
                        except Exception as e:
                            print(f'Error occurred: {e}')
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤，請稍後再試。"))
                    elif res_text == "@附近醫療機構":
                        google_maps_url = "https://www.google.com/maps/search/?api=1&query=hospitals&query"
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"請點擊以下連結來查看附近的醫療機構：\n{google_maps_url}"))
                    elif res_text == "@衛生署公告":
                        feed_url = "https://www.mohw.gov.tw/rss-16-1.html"
                        feed = feedparser.parse(feed_url)
                        announcements = []
                        for entry in feed.entries[:5]:  # 只取前5則公告
                            title = entry.title
                            link = entry.link
                            announcements.append(f"{title}\n{link}")
                            announcement_text = "\n\n".join(announcements)
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=announcement_text))
                    else:
                        # 將症状描述存到資料庫
                        record = MedicalRecord(symptom_description=res_text)
                        record.save()

                        # 回復用戶
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="您的症状已經存入資料庫，謝謝！"))
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

def home(request):
    return HttpResponse("Welcome to the home page!")

def sendMsg(request, uid, msg):
    line_bot_api.push_message(uid, TextSendMessage(text=msg))
    return HttpResponse()
def home(request):
    return HttpResponse("Welcome to the home page!")