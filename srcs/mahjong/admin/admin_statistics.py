#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    数据统计模块
"""
from bottle import *
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,RES_VERSION
from common.utilt import *
from common.log import *
from datetime import datetime
from web_db_define import *
from model.orderModel import *
from model.agentModel import *
from model.statisticsModel import *
from model.userModel import *
from common import log_util,convert_util
import json
import copy


@admin_app.get('/statistics/buyReport')
@checkAccess
def getBuyReport(redis,session):
    """
    获取代理的订单报表
    """
    lang      = getLang()

    isList = request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()

    selfAccount,selfUid = session['account'],session['id']

    if not startDate or not endDate:
        #默认显示一周时间
        startDate,endDate = getDaya4Week()

    if isList:
        reports = getBuyCardReport(redis,selfUid,startDate,endDate)
        return json.dumps(reports)
    else:
        info = {
                'title'         :    '[%s]购钻报表'%(selfAccount),
                'searchStr'     :    '',
                'showLogType'   :    '',
                'startDate'     :    startDate,
                'endDate'       :    endDate,
                'listUrl'       :    BACK_PRE+'/statistics/buyReport?list=1',
                'STATIC_LAYUI_PATH'      :   STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :   STATIC_ADMIN_PATH
        }

        return template('admin_report_buy',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/saleReport')
@checkAccess
def getSaleReport(redis,session):
    """
    获取代理的订单报表
    """
    lang      = getLang()

    isList = request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()

    selfAccount,selfUid = session['account'],session['id']

    if not startDate or not endDate:
        #默认显示一周时间
        startDate,endDate = getDaya4Week()

    if isList:
        reports = getSaleCardReport(redis,selfUid,startDate,endDate)
        return json.dumps(reports)
    else:
        info = {
                'title'         :    '[%s]售钻报表'%(selfAccount),
                'searchStr'     :    '',
                'showLogType'   :    '',
                'startDate'     :    startDate,
                'endDate'       :    endDate,
                'listUrl'       :    BACK_PRE+'/statistics/saleReport?list=1',
                'STATIC_LAYUI_PATH'      :   STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :   STATIC_ADMIN_PATH
        }

        return template('admin_report_sale',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/allAgentSaleReport')
@checkAccess
def getAgentSaleReport(redis,session):
    """
    获取下线代理的售钻订单报表
    """
    lang      = getLang()

    isList = request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()
    group_id = request.GET.get('group_id','').strip()

    selfAccount,selfUid = session['account'],session['id']

    if not startDate or not endDate:
        #默认显示一周时间
        startDate,endDate = getDaya4Week()

    if isList:
        reports = getAgentSaleCardReport(redis,selfUid,startDate,endDate,group_id)
        return json.dumps(reports)
    else:
        info = {
                'title'         :    '[%s]的下线代理售钻报表'%(selfAccount),
                'searchStr'     :    '',
                'showLogType'   :    '',
                'startDate'     :    startDate,
                'endDate'       :    endDate,
                'group_search'  :    True,#开启代理查询
                'listUrl'       :    BACK_PRE+'/statistics/allAgentSaleReport?list=1',
                'STATIC_LAYUI_PATH'      :   STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :   STATIC_ADMIN_PATH
        }

        return template('admin_report_agent_sale',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/allAgentBuyReport')
@checkAccess
def getAgentBuyReport(redis,session):
    """
    获取下线代理的购钻订单报表
    """
    lang      = getLang()

    isList = request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()
    group_id = request.GET.get('group_id','').strip()

    selfAccount,selfUid = session['account'],session['id']

    if not startDate or not endDate:
        #默认显示一周时间
        startDate,endDate = getDaya4Week()

    if isList:
        reports = getAgentBuyCardReport(redis,selfUid,startDate,endDate,group_id)
        return json.dumps(reports)
    else:
        info = {
                'title'         :    '[%s]的下线代理购钻报表'%(selfAccount),
                'searchStr'     :    '',
                'showLogType'   :    '',
                'startDate'     :    startDate,
                'endDate'       :    endDate,
                'group_search'  :    True,#开启代理查询
                'listUrl'       :    BACK_PRE+'/statistics/allAgentBuyReport?list=1',
                'STATIC_LAYUI_PATH'      :   STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :   STATIC_ADMIN_PATH
        }

        return template('admin_report_agent_buy',info=info,lang=lang,RES_VERSION=RES_VERSION)



def getTimeList(begin_date,end_date):
    date_list = []
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)
    return date_list


def get_downline_rate(redis,date,my_downline_agents,selfUid=''):
    """
    获取下线抽成的列表(循环查询)
    """
    RateReportList = []
    for agent_id in my_downline_agents:
        agentTable = AGENT_TABLE%(agent_id)
        aType,parentId = redis.hmget(agentTable,('type','parent_id'))
        log_util.debug('agent_id[%s] aType[%s] parentId[%s]'%(agent_id,aType,parentId))
        if aType in ['2','3']:
            agentPerPriceList  =  redis.smembers(AGENT_ROOMCARD_PER_PRICE%(parentId))
        else:
            agentPerPriceList  =  redis.smembers(AGENT_ROOMCARD_PER_PRICE%(agent_id))
        log_util.debug('----------------------------------------agentPerPriceList[%s]'%(agentPerPriceList))
        agentRateList =  redis.smembers(AGENT_RATE_SET%(agent_id))
        log_util.debug('----------------------------------------agentRateList[%s]'%(agentRateList))
        for price in agentPerPriceList:
            for rate in agentRateList:
                agentRateTable = AGENT_RATE_DATE%(agent_id,rate,price,date)
                if redis.exists(agentRateTable):
                    agentRate = redis.hgetall(agentRateTable)
                    agentRate['date'] = date
                    agentRate['id'] = agent_id
                    if agent_id == selfUid and 'superRateTotal' in agentRate and 'rateTotal' in agentRate:
                        agentRate['superRateTotal'] = ''
                        agentRate['rateTotal'] = ''
                        agentRate['unitPrice'] = ''
                        agentRate['rate'] = ''
                    RateReportList.append(agentRate)

    #log_util.debug('[RateReportList] agentTable[%s] RateReportList[%s]'%(agentTable,RateReportList))
    return RateReportList

def get_downline_rate2(redis,date_list,selfUid,agent_id):
    """
    获取下线抽成的列表(循环查询)
    """
    RateReportList = []
    RateReportDict = {}

    New_agentRate = {'id': agent_id, 'number': 0.0, 'rateTotal': 0.0, 'superRateTotal': 0.0, 'meAndNextTotal': 0.0}

    agentTable = AGENT_TABLE % (agent_id)
    aType, parentId = redis.hmget(agentTable, ('type', 'parent_id'))
    log_util.debug('agent_id[%s] aType[%s] parentId[%s]' % (agent_id, aType, parentId))
    if aType in ['2', '3']:
        agentPerPriceList = redis.smembers(AGENT_ROOMCARD_PER_PRICE % (parentId))
    else:
        agentPerPriceList = redis.smembers(AGENT_ROOMCARD_PER_PRICE % (agent_id))
    log_util.debug('----------------------------------------agentPerPriceList[%s]' % (agentPerPriceList))
    agentRateList = redis.smembers(AGENT_RATE_SET % (agent_id))
    log_util.debug('----------------------------------------agentRateList[%s]' % (agentRateList))

    for price in agentPerPriceList:
        for rate in agentRateList:
            Tmp_agentRate = copy.deepcopy(New_agentRate)

            Tmp_agentRate['rate'] = rate
            Tmp_agentRate['unitPrice'] = price

            for date in date_list:
                agentRateTable = AGENT_RATE_DATE % (agent_id, rate, price, date)
                if redis.exists(agentRateTable):
                    agentRate = redis.hgetall(agentRateTable)
                    for _key in ['number','meAndNextTotal','rateTotal','superRateTotal']:
                        Tmp_agentRate[_key] += float(agentRate.get(_key,0))

            if Tmp_agentRate.get('number',0):
                if agent_id == selfUid:
                    Tmp_agentRate['superRateTotal'] = ''
                    Tmp_agentRate['rateTotal'] = ''
                    Tmp_agentRate['unitPrice'] = ''
                    Tmp_agentRate['rate'] = ''

                RateReportList.append(Tmp_agentRate)

            print 'agent_id %s Tmp_agentRate %s price %s rate %s'%(agent_id,Tmp_agentRate,price,rate)

    #log_util.debug('[RateReportList] agentTable[%s] RateReportList[%s]'%(agentTable,RateReportList))
    if RateReportList:
        print 'RateReportList',RateReportList
    return RateReportList


def get_rate_reports(redis,selfUid,startDate,endDate,agent_type):
    """
    获取抽成的列表
    """
    date_list = convert_util.to_week_list(startDate,endDate)
    if agent_type == 0:
        my_downline_agents = redis.smembers(AGENT_CHILD_TABLE%(selfUid))
    elif agent_type >0:
        my_downline_agents = getAllChildAgentId(redis,selfUid)
    else:
        my_downline_agents = []
    if agent_type == 2:
        my_downline_agents.append(selfUid)
    log_util.debug('my_downline_agents[%s]'%(my_downline_agents))
    RateReportList = []
    for date in date_list:
        downline_reports = get_downline_rate(redis,date,my_downline_agents,selfUid)
        log_util.debug('[get_rate_reports] date[%s] selfId[%s] downline_reports[%s]'%(date,selfUid,downline_reports))
        if not downline_reports:
            continue
        RateReportList.extend(downline_reports)

    log_util.debug('[agentRateTable1111] selfUid[%s] RateReportList[%s]'%(selfUid,RateReportList))
    return {'date':RateReportList}

def get_rate_reports2(redis,selfUid,startDate,endDate,agent_type):
    """
    获取抽成的列表
    """
    date_list = convert_util.to_week_list(startDate,endDate)
    if agent_type == 0:
        my_downline_agents = redis.smembers(AGENT_CHILD_TABLE%(selfUid))
    elif agent_type >0:
        my_downline_agents = getAllChildAgentId(redis,selfUid)
    else:
        my_downline_agents = []
    if agent_type == 2:
        my_downline_agents.append(selfUid)
    log_util.debug('my_downline_agents[%s]'%(my_downline_agents))
    RateReportList = []

    for _agentid in my_downline_agents:
        downline_reports = get_downline_rate2(redis,date_list,selfUid,_agentid)
        log_util.debug('[get_rate_reports2] _agentid[%s] selfId[%s] date_list[%s]'%(_agentid,selfUid,date_list))
        if not downline_reports:
            continue
        RateReportList.extend(downline_reports)

    print 'RateReportList',RateReportList
    log_util.debug('[agentRateTable1111] selfUid[%s] RateReportList[%s]'%(selfUid,RateReportList))
    return {'date':RateReportList}

@admin_app.get('/statistics/rateReport')
@checkAccess
def get_rate_info(redis,session):
    """
    获取代理的利润分成报表
    """
    lang  =  getLang()
    isList = request.GET.get('list','').strip()

    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()
    selfUid = request.GET.get('id','').strip()
    date = request.GET.get('date','').strip()
    unitPrice = request.GET.get('unitPrice','').strip()

    log_util.debug('[try get_rate_info] selfUid[%s] date[%s]'%(selfUid,date))

    # if selfUid and date and unitPrice:
    #     reports = getNextRateReportInfo(redis,selfUid,date)
    #     return json.dumps(reports)

    if not selfUid:
        selfUid  =  session['id']

    selfAccount = session['account']
    agent_type  = convert_util.to_int(session['type'])
    agentTable = AGENT_TABLE%(selfUid)
    if isList:
        reports = get_rate_reports(redis,selfUid,startDate,endDate,agent_type)
        return json.dumps(reports)
    else:
        info = {
                    'title'         :       '[%s]销售利润报表'%(selfAccount),
                    'startDate'     :       startDate,
                    'endDate'       :       endDate,
                    'listUrl'       :       BACK_PRE+'/statistics/rateReport?list=1',
                    'STATIC_LAYUI_PATH'  :   STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'  :   STATIC_ADMIN_PATH,
                    'aType'              :  session['type'],
        }

        return template('admin_report_rate',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/rateReport2')
@checkAccess
def get_rate_info2(redis,session):
    """
    获取代理的利润分成报表
    """
    lang  =  getLang()
    isList = request.GET.get('list','').strip()

    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()
    selfUid = request.GET.get('id','').strip()
    date = request.GET.get('date','').strip()
    unitPrice = request.GET.get('unitPrice','').strip()

    log_util.debug('[try get_rate_info] selfUid[%s] date[%s]'%(selfUid,date))

    # if selfUid and date and unitPrice:
    #     reports = getNextRateReportInfo(redis,selfUid,date)
    #     return json.dumps(reports)

    if not selfUid:
        selfUid  =  session['id']

    selfAccount = session['account']
    agent_type  = convert_util.to_int(session['type'])
    agentTable = AGENT_TABLE%(selfUid)
    if isList:
        reports = get_rate_reports2(redis,selfUid,startDate,endDate,agent_type)
        return json.dumps(reports)
    else:
        info = {
                    'title'         :       '[%s]销售利润报表2'%(selfAccount),
                    'startDate'     :       startDate,
                    'endDate'       :       endDate,
                    'listUrl'       :       BACK_PRE+'/statistics/rateReport2?list=1',
                    'STATIC_LAYUI_PATH'  :   STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'  :   STATIC_ADMIN_PATH,
                    'aType'              :  session['type'],
        }

        return template('admin_report_rate2',info=info,lang=lang,RES_VERSION=RES_VERSION)

def getRegCountList(redis,startDate,endDate):
    """
        获取某个时间段注册人数列表
        params:
            [ startDate ] : 开始日期
            [ endDate ]   : 结束日期

    """
    try:
        startDate = datetime.strptime(startDate,'%Y-%m-%d')
        endDate   = datetime.strptime(endDate,'%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now()-weekDelTime
        startDate = weekBefore
        endDate   = datetime.now()

    deltaTime = timedelta(1)

    res = []
    now_time = datetime.now()
    while startDate <= endDate:
        if startDate>now_time:
            startDate += deltaTime
            continue
        regInfo = {}
        dateStr = startDate.strftime('%Y-%m-%d')
        regTable = FORMAT_REG_DATE_TABLE%(dateStr)
        regCount = redis.scard(regTable)
        regInfo['reg_date'] = dateStr
        regInfo['reg_count'] = regCount
        regInfo['op'] = []
        regInfo['op'].append({'url':'/admin/statistics/reg/list','method':'GET','txt':'查看详情'})
        res.append(regInfo)

        startDate += deltaTime

    res.reverse()
    return res

def getCardCountList(redis,agentId,startDate,endDate):
    """
        获取某个时间段注册人数列表
        params:
            [ startDate ] : 开始日期
            [ endDate ]   : 结束日期

    """
    try:
        startDate = datetime.strptime(startDate,'%Y-%m-%d')
        endDate   = datetime.strptime(endDate,'%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now()-weekDelTime
        startDate = weekBefore
        endDate   = datetime.now()

    deltaTime = timedelta(1)

    res = []

    while startDate <= endDate:
        regInfo = {}
        dateStr = startDate.strftime('%Y-%m-%d')
        if agentId == '1':
            regTable = DAY_ALL_PLAY_ROOM_CARD%(dateStr)
            regCount = redis.get(regTable)
        else:
            regCount = getAgentRoomByDay(redis,agentId,dateStr)
        if not regCount:
            regCount = 0
        regInfo['reg_date'] = dateStr
        regInfo['reg_count'] = regCount
        res.append(regInfo)

        startDate += deltaTime

    res.reverse()
    return res


@admin_app.get('/statistics/reg')
@checkAccess
def getRegStatistics(redis,session):
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate   = request.GET.get('endDate','').strip()

    if isList:
        res = getRegCountList(redis,startDate,endDate)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '注册人数统计',
                'listUrl'                :           BACK_PRE+'/statistics/reg?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
        }

        return template('admin_statistics_reg',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/takeCard')
@checkAccess
def getCardStatistics(redis,session):
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate   = request.GET.get('endDate','').strip()

    if isList:
        res = getCardCountList(redis,session['id'],startDate,endDate)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '日耗钻统计',
                'listUrl'                :           BACK_PRE+'/statistics/takeCard?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
        }

        return template('admin_statistics_card',info=info,lang=lang,RES_VERSION=RES_VERSION)


def getRegListByRegDate(redis,reg_date):
    """
        获取某个时间段注册人数详情
        params:
            [ reg_date ] : 某一天

    """
    print 'reg_date',reg_date
    registMemberList =  redis.smembers(FORMAT_REG_DATE_TABLE%(reg_date))
    res = []
    for member in registMemberList:
        memberInfo = {}
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(member) #从账号获得账号信息，和旧系统一样
        table = redis.get(account2user_table)
        nickname,reg_date,regIp,login_out_date,last_login_date,parentAg,headImgUrl= \
        redis.hmget(table,('nickname','regDate','regIp','last_logout_date','last_login_date','parentAg','headImgUrl'))
        memberInfo['nickname'] = nickname
        memberInfo['reg_date'] = reg_date
        memberInfo['regIp'] = regIp
        memberInfo['parentAg'] = regIp
        memberInfo['last_login_date'] = last_login_date if last_login_date else '-'
        memberInfo['login_out_date'] = login_out_date if login_out_date else '-'
        memberInfo['parentAg'] = parentAg if parentAg else '未加入任何公会'
        memberInfo['headImgUrl'] = headImgUrl
        memberInfo['account'] = member

        res.append(memberInfo)
    return res



@admin_app.get('/statistics/reg/list')
def getRegStatisticsList(redis,session):
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    reg_date = request.GET.get('reg_date','').strip()

    if isList:
        res = getRegListByRegDate(redis,reg_date)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '%s 注册列表'%(reg_date),
                'listUrl'                :           BACK_PRE+'/statistics/reg/list?list=1&reg_date=%s'%(reg_date),
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
        }

        return template('admin_statistics_reg_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/card/list')
def getRegStatisticsList(redis,session):
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    reg_date = request.GET.get('reg_date','').strip()

    if isList:
        res = getRegListByRegDate(redis,reg_date)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '%s 注册列表'%(reg_date),
                'listUrl'                :           BACK_PRE+'/statistics/reg/list?list=1&reg_date=%s'%(reg_date),
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
        }

        return template('admin_statistics_reg_list',info=info,lang=lang,RES_VERSION=RES_VERSION)


def getloginCountList(redis,agentId,agentIds,startDate,endDate):
    """
        获取某个时间段注册人数列表
        params:
            [ startDate ] : 开始日期
            [ endDate ]   : 结束日期

    """
    try:
        startDate = datetime.strptime(startDate,'%Y-%m-%d')
        endDate   = datetime.strptime(endDate,'%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now()-weekDelTime
        startDate = weekBefore
        endDate   = datetime.now()

    deltaTime = timedelta(1)

    res = []

    while startDate <= endDate:
        regInfo = {}
        dateStr = startDate.strftime('%Y-%m-%d')
        if not agentIds and int(agentId) == 1:
            regTable = FORMAT_LOGIN_DATE_TABLE%(dateStr)
            regCount = redis.scard(regTable)
        else:
            if not agentIds:
                agentIds = [agentId]
            regCount = 0
            for _agentId in agentIds:
                count = redis.get(DAY_AG_LOGIN_COUNT%(_agentId,dateStr))
                if not count:
                    count = 0
                regCount+=int(count)

        regInfo['reg_date'] = dateStr
        regInfo['reg_count'] = regCount
        regInfo['op'] = []
        regInfo['op'].append({'url':'/admin/statistics/login/list','method':'GET','txt':'查看详情'})
        res.append(regInfo)

        startDate += deltaTime

    res.reverse()
    return res

@admin_app.get('/statistics/login')
@checkAccess
def getLoginStatistics(redis,session):

    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate   = request.GET.get('endDate','').strip()

    selfUid  = session['id']
    if int(selfUid) == 1:
        agentIds = []
    else:
        agentIds = getAllChildAgentId(redis,selfUid)

    if isList:
        res = getloginCountList(redis,selfUid,agentIds,startDate,endDate)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '日登录人数统计',
                'listUrl'                :           BACK_PRE+'/statistics/login?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }


    return template('admin_statistics_login',info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/statistics/login/list')
def getRegStatisticsList(redis,session):
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    reg_date = request.GET.get('reg_date','').strip()
    selfUid  = session['id']

    if isList:
        res = getLoginListByRegDate(redis,session['id'],reg_date)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           '%s 登录列表'%(reg_date),
                'listUrl'                :           BACK_PRE+'/statistics/login/list?list=1&reg_date=%s'%(reg_date),
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
        }

        return template('admin_statistics_login_list',reg_date=reg_date,info=info,lang=lang,RES_VERSION=RES_VERSION)

# @admin_app.get('/statistics/count')
# def getCountStatics(redis,session):
#     """
#     获取每日的局数统计
#     """
#     lang = getLang()
#     curTime = datetime.now()
#     isList = request.GET.get('list','').strip()
#     startDate = request.GET.get('startDate','').strip()
#     endDate = request.GET.get('endDate','').strip()
#     selfUid = request.GET.get('id','').strip()
#     date    = request.GET.get('date','').strip()

#     if date:
#         endDate = date

#     log_debug('[count] startDate[%s] endDate[%s]'%(startDate,endDate))

#     if not selfUid:
#         selfUid = session['id']

#     agentType = session['type']
#     openList = 'true'
#     if int(agentType) == 2:
#         openList = 'false'
#     if isList:
#         res = getCountTotal(redis,selfUid,startDate,endDate)
#         return json.dumps(res)
#     else:
#         info = {
#                 'title'         :       '局数统计',
#                 'listUrl'                :           BACK_PRE+'/statistics/count?list=1',
#                 'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
#                 'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
#         }

#     return template('admin_statistics_count',openList=openList,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/statistics/active')
def get_active_page(redis,session):
    """
    活跃人数统计
    """
    curTime = datetime.now()
    lang = getLang()

    isList = request.GET.get('list','').strip()
    start_date = request.GET.get('startDate','').strip()
    end_date = request.GET.get('endDate','').strip()
    selfUid = session['id']
    if isList:
        active_reports = get_active_reports(redis,start_date,end_date,selfUid)
        return json.dumps(active_reports)
    else:
        info = {
                'title'         :       '活跃人数统计',
                'listUrl'                :           BACK_PRE+'/statistics/active?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_statistics_active',PAGE_LIST=PAGE_LIST,info=info,RES_VERSION=RES_VERSION,lang=lang)

@admin_app.get('/statistics/active/showDay')
def get_active_day(redis,session):
    """
    活跃人数统计
    """
    curTime = datetime.now()
    lang = getLang()

    isList = request.GET.get('list','').strip()
    date = request.GET.get('day','').strip()
    selfUid = session['id']
    if isList:
        active_reports = get_login_list(redis,session['id'],date)
        return json.dumps(active_reports)
    else:
        info = {
                'title'                  :          '[%s]统计列表'%(date),
                'listUrl'                :           BACK_PRE+'/statistics/active/showDay?list=1&day=%s'%(date),
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_statistics_login_list',PAGE_LIST=PAGE_LIST,date=date,info=info,RES_VERSION=RES_VERSION,lang=lang)


@admin_app.get('/statistics/history')
def get_history_active_page(redis,session):
    """
    活跃人数统计
    """
    curTime = datetime.now()
    lang = getLang()

    isList = request.GET.get('list','').strip()
    start_date = request.GET.get('startDate','').strip()
    end_date = request.GET.get('endDate','').strip()
    selfUid = session['id']

    if isList:
        active_reports = get_active_reports_history(redis,selfUid,start_date,end_date)
        return json.dumps(active_reports)
    else:
        info = {
                'title'                  :          '活跃人数统计历史',
                'listUrl'                :           BACK_PRE+'/statistics/history?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_statistics_history_list',PAGE_LIST=PAGE_LIST,info=info,RES_VERSION=RES_VERSION,lang=lang)
