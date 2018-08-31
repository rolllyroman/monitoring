#coding:utf-8
import redis

r = redis.Redis(host='127.0.0.1',password="168joyvick",db="1")

def main():
    print '-'*66
    change_before = str(raw_input('please input the agent id which you want to change:'))
    print '-'*66
    change_after = str(raw_input('please input the new agent id which you want:'))
    print '-'*66
    id_set = r.smembers('agents:ids:set')
    if change_after in id_set:
        print 'failed! repeat!'
        return
    else:
        r.sadd('agents:ids:set',change_after)
        r.srem('agents:ids:set',change_before)
        
    dic = r.hgetall('agents:id:%s'%change_before)
    if not dic:
        print 'failed! no exist!'
        return

    print '======================'
    print dic
    print '======================'
    regDate = dic['regDate'][:10]
    account = dic['account']
    dic['id'] = change_after
    r.hmset('agents:id:%s'%change_after,dic)
    r.delete('agents:id:%s'%change_before)

    ars = r.smembers('agent:%s:rate:set'%change_before)
    for x in ars:
        r.sadd('agent:%s:rate:set'%change_after,x)
    r.delete('agent:%s:rate:set'%change_before)
    arpp = r.smembers('agent:%s:roomcard:per:price'%change_before)
    for x in arpp:
        r.sadd('agent:%s:roomcard:per:price'%change_after,x)
    r.delete('agent:%s:roomcard:per:price'%change_before)

    #  创造日期`
    r.srem("agent:create:date:%s"%regDate,change_before)
    r.sadd("agent:create:date:%s"%regDate,change_after)

    # 账号to id
    r.set('agents:account:%s:to:id'%account,change_after)

    # 找上级
    r.set('agents:id:%s:parent'%change_after,dic['parent_id'])
    r.delete('agents:id:%s:parent'%change_before)

    # 上级的下级集合
    r.sadd('agents:id:%s:child'%dic['parent_id'],change_after)
    r.srem('agents:id:%s:child'%dic['parent_id'],change_before)

    # 邀请码
    s_key = r.hget("exchange:agent:find:hset",change_before)
    r.hset("exchange:agent:find:hset",change_after,s_key)
    r.hdel("exchange:agent:find:hset",change_before)

    print 'ok!'


if __name__ == '__main__':
    main()
