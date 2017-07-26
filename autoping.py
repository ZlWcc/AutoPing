
# coding: utf-8

# In[19]:


import os, re, time, requests
from bs4 import BeautifulSoup as bs
from threading import Thread, Lock
from tkinter import *
from tkinter import ttk
import sqlite3

db='serverslist.db'
mutex = Lock()#创建锁 
thread_count = 0

#   == tk top====================    
root = Tk()
root.geometry("700x550+70+0")
root.title("Auto Ping Panel")
text_Input = StringVar()

#数据库语句执行函数
def sqlit(sql,parament=None,database=db):
    global thread_count
    try:
        with sqlite3.connect('serverslist.db') as conn :
            cursor = conn.cursor() 
            if parament:
                cursor.execute(sql,parament)
            else:
                cursor.execute(sql)
            rs = cursor.fetchall()
            cursor.close()
            conn.commit()
            return rs
    except Exception as e:
        thread_count -= 10000
        print ("sqlit出现问题： " + str(e))
        print("sql :" + str(sql))
        if parament != None:
            print("para :"+ str(parament))


#########################No1 初始化数据表#####

def init_tables():
    sql1 = '''CREATE TABLE  if not exists servers (
        id INTEGER PRIMARY KEY,
        RegionName VARCHAR(45) NULL,
        Country VARCHAR(45) NULL,
        City VARCHAR(45) NULL,
        PPTP VARCHAR(45) NULL,
        UDP VARCHAR(45) NULL,
        TCP VARCHAR(45) NULL)'''
    sqlit(sql1)
    sql2 = """CREATE TABLE  if not exists ping (
      id INTEGER NOT NULL PRIMARY KEY,
      maxping SMALLINT(8) NULL ,
      minping SMALLINT(8) NULL,
      aveping SMALLINT(8) NULL,
      timeout INTEGER NOT NULL DEFAULT 0,
      star INTEGER NOT NULL DEFAULT 0)"""
    sqlit(sql2)
    
    sql3 = "select name from sqlite_master where type = 'table' order by name"
    value = "has tables： ",sqlit(sql3)
    text_Input.set(value)

########################No.2 更新服务器列表######


#=================爬取数据==================
def spider():
    url = 'https://support.purevpn.com/vpn-servers'
    html_doc = requests.get(url).content
    soup = bs(html_doc, 'html.parser')
    table = soup.find('tbody')
    return table('tr')

def Insert2servers(data):
    sql = 'SELECT * FROM servers WHERE PPTP=?'
    para = (data[3],)
    rs = sqlit(sql,para)
    if len(rs) == 0:
        sql1 = 'INSERT INTO servers (RegionName,Country,City,PPTP,UDP,TCP) VALUES(?,?,?,?,?,?)'
        para1 = tuple(data)
        sqlit(sql1, para1)
def UpdateServerlist():
    index = spider()
    for r in index:
        data = [_.get_text() for _ in r('td')]  
        Insert2servers(data)
    sql = 'select * from servers'
    value = "servers 表中已添加 %d 条数据"%len(sqlit(sql))
    text_Input.set(value)
    


    
    
######################## No.3 GUI界面 ############

#================获取地址信息=====================
def getData():
    sql='select * from servers'
    rs = sqlit(sql)
    return rs    


#==========将ping的结果返回到数据库中==============
def ist_rs(id,rs):
    rs=rs[0]
    sql = 'SELECT * FROM ping WHERE id=?'
    para = (id,)
    result = sqlit(sql, para)
    if len(result) == 0:
        sql1 = 'INSERT INTO ping (id, minping, maxping, aveping) VALUES(?, ?, ?, ?)'
        para1 = (id,rs[0],rs[1],rs[2]) 
    else:
        sql1 = 'UPDATE ping SET minping=?, maxping=?, aveping=? WHERE id=?'
        para1 = (rs[0],rs[1],rs[2],id)
    sqlit(sql1,para1)  
    

            
#============若超时，记录 timeout+1 ========================
def add_timeout(id):
    sql = 'SELECT timeout FROM ping WHERE id=?'
    para = (id,)
    result = sqlit(sql, para)
    if len(result) == 0:
        sql1 = 'INSERT INTO ping (id, timeout) VALUES(?, 1)'
        para1 = (id,) 
    else:
        times = int(result[0][0]) + 1
        sql1 = 'UPDATE ping SET timeout=? WHERE id=?'
        para1 = (times, id)
    sqlit(sql1, para1)
        
#=================对地址进行多线程ping============
def ping_thread(id,ip):
    global thread_count
    ping = 'ping this'.replace('this',ip)
    line = os.popen(ping).read()
    ping_time = re.findall(r"最短 = (\d+)ms，最长 = (\d+)ms，平均 = (\d+)ms", line)
    mutex.acquire()#取得锁 
    if len(ping_time) == 1:
        ist_rs(id,ping_time)
    else:
        add_timeout(id)
    thread_count = thread_count - 1
    mutex.release()#释放锁  
    



def update_ping():
    global thread_count
    urllist = getData()
    if len(urllist) > 0:
        r = urllist[-1]
        id, ip = r[0], r[4]
        Thread(target=ping_thread, args=(id,ip)).start()
        for r in urllist:
            id, ip = r[0], r[4]
            Thread(target=ping_thread, args=(id,ip)).start()
            thread_count += 1
        while thread_count > 0:
            time.sleep(5)
            tell = 'Threading Ping ....rest(%d)' %thread_count
            print(tell)
 
    else:
        print('出现问题，请检查server数据库')


#  查询网络状况良好的ip
def select_servers():
    sql = """select regionname,country,city,aveping,PPTP from servers s,ping p
            where s.id=p.id and
            p.timeout=0
            order by p.aveping ASC 
            """
    return sqlit(sql)[:10]
    
    
#=======================GUI============================    




Tops = Frame(root, width=600, height=90, bg="powder blue", relief=SUNKEN)
Tops.pack(side=TOP)

f1 = Frame(root, width=200, height=400, bg="powder blue", relief=SUNKEN)
f1.pack(side=LEFT)

f2 = Frame(root, width=500, height=400, bg="powder blue", relief=SUNKEN)
f2.pack(side=RIGHT)

#    func==========
def showTop10():
    tree.delete(*tree.get_children(''))
    a = select_servers()
    for i in a:
        tree.insert('','end', values=(i[0],i[1],i[2],i[3],i[4]))
        

def update():
    update_ping()
    showTop10()
    text_Input.set(' auto ping complete!')
    
updatetime = time.asctime(time.localtime())


#  f1 按钮区===================
lb1Info = Label(Tops, font=('arial', 30, 'bold'), text='AUTO  PING  TOOL ', fg='Steel Blue', bd=10, anchor='w' )
lb1Info.grid(row=0, column=0)
lb1Info = Label(Tops, font=('arial', 10, 'bold'), text=updatetime, fg='Steel Blue', bd=10, anchor='w' )
lb1Info.grid(row=1, column=0)


                                       
btnInit = Button(f1, bd=8, fg="black", font=('arial', 10, 'bold' ), text='InitDB', bg='#D3D3D3',width=10,
              command=init_tables).grid(row=0, column=0)
btnUpdate = Button(f1, bd=8, fg="black", font=('arial', 10, 'bold' ), text='RsURL', bg='#D3D3D3',width=10,
              command=UpdateServerlist).grid(row=1, column=0)
                                       
btnUpdate = Button(f1, bd=8, fg="black", font=('arial', 10, 'bold' ), text='PING', bg='#D3D3D3',width=10,
              command=update).grid(row=2, column=0)
btnTop10 = Button(f1, pady=3, bd=8, fg="black", font=('arial', 10, 'bold' ), text='BEST', bg='#D3D3D3', width=10,
              command=showTop10).grid(row=3, column=0)
close = Button(f1, pady=3, bd=8, fg="black", font=('arial', 10, 'bold' ), text='QUIT', bg='#D3D3D3',width=10, 
              command=root.destroy).grid(row=4, column=0)

#  f2 显示区===============
#滚动条
scrollBar = Scrollbar(f2)
scrollBar.grid(row=0, column=1, rowspan=6, sticky=W+E+N+S)

#Treeview组件，5列，显示表头，带垂直滚动条
tree = ttk.Treeview(f2, columns=('c1', 'c2', 'c3', 'c4', 'c5'), show="headings", height=18, yscrollcommand=scrollBar.set)
tree.grid(row=0, column=0,sticky=W)

#设置每列宽度和对齐方式
tree.column('c1', width=90, anchor='center')
tree.column('c2', width=80, anchor='center')
tree.column('c3', width=80, anchor='center')
tree.column('c4', width=80, anchor='center')
tree.column('c5', width=180, anchor='center')

#设置每列表头标题文本
tree.heading('c1', text='RegionName')
tree.heading('c2', text='Country')
tree.heading('c3', text='City')
tree.heading('c4', text='AvePing')
tree.heading('c5', text='PPTP')

#Treeview组件与垂直滚动条结合
scrollBar.config(command=tree.yview)

#文本框
e1 = Entry(f2, textvariable=text_Input)
e1.grid(row=1, column=0, rowspan=1,sticky=W+E)

#定义并绑定Treeview组件的鼠标单击事件
def treeviewClick(event):
    item = tree.focus()
    if not item:
        return
    value = tree.item(item)['values'][-1]
    text_Input.set(value)
    
tree.bind('<ButtonRelease-1>', treeviewClick)

if __name__ =="__main__":
    root.mainloop()


