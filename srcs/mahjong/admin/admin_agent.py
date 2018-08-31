#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    代理模块
"""
from bottle import *
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,RES_VERSION
from common.utilt import *
from common.log import *
from datetime import datetime
from web_db_define import *
from model.agentModel import *
from model.userModel import *
from access_module import *
from common import convert_util,web_util,json_util
from model.protoclModel import sendProtocol2GameService
import hashlib
import json
import random
import time
from wechat.wechatData import fishShareCode
import urllib

from model import userModel

GET_FORMS = "%s = request.GET.get('%s','').strip()"
POST_FORMS = "%s = request.forms.get('%s','').strip()"

@admin_app.get('/agent/list')
@checkAccess
def getAgentList(redis,session):
    """
    代理列表
    """
    lang    = getLang()
    #fields = ('isList','id','searchId','start_date','end_date')
    fields = ('isList','id','searchId','start_date','end_date')
    for field in fields:
        exec(GET_FORMS%(field,field))

    if not id:
        id = session['id']

    adminTable = AGENT_TABLE%(id)
    creatAgUrl = BACK_PRE + '/agent/create'
    #搜索条件
    condition = {'start_date':start_date,'end_date':end_date,'searchId':searchId}
    create_auth,aType = redis.hmget(adminTable,('create_auth','type'))

    create_auth = convert_util.to_int(create_auth)

    if redis.sismember(AGENT2ACCESSBAN%(id),creatAgUrl):
        createAg = '0'
    else:
        createAg = '1'

    if isList:
        res = getAgListInfos(redis,session,id,condition,lang)
        return json.dumps(res)
    else:
        info = {
                'title'                  :       '下线代理列表(%s)'%(lang.TYPE_2_ADMINTYPE[str(int(aType)+1)]),
                'showPlus'               :       'true' if aType in ['0','1'] else 'false',
                "agent_id"               :       id,
                'createAccess'           :       createAg,
                'atype'                  :       aType,
                'searchTxt'              :       '公会/代理ID',
                'createUrl'              :       BACK_PRE+'/agent/create',
                'listUrl'                :       BACK_PRE+'/agent/list?isList=1',
                'create_auth'            :       create_auth,
                'show_date_search'       :       True,
                'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
        }
        return template('admin_agent_list',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/agent/info')
@admin_app.get('/agent/info/<agent_id>')
def get_agent_info(redis,session,agent_id=None):
    """
    代理信息查看
    """
    curTime = datetime.now()
    lang    = getLang()

    if not agent_id:
        abort(404,'Nont Found')

    adminTable = AGENT_TABLE%(agent_id)
    account,name,roomCard,regDate,regIp,valid,aType = \
                redis.hmget(adminTable,('account','name','roomcard','regDate','regIp','valid','type'))

    userDict = []
    manager = redis.smembers("agent:%s:manager:member:set" % agent_id)
    for ids in manager:
        if not redis.exists("users:%s" % ids):
            continue
        nickname, avatar_url = redis.hmget("users:%s" % ids, "nickname", "headImgUrl")
        userDict.append(
            {
                "user_id": ids,
                "name": nickname,
                "avatar_url": avatar_url
             }

        )
    agentInfo = {
            'title'         :        '代理[%s]详细信息'%(account),
            'backUrl'       :        BACK_PRE+'/agent/list',
            'name'          :        name,
            'account'       :        account,
            'roomCard'      :        '无限制' if aType == '0' else roomCard,
            'regDate'       :        regDate,
            'regIp'         :        regIp,
            'valid'         :        '有效' if valid == '1' else '冻结',
            'aType'         :        lang.TYPE_2_ADMINTYPE[aType],
            'aid'           :        agent_id,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            "userDict"      : userDict
    }

    return template('admin_agent_info',info=agentInfo,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get("/agent/qrcode/<agent_id>")
def get_qrcode(redis,session, agent_id):

    # path = qrCodeImageSave("http://wxfish.dongshenggame.cn/?rid=gid:%s" % agent_id)
    url = "http://wxfish.dongshenggame.cn/?rid=gid:%s" % agent_id
    #urlencode = urllib.urlencode({"rid": "gid:%s" % agent_id}).encode("utf8")
    url = fishShareCode(url)
    print(url)
    path = qrCodeImageSave(url)
    print '----------------------------'
    print API_ROOT + '/' + path
    print '----------------------------'
    return {"code": 0, 'path':  API_ROOT + '/' + path}

@admin_app.get('/agent/create')
@admin_app.get('/agent/create/<agent_id>')
def get_agent_create(redis,session,agent_id=None):
    """
    创建代理
    """
    curTime = datetime.now()
    if agent_id:
        agentId = agent_id
    else:
        agentId =  request.GET.get('id','').strip()
    lang    = getLang()

    if not agentId:
        agentId = session['id']

    adminTable = AGENT_TABLE%(agentId)
    aType,shareRate = redis.hmget(adminTable,('type','shareRate'))

    createAgentType = int(aType)+ 1
    if createAgentType == 2:
        url = BACK_PRE+'/agent/create/{}'.format(agentId)
    else:
        url = BACK_PRE+'/agent/createAgentOther/{}'.format(agentId)
    access = getListAccess(createAgentType,lang)

    info = {
            'title'                  :       '创建代理（上级代理:%s）'%(agentId),
            'parentAg'               :       agentId,
            'aType'                  :       aType,
            'backUrl'                :       BACK_PRE+'/agent/list',
            'submitUrl'              :       url,
            'games'                  :       getCreatAgentGames(redis,agentId),
            'defaultGames'           :       redis.smembers(GAME_DEFAULT_BIND),
            'shareRate'              :       shareRate,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
    }

    return template('agent_create',Access=access,info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.post('/agent/create/<agent_id>')
def do_create_agent(redis,session,agent_id=None):
    """
    创建代理操作
    """
    lang = getLang()
    parent_id = agent_id
    account = int(time.time())/random.randint(1, 10)
    admimtoIdTalbel = AGENT_ACCOUNT_TO_ID % (account)
    parentSetTable = AGENT_CHILD_TABLE % (parent_id)
    target_user_id = account
    curTime = datetime.now()
    now_date = curTime.strftime('%Y-%m-%d')
    agent_type, is_trail, parent_unitPrice, parent_id = redis.hmget(AGENT_TABLE % (agent_id),
                                                                    ('type', 'isTrail', 'unitPrice', "parent_id"))
    pipe = redis.pipeline()
    shareRate = 0
    id_no = getAgentIdNo(redis)
    is_trail = int(is_trail) if is_trail else 0
    recharge, create_auth, open_auth = '1', '0', '0'
    agentType = int(agent_type) + 1
    agentInfo = {
        'id': id_no,
        'account': account,
        'passwd': hashlib.sha256('12345678').hexdigest(),
        'name': '',
        'shareRate': shareRate,
        'valid': 1,
        'roomcard_id': 0,
        'parent_id': agent_id,
        'roomcard': 0,
        'regIp': '127.0.0.1',
        'regDate': convert_util.to_dateStr(curTime.now(), "%Y-%m-%d %H:%M:%S"),
        'lastLoginIP': 1,
        'lastLoginDate': 1,
        'isTrail': is_trail,
        'recharge': recharge,
        'isCreate': '1',
        'create_auth': create_auth,
        'open_auth': open_auth,
        'type': agentType,
        'defaultRoomCard': 0,
    }

    adminTable = AGENT_TABLE % (id_no)
    agent_type, is_trail, parent_unitPrice, parent_id = redis.hmget(adminTable,
                                                                    ('type', 'isTrail', 'unitPrice', "parent_id"))


    if shareRate and agent_type in ['0', '1', '2']:
        if agent_type == '1':
            unitPrice = parent_unitPrice
        elif agent_type == '2':
            unitPrice = get_user_card_money(redis, parent_id)
        pipe.sadd(AGENT_RATE_SET % (id_no), shareRate)
        pipe.sadd(AGENT_ROOMCARD_PER_PRICE % (id_no), unitPrice)

    # 创建日期索引
    pipe.sadd(AGENT_CREATE_DATE % (now_date), id_no)
    pipe.hmset(adminTable, agentInfo)
    # 创建代理账号映射id
    pipe.set(admimtoIdTalbel, id_no)
    # 将该代理添加进父代理集合
    pipe.set(AGENT2PARENT % (id_no), parent_id)
    # 创建代理账号的父Id映射
    pipe.sadd(parentSetTable, id_no)
    pipe.hset(FORMAT_USER_TABLE % target_user_id, "ownAgent", id_no)
    
    securyKeys = SecretKeys(redis)
    pipe.hset(EXCHANGE_AGENT_FIND, id_no, securyKeys)
    pipe.execute()

    #创建成功日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
               'ip':request.remote_addr,
               'desc':lang.AGENT_OP_LOG_TYPE['openAgent']%(id_no)}
    selfAccount, selfUid = session['account'], session['id']
    writeAgentOpLog(redis,selfUid,logInfo)
    log_util.debug('[try createAgent] SUCCESS agent create success! info[%s]'%(agentInfo))
    return web_util.do_response(0,msg='创建代理[%s]成功'%(account),jumpUrl='/admin/agent/list')


@admin_app.post('/agent/createAgentOther')
@admin_app.post('/agent/createAgentOther/<agent_id>')
def createAgentOther(redis,session,agent_id=None):
    """
    创建代理操作
    """
    curTime = datetime.now()
    now_date = curTime.strftime('%Y-%m-%d')
    selfUid = session['id']
    lang = getLang()

    for fields in AGENT_FIELDS:
        exec(POST_FORMS%(fields,fields))

    parentAg = agent_id
    if not parentAg:
        return {'code':1,'msg':'非法创建代理!'}


    #当前创建的是
    agent_type,is_trail,parent_unitPrice = redis.hmget(AGENT_TABLE%(parentAg),('type','isTrail','unitPrice'))
    is_trail = convert_util.to_int(is_trail)
    #打印一下
    log_util.debug('[try do_create_agent] parentAg[%s] account[%s] passwd[%s] comfirmPasswd[%s]'\
                    %(parentAg,account,passwd,comfirPasswd))

    checkFields = [
        {'field':account,'msg':'代理账号不能为空'},
        {'field':passwd,'msg':'密码不能为空'},
        {'field':comfirPasswd,'msg':'密码不能为空'}
    ]

    for field in checkFields:
        if not field['field']:
            return {'code':1,'msg':field['msg']}

    if unitPrice and shareRate:
        if float(shareRate) > float(unitPrice):
            return {'code':1,'msg':'给下级分成不能大于钻石单价!'}

    if myRate and shareRate:
        if float(shareRate) > float(myRate):
            return {'code':1,'msg':'给下级分成不能大于自己的分成!'}

    agent_table = AGENT_TABLE%(agentId)
    if redis.exists(agent_table):
        return {'code':1,'msg':'代理ID[%s]已存在'%(agentId)}

    parentSetTable  =  AGENT_CHILD_TABLE%(parentAg)
    if int(parentAg) == 1:
        recharge,create_auth,open_auth ='1','0','0'
    else:
        topAgentId = getTopAgentId(redis,parentAg)
        recharge,create_auth = redis.hmget(AGENT_TABLE%(topAgentId),('recharge','create_auth'))
        open_auth = '0'
        create_auth = convert_util.to_int(create_auth)
        if not recharge:
            recharge = '1'

    admimtoIdTalbel = AGENT_ACCOUNT_TO_ID%(account)
    pipe = redis.pipeline()

    if not redis.exists(admimtoIdTalbel):
        if not agentId:
            agentId = getAgentIdNo(redis)
        else:
            pipe.sadd(AGENT_ID_TABLE,agentId)

        agentType = int(agent_type)+1
        agentInfo = {
                'id'                    :           agentId,
                'account'               :           account,
                'passwd'                :           hashlib.sha256(passwd).hexdigest(),
                'name'                  :           '',
                'shareRate'             :           shareRate,
                'valid'                 :            1,
                'roomcard_id'           :           0,
                'parent_id'             :           parentAg,
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
        }

        adminTable  =  AGENT_TABLE%(agentId)
        if unitPrice:
            pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(agentId),unitPrice)

        if shareRate and agent_type in ['0','1','2']:
            if agent_type == '1':
                unitPrice = parent_unitPrice
            elif agent_type == '2':
                unitPrice = get_user_card_money(redis,parentAg)
            pipe.sadd(AGENT_RATE_SET%(agentId),shareRate)
            pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(agentId),unitPrice)

        #创建日期索引
        pipe.sadd(AGENT_CREATE_DATE%(now_date),agentId)
        pipe.hmset(adminTable,agentInfo)
        #创建代理账号映射id
        pipe.set(admimtoIdTalbel,agentId)
        #将该代理添加进父代理集合
        pipe.set(AGENT2PARENT%(agentId),parentAg)
        #创建代理账号的父Id映射
        pipe.sadd(parentSetTable,agentId)
        # 为该代理绑定拥有的游戏
        setAgentGames(request,redis,parentAg,agentId)
        # 为该代理绑定拥有的权限(通过type)
        setAgentAccess(redis,agentType,agentId)
        # 禁止改代理的列表权限
        banAgentAccess(redis,request,agentType,agentId)
        pipe.execute()
    else:
        log_util.debug('[try crateAgent] agent account[%s] is exists!'%(account))
        return {'code':1,'msg':'代理账号(%s)已经存在.'%(account)}

    #创建成功日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['openAgent']%(agentId)}

    writeAgentOpLog(redis,selfUid,logInfo)
    log_util.debug('[try createAgent] SUCCESS agent create success! info[%s]'%(agentInfo))
    return web_util.do_response(0,msg='创建代理[%s]成功'%(account),jumpUrl='/admin/agent/list')


@admin_app.get('/agent/modify')
@admin_app.get('/agent/modify/<agent_id>')
def getAgentModify(redis,session,agent_id=None):
    """
    代理修改
    """
    curTime = datetime.now()
    agentId =  request.GET.get('id','').strip()
    lang    = getLang()
    if not agent_id:
        abort(404,"Not Found")

    adminTable = AGENT_TABLE%(agent_id)
    agent_type,rate,parentId,account,unitPrice,name,defaultRoomCard = \
                                redis.hmget(adminTable,('type','shareRate','parent_id','account','unitPrice','name','defaultRoomCard'))
    parentAdminTable = AGENT_TABLE%(parentId)
    #父代理的属性
    aType,shareRate = redis.hmget(parentAdminTable,('type','shareRate'))
    log_debug('[%s][admin][ag][info] modify ag.parentId[%s]'%(curTime,agent_id))
    #获取自己的游戏
    ownGames = getAgentOwnGames(redis,agent_id)
    #获取权限
    access = getListAccess(agent_type,lang)
    #获取搬掉的权限
    banAccess = getListBanAccess(redis,agent_id)

    info = {
            'title'                  :       '修改代理（上级代理:%s）'%(parentId),
            'agentId'                :       agent_id,
            'aType'                  :       aType,
            'backUrl'                :       BACK_PRE+'/agent/list',
            'submitUrl'              :       BACK_PRE+'/agent/modify',
            'games'                  :       getAgentGames(redis,parentId,agent_id),
            'ownGames'               :       ownGames,
            'shareRate'              :       shareRate,
            'unitPrice'              :       unitPrice,
            'rate'                   :       rate,
            'account'                :       account,
            'name'                   :       name,
            'defaultRoomCard'        :       defaultRoomCard if defaultRoomCard else 0,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
    }

    return template('admin_agent_modify',Access=access,banAccess=banAccess,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post("/agent/upManager")
def upManager(redis, session):

    fields = ('user_id', "agent_id")
    for field in fields:
        exec("%s = request.forms.get('%s','').strip()"%(field,field))
    print("user: %s" % user_id)
    user_id = user_id.split(",")
    print("upManager : %s %s" % (user_id, agent_id))
    number = len(redis.smembers("agent:%s:manager:member:set" % agent_id))
    number += len(user_id)
    if number > 10:
        return {"code": 1, "msg": "管理人数不能超过10个"}

    for ids in user_id:
        if redis.exists("users:%s" % ids):
            redis.sadd("agent:%s:manager:member:set" % agent_id, ids)

    return {"code": 0, "msg": "成功"}

@admin_app.post("/agent/delete/<agent_id>")
def delete_agent(redis, session, agent_id):

    user_id = request.forms.get('user_id','').strip()
    redis.srem("agent:%s:manager:member:set" % agent_id, user_id)
    curTime = datetime.now()
    auto_check = 1
    default = '540302'
    id = user_id
    userTable = "users:%s" % user_id
    account = redis.hget(userTable, "account")
    groupId4old = redis.hget(userTable, 'parentAg')
    adminTable4Old = AGENT_TABLE%(groupId4old)
    if redis.exists(adminTable4Old) and redis.exists(userTable):
        userModel.tryExitGroup(redis, userTable, account, id, groupId4old)

    pipe = redis.pipeline()
    pipe.hset(FORMAT_USER_TABLE%(id),'parentAg',default)
    pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(default), id)
    pipe.lpush(JOIN_GROUP_LIST%(default), id)
    pipe.set(JOIN_GROUP_RESULT%(id), '%s:%s:%s'%(agent_id,auto_check,curTime.strftime('%Y-%m-%d %H:%M:%S')))
    pipe.execute()

    return {"code": 0, "msg": "成功"}

@admin_app.post('/agent/modify')
@checkAccess
def do_agent_modify(redis,session):
    """
    代理修改接口
    :params agentId 修改的代理ID
    :params account
    """
    curTime = datetime.now()
    fields = ('agentId','account','unitPrice','shareRate','myRate','name','defaultRoomCard')
    for field in fields:
        exec("%s = request.forms.get('%s','').strip()"%(field,field))

    if not agentId:
        return {'code':1,'msg':'非法修改代理!'}

    agent_type,parent_id = redis.hmget(AGENT_TABLE%(agentId),('type','parent_id'))
    log_util.debug('[do_agModify] try to modify agentId[%s] account[%s]'\
                    %(agentId,account))


    if unitPrice and shareRate:
        if float(shareRate) > float(unitPrice):
            return {'code':1,'msg':'给下级分成不能大于钻石单价!'}
    if myRate and shareRate:
        if float(shareRate) > float(myRate):
            return {'code':1,'msg':'给下级分成不能大于父代理的分成!'}

    pipe = redis.pipeline()
    adminTable  =  AGENT_TABLE%(agentId)
    agentInfo = {
                'shareRate'             :           shareRate,
                'unitPrice'             :           unitPrice,
                'name'                  :           name,
                'defaultRoomCard'       :           defaultRoomCard,
    }

    if unitPrice:
        log_util.debug('[modify] unitPrice[%s]'%(unitPrice))
        pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(agentId),unitPrice)

    if shareRate and agent_type in ['1','2']:
        unitPrice = get_user_card_money(redis,agentId)
        log_util.debug('[modify] agentId[%s] shareRate[%s]'%(agentId,unitPrice))
        pipe.sadd(AGENT_RATE_SET%(agentId),shareRate)
        if unitPrice:
            pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(agentId),unitPrice)

    elif myRate and agent_type in ['3']:
        unitPrice = get_user_card_money(redis,agentId)
        log_util.debug('[modify] agentId[%s] shareRate[%s]'%(agentId,unitPrice))
        pipe.sadd(AGENT_RATE_SET%(agentId),myRate)
        pipe.sadd(AGENT_ROOMCARD_PER_PRICE%(agentId),unitPrice)

    pipe.hmset(adminTable,agentInfo)
    #为该代理重新绑定拥有的游戏
    modifyAgentGames(request,redis,agentId)
    # 修改代理的禁用列表权限
    banAgentAccessModify(redis,request,agent_type,agentId)
    pipe.execute()

    #创建成功日志
    log_util.debug('[try do_agent_modify] modify success! info[%s]'%(agentInfo))
    return web_util.do_response(0,'修改代理[%s]成功'%(account),jumpUrl='/admin/agent/list')

@admin_app.get('/agent/freeze')
@checkAccess
def do_agFreeze(redis,session):
    """
        代理冻结
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']

    agentId = request.GET.get('id','').strip()

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][freeze][error] agent[%s] is not exists!'%(curTime,agentId))
        return abort(403)

    if redis.hget(adminTable,'valid') == '1':
        agentFreeze(redis,agentId)
        #记录操作日志
        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['freezeAgent']%(agentId)}
    else:
        redis.hset(adminTable,'valid','1')
        #记录操作日志
        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['unfreezeAgent']%(agentId)}

    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':'(%s)状态更改成功!'%(agentId),'jumpUrl':'/admin/agent/list'}

@admin_app.get('/agent/trail')
@checkAccess
def do_agTrail(redis,session):
    """
    设置公会为试玩
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']

    agentId = request.GET.get('id','').strip()

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][trail][error] agent[%s] is not exists!'%(curTime,agentId))
        return {'code':1,'msg':lang.GROUP_NOT_EXISTS_TXT%(agentId)}

    if redis.hget(adminTable,'isTrail') == '0':
        doAgentChange(redis,agentId,'isTrail',1)
        #记录操作日志
        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['trailAgent']%(agentId)}
    else:
        doAgentChange(redis,agentId,'isTrail',0)
        #记录操作日志
        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['unTrailAgent']%(agentId)}

    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_STATUS_SETTING_SUCCESS%(agentId),'jumpUrl':BACK_PRE+'/agent/list'}

@admin_app.get('/agent/recharge')
@checkAccess
def do_agRecharge(redis,session):
    """
    设置公会是否能给会员充卡接口
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']
    agentId = request.GET.get('id','').strip()

    login_info_dict = {
            '0'             :       'rechargeAg',
            '1'             :       'unRechargeAg'
    }

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][trail][error] agent[%s] is not exists!'%(curTime,agentId))
        return {'code':1,'msg':lang.GROUP_NOT_EXISTS_TXT%(agentId)}

    re_status = redis.hget(adminTable,'recharge')
    if not re_status:
        re_status = '1'

    if re_status == '0':
        doAgentChange(redis,agentId,'recharge',1)
    else:
        doAgentChange(redis,agentId,'recharge',0)

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE[login_info_dict[re_status]]%(agentId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_RECHARGE_SETTING_SUCCESS%(agentId),'jumpUrl':BACK_PRE+'/agent/list'}

@admin_app.get('/agent/auto_check')
@checkAccess
def do_Auto(redis,session):
    """
    设置公会是否能给会员充卡接口
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']
    agentId = request.GET.get('id','').strip()

    login_info_dict = {
            '0'             :       'autocheck',
            '1'             :       'unAutocheck'
    }

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][trail][error] agent[%s] is not exists!'%(curTime,agentId))
        return {'code':1,'msg':lang.GROUP_NOT_EXISTS_TXT%(agentId)}

    auto_check = redis.hget(adminTable,'auto_check')
    if not auto_check:
        auto_check = '1'

    if auto_check == '0':
        doAgentChange(redis,agentId,'auto_check',1)
    else:
        doAgentChange(redis,agentId,'auto_check',0)

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE[login_info_dict[auto_check]]%(agentId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_CHECK_SETTING_SUCCESS,'jumpUrl':BACK_PRE+'/agent/list'}

@admin_app.get('/agent/create_auth')
@checkAccess
def do_createAuth(redis,session):
    """
    是否允许公会创建三级公会
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']
    agentId = request.GET.get('id','').strip()

    login_info_dict = {
            '0'             :       'createAuth',
            '1'             :       'unCreateAuth'
    }

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][trail][error] agent[%s] is not exists!'%(curTime,agentId))
        return {'code':1,'msg':lang.GROUP_NOT_EXISTS_TXT%(agentId)}

    create_auth = redis.hget(adminTable,'create_auth')
    if not create_auth:
        create_auth = '0'

    if create_auth == '0':
        doAgentChange(redis,agentId,'create_auth',1)
    else:
        doAgentChange(redis,agentId,'create_auth',0)

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE[login_info_dict[create_auth]]%(agentId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_CHECK_SETTING_SUCCESS,'jumpUrl':BACK_PRE+'/agent/list'}

@admin_app.get('/agent/open_auth')
@checkAccess
def do_openAuth(redis,session):
    """
    是否允许有权限的玩家代开房
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']
    agentId = request.GET.get('id','').strip()

    login_info_dict = {
            '0'             :       'openAuth',
            '1'             :       'unOpenAuth'
    }

    adminTable = AGENT_TABLE%(agentId)
    if not redis.exists(adminTable):
        log_debug('[%s][agent][trail][error] agent[%s] is not exists!'%(curTime,agentId))
        return {'code':1,'msg':lang.GROUP_NOT_EXISTS_TXT%(agentId)}

    open_auth = redis.hget(adminTable,'open_auth')
    if not open_auth:
        open_auth = '0'

    if open_auth == '0':
        redis.hset(adminTable,'open_auth',1)
        #doAgentChange(redis,agentId,'open_auth',1)
    else:
        redis.hset(adminTable,'open_auth',0)

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE[login_info_dict[open_auth]]%(agentId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_CHECK_SETTING_SUCCESS,'jumpUrl':BACK_PRE+'/agent/list'}

@admin_app.get('/agent/member/curOnline')
@checkAccess
def getCurOnline(redis,session):
    """
    获取在线用户接口
    """
    lang    =  getLang()
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()

    if isList:
        onlineInfos = get_member_online_list(redis,lang,session['id'])
        return json.dumps(onlineInfos)
    else:
        info = {
                'title'                  :           '会员实时在线',
                'listUrl'                :           BACK_PRE+'/agent/member/curOnline?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_member_online',info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/agent/checkBuyCard')
def getAgentCardRefresh(redis,session):
    """
    轮询检查下级代理向自己是否购买钻石
    """
    curTime = datetime.now()
    selfUid = session['id']

    number = request.GET.get('number','').strip()
    buyOrderTable = AGENT_SALEPENDING_ORDER_LIST%(selfUid,curTime.strftime('%Y-%m-%d'))
    if not redis.exists(buyOrderTable):
        return {'code':2,'orderNo':0}

    orderNo = redis.llen(buyOrderTable)

    if int(number) > orderNo:
        return {'code':2,'orderNo':orderNo}
    elif int(number) < orderNo:
        return {'code':0,'msg':'您有%s笔未处理的订单'%(orderNo),'orderNo':orderNo,'jumpUrl':BACK_PRE+'/order/sale/record'}
    else :
        return {'code':3}

@admin_app.get('/agent/cardRefresh')
def getAgentCardRefresh(redis,session):
    """
    代理钻石刷新
    """
    curTime = datetime.now()
    selfAccount,selfUid = session['account'],session['id']
    if selfUid == '1':
        #超级管理员直接返回
        return {'roomCard':'无限制'}

    adminTable = AGENT_TABLE%(selfUid)
    roomCards,agent_type = redis.hmget(adminTable,('roomcard','type'))
    if not agent_type:
        return {'roomCard':'会话信息超时'}

    return {'roomCard':roomCards}

@admin_app.get('/agent/comfirmJoin')
def getComfirmJoin(redis,session):
    """
    确认加入
    """
    curTime = datetime.now()

    selfAccount,selfUid = session['account'],session['id']

    memberIds = redis.lrange(JOIN_GROUP_LIST%(selfUid),0,-1)
    pipe = redis.pipeline()
    for memberId in memberIds:
        if int(memberId) <= 0:
            continue
        status = redis.get(JOIN_GROUP_RESULT%(memberId)).split(':')[1]
        if int(status) == 0:
            status = 1
            pipe.set(JOIN_GROUP_RESULT%(memberId),"%s:%s"%(selfUid,status))
            pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(selfUid), memberId)
            pipe.hset(FORMAT_USER_TABLE%(memberId),'parentAg',selfUid)
            pipe.lrem(JOIN_GROUP_LIST%(selfUid),memberId)
            pipe.execute()
            return {'code':0,'msg':'会员[%s]审核成功.'%(memberId)}

    return {'code':1}

@admin_app.get('/agent/room/list')
@checkAccess
def getAgentRoomList(redis,session):
    """
    代理直属玩家房间列表
    """
    curTime = datetime.now()
    lang    = getLang()
    isList  = request.GET.get('list','').strip()
    agentId = session['id']

    if isList:
        res = getAgRoomListInfos(redis,session,agentId,lang)
        log_debug('res[%s]'%(res))
        return json.dumps(res)
    else:
        info = {
                'title'                  :       '玩家房间列表',
                'listUrl'                :       BACK_PRE+'/agent/room/list?list=1',
                'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
        }
        return template('admin_agent_room_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/agent/room/kick')
@checkAccess
def getAgentRoomList(redis,session):
    """
    代理直属玩家房间列表 - 强制解散房间
    """
    curTime = datetime.now()
    lang    = getLang()
    roomId  = request.GET.get('id','').strip()
    print 'roomId',roomId
    roomTable = ROOM2SERVER%(roomId)
    try:
        gameId = redis.hget(roomTable,'gameid')
    except:
        return {'code':1,'msg':'房间已解散'}

    sendProtocol2GameService(redis, gameId,HEAD_SERVICE_PROTOCOL_DISSOLVE_ROOM%(roomId))

    return {'code':0,'msg':lang.GAME_DISSOLVE_ROOM_SUCCESS,'jumpUrl':BACK_PRE+'/agent/room/list'}

@admin_app.get('/agent/active')
@checkAccess
def getAgentActive(redis,session):
    """
    下线代理活跃数统计
    """
    curTime  = datetime.now()
    lang     = getLang()

    fields = ('isList','id','startDate','endDate','date')
    for field in fields:
        exec("%s = request.GET.get('%s','').strip()"%(field,field))

    if date:
        endDate = date

    if not id:
        id = session['id']

    if isList:
        """  获取接口数据 """
        report = get_agent_active(redis,id,startDate,endDate)
        return json.dumps(report)
    else:
        """ 返回模板信息 """
        info = {
                    'title'                  :       '下线代理活跃',
                    'listUrl'                :       BACK_PRE+'/agent/active?isList=1',
                    'searchTxt'              :       '请输入公会号',
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
        }

    return template('admin_agent_active',info=info,lang=lang,RES_VERSION=RES_VERSION)
