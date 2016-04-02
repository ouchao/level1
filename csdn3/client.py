#encoding:utf-8
import os,sys
import signal  
from serializer import serializer
   
#发送信号，16175是前面那个绑定信号处理函数的pid，需要自行修改  
data=serializer('working/data/pids.json')
for i in data.loader():
    if i['name'] == 'get_html_a':
        print 'send term to pid:%s'%i['pid']
        os.kill(i['pid'],signal.SIGUSR1)
    #else:    
    #    print 'send kill to pid:%s'%i['pid']
    #    os.kill(i['pid'],signal.SIGKILL)  

#for i in spid:
#        print 'send kill to pid:%s'%i
#        os.kill(i,signal.SIGKILL)  

#发送信号，16175是前面那个绑定信号处理函数的pid，需要自行修改  
