#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    订单模型
"""

from web_db_define import *
from datetime import datetime,timedelta
from common.log import *
from common import log_util,convert_util
from common.record_player_info import record_player_balance_change
from model import mysql
import time
import json
import decimal
from db_define import  Mysql_instance,bag_redis

def default(o):
    if isinstance(o, decimal.Decimal):
        return str(o)

def setHonorField(is_honor,id):
    mysql = Mysql_instance()
    sql = "update reward_course_config set is_honor='%s' where id ='%s'"%(is_honor,id)
    mysql.cursor.execute(sql)
    mysql.commit()
    mysql.close()

def updateCourseInfo(id,title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price):
    mysql = Mysql_instance()
    sql = "update reward_course_config set title='%s',cost='%s',price='%s',item_id='%s',cost_type='%s',cost_num='%s',cost_type_name='%s',icon='%s',item_type='%s',limit_price='%s' where id='%s'"%(title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price,id)
    mysql.cursor.execute(sql)
    mysql.commit()
    mysql.close()

def getThisRewardCourse(id):
    mysql = Mysql_instance()
    sql = "select title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price from reward_course_config where id='%s'"%id
    mysql.cursor.execute(sql)
    res = mysql.cursor.fetchone()
    return {
        "id":id,
        "title":res[0],
        "cost":res[1],
        "price":res[2],
        "item_id":res[3],
        "cost_type": res[4],
        "cost_num": res[5],
        "cost_type_name": res[6],
        "icon": res[7],
        "item_type": res[8],
        "limit_price": res[9],
    }

def delRewardCourse(id):
    mysql = Mysql_instance()
    sql = "delete from reward_course_config where id = '%s'"%id
    mysql.cursor.execute(sql)
    mysql.commit()
    mysql.close()

def getRewardCourseInfo():
    mysql = Mysql_instance()
    sql = "select id,title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price,is_honor from reward_course_config"
    mysql.cursor.execute(sql)
    res = mysql.cursor.fetchall()
    data = []
    for row in res:
        data.append({
            "id" : row[0],
            "title" : row[1],
            "cost" : round(float(row[2])/100,2),
            "price" : round(float(row[3])/100,2),
            "item_id" : row[4],
            "cost_type" : row[5],
            "cost_num" : row[6],
            "cost_type_name" : row[7],
            "icon" : row[8],
            "item_type" : row[9],
            "limit_price" : row[10],
            "is_honor" : row[11],
        })
    return json.dumps({"count":len(data),"data":data})

def createRewardCourse(title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price):
    mysql = Mysql_instance()
    cost = int(float(cost)*100)
    price = int(float(price)*100)
    sql = "insert into reward_course_config(title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(title,cost,price,item_id,cost_type,cost_num,cost_type_name,icon,item_type,limit_price)
    mysql.cursor.execute(sql)
    mysql.commit()
    mysql.close()

def sendReward(redis,key_code,card_no,card_pwd):
    mysql = Mysql_instance()
    # 有可能重复记录，所以获取是否第一次记录
    is_first_get = True
    sql_is_first_record = 'select * from reward_record where status = 1 and key_code = "%s"' % key_code
    mysql.cursor.execute(sql_is_first_record)
    is_first_res = mysql.cursor.fetchall()
    if len(is_first_res) > 0:
        is_first_get = False

    sql = "select status,item_id,uid,reward_value from reward_record where key_code = '%s'"%key_code
    mysql.cursor.execute(sql)
    res = mysql.cursor.fetchone()

    sql = "update reward_record set card_no = '%s',card_pwd = '%s' where key_code = '%s'"%(card_no,card_pwd,key_code)
    if res and res[0] == 0:
        now = str(datetime.now())
        if res[1] is not None:
            bag_redis.hdel('reward:%s:user:%s:keycode'%(res[1],res[2]),res[3])
        sql = "update reward_record set card_no = '%s',card_pwd = '%s',status = 1,deliver_time = '%s' where key_code = '%s'"%(card_no,card_pwd,now,key_code)
    mysql.cursor.execute(sql)
    mysql.commit()
    mysql.close()
    # 金币追踪
    if is_first_get:
        record_player_balance_change(bag_redis,'',-1,0,0,59,extra1=key_code)
    return getRewardUserInfo(key_code)

def getRewardUserInfo(key_code):
    sql = "select uid,nickname,card_no,card_pwd from reward_record where key_code='%s'" %key_code
    mysql = Mysql_instance()
    mysql.cursor.execute(sql)
    res = mysql.cursor.fetchone()
    return {
       "uid":res[0],
       "nickname":res[1],
       "card_no":res[2] or "",
       "card_pwd":res[3] or "",
       "key_code":key_code
    }

def getRewardDataInfo(startDate,endDate):
    mysql = Mysql_instance()
    startDate = str(datetime.strptime(startDate,'%Y-%m-%d'))
    endDate = str(datetime.strptime(endDate,'%Y-%m-%d')+timedelta(1))
    sql = "select uid,nickname,key_code,reward_cost,reward_value,reward_time,deliver_time,card_no,card_pwd,status,reward_name,cost_type_name,cost_num from reward_record "\
          +"where reward_time >= '%s' and reward_time < '%s'"%(startDate,endDate)
    print '---------------------------'
    print sql
    print '---------------------------'
    mysql.cursor.execute(sql)
    res = mysql.cursor.fetchall()
    data = []
    for row in res:
        data.append({
            "uid":row[0],
            "nickname":row[1],
            "key_code":row[2],
            "reward_cost":round(float(row[3])/100,2),
            "reward_value":round(float(row[4])/100,2),
            "reward_time":str(row[5]),
            "deliver_time":str(row[6] or ""),
            "card_no":row[7] or "",
            "card_pwd":row[8] or "",
            "status":row[9],
            "reward_name":row[10],
            "cost_type_name":row[11],
            "cost_num":row[12],
        })
    mysql.close()
    return json.dumps({"count":len(data),"data":data})

def createOrder(redis,orderInfo):
    """
    创建新订单
    @param:
        redis       redis链接实例
        orderInfo   游戏信息
    """

    orderInfo['id']  = redis.incr(ORDER_COUNT)

    orderTable = ORDER_TABLE%(orderInfo['orderNo'])
    pipe = redis.pipeline()

    pipe.hmset(orderTable,orderInfo)
    pipe.lpush(ORDER_LIST,orderInfo['orderNo'])
    return pipe.execute()

def get_gid(redis,agent_id):
    pid,rtype = redis.hmget(AGENT_TABLE%agent_id,'parent_id','type')
    if rtype == '1':
        return pid
    elif rtype == '0':
        return agent_id
    else:
        pid = redis.hget(AGENT_TABLE%pid,'parent_id')
        return pid

def getBuyOrdersById(redis,selfUid,startDate,endDate):
    """
    获取代理购卡订单列表
    """
    deltaTime = timedelta(1)

    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate  = datetime.strptime(endDate,'%Y-%m-%d')
   
    startTime = int(time.mktime(startDate.timetuple()))
    endTime = int(time.mktime(endDate.timetuple())) + 86400

    orderList = mysql.query("SELECT * FROM accounts WHERE create_time>=:startTime and create_time<=:endTime;",
        {
        "startTime": startTime,
        "endTime": endTime
        })
    dup_orderList = []
    god_id = redis.get('god:id')
    if selfUid != god_id:
        for order in orderList:
            gid = get_gid(redis,order['agent_id'])
            if gid == selfUid:
                dup_orderList.append(order)
    else:
        dup_orderList = orderList

    consumeSucc = []
    consumeFail = []
    order_set = set()
    res_orderList = []
    for k, v in enumerate(dup_orderList):
        bill_time = v["bill_time"]
        v["bill_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bill_time))
        v["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["create_time"]))
        consume = float(v["balance"]) if v["balance"] else 0
        v['gid'] = redis.hget('agents:id:%s'%v['top_agent'],'parent_id')
        if v['order_no'] not in order_set:
            if v["status"] == 1:
                consumeSucc.append(consume)
            else:
                consumeFail.append(consume)
            res_orderList.append(v)
            order_set.add(v['order_no'])
    consumeFaild  = sum(consumeFail)
    consumeSucces = sum(consumeSucc)
    
    orderList = json.loads(json.dumps(res_orderList, default=default))
    result = {"consumeSucces": consumeSucces, "consumeFaild": consumeFaild, "data": orderList}
    return result

def getSaleOrdersById(redis,agentId,startDate,endDate):
    """
    获取代理售卡订单列表
    """
    deltaTime = timedelta(1)

    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate  = datetime.strptime(endDate,'%Y-%m-%d')

    orderList = []
    while endDate >= startDate:
        buyOrderTable = AGENT_SALE_ORDER_LIST%(agentId,endDate.strftime('%Y-%m-%d'))
        if not redis.exists(buyOrderTable):
            endDate-=deltaTime
            continue
        orderNos = redis.lrange(buyOrderTable,0,-1)
        for orderNo in orderNos:
            orderInfo = redis.hgetall(ORDER_TABLE%(orderNo))
            if not orderInfo:
                continue
            orderInfo['op'] = [{'url':'/admin/order/sale/cancel','txt':'取消订单','method':'post'},{'url':'/admin/order/comfirm','txt':'确认订单','method':'post'}]
            orderList.append(orderInfo)

        endDate-=deltaTime

    return orderList


def getBuyCardReport(redis,agentId,startDate,endDate):
    """
        获取代理购卡报表
        @params:
            redis   :  链接实例
            agentId :  代理ID
            startDate  :  开始日期
            endDate    :  结束日期
    """
    deltaTime = timedelta(1)

    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate  = datetime.strptime(endDate,'%Y-%m-%d')

    reportList = []
    cardNumsTotal = 0

    while endDate >= startDate:
        dateStr = endDate.strftime('%Y-%m-%d')
        buyReportTable = AGENT_BUY_CARD_DATE%(agentId,dateStr)
        if not redis.exists(buyReportTable):
            endDate-=deltaTime
            continue
        reportInfo  =  redis.hgetall(buyReportTable)
        #添加入报表list
        reportList.append(reportInfo)
        endDate-=deltaTime

    return {'cardNumsTotal':cardNumsTotal,'result':reportList}

def getSaleCardReport(redis,agentId,startDate,endDate):
    """
        获取代理售卡报表
        @params:
            redis   :  链接实例
            agentId :  代理ID
            startDate  :  开始日期
            endDate    :  结束日期
    """
    deltaTime = timedelta(1)

    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate   = datetime.strptime(endDate,'%Y-%m-%d')

    reportList = []
    cardNumsTotal = 0

    while endDate >= startDate:
        dateStr = endDate.strftime('%Y-%m-%d')
        saleReportTable = AGENT_SALE_CARD_DATE%(agentId,dateStr)
        if not redis.exists(saleReportTable):
            endDate-=deltaTime
            continue
        reportInfo  =  redis.hgetall(saleReportTable)
        #添加入报表
        reportList.append(reportInfo)

        endDate-=deltaTime

    return {'result':reportList}


def getAgentSaleCardReport(redis,agentId,startDate,endDate,group_id):
    """
        获取该代理的下线代理售卡报表
        @params:
            redis   :  链接实例
            agentId :  代理ID
            startDate  :  开始日期
            endDate    :  结束日期
    """
    deltaTime = timedelta(1)
    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate   = datetime.strptime(endDate,'%Y-%m-%d')

    parentTable = AGENT_CHILD_TABLE%(agentId)
    subIds = []
    if group_id:
        #按代理查询
        subIds = [group_id]
    else:
        subIds = redis.smembers(parentTable)
    reportList = []
    now_time = datetime.now()
    cardNumsTotal = 0
    for subId in subIds:
        agentTable = AGENT_TABLE%(subId)
        account = redis.hget(agentTable,'account')
        endDateCopy = endDate
        while endDateCopy >= startDate:
            if endDateCopy > now_time:
                endDateCopy-=deltaTime
                continue
            dateStr = endDateCopy.strftime('%Y-%m-%d')
            saleReportTable = AGENT_SALE_CARD_DATE%(subId,dateStr)
            log_debug('saleReport[%s]'%(saleReportTable))
            if not redis.exists(saleReportTable):
                endDateCopy-=deltaTime
                continue
            reportInfo = {}
            date,cardNums,totalNums  =  redis.hmget(saleReportTable,('date','cardNums','totalNums'))
            reportInfo['account'] = account
            reportInfo['cards'] = cardNums
            reportInfo['cardNumsTotal'] = totalNums
            reportInfo['date'] = date
            reportInfo['aId'] = subId
            #添加入报表
            reportList.append(reportInfo)
            endDateCopy-=deltaTime

    return {'result':reportList}

def getAgentBuyCardReport(redis,agentId,startDate,endDate,group_id):
    """
        获取该代理的下线代理购卡报表
        @params:
            redis   :  链接实例
            agentId :  代理ID
            startDate  :  开始日期
            endDate    :  结束日期
    """
    deltaTime = timedelta(1)

    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate   = datetime.strptime(endDate,'%Y-%m-%d')

    parentTable = AGENT_CHILD_TABLE%(agentId)
    if group_id:
        #按代理查询
        subIds = [group_id]
    else:
        subIds = redis.smembers(parentTable)

    reportList = []
    cardNumsTotal = 0
    now_time = datetime.now()
    for subId in subIds:
        agentTable = AGENT_TABLE%(subId)
        account = redis.hget(agentTable,'account')
        endDateCopy = endDate
        while endDateCopy >= startDate:
            if endDateCopy > now_time:
                endDateCopy-=deltaTime
                continue
            dateStr = endDateCopy.strftime('%Y-%m-%d')
            buyReportTable = AGENT_BUY_CARD_DATE%(subId,dateStr)
            if not redis.exists(buyReportTable):
                endDateCopy-=deltaTime
                continue
            reportInfo = {}
            date,cardNums,totalNums  =  redis.hmget(buyReportTable,('date','cardNums','totalNums'))

            reportInfo['account'] = account
            reportInfo['cards'] = cardNums
            reportInfo['date'] = date
            reportInfo['cardNumsTotal'] = totalNums
            reportInfo['aId'] = subId
            #添加入报表
            reportList.append(reportInfo)
            endDateCopy-=deltaTime

    return {'cardNumsTotal':cardNumsTotal,'result':reportList}

    return {'result':reportList}

def get_wechat_order_records(redis,groupId,condition,action="HALL"):
    """
    获取微信支付订单记录
    :params redis Redis实例
    :params groupId 公会ID
    :params condition 查询条件
    :params action 查询 捕鱼FISH 或 棋牌HALL的订单
    """
    deltaTime = timedelta(1)
    orderList = []

    roomCardCount,pendingMoney,successMoney,moneyCount = 0,0,0,0
    date_lists = convert_util.to_week_list(condition['startDate'],condition['endDate'])

    if action == "HALL":
        date_table = DAY_ORDER
        order_table = ORDER_TABLE
    else:
        date_table = DAY_ORDER4FISH
        order_table = ORDER_TABLE4FISH

    pipe = redis.pipeline()

    for date in date_lists:
        orders = redis.lrange(date_table%(date),0,-1)
        #roomCardCount+=len(orders)
        for order in orders:
            orderInfo = {}
            if not order_table%(order):
                pipe.lrem(ORDER_NUM_LIST,orders)
                pipe.lrem(date_table%(date),order)
                continue
            orderDetail = redis.hgetall(order_table%(order))
            if not orderDetail:
                pipe.lrem(ORDER_NUM_LIST,orders)
                pipe.lrem(date_table%(date),order)
                continue

            dateStr1 = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(orderDetail['time'])))
            log_util.debug('time[%s]'%(dateStr1))
            moneyCount+=round(float(orderDetail['money']),2)
            if orderDetail['type'] == 'pending':
                pendingMoney+=round(float(orderDetail['money']),2)
            else:
                successMoney+=round(float(orderDetail['money']),2)

            user_table = redis.get(FORMAT_ACCOUNT2USER_TABLE%(orderDetail['account']))
            group_id  = redis.hget(user_table,'parentAg')

            if 'groupId' in orderDetail:
                orderInfo['groupId'] = orderDetail['groupId']
                parentId = redis.hget(AGENT_TABLE%(orderDetail['groupId']),'parent_id')
                if parentId:
                    orderInfo['parentId'] = parentId
            orderInfo['orderNo'] = order
            orderInfo['good_name'] = orderDetail['name']
            orderInfo['good_money'] = round(float(orderDetail['money'])*0.01,2)
            orderInfo['order_paytime'] = dateStr1
            orderInfo['good_count'] = orderDetail['roomCards']
            orderInfo['order_type'] = orderDetail['type']
            orderInfo['group_id'] = group_id if group_id else '-'
            orderInfo['memberId'] = user_table.split(':')[1]
            orderList.append(orderInfo)
    pipe.execute()
    return {'data':orderList,'orderCount':len(orderList),'moneyCount':moneyCount*0.01,'pendingMoney':pendingMoney*0.01,'successMoney':successMoney*0.01}
