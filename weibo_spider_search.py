# coding=utf-8

"""  
Created on 2016-04-28 
@author: xuzhiyuan

功能: 爬取新浪微博的搜索结果,支持高级搜索中对搜索时间的限定
网址：http://s.weibo.com/
实现：采取selenium测试工具，结合PhantomJS/Firefox对后台JS代码进行解析，进而抓取需要的信息

"""

import time
import datetime
import re            
import os    
import sys  
import codecs  
import shutil
import urllib 
from selenium import webdriver        
from selenium.webdriver.common.keys import Keys        
import selenium.webdriver.support.ui as ui        
from selenium.webdriver.common.action_chains import ActionChains
import xlwt

#先调用无界面浏览器PhantomJS或Firefox    
#driver = webdriver.PhantomJS()
driver = webdriver.Firefox()

#********************************************************************************
#                            第一步: 登陆login.sina.com
#                     这是一种很好的登陆方式，有可能有输入验证码
#                          登陆之后即可以登陆方式打开网页
#********************************************************************************

def LoginWeibo(username, password):
    try:
        #输入用户名/密码登录
        print u'准备登陆Weibo.cn网站...'
        driver.get("http://login.sina.com.cn/")
        elem_user = driver.find_element_by_name("username")
        elem_user.send_keys(username) #用户名
        elem_pwd = driver.find_element_by_name("password")
        elem_pwd.send_keys(password)  #密码
        elem_sub = driver.find_element_by_xpath("//input[@class='smb_btn']")
        elem_sub.click()              #点击登陆 因无name属性

        try:
            #输入验证码
            time.sleep(10)
            elem_sub.click() 
        except:
            #不用输入验证码
            pass

        #获取Coockie 推荐资料：http://www.cnblogs.com/fnng/p/3269450.html
        print 'Crawl in ', driver.current_url
        print u'输出Cookie键值对信息:'
        for cookie in driver.get_cookies(): 
            print cookie
            for key in cookie:
                print key, cookie[key] 
        print u'登陆成功...'
    except Exception,e:      
        print "Error: ",e
    finally:    
        print u'End LoginWeibo!\n'

#********************************************************************************
#                  第二步: 访问http://s.weibo.com/页面搜索结果
#               输入关键词、时间范围，得到所有微博信息、博主信息等
#                     考虑没有搜索结果、翻页效果的情况
#********************************************************************************    

def GetSearchContent(key):

    driver.get("http://s.weibo.com/")
    print '搜索热点主题：', key.decode('utf-8')

    #输入关键词并点击搜索
    item_inp = driver.find_element_by_xpath("//input[@class='searchInp_form']")
    item_inp.send_keys(key.decode('utf-8'))
    item_inp.send_keys(Keys.RETURN)    #采用点击回车直接搜索

    #获取搜索词的URL，用于后期按时间查询的URL拼接
    current_url = driver.current_url
    current_url = current_url.split('&')[0] #http://s.weibo.com/weibo/%25E7%258E%2589%25E6%25A0%2591%25E5%259C%25B0%25E9%259C%2587

    global start_stamp
    global page

    #需要抓取的开始和结束日期
    start_date = datetime.datetime(2010,4,13,0)
    end_date = datetime.datetime(2010,4,26,0)
    delta_date = datetime.timedelta(days=1)

    #每次抓取一天的数据
    start_stamp = start_date
    end_stamp = start_date + delta_date

    global outfile
    global sheet

    outfile = xlwt.Workbook(encoding = 'utf-8')

    while end_stamp <= end_date:

        page = 1

        #每一天使用一个sheet存储数据
        sheet = outfile.add_sheet(str(start_stamp.strftime("%Y-%m-%d-%H")))
        initXLS()

        #通过构建URL实现每一天的查询
        url = current_url + '&typeall=1&suball=1&timescope=custom:' + str(start_stamp.strftime("%Y-%m-%d-%H")) + ':' + str(end_stamp.strftime("%Y-%m-%d-%H")) + '&Refer=g'
        driver.get(url)
        
        handlePage()  #处理当前页面内容

        start_stamp = end_stamp
        end_stamp = end_stamp + delta_date

#********************************************************************************
#                  辅助函数，考虑页面加载完成后得到页面所需要的内容
#********************************************************************************   

#页面加载完成后，对页面内容进行处理
def handlePage():
    while True:
        #之前认为可能需要sleep等待页面加载，后来发现程序执行会等待页面加载完毕
        #sleep的原因是对付微博的反爬虫机制，抓取太快可能会判定为机器人，需要输入验证码
        time.sleep(2)
        #先行判定是否有内容
        if checkContent():
            print "getContent"
            getContent()
            #先行判定是否有下一页按钮
            if checkNext():
                #拿到下一页按钮
                next_page_btn = driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']")
                next_page_btn.click()
            else:
                print "no Next"
                break
        else:
            print "no Content"
            break

#判断页面加载完成后是否有内容
def checkContent():
    #有内容的前提是有“导航条”？错！只有一页内容的也没有导航条
    #但没有内容的前提是有“pl_noresult”
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag

#判断是否有下一页按钮
def checkNext():
    try:
        driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']")
        flag = True
    except:
        flag = False
    return flag

#在添加每一个sheet之后，初始化字段
def initXLS():
    name = ['博主昵称', '博主主页', '微博认证', '微博达人', '微博内容', '发布时间', '微博地址', '微博来源', '转发', '评论', '赞']
    
    global row
    global outfile
    global sheet

    row  = 0
    for i in range(len(name)):
        sheet.write(row, i, name[i])
    row = row + 1
    outfile.save("./crawl_output_YS.xls")

#将dic中的内容写入excel
def writeXLS(dic):
    global row
    global outfile
    global sheet

    for k in dic:
        for i in range(len(dic[k])):
            sheet.write(row, i, dic[k][i])
        row = row + 1
    outfile.save("./crawl_output_YS.xls")

#在页面有内容的前提下，获取内容
def getContent():

    #寻找到每一条微博的class
    nodes = driver.find_elements_by_xpath("//div[@class='WB_cardwrap S_bg2 clearfix']")

    #在运行过程中微博数==0的情况，可能是微博反爬机制，需要输入验证码
    if len(nodes) == 0:
        raw_input("请在微博页面输入验证码！")
        url = driver.current_url
        driver.get(url)
        getContent()
        return

    dic = {}

    global page
    print str(start_stamp.strftime("%Y-%m-%d-%H"))
    print u'页数:', page
    page = page + 1
    print u'微博数量', len(nodes)

    for i in range(len(nodes)):
        dic[i] = []
        
        try:
            BZNC = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").text
        except:
            BZNC = ''
        print u'博主昵称:', BZNC
        dic[i].append(BZNC)

        try:
            BZZY = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").get_attribute("href")
        except:
            BZZY = ''
        print u'博主主页:', BZZY
        dic[i].append(BZZY)

        try:
            WBRZ = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='approve_co']").get_attribute('title')#若没有认证则不存在节点
        except:
            WBRZ = ''
        print '微博认证:', WBRZ
        dic[i].append(WBRZ)

        try:
            WBDR = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='ico_club']").get_attribute('title')#若非达人则不存在节点
        except:
            WBDR = ''
        print '微博达人:', WBDR
        dic[i].append(WBDR)

        try:
            WBNR = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/p[@class='comment_txt']").text
        except:
            WBNR = ''
        print '微博内容:', WBNR
        dic[i].append(WBNR)

        try:
            FBSJ = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']").text
        except:
            FBSJ = ''
        print u'发布时间:', FBSJ
        dic[i].append(FBSJ)

        try:
            WBDZ = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']").get_attribute("href")
        except:
            WBDZ = ''
        print '微博地址:', WBDZ
        dic[i].append(WBDZ)

        try:
            WBLY = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@rel]").text
        except:
            WBLY = ''
        print '微博来源:', WBLY
        dic[i].append(WBLY)

        try:
            ZF_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_forward']//em").text
            if ZF_TEXT == '':
                ZF = 0
            else:
                ZF = int(ZF_TEXT)
        except:
            ZF = 0
        print '转发:', ZF
        dic[i].append(str(ZF))

        try:
            PL_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_comment']//em").text#可能没有em元素
            if PL_TEXT == '':
                PL = 0
            else:
                PL = int(PL_TEXT)
        except:
            PL = 0
        print '评论:', PL
        dic[i].append(str(PL))

        try:
            ZAN_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_like']//em").text #可为空
            if ZAN_TEXT == '':
                ZAN = 0
            else:
                ZAN = int(ZAN_TEXT)
        except:
            ZAN = 0
        print '赞:', ZAN
        dic[i].append(str(ZAN))

        print '\n'

    #写入Excel
    writeXLS(dic)

#*******************************************************************************
#                                程序入口
#*******************************************************************************
if __name__ == '__main__':

    #定义变量
    username = '151XXXXXXX'             #输入你的用户名
    password = 'XXXXXX'               #输入你的密码

    #操作函数
    LoginWeibo(username, password)       #登陆微博

    #搜索热点微博 爬取评论
    key = '玉树地震' 
    GetSearchContent(key)
