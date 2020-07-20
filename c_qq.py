from _overlapped import NULL
import hashlib
import sqlite3
import time
import os
import json
from c_decoder import c_decoder

class c_qqex():
    # init 设置解密key和导出文件夹 连接数据库
    def __init__(self, db, key, outdir):
        self.key = key  # 解密用的密钥
        # 导出路径
        self.outdir = outdir
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        # 连接数据库
        self.connectDB(db)
        # 初始化decoder
        self.d = c_decoder(self.key)
        # 初始化信息
        self.friends = {}
        self.troop = {}
        self.troopmem = {}
        # 初始化聊天记录表
        self.msgf = {}
        self.msgt = {}

    def connectDB(self,db):
        self.c = sqlite3.connect(db).cursor()

    # 1.1 获取好友信息 self.friends = { uin: [name, remark, age, gender, md5] }
    def getFriends(self):
        # uin QQ号 name 昵称 remark 备注 age 年龄 gender 性别
        execute = "select uin,name,remark,age,gender from Friends"
        cursor = self.c.execute(execute)
        for i in cursor:
            # 获取单条数据
            uin, name, remark, age, gender = i[0], i[1], i[2], i[3], i[4]

            # 解密
            uin = self.d.decode(uin, 1)
            name = self.d.decode(name, 1)
            remark = self.d.decode(remark, 1)

            # 写入FriendsData
            if (uin):
                self.friends[uin] = [name, remark, age, gender]
            else:
                print('unkown uin!', i)
        return self.friends
    
    # 1.2 获取群组信息 self.troop = { tuin: [name, code, owneruin, memo]}
    def getTroop(self):
        # troopuin 群号 troopname 群名 troopcode 群号? trooponweruin 群主 troopmemo 群简介
        execute = "select troopuin, troopname, troopcode,troopowneruin,troopmemo from TroopInfoV2"
        cursor = self.c.execute(execute)
        for i in cursor:
            # 获取单条数据
            tuin, name, code, owneruin, memo = i[0], i[1], i[2], i[3], i[4]
            
            # 解密
            tuin = self.d.decode(tuin, 1)
            name = self.d.decode(name, 1)
            code = self.d.decode(code, 1)
            owneruin = self.d.decode(owneruin, 1)
            memo = self.d.decode(memo, 1)
            
            if (tuin):
                self.troop[tuin] = [name, code, owneruin, memo]
            else:
                print('unkown uin!', i)
        return self.troop
    
    # 1.3 获取群成员信息 self.troopmem = { tuin: { quin: [tname(群名片), qname(), jtime] }}
    def getTroopMem(self):
        # troopuin 群号 memberuin qq号 troopnick 群名片 friendnick qq名 join_time 入群时间
        execute = "select troopuin,memberuin,troopnick,friendnick,join_time from TroopMemberInfo"
        cursor = self.c.execute(execute)
        for i in cursor:
            # 获取单条数据
            tuin, quin, tname, qname, jtime = i[0], i[1], i[2], i[3], i[4]

            # 解密
            tuin = self.d.decode(tuin, 1)
            quin = self.d.decode(quin, 1)
            tname = self.d.decode(tname, 1)
            qname = self.d.decode(qname, 1)
            jtime = self.d.decode(jtime, 1)

            # 写入troopmem
            if (tuin):
                if tuin not in self.troopmem:
                    self.troopmem[tuin] = {}
                self.troopmem[tuin][quin] = [tname,qname,jtime]
            else:
                print('unkown tuin!', i)
        return self.troopmem

    # 1.4 获取单个好友聊天记录 self.msgf = { fuin: msgs } msgs = [[uin, stime, msg, suin, fuin]]
    def getMsgFriends(self, qq='', md5='', table='', save=False):

        msgs = []

        # 如果给的是QQ号，计算md5
        if len(qq) > 0:
            md5 = hashlib.md5(qq).hexdigest().upper()
        elif len(md5) > 0:
            md5 = md5.upper()
        if len(table) <= 0:
            table = 'mr_friend_{}_New'.format(md5)
        
        # senderuin 发送者qq time 发送时间 msgData 消息内容 selfuin 自己的qq frienduin 好友的qq
        execute = "select senderuin, time, msgData, selfuin, frienduin from {}".format(table)
        cursor = self.c.execute(execute)

        for i in cursor:
            # 单条数据处理
            uin, stime, msg, suin, fuin = i[0], i[1], i[2], i[3], i[4]

            # 解密
            uin = self.d.decode(uin, 1)
            stime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stime))
            msg = self.d.decode(msg, 0)
            suin = self.d.decode(suin, 1)
            fuin = self.d.decode(fuin, 1)

            # 写入msgs
            if (save):
                if uin not in self.msgf:
                    self.msgf[uin] = []
                self.msgf[uin].append([uin, stime, msg, suin, fuin])
            else:
                msgs.append([uin, stime, msg, suin, fuin])
        
        if (save):
            return self.msgf
        else:
            return msgs

    # 1.5 获取单个群聊记录 self.msgt = { tuin: msgs } msgs = [[tuin, uin, stime, msg, suin]]
    def getMsgTroop(self, troop='', md5='', table='', save=False):
        msgs = []

        # 如果给的是QQ号，计算md5
        if len(troop) > 0:
            md5 = hashlib.md5(troop).hexdigest().upper()
        elif len(md5) > 0:
            md5 = md5.upper()
        if len(table) <= 0:
            table = 'mr_troop_{}_New'.format(md5)
        
        # frienduin 群号 senderuin 发送者qq time 发送时间 msgData 消息内容 selfuin 自己的qq
        execute = "select frienduin, senderuin, time, msgData, selfuin from {}".format(table)
        cursor = self.c.execute(execute)

        for i in cursor:
            # 单条数据处理
            tuin, uin, stime, msg, suin = i[0], i[1], i[2], i[3], i[4]

            # 解密
            tuin = self.d.decode(tuin, 1)
            uin = self.d.decode(uin, 1)
            stime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stime))
            msg = self.d.decode(msg, 0)
            suin = self.d.decode(suin, 1)

            # 写入msgs
            if (save):
                if tuin not in self.msgt:
                    self.msgt[tuin] = []
                self.msgt[tuin].append([tuin, uin, stime, msg, suin])
            else:
                msgs.append([tuin, uin, stime, msg, suin])
        
        if (save):
            return self.msgt
        else:
            return msgs

    # 1.6 获取所有聊天记录
    def getMsgAll(self):
        # 先获取所有'mr_'开头的表格
        execute = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor = self.c.execute(execute)
        tables = []
        for i in cursor:
            table = i[0]
            if (i[0].startswith('mr_')):
                tables.append(table)
        pass
        # 获取所有聊天记录
        for table in tables:
            if (table.startswith('mr_friend')):
                # 处理好友聊天记录
                self.getMsgFriends(table=table,save=True)
            elif (table.startswith('mr_troop')):
                # 处理群聊天记录
                self.getMsgTroop(table=table,save=True)
            else:
                pass
        return (self.msgf, self.msgt)

    # 1.7 获取所有信息
    def getInfo(self):
        return (self.getFriends(),self.getTroop(),self.getTroopMem())

    # 2.1 获取好友名称
    def getNamef(self, uin):
        if uin in self.friends:
            if (len(self.friends[uin][1])>0):
                # 存在备注则返回备注
                return self.friends[uin][1]
            else:
                # 否则返回名字
                return self.friends[uin][0]
        else:
            # 不存在则返回qq
            return uin

    # 2.2 获取群成员名称
    def getNamet(self, uin, tuin):
        # 检查群号是否存在
        if tuin in self.troopmem:
            # 检测群成员是否存在
            if uin in self.troopmem[tuin]:
                [tname, qname, jtime] = self.troopmem[tuin][uin]
                if (len(tname)>0):
                    # 存在群名片则返回群名片
                    return tname
                else:
                    # 否则返回qq名
                    return qname
            else:
                return uin
        else:
            # 不存在则返回qq
            return uin

    # 3.1 导出好友信息
    def exFriends(self, mode='txt', name = 'friends'):
        # 打开文件
        outfile = os.path.join(self.outdir,"{}.txt".format(name))
        fc = open(outfile, "w+", encoding="utf-8")

        # 3.1.1 导出为txt文本
        if (mode == 'txt'):
            for uin in self.friends:
                fc.write('qq:{}\t昵称:{}\t备注:{}\t年龄:{}\t性别:{}\n'.format(uin, self.friends[uin][0], self.friends[uin][1], self.friends[uin][2], self.friends[uin][3]))
        # 3.1.2 导出为json
        elif (mode == 'json'):
            json.dump(self.friends, fc)
        else:
            pass

        fc.close()
    
    # 3.2 导出群组信息
    def exTroop(self, mode='txt', name = 'troop'):
        # 打开文件
        outfile = os.path.join(self.outdir,"{}.txt".format(name))
        fc = open(outfile, "w+", encoding="utf-8")

        # 3.1.1 导出为txt文本
        if (mode == 'txt'):
            for uin in self.troop:
                # self.troop = { uin: [name, code, owneruin, memo]}
                fc.write('群号:{}\t群名:{}\t群号2:{}\t群主:{}\t群简介:{}\n'.format(uin, self.friends[uin][0], self.friends[uin][1], self.friends[uin][2], self.friends[uin][3]))
        # 3.1.2 导出为json
        elif (mode == 'json'):
            json.dump(self.troop, fc)
        else:
            pass

        fc.close()

    # 3.3 导出群成员信息
    def exTroopMem(self, mode='txt', name = 'troop'):
        # 打开文件
        outfile = os.path.join(self.outdir,"{}.txt".format(name))
        fc = open(outfile, "w+", encoding="utf-8")

        # 3.1.1 导出为txt文本
        if (mode == 'txt'):
            for tuin in self.troopmem:
                fc.write('---群号:{}\n'.format(tuin))
                for quin in self.troopmem[tuin]:
                    # self.troopmem = { tuin: { quin: [tname(群名片), qname(), jtime] }}
                    fc.write('QQ号:{}\t群名片:{}\tQQ名:{}\t入群时间:{}\n'.format(quin, self.friends[tuin][quin][0], self.friends[tuin][quin][1], self.friends[tuin][quin][2]))
                fc.write('\n')
        # 3.1.2 导出为json
        elif (mode == 'json'):
            json.dump(self.troopmem, fc)
        else:
            pass

        fc.close()

    # 3.4 导出单个好友聊天记录
    def exMsgsf(self, msgs, mode='txt', name = ''):
        if (name == ''):
            print('未知好友')
            name = str(time.time())
        # 打开文件
        outfile = os.path.join(self.outdir,"f_{}.txt".format(name))
        fc = open(outfile, "w+", encoding="utf-8")

        # 3.1.1 导出为txt文本
        if (mode == 'txt'):
            for i in msgs:
                # msgs = [[uin, stime, msg, suin, fuin]]
                uin, stime, msg, suin, fuin = i
                if (uin==suin):
                    # 是自己发言，以===开头
                    fc.write('==={}({}) {}\n{}\n\n'.format(self.getNamef(uin),uin,stime,msg))
                else:
                    # 不是自己发言，以---开头
                    fc.write('---{}({}) {}\n{}\n\n'.format(self.getNamef(uin),uin,stime,msg))
        # 3.1.2 导出为json
        elif (mode == 'json'):
            json.dump(msgs, fc)
        else:
            pass

        fc.close()

    # 3.5 导出单个群聊聊天记录
    def exMsgst(self, msgs, mode='txt', name = ''):
        if (name == ''):
            # 取得群号
            name = str(msgs[0][0])

        # 打开文件
        outfile = os.path.join(self.outdir,"{}.txt".format(name))
        fc = open(outfile, "w+", encoding="utf-8")

        # 3.1.1 导出为txt文本
        if (mode == 'txt'):
            for i in msgs:
                # msgs = [[uin, stime, msg, suin]]
                tuin, uin, stime, msg, suin = i
                if (uin==suin):
                    # 是自己发言，以===开头
                    fc.write('==={}({}) {}\n{}\n\n'.format(self.getNamet(uin, tuin),uin,stime,msg))
                else:
                    # 不是自己发言，以---开头
                    fc.write('---{}({}) {}\n{}\n\n'.format(self.getNamet(uin, tuin),uin,stime,msg))
        # 3.1.2 导出为json
        elif (mode == 'json'):
            json.dump(msgs, fc)
        else:
            pass

        fc.close()

    # 3.6 导出所有聊天记录
    def exMsgsAll(self):
        # 导出好友
        for i in self.msgf:
            self.exMsgsf(self.msgf[i], name=i)
        # 导出群聊
        for i in self.msgt:
            self.exMsgst(self.msgt[i])
        pass