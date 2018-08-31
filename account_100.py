#coding:utf-8
import redis
import hashlib

r = redis.Redis(host='127.0.0.1',password="168joyvick",db="1")

dic = r.hgetall('agents:id:%s'%"1")
r.set('god:id',101)

for x in range(1001,1100):
    sysid = str(x)
    r.sadd('sysadmin:id:set',sysid)
    if x == 1:
        continue
    account = dic['account'] = "sysadmin" + sysid
    sha256 = hashlib.sha256()
    sha256.update(account)
    pwd = sha256.hexdigest()
    dic['passwd'] = pwd
    dic['id'] = sysid

    r.hmset('agents:id:%s'%sysid,dic)
    r.set('agents:account:%s:to:id'%account,sysid)



