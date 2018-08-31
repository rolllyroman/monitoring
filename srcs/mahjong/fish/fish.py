#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    捕鱼大厅接口
"""

from bottle import request, Bottle, redirect, response,default_app
from web_db_define import *
import mahjong_pb2
import poker_pb2
import replay4proto_pb2
from talk_data import sendTalkData
from wechat.wechatData import *
from common.install_plugin import install_redis_plugin,install_session_plugin
from common.log import *
from common.utilt import allow_cross,getInfoBySid
from fish_util.fish_func import *
#from config.config import *
from fish_config import consts
from datetime import datetime, date, timedelta
from model.goodsModel import *
from model.userModel import do_user_modify_addr,do_user_del_addr,get_user_exchange_list
from model.hallModel import *
from model.protoclModel import sendProtocol2GameService
from model.mailModel import *
from model.agentModel import *
from model.fishModel import get_room_list
from common import web_util,log_util,convert_util
import time
import urllib2
import json
import random
import md5
import re
import pdb
from urlparse import urlparse
from fish_utils import *

from model import mysql

from decimal import Decimal

#from pyinapp import *
ACCEPT_NUM_BASE = 198326
ACCEPT_TT = [md5.new(str(ACCEPT_NUM_BASE+i)).hexdigest() for i in xrange(10)]
SESSION_TTL = 60*60
CHECK_SUCCESS = 1
#生成捕鱼APP
fish_app = Bottle()
#获取配置
conf = default_app().config
#安装插件
install_redis_plugin(fish_app)
install_session_plugin(fish_app)

import fish_broad
import fish_invite
import fish_pay
import fish_exchange

FORMAT_PARAMS_POST_STR = "%s = request.forms.get('%s','').strip()"
FORMAT_PARAMS_GET_STR  = "%s = request.GET.get('%s','').strip()"
#用户信息
USER_INFO = ('headImgUrl', 'sex', 'isVolntExitGroup','coin','exchange_ticket')

DEFAULT_AGENT_ID = '540302'
# DEFAULT_AGENT_ID = '000000'


def join_group(redis, session, user_id, code):
    """ 加入工会

    """
    curTime = datetime.now()
    user_id = user_id
    code = code
    
    if not redis.hexists(EXCHANGE_AGENT_INTO, code):
        return {"code": 1, "msg": "邀请码不存在"}

    agent_id = redis.hget(EXCHANGE_AGENT_INTO, code)

    userTable = "users:%s" % user_id
    adminTable = AGENT_TABLE%(agent_id)
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}

    if not (redis.exists(adminTable)):
        return {'code':-1, 'msg':'加入公会失败, 公会不存在'}

    agValid,auto_check = redis.hmget(adminTable,('valid','auto_check'))
    if not auto_check:
        auto_check = CHECK_SUCCESS
    auto_check = int(auto_check)
    if agValid != '1':
        print  '[JoinRoom][info] agentId[%s] has freezed. valid[%s] '%(groupId,agValid)
        return {'code':-7,'msg':'该公会已被冻结,不能申请加入'}

    type = redis.hget(adminTable, 'type')
    if int(type) == 1:
        print '[%s][HALL][url:/joinGroup][info] code[%s] sid[%s] groupId[%s] type[%s]'%(curTime,-1,sid,groupId,type)
        return {'code':-1, 'msg':'加入公会失败，不能直接加入总公司。'}

    id = userTable.split(':')[1]
    account = redis.hget(userTable, "account")

    #自动退出当前公会
    groupId4old = redis.hget(userTable, 'parentAg')
    adminTable4Old = AGENT_TABLE%(groupId4old)
    if redis.exists(adminTable4Old) and redis.exists(userTable):
        tryExitGroup(redis, userTable, account, id, groupId4old)
    topAgent = getTopAgentId(redis, agent_id)
    #如果存在,绑定
    pipe = redis.pipeline()
    if auto_check == CHECK_SUCCESS:
        pipe.hset(FORMAT_USER_TABLE%(id),'parentAg',agent_id)
        pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(agent_id), id)
    pipe.lpush(JOIN_GROUP_LIST%(agent_id), id)
    pipe.set(JOIN_GROUP_RESULT%(id), '%s:%s:%s'%(agent_id,auto_check,curTime.strftime('%Y-%m-%d %H:%M:%S')))
    pipe.execute()
    # if auto_check == CHECK_SUCCESS:
    return {'code':0, 'msg':'成功', "data": {"agent_id": agent_id, "top_agent": topAgent, "level": 3, "exchangeIntoCode": code}}
    #return {'code':0, 'msg':'等待公会确认中'}


@fish_app.post('/login')
@allow_cross
def do_login(redis,session):
    """
    大厅登录接口

    """
    tt = request.forms.get('tt', '').strip()
    curTime = datetime.now()
    ip = web_util.get_ip()
    getIp = request['REMOTE_ADDR']
    _account = request.forms.get('account', '').strip()
    clientType = request.forms.get('clientType', '').strip()
    intoGroupId = request.forms.get('groupId','').strip()
    if not clientType:
        clientType = 0
    passwd = request.forms.get('passwd', '').strip()
    login_type = request.forms.get('type', '').strip() #登录类型
    login_type = int(login_type)
    sid=0
    log_util.debug("[ do_login ] account[%s] intoGroupid [%s] " % (_account, intoGroupId))

    try:
        log_util.debug('[on login]account[%s] clientType[%s] passwd[%s] type[%s]'%(_account, clientType, passwd, login_type))
    except Exception as e:
        print 'print error File', e

    login_pools = redis.smembers(FORMAT_LOGIN_POOL_SET)
    log_util.debug('[try do_login] account[%s] login_pools[%s]'%(_account,login_pools))

    if _account in login_pools:
        log_util.debug('[try do_login] account[%s] is already login.'%(_account))
        return {'code':0}
    dgid=DEFAULT_AGENT_ID
    #dgid='407522'
    DEFAULT_GID=DEFAULT_AGENT_ID # 默认公会暂不开放
    #DEFAULT_GID='407522'#默认公会暂不开放
    defaultgid=''


    redis.sadd(FORMAT_LOGIN_POOL_SET,_account)
    log_util.debug('[try do_login] account[%s] login_pools[%s]'%(_account,login_pools))
    reAccount, rePasswd = onRegFish(redis, _account, passwd, login_type, ip)

    if reAccount:
        if login_type:
            realAccount = redis.get(WEIXIN2ACCOUNT4FISH%(reAccount))
        else:
            realAccount = reAccount
        #读取昵称和group_id
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
        userTable = redis.get(account2user_table)
        id = userTable.split(':')[1]
        if not redis.sismember(ACCOUNT4WEIXIN_SET4FISH, realAccount): #初次登录
            redis.sadd(ACCOUNT4WEIXIN_SET4FISH, realAccount)
            redis.sadd(FORMAT_REG_DATE_TABLE4FISH%(curTime.strftime("%Y-%m-%d")), realAccount)
            
        #     redis.hset(userTable, 'coin', consts.GIVE_COIN_FIRST_LOGIN)
        account, name, groupId,loginIp, loginDate, picUrl, gender,valid, lockCount, ownAgent = \
                redis.hmget(userTable, ('account', 'nickname', 'parentAg', 'lastLoginIp',\
                'lastLoginDate', 'picUrl', 'gender','valid', 'lockCount', "ownAgent"))
        if intoGroupId != '' and (groupId == DEFAULT_AGENT_ID or not groupId):
            DEFAULT_GID = intoGroupId

        topAgent = getTopAgentId(redis, groupId)
        if not topAgent:
            groupId = None            

        if not groupId or (intoGroupId != '' and (groupId == DEFAULT_AGENT_ID or not groupId)):
            print(u"加入公会")
            curTime=datetime.now()
            pipe = redis.pipeline()
            agValid, auto_check, groupType = redis.hmget(AGENT_TABLE%(DEFAULT_GID), ('valid', 'auto_check', 'type'))
            if agValid == '1' and groupType != '1':
                if not auto_check:
                    auto_check = CHECK_SUCCESS
            # if auto_check == CHECK_SUCCESS:
            pipe.hset(FORMAT_USER_TABLE%(id),'parentAg',DEFAULT_GID)
            pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(DEFAULT_GID), id)
            pipe.lpush(JOIN_GROUP_LIST%(DEFAULT_GID), id)
            pipe.set(JOIN_GROUP_RESULT%(id), '%s:%s:%s'%(DEFAULT_GID,auto_check,curTime.strftime('%Y-%m-%d %H:%M:%S')))
            pipe.execute()
            groupId = DEFAULT_GID

        if not lockCount:
            lockCount = 0
        else:
            lockCount = int(lockCount)

        agentTable = AGENT_TABLE%(groupId)
        isTrail, shop, parent_id = redis.hmget(agentTable,('isTrail','recharge', 'parent_id'))
        if not isTrail:
            isTrail = 0

        level = 3
        own_level = -1
        topAgent = getTopAgentId(redis, groupId)
        print(u"顶级公会ID：%s" % topAgent)
        # if ownAgent:
        #     own_parent_id = redis.hget(AGENT_TABLE%(ownAgent), "parent_id")
        #     intOwn_parent_id = int(own_parent_id) if own_parent_id else 0
        #     if intOwn_parent_id == 1:
        #         level = 1
        #     elif intOwn_parent_id == 0:
        #         level = 3
        #     else:
        #         level = 2
        # else:
        #     ownAgent = ''
        topManager = redis.smembers("agent:%s:manager:member:set" % topAgent)
        parentManager = redis.smembers("agent:%s:manager:member:set" % groupId)
        if id in topManager:
            level = 1
        elif id in parentManager:
            level = 2
        else:
            level = 3

        exchangeIntoCode = redis.hget(EXCHANGE_AGENT_CODE, groupId)
        if not exchangeIntoCode:
            exchangeIntoCode = SecretKeysInto(redis, groupId)


        #默认开放
        shop = 1
        shop = int(shop)
        #会话信息
        type2Sid = {
            True     :  sid,
            False    :  md5.new(str(id)+str(time.time())).hexdigest()
        }
        sid = type2Sid[login_type == 3]
        SessionTable = FORMAT_USER_HALL_SESSION%(sid)
        if redis.exists(SessionTable):
            log_util.debug("[try do_login] account[%s] sid[%s] is existed."%(curTime,realAccount,sid))
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return {'code':-1, 'msg':'链接超时'}

        urlRes = urlparse(request.url)
        serverIp = ''
        serverPort = 0
        gameid = 0
        loginMsg = []

        userInfo = {'name':name,'isTrail':int(isTrail),'shop':int(shop),
                    'agent_id':groupId,'account':reAccount,
                    "parent_id":parent_id,
                    'passwd':rePasswd, 
                    "level": level, 
                    "top_agent": topAgent,
                    "user_id": id,
                    "exchangeIntoCode": exchangeIntoCode
                    }
        joinNum = ''
        id = userTable.split(':')[1]
        joinMessage = redis.get(JOIN_GROUP_RESULT%(id))
        if joinMessage:
            try:
                joinMessage = joinMessage.split(':')
                joinNum = int(joinMessage[0])
                joinResult = int(joinMessage[1])
                userInfo['applyId'] = joinNum
                if joinResult == 1:
                    redis.delete(JOIN_GROUP_RESULT%(id))
            except Exception as err:
                print("ERROR joinMessage: %s, %s" % (JOIN_GROUP_RESULT%(id), err) )

        key = redis.get(ACCOUNT2WAIT_JOIN_PARTY_TABLE%account)
        # for key in redis.keys(WAIT_JOIN_PARTY_ROOM_PLAYERS%('*', '*', '*')):
        if key:
            if account in redis.lrange(key, 0, -1):
                try:
                    gameId, serviceTag = redis.get('account:%s:wantServer'%account).split(',')
                    message = HEAD_SERVICE_PROTOCOL_NOT_JOIN_PARTY_ROOM%(account, ag)
                    redis.lpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, serviceTag), message)
                except:
                    print '[account wantServer][%s]'%(redis.get('account:%s:wantServer'%account))
                redis.lrem(key, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,_account)
            return {'code':0, 'sid':sid, 'userInfo':userInfo, 'gameInfo':gameInfo, 'gameState':gameState}
        else:
            if joinNum:
                redis.srem(FORMAT_LOGIN_POOL_SET,_account)
                return {'code':0, 'sid':sid, 'userInfo':userInfo, 'joinResult':joinResult, 'loginMsg':loginMsg, }
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return {'code':0, 'sid':sid, 'userInfo':userInfo, 'loginMsg':loginMsg}
    else: #失败
        redis.srem(FORMAT_LOGIN_POOL_SET,_account)
        return {'code':101, 'msg':'账号或密码错误或者微信授权失败'}

@fish_app.get("/exchange/agentCode")
@allow_cross
def agentCode(redis, session):
    """ 效验兑换码， 成功则加入代理
    
    """
    user_id = request.params.get("user_id", '').strip()
    code = request.params.get("code", '').strip()
    # agent_id = request.params.get("agent_id", '').strip()
    if len(code) == 12:
        result = join_group(redis, session, user_id, code)
        return result
    exchangeIntoCode = code
    exchageList = redis.smembers(EXCHANGE_AGENT_LIST)


    print("%s, %s" % (code, exchageList))
    if code in exchageList:
        # 查询对应的公会ID
        agent_id = redis.hget("users:%s" % user_id, "parentAg")
        topAgent  = getTopAgentId(redis, agent_id)



        findCurAgent = redis.hget(EXCHANGE_AGENT_FIND, agent_id)
        findTopAgent = redis.hget(EXCHANGE_AGENT_FIND, topAgent)
        print(agent_id)
        if findCurAgent != code and findTopAgent != code:

            if agent_id == DEFAULT_AGENT_ID:
                intoAgent = None
                # 检查AGNET对应的所有CODE
                codeList = redis.hgetall(EXCHANGE_AGENT_FIND)
                for aid, value in codeList.items():
                    if value == code:
                        intoAgent = aid
                        break
                managerUser = redis.smembers("agent:%s:manager:member:set" % intoAgent)
                if len(managerUser) > 3:
                    return {"code": 1, "msg": "管理员已经超出限定."}

                if intoAgent:
                    agent_id = intoAgent
                    DEFAULT_GID = agent_id
                    topAgent = getTopAgentId(redis, agent_id)
                    id = user_id
                    if topAgent == agent_id:
                        child = redis.smembers("agents:id:%s:child" % agent_id)
                        if not child:
                            return {"code": 1, "msg": "该公会并不存在二级代理，暂时无法加入和设置."}
                        agent = random.choice(list(child))
                        DEFAULT_GID = agent


                    curTime = datetime.now()
                    pipe = redis.pipeline()
                    agValid, auto_check, groupType = redis.hmget(AGENT_TABLE % (DEFAULT_GID), ('valid', 'auto_check', 'type'))
                    if agValid == '1' and groupType != '1':
                        if not auto_check:
                            auto_check = CHECK_SUCCESS

                    # if auto_check == CHECK_SUCCESS:
                    pipe.hset(FORMAT_USER_TABLE % (id), 'parentAg', DEFAULT_GID)
                    pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE % (DEFAULT_GID), id)
                    pipe.lpush(JOIN_GROUP_LIST % (DEFAULT_GID), id)
                    pipe.set(JOIN_GROUP_RESULT % (id),
                             '%s:%s:%s' % (DEFAULT_GID, auto_check, curTime.strftime('%Y-%m-%d %H:%M:%S')))
                    pipe.execute()
            else:
                return {"code": 1, "msg": "效验码已经失效"}
        else:
            if findTopAgent == code:
                agent_id = topAgent
        print(agent_id)
        managerUser = redis.smembers("agent:%s:manager:member:set" % agent_id)
        if user_id in managerUser:
            return {"code": 1, "msg":"你已经是管理员了" }
        number = len(managerUser)
        number += 1

        # 查看公会等级
        aType = redis.hget(AGENT_TABLE % agent_id, "type")
        aType = int(aType)
        if number > 3:
            return {"code": 1, "msg": "管理人数不能超过3个"}

        if aType == 1:
            level = 1
        elif aType == 2:
            level = 2
        else:
            level = 3
        #exchangeIntoCode = ''
        if level in [2, 3]:
           exchangeIntoCode = redis.hget(EXCHANGE_AGENT_CODE, agent_id)

        if redis.exists("users:%s" % user_id):
            redis.sadd("agent:%s:manager:member:set" % agent_id, user_id)
        return {"code": 0, "msg": "成功", "data": {"level": level, "top_agent": topAgent, "agent_id": agent_id, "exchangeIntoCode": exchangeIntoCode}}
    return {"code": 1, "msg": "失败， 你的兑换码不正确."}

@fish_app.get("/agent/child")
@allow_cross
def agent_child(redis, session):
    "获取下级公会列表"

    agent_id = request.params.get("agent_id", '').strip()
    user_id = request.params.get("user_id", '').strip()
    userTable = FORMAT_USER_TABLE % user_id
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}
        
    managerUser = redis.smembers("agent:%s:manager:member:set" % agent_id)
    if user_id not in managerUser:
        return {"code": -1, "msg": "你没有权限操作该工会"}

    agent_list = []
    for i in redis.smembers("agents:id:%s:child" % agent_id):
        tmp =  AGENT_TABLE%(i)
        valid, regDate = redis.hmget(tmp, "valid", "regDate")
        # 获取需邀请码信息
        code = redis.hget(EXCHANGE_AGENT_FIND, i)
        manager_id = redis.smembers("agent:%s:manager:member:set" % agent_id)
        exchangeIntoCode = redis.hget(EXCHANGE_AGENT_CODE, i)
        if not exchangeIntoCode:
            exchangeIntoCode = SecretKeysInto(redis, i)
        valid = int(valid) if valid else 0
        user = []
        for _manager in manager_id:
            tmpuserTable = "users:%s" % _manager
            name, headImg, sex = redis.hmget(tmpuserTable, "name", "headImgUrl", "sex")
            user.append({"name": name, "avatar_url": headImg, "sex": int(sex), "user_id": int(_manager) })

        number = len(redis.smembers(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE %(i)))
        agentdict = {
            "agent_id": i,
            "manager": user,
            "number" : number,
            "valid"  : int(valid),
            "reg_date" : regDate,
            "exchangeIntoCode": exchangeIntoCode,
            "code": code
        }
        agent_list.append(agentdict)

    return {"code": 0, "msg": "成功", "list": agent_list}


@fish_app.post("/agent/child")
@allow_cross
def agent_addchild(redis, session):
    "新增下级公会"
    agent_id = request.forms.get("agent_id", '').strip()
    user_id  = request.forms.get("user_id", '').strip()
    target_user_id = int(time.time()) / random.randint(1, 10)
    shareRate = 0 
    defaultRoomCard = 0 
    curTime = datetime.now()
    now_date = curTime.strftime('%Y-%m-%d')

    userTable = "users:%s" % user_id
    adminTable = AGENT_TABLE%(agent_id)
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}

    if not (redis.exists(adminTable)):
        return {'code':-1, 'msg':'公会不存在'}

    managerUser = redis.smembers("agent:%s:manager:member:set" % agent_id)
    if user_id not in managerUser:
        return {"code": -1, "msg": "你没有权限操作该工会"}
    myRate = 0
    myRate = 0
    parentAg = agent_id
    agent_type,is_trail,parent_unitPrice, parent_id = redis.hmget(AGENT_TABLE%(agent_id),('type','isTrail','unitPrice', "parent_id"))
    parent_id = int(parent_id) if parent_id else 0
    if parent_id != 1:
        return {"code":1, "msg": "你不属于一级工会，不能添加工会"}

    account =  target_user_id
    admimtoIdTalbel = AGENT_ACCOUNT_TO_ID%(account)
    parentSetTable  =  AGENT_CHILD_TABLE%(parentAg)
    # 查看下级代理
    SetTables = redis.smembers(parentSetTable)
    if len(SetTables) > 10:
        return {"code": 1, "msg": "你的下级公会超过了上限"}

    pipe = redis.pipeline()
    unitPrice     = 0
    id_no = getAgentIdNo(redis)
    is_trail = int(is_trail) if is_trail else 0
    recharge,create_auth,open_auth ='1','0','0'
    agentType = int(agent_type)+1
    agentInfo = {
            'id'                    :           id_no,
            'account'               :           account,
            'passwd'                :           hashlib.sha256("ertyjklzc").hexdigest(),
            'name'                  :           '',
            'shareRate'             :           shareRate,
            'valid'                 :            1,
            'roomcard_id'           :           0,
            'parent_id'             :           agent_id,
            'roomcard'              :           0,
            'regIp'                 :           '127.0.0.1',
            'regDate'               :           convert_util.to_dateStr(curTime.now(),"%Y-%m-%d %H:%M:%S"),
            'lastLoginIP'           :           1,
            'lastLoginDate'         :           1,
            'isTrail'               :           is_trail,
            'unitPrice'             :           unitPrice,
            'recharge'              :           recharge,
            'isCreate'              :           '1',
            'create_auth'           :           create_auth,
            'open_auth'             :           open_auth,
            'type'                  :           agentType,
            'defaultRoomCard'       :           defaultRoomCard,
            "super_manager"         :           target_user_id,
    }

    adminTable  =  AGENT_TABLE%(id_no)
    if unitPrice:
        pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(id_no),unitPrice)

    if shareRate and agent_type in ['0','1','2']:
        if agent_type == '1':
            unitPrice = parent_unitPrice
        elif agent_type == '2':
            unitPrice = get_user_card_money(redis,parent_id)
        pipe.sadd(AGENT_RATE_SET%(id_no),shareRate)
        pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(id_no),unitPrice)

    #创建日期索引
    pipe.sadd(AGENT_CREATE_DATE%(now_date),id_no)
    pipe.hmset(adminTable,agentInfo)
    #创建代理账号映射id
    pipe.set(admimtoIdTalbel,id_no)
    #将该代理添加进父代理集合
    pipe.set(AGENT2PARENT%(id_no),parent_id)
    #创建代理账号的父Id映射
    pipe.sadd(parentSetTable,id_no)
    # pipe.hset(FORMAT_USER_TABLE % target_user_id, "ownAgent", id_no)
    extendCode = SecretKeys(redis)
    
    intoCode   = SecretKeysInto(redis, id_no)
    
    pipe.hset(EXCHANGE_AGENT_FIND, id_no, extendCode)
    pipe.execute()
    return {"code": 0, "msg": "成功", "extendCode": extendCode, "agent_id": id_no, "exchangeIntoCode": intoCode}

@fish_app.get("/agent/child/<child_id>")
@allow_cross
def agent_child_get_one(redis, session, child_id = None):
    "获取下级公会的信息"
    child_id = child_id 
    agent_id = request.forms.get("agent_id", '').strip()
    user_id  = request.forms.get("user_id", '').strip()

    userTable = FORMAT_USER_TABLE % user_id
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}
    if not redis.exists(AGENT_TABLE % agent_id):
        return {'code':1,'msg':'公会不存在'}

    managerUser = redis.smembers("agent:%s:manager:member:set" % agent_id)
    if user_id not in managerUser:
        return {"code": -1, "msg": "你没有权限操作该工会"}

    tmp =  AGENT_TABLE%(child_id)
    manager_id = redis.hmget(tmp, "super_manager", "shaRate")
    tmpuserTable = "users:%s" % user_id
    name, headImg, sex = redis.hmget(tmpuserTable, "name", "headImgUrl", "sex")
    # number = len(redis.smembers("agents:id:%s:users" % i))
    number = len(redis.smembers(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE %(child_id)))
    agentdict = {
        "agent_id": i,
        "manager_user_id" : manager_id,
        "user_number": number,
        "manager_head_image": headImg,
        "manager_user_name": name,
        "sex": sex
    }

    return {"code": 0, "data": agentdict}

@fish_app.post("/agent/child/<child_id>")
@allow_cross
def agent_child_get_one(redis, session, child_id = None):
    "冻结公会"
    child_id = child_id 
    agent_id = request.forms.get("agent_id", '').strip()
    user_id  = request.forms.get("user_id", '').strip()
    userTable = FORMAT_USER_TABLE % user_id
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}

    if not redis.exists(AGENT_TABLE % agent_id):
        return {'code':1,'msg':'公会不存在'}

    managerUser = redis.smembers("agent:%s:manager:member:set" % agent_id)
    if user_id not in managerUser:
        return {"code": -1, "msg": "你没有权限操作该工会"}

    agentList = redis.smembers("agents:id:%s:child" % agent_id)
    if child_id not in agentList:
        return {"code": 1, "msg": "失败"}

    adminTable = AGENT_TABLE%(child_id)
    redis.hset(adminTable,'valid','1')
    return {"code": 0, "msg": "成功"}



@fish_app.post("/order")
@allow_cross
def orderSave(redis, session):
    """ 存储捕鱼订单信息

    """
    #appid = request.forms.get("appid", '').strip()
    #mch_id = request.forms.get("mch_id", '').strip()
    #device_info = request.forms.get("device_info", '').strip()
    #nonce_str = request.forms.get("nonce_str", '').strip()
    #sign = request.forms.get("sign", '').strip()
    #result_code = request.forms.get("result_code", '').strip()
    #err_code = request.forms.get("err_code", '').strip()
    #err_code_des = request.forms.get("err_code_des", '').strip()
    #openid = request.forms.get("openid", '').strip()
    #is_subscribe = request.forms.get("is_subscribe", '').strip()
    #trade_type = request.forms.get("trade_type", '').strip()
    #bank_type = request.forms.get("bank_type", '').strip()
    #total_fee = request.forms.get("total_fee", '').strip()
    #fee_type = request.forms.get("fee_type", '').strip()
    #cash_fee = request.forms.get("cash_fee", '').strip()
    #cash_fee_type = request.forms.get("cash_fee_type", '').strip()
    #coupon_fee	= request.forms.get("coupon_fee", '').strip()
    #coupon_count = request.forms.get("coupon_count", '').strip()
    #transaction_id = request.forms.get("transaction_id", '').strip()
    #out_trade_no = request.forms.get("out_trade_no", '').strip()
    #attach = request.forms.get("attach", '').strip()
    #time_end = request.forms.get("time_end", '').strip()

    # 游戏的订单号，游戏账号和消费点
    user_id = request.forms.get("user_id", '').strip()
    payResult = request.forms.get("pay_result", '').strip()
    order_no = request.forms.get("order_no", '').strip()
    consume = request.forms.get("consume", '').strip()
    agent_id = request.forms.get("agent_id", '').strip()
    topAgent = request.forms.get("top_agent", '').strip()
    level = request.forms.get("level", '').strip()



    pre_balance = request.forms.get("pre_balance", '').strip()
    after_balance = request.forms.get("after_balance", '').strip()
    status = request.forms.get("status", '').strip()
    balance = request.forms.get("balance", '').strip()
    bill_time = request.forms.get("bill_time", '').strip()
    user_account = request.forms.get("user_account", '').strip()
    
    

    try:
        status = int(status)
        pre_balance = Decimal(pre_balance)
        after_balance = Decimal(after_balance)
        balance = Decimal(balance)
        bill_time = int(bill_time)
    except Exception as err:
        return {"code": 1, 'msg': "错误的时间戳"}
    

    userTable = "users:%s" % user_id
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}

    try:
        payResult = json.loads(payResult)
    except Exception as err:
        return {'code':1,'msg':'微信信息出错，请传递一个正确格式的JSON'}

    payResult = json.dumps(payResult)

    name, avatar_url = redis.hmget(userTable, "nickname", "headImgUrl")
    
    create_time = int(time.time())
    
    """
    pre_balance = request.forms.get("pre_balance", '').strip()
    after_balance = request.forms.get("after_balance", '').strip()
    status = request.forms.get("status", '').strip()
    balance = request.forms.get("balance", '').strip()
    bill_time = request.forms.get("bill_time", '').strip()
    

    """

    sql = """
    INSERT INTO `accounts` 
    (`user_id`, `user_name`, `avatar_url`, `level`, `order_no`, `consume`, `agent_id`, `top_agent`, `pay_result`,
     `create_time`, `pre_balance`, `after_balance`, `status`, `balance`, `bill_time`, `account`) 
    VALUES (:user_id, :user_name, :avatar_url, :level, :order_no, :consume,
            :agent_id, :top_agent, :pay_result, :create_time,
            :pre_balance, :after_balance, :status, :balance, :bill_time, :user_account
            );
    """
    
    result = mysql.insert(sql, 
        {
        "user_id": user_id,
        "user_name": name,
        "order_no": order_no,
        "avatar_url": avatar_url,
        "level": level,
        "consume": consume,
        "agent_id": agent_id,
        "top_agent": topAgent,
        "pay_result": payResult,
        "create_time": create_time,
        "pre_balance": pre_balance,
        "after_balance": after_balance,
        "status": status,
        "balance": balance,
        "bill_time": bill_time,
        "user_account": user_account
        })
    if not result:
        return {"code": 1, "msg": "写入失败"}

    return {"code": 0, "msg": "成功"}

@fish_app.post("/user/relate")
@allow_cross
def relate(redis, session):
    """ 存储用户关联信息

    """
    user_id = request.params.get("user_id", '').strip()
    number = request.params.get("number", '').strip()

    userTable = "users:%s" % user_id
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}

    # redis.smembers("users:relate:%s:set" % user_id)
    pipe = redis.pipeline()
    pipe.sadd("users:relate:%s:set" % user_id, number)
    pipe.hset("users:relate:number:hset", number, user_id)
    pipe.execute()

    return {"code": 0, 'msg': "成功"}

@fish_app.post("/check")
@allow_cross
def check(redis, session):
    userid = request.params.get("userid", '').strip()
    id = userid
    userTable = "users:%s" % userid
    if not redis.exists(userTable):
        return {'code':-5,'msg':'该用户不存在'}
    
    parentAg = redis.hget(userTable,'parentAg')
    topAgent = getTopAgentId(redis, parentAg)
    groupId=parentAg
    if True:
        
        agentTable = AGENT_TABLE%(groupId)
        isTrail, shop, parent_id = redis.hmget(agentTable,('isTrail','recharge', 'parent_id'))
        if not isTrail:
            isTrail = 0

        level = 3
        own_level = -1
        topAgent = getTopAgentId(redis, groupId)
        print(u"顶级公会ID：%s" % topAgent)
        # if ownAgent:
        #     own_parent_id = redis.hget(AGENT_TABLE%(ownAgent), "parent_id")
        #     intOwn_parent_id = int(own_parent_id) if own_parent_id else 0
        #     if intOwn_parent_id == 1:
        #         level = 1
        #     elif intOwn_parent_id == 0:
        #         level = 3
        #     else:
        #         level = 2
        # else:
        #     ownAgent = ''
        topManager = redis.smembers("agent:%s:manager:member:set" % topAgent)
        parentManager = redis.smembers("agent:%s:manager:member:set" % groupId)
        if id in topManager:
            level = 1
        elif id in parentManager:
            level = 2
        else:
            level = 3

        exchangeIntoCode = redis.hget(EXCHANGE_AGENT_CODE, groupId)
        if not exchangeIntoCode:
            exchangeIntoCode = SecretKeysInto(redis, groupId)


        #默认开放
        shop = 1
        shop = int(shop)
        #会话信息
        # type2Sid = {
        #     True     :  sid,
        #     False    :  md5.new(str(id)+str(time.time())).hexdigest()
        # }
        # sid = type2Sid[login_type == 3]
        # SessionTable = FORMAT_USER_HALL_SESSION%(sid)
        # if redis.exists(SessionTable):
        #     log_util.debug("[try do_login] account[%s] sid[%s] is existed."%(curTime,realAccount,sid))
        #     redis.srem(FORMAT_LOGIN_POOL_SET,account)
        #     return {'code':-1, 'msg':'链接超时'}

        #urlRes = urlparse(request.url)
        serverIp = ''
        serverPort = 0
        gameid = 0
        loginMsg = []
        name=''
        
        userInfo = {
                    'agent_id':groupId,
                    "parent_id":parent_id,                    
                    "level": level, 
                    "top_agent": topAgent,
                    "user_id": id,
                    "exchangeIntoCode": exchangeIntoCode
                    }
    
    return {'code':0,'userInfo':userInfo}