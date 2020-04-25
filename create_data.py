#此程式有使用google瀏覽器套件
#不能在notebook上執行
#目的為抓取網路店上ZenBook系列筆電的資料
#結果的csv檔，是我用自己的電腦跑完再上傳到notebook上的
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup as bs
import requests
import csv
import os
import pymysql

username = 'root'
password = 'peng1234'
databaseName = 'ChatBot'


chrome_option = Options()
chrome_option.add_argument('--headless')#不希望出現視窗
driver = webdriver.Chrome('chromedriver',chrome_options = chrome_option)#透過瀏覽器開啟

driver.get('https://store.asus.com/tw/category/A15061')#Asus的官方網路店
time.sleep(3)#等待網頁載入完成

content = bs(driver.page_source, 'html.parser')#透過BeautifulSoup開啟
linkList = content.select('a.photo')#抓取各種筆電的連結
urls = []
for i in linkList:
    urls.append(i.get('href'))#把連結放進urls
#print(urls)
driver.close()#關閉瀏覽器


wantlist = ['型號','價格','CPU',"GPU","RAM","資料儲存應用",'保固']#這是我想找的資料，也是csv的第一列

db = pymysql.connect('localhost',username,password,databaseName)
cursor = db.cursor()

tmp = []#用於暫存從網頁擷取下來的資料
width = [0]*7#用於控制excel欄位寬度
j = 1
for url in urls: #透過urls，瀏覽每一台筆電的詳情
    tmp.append(j)
    web = requests.get("https:" + url)#請求網頁
    content = bs(web.text,"html.parser")#用湯開啟
    name = content.find('h1',id='pro_title').text#找到產品名稱
    tmp.append(name)#放入暫存
    #print(name)
    price = content.find("span",{'class':"price"}).text#找到價格
    tmp.append(price)
    #print(price)
    item = content.select(".css-spec-item")#找到詳細資料標頭
    itemData = content.select(".css-spec-data")#找到詳細資料
    for i in range(len(item)):#將兩個list文字化(.text)
        item[i] = item[i].text
        itemData[i] = itemData[i].text.replace('\n',"")
    check = 0#用於確定資料完整

    for i in range(len(item)):
        if item[i] in wantlist:#篩選想要的資料
            #print(item[i] + ":" + itemData[i])
            tmp.append(itemData[i])
            check += 1
    if check == 5:#如果資料完整
        tmp[2] = int(tmp[2].replace(',',""))
        print(tmp)
        cursor.execute('insert into laptop value(%s,%s,%s,%s,%s,%s,%s,%s,null,"ASUS")', [tmp[i] for i in range(8)])
        j+=1
    tmp.clear()#清空暫存
db.commit()

# crawler.py
# 目前顯示的是「crawler.py」。