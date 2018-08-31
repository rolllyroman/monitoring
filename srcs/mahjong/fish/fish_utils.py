#!/usr/bin/env python
#-*-coding:utf-8 -*-
"""
@Author: $Author$
@Date: $Date$
@version: $Revision$

Description:
 Description
"""
from web_db_define import *
from common.log import *
import random

def VerifySid(redis, sid, verfiySid):

    log_util.debug('[on refresh] account[%s] sid[%s]'%(account, sid))
    if verfiySid and sid != verfiySid:
        #session['member_account'],session['member_id'] = '',''
        return -4,'账号已在其他地方登录',False
    if not redis.exists(SessionTable):
        return -3,'sid 超时',False

    account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
    userTable = redis.get(account2user_table)
    if not redis.exists(user_table):
        return -5,'该用户不存在',False

    return 0,True,user_table


def SecretKeys(redis):
    """ 计算公会兑换码

    """
    extendCode = ''
    for i in range(16):
        # a = random.randint(0,9)
        a = random.randrange(9)
        extendCode += str(a)
    if not redis.sadd(EXCHANGE_AGENT_LIST,extendCode):
        SecretKeys(redis)
    return extendCode
    
def SecretKeysInto(redis, groupId):
    """ 计算公会兑换码

    """
    extendCode = ''
    for i in range(12):
        a = random.randrange(9)
        extendCode += str(a)

    if redis.hexists(EXCHANGE_AGENT_INTO, extendCode) and redis.hexists(EXCHANGE_AGENT_CODE, groupId):
        SecretKeysInto(redis, groupId)
    else:
        if redis.hexists(EXCHANGE_AGENT_CODE, groupId):
            extendCode = redis.hget(groupId)
        
    pipe = redis.pipeline()
    pipe.hset(EXCHANGE_AGENT_INTO, extendCode, groupId)
    pipe.hset(EXCHANGE_AGENT_CODE, groupId, extendCode) 
    pipe.execute()
    return extendCode
    