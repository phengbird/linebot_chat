# DataBase
import pymysql

import json
import apiai
from flask import Flask, request, abort

# Line API
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError


username = 'root'
password = 'peng1234'
databaseName = 'ChatBot'
line_bot_api = LineBotApi('2Z1HOdVWmnU4/ODxlT/tViRPihmb4LzTOn2M+VuW16RZUTOMQ8LTXbBbinNSE+pdrVP3FV5NWmkl7+EIw0EWXcnAQsKsxs4IVLZQL8q9ZnSIv9hDYCNX6wuP0kvGHzNzqh0HdhDzKAgJ6htqnFKn9AdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler("05a10ac08da7015e077a0c40cb75771a")
# line_bot_api = LineBotApi(
#     'Zw/UeT9vgPprJsdI7GFUplnXF2n0W0CkQa+/UFs2t9rStFgpow/jrcZ0u6N9jwwGbU5xSBEfhWs2ExxqKY/FwEcaGByFYGWt9U4zMNLoLBLQLmff6ZhZCkMmmaxZUkl3mxe1dK74r6ejmlBvd6l7cQdB04t89/1O/w1cDnyilFU=')
# handler = WebhookHandler("b91b2275de12e3cb69be56c3f29ac11b")

# 程式要列出資料
def res_out(command,flag = None):

    db = pymysql.connect('localhost', username, password, databaseName)

    cursor = db.cursor()
    cursor.execute(command)
    result = cursor.fetchall()
    if flag != None:
        titles = ['編號', "名稱", "原價","折扣價","特價開始","特價結束"]
    else:
        titles = ['編號', "名稱", "價錢", "CPU", "GPU", "RAM", "硬碟", "保固", "image", "品牌"]
    data = ""
    print(command)
    if not result:
        line_bot_api.push_message(userId, TextSendMessage(text="沒有資料"))
    else:
        for row in result:
            for col, title in zip(row, titles):
                if col != None:
                    data += title + " : " + str(col) + "\n"
            line_bot_api.push_message(userId, TextSendMessage(text=data))
            data = ""
    db.commit()
    cursor.close()
    db.close()

# 程式只執行指令
def res_alter_out(command,flag=None):
    db = pymysql.connect('localhost', username, password, databaseName)

    cursor = db.cursor()
    try:
        cursor.execute(command)
        print(command)
        if(flag == None):  # 避免判斷使用者 ID 時跑出
             line_bot_api.push_message(userId, TextSendMessage(text="已完成命令"))
    except Exception :
        line_bot_api.push_message(userId, TextSendMessage(text="資料重複"))
    db.commit()
    cursor.close()
    db.close()

#找where
def do_where(keyword,where):
    tmp = ''
    for key,value in keyword.items():
        if value != '':
            # 條件判斷
            if key == "laptopID":
                tmp += 'lapID Like "%' + value + '%"'
            elif key == "lapNO":
                tmp += ' lapNo = ' + str(int(value["number"]))
            elif key == "Warranty" :
                tmp += 'lapWarranty Like "%' + value + '%"'
            elif key == "number1":
                tmp += 'lapPrice between ' + str(keyword["number"]) + ' and ' + str(value)
                keyword["number"] = ''
            elif key == "number" :
                if keyword["number1"] != '':
                    tmp += 'lapPrice between ' + str(value) + ' and ' + str(keyword["number1"])
                    keyword["number1"] = ''
                if "小於" in keyword["valueCompare"]:
                    tmp += 'lapPrice <= ' + str(value)
                elif "大於" in keyword["valueCompare"]:
                    tmp += 'lapPrice >= ' + str(value)
            elif key == "GPU":
                tmp += 'lapGPU Like "%' + value + '%"'
            elif key == "CPU":
                tmp += 'lapCPU Like "%' + value + '%"'
            elif key == "Capacity":
                 tmp += keyword["Attribute"] + ' Like "%' + value + '%"'
            elif key == "RAM":
                tmp += 'lapRAM Like "%' + value + '%"'
            elif key == "Max_Min":
                tmp +=  keyword["Attribute"] + ' in (select '+value +'('+ keyword["Attribute"] + ') from laptop )'
            elif key == "date-period":
                time = value.split('/')
                start = time[0]
                end = time[1]
                tmp = ' disStart between "' + start + '" and "' + end + '"'

            # 多條件時
            if where != "where " and tmp != '':
                where += " and " + tmp
                tmp = ''
            elif where == "where ":
                where += tmp
                tmp = ''
    return where

# 電腦基本資料和排序
def res_comp(keyword):
    command = "select distinct lapNO,lapID,if(lapNO in (select lapNO from laptop,discount where lapNO = disNO and CURDATE() between disStart and disEnd),disprice,lapprice) as lapPrice,lapCPU,lapGPU,lapRAM,lapDisk,lapWarranty,lapImage,lapBrand from laptop left join discount on lapNO = disNO "
    command += do_where(keyword, "where ")
    try:
        if keyword["orderby"]!= '':
            orderby = ' order by ' + keyword["orderby"]["Attribute"] + " " + keyword["ASC_DESC"]
        command += orderby
    finally:
        res_out(command)

# 關注清單
def res_attention(keyword):
    select = 'select * '
    From = 'from laptop,attention '
    where = 'where att_NO = lapNO and att_userID = "'+ userId + '"'
    where = do_where(keyword, where)
    command = select + From + where
    res_out(command)

# 變更關注清單
def res_alter(keyword):
    if keyword["Action"] == "delete":
        delete = 'delete from attention '
        where = 'where att_userID = "' + userId + '" and att_NO in ('
        select = 'select lapNO from laptop '+ do_where(keyword, "where ") + ')'
        command = delete + where + select
    elif keyword["Action"] == 'insert':
        insert = 'insert into attention(att_NO,att_userID)'
        select = 'select lapNO,"' + userId + '"'
        From = " from laptop "
        where = do_where(keyword, "where ")
        command = insert + select + From + where

    res_alter_out(command)

# 價價功能
def res_discount(keyword):
    select = 'select lapNO,lapID,lapPrice,disPrice,disStart,disEnd'
    From = ' from laptop discount '
    where = 'where lapNO = disNO'
    where = do_where(keyword, where)
    command = select + From + where
    try:
        if keyword["orderby"] != '':
            if keyword["orderby"]["Attribute"] == "lapPrice":
                orderby = ' order by disPrice ' + keyword["ASC_DESC"]
            else:
                orderby = ' order by ' + keyword["orderby"]["Attribute"] + " " + keyword["ASC_DESC"]
            command += orderby
    finally:
        res_out(command, flag=1)

def webhook(result):

    para = result['result']['parameters']
    #確認使用者輸入的功能

    intent = None
    # 事件
    if result['result']['metadata']['intentName'] != '':
        intent = result['result']['metadata']['intentName']

    if "電腦" in intent:
        if para["Action"]!= '':
            res_comp(para)
        else:
            line_bot_api.push_message(userId, TextSendMessage(text="請輸入查詢/關注/移除"))
    elif "排序" in intent:
        if para["orderby"]!= '':
            res_comp(para)
        else:
            line_bot_api.push_message(userId, TextSendMessage(text="請輸入以什麼排序"))
    elif "變更" in intent:
        res_alter(para)
    elif "關注資料" in intent:
        res_attention(para)
    elif "特價" in intent:
        res_discount(para)
    else:
        line_bot_api.push_message(userId, TextSendMessage(text=result['result']['fulfillment']['speech']))


app = Flask(__name__)

# 程式開頭
@app.route("/", methods=['POST'])
def callback(): #Line連接程式
    signature = request.headers['X-Line-Signature'] # Line 訊息標頭

    body = request.get_data(as_text = True) # 要求資料主體
    # print("Request body: " + body, "Signature: " + signature)
    try:
        handler.handle(body, signature) # 呼叫 handler 處理訊息
    except InvalidSignatureError:
       abort(400)

    return 'OK'

# Line 訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    global userId
    msg = event.message.text # 拿到訊息

    # 判斷使用者有沒有在資料庫
    userId = event.source.user_id
    command = 'insert into users(userID) select "' + userId + '" where "' + userId + '" not in (select userID from users)'
    res_alter_out(command,flag=1)

    # 全形(手機中文)半形(手機英文)有差
    if msg.strip() == '?' or msg.strip() == '？':
        f = open("questionMark.txt", 'r', encoding="UTF-8")
        line_bot_api.push_message(userId, TextSendMessage(text=f.read()))
        f.close()
    else:
        dialog_req(msg)

# 連接 Dialogflow
def dialog_req(text):
    CLIENT_ACCESS_TOKEN = '1e0a1ed2c63c4f999d487e432eba1772'
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
    request = ai.text_request()
    request.lang = 'tw'
    request.query = text
    response = request.getresponse().read().decode()
    result = json.loads(response)
    webhook(result)

if __name__ == "__main__":
    app.run(port=5000)