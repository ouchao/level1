#coding:utf-8
import re
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')

opener=r'[\s\.\!\/\-\_\,\$\%\^\*\(\)\+\"\'\[\]\|\~\@\#\*\&——！，。？、￥…（）●]'
print opener

tmp=[]
with open('data','r') as dd:
    for i in dd.readlines():
        w=i.strip()
        print "1:"+w
        w=w.replace('❤','')
        w=w.replace('【','[').replace('】',']')
        w=w.strip('[]')
        w=re.sub('\[','',w)

        sw=re.search('^%s*(.*)'%opener,w).groups()[0]
        if sw :
            sw=re.sub('^(\d+%s+)'%opener,'',sw)
            print "2:"+sw
        else:
            sw="nall"
            print "2:%s"%sw
            
        print "\n"

            
        #w=re.search('^[0-9]*%s*(.+)'%opener,w).groups()[0]
        #if re.search(ur'[\u4e00-\u9fa5]',w):
        #    print i

        #if re.search('【(.+)】',unicode(i)) :
        #    print rr.groups()[0]
        #print a[1].encode('utf-8')

