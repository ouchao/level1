#encoding:utf-8
from bs4 import BeautifulSoup
from pprint import pprint

import multiprocessing
import Queue
import json
import signal

import mongodb
from serializer import serializer

import urllib
import urllib2

import httplib

import cookielib

import hashlib
import time
import sys,os
import re

import inspect

reload(sys)
sys.setdefaultencoding('utf-8')
print  sys.getdefaultencoding()

def word_correct(w):
    opener=r'[\s\.\!\/\-\_\,\$\%\^\*\(\)\+\"\'\[\]\|\~\@\#\*\&——！，。？、￥…（）●]'

    w=w.strip()
    w=w.replace('❤','')
    w=w.replace('【','[').replace('】',']')
    w=w.strip('[]')
    w=re.sub('\[','',w)

    sw=re.search('^%s*(.*)'%opener,w).groups()[0]
    if sw :
        sw=re.sub('^(\d+%s+)'%opener,'',sw)
    else:
        sw=""

    if not sw :
        sw="其他"
    return sw

def md5(str):
    m=hashlib.md5()
    m.update(str)
    psw = m.hexdigest()
    return psw

def function_logs(args):
    def _logs(func):
        def __logs(self,a,b):
            print "[%s] : %s-%s begin" %(time.strftime('%Y-%m-%d %H:%M:%S'),self.__class__.__name__,func.func_name)
            ret=func(self,a,b)
            print "[%s] : %s-%s begin" %(time.strftime('%Y-%m-%d %H:%M:%S'),self.__class__.__name__,func.func_name)
            print "\n"
            return ret
        return __logs
    return _logs


def postdata_category_encap(data):
    category_data={
        'info[modelid]'       : '1',
        'info[parentid]'      : '1',
        'info[catname]'       : data['category'],
        'info[catdir]'        : data['category'],
        'info[image]'         : '',
        'info[child]'         : '0',
        'info[description]'   : '',
        'info[ismenu]'        : '1',
        'info[listorder]'     : '0',
        'info[url]'           : '',

        'isbatch'       : '0',
        #'batch_add'     : category,

        'setting[seturl]'              : '',
        'setting[generatehtml]'        : '1',
        'setting[generatelish]'        : '0',
        'setting[member_check]'        : '0',
        'setting[member_admin]'        : '1',
        'setting[member_editcheck]'    : '1',
        'setting[member_generatelish]' : '0',
        'setting[member_addpoint]'     : '0',

        'setting[meta_title]'          : 'title',
        'setting[meta_keywords]'       : 'keyworks',
        'setting[meta_description]'    : 'description',

        'setting[category_template]'   : 'category.php',
        'setting[list_template]'       : 'list.php',
        'setting[show_template]'       : 'show.php',

        'setting[list_customtemplate]' : '',
        'setting[ishtml]'              : '0',
        'setting[repagenum]'           : '',
        'setting[content_ishtml]'      : '0',

        'category_php_ruleid'   : '1',
        'category_html_ruleid'  : '2',
        'show_php_ruleid'       : '4',
        'show_html_ruleid'      : '3',

        'priv_groupid[0]' : 'add,2',
        'priv_groupid[1]' : 'add,6',
        'priv_groupid[2]' : 'add,4',
        'priv_groupid[3]' : 'add,5',

        'extend_add[fieldname]' : '',
        'extend_add[type]'      : 'input',
        'extend_add[setting][title]'  : '',
        'extend_add[setting][tips]'   : '',
        'extend_add[setting][style]'  : '',
        }
    return category_data


def postdata_content_encap(data,result,catid,csdn):
    content_data={
        'info[thumb]'         :""         ,
        'info[relation]'      :""         ,
        'info[updatetime]'    :""         ,
        'info[template]'      :"show.php" ,
        'info[allow_comment]' :1          ,
        'info[islink]'        :0          ,
        'info[status]'        :99         ,
        'info[catid]'         :catid      ,
        'info[title]'         :data['title'],

        'info[posid][0]'      :1          ,
        'info[posid][1]'      :2          ,
        'info[posid][2]'      :3          ,
        'info[content]'       :data['content']    ,
        'info[description]'   :result['desc']     ,
        'info[pages][paginationtype]'   :2          ,
        'info[pages][maxcharperpage]'   :10000      ,
        'info[csdn_url]'            : result['href'],
        'info[csdn_author]'         : csdn['user'],
        'info[csdn_reading_num]'    : data['reading_num'] ,
        'info[csdn_comments_num]'   : data['comments_num'],
        'info[csdn_urlmd5]'         : data['urlmd5'],

        'catname'               :data['category'],
        'style_font_weight'     :'',
        'style_color'           :'',
        'add_introduce'         :1,
        'introcude_length'      :200,
        'auto_thumb'            :1,
        'auto_thumb_no'         :1,
        'ajax'                  :1,
        'catid'                 :1,
        }

    if data['tags'] == data['category'] :
        content_data['info[keywords]']=data['tags']
        content_data['info[tags]']    =data['tags']
    elif data['tags'] and data['category'] :
        content_data['info[keywords]']=data['tags']+','+data['category']
        content_data['info[tags]']    =data['tags']+','+data['category']
    elif data['tags'] and not data['category']:
        content_data['info[keywords]']=data['tags']
        content_data['info[tags]']    =data['tags']
    elif data['category'] and not data['tags'] :
        content_data['info[keywords]']=data['category']
        content_data['info[tags]']    =data['category']
    else:
        content_data['info[keywords]']=data['category']
        content_data['info[tags]']    =data['tags']

    return content_data

class SpiderDefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):  
    def http_error_default(self, req, fp, code, mesg, header):
        result     = urllib2.HTTPError(req.get_full_url(), code, mesg, header, fp)  
        #print "err:%s end"%result
        self.url    = req.get_full_url()
        self.fp     = fp
        self.mesg   = result
        self.header = header
        self.code   = code
        return self

    def read(self):
        return self.fp.read()

def Get_decorator(arg=''):
    def __Get(func):
        def _Get(self,url):
            r1=func(self,url)
            if r1 == None :
                super_mothed=inspect.stack()[2][3]
                if super_methed == '__filter_blog_url':
                    self.html_a.put(url)
                    self.push_debug("%s get url:%s return None error,redo push html_a queue"%(super_methed,url),'geterr.log')

                elif super_methed == '__get_pageurl':
                    self.htmlblog_a.put(url)
                    self.push_debug("%s get url:%s return None error,redo push htmlblog queue"%(super_methed,url),'geterr.log')

                elif super_methed == 'get_blog':
                    self.pageurl.put(url)
                    self.push_debug("%s get url:%s return None error,redo push pageurl queue"%(super_methed,url),'geterr.log')

                elif super_methed == '__get_blog_content':
                    self.pageurl.put(url)
                    self.push_debug("%s get url:%s return None error"%(super_methed,url),'geterr.log')

                else:
                    self.push_debug("%s get url:%s return None error"%(super_methed,url),'geterr.log')

            elif r1 != 200:
                    self.push_debug("%s get url:%s return %d error"%(super_methed,url,r1),'geterr.log')
            return r1
        return _Get
    return __Get



class BlogRoobt():
    def __init__(self):
        self.workdir    = '/home/qilong/python/csdn3/working'
        self.domain     = 'http://blog.csdn.net'
        self.urls       = self.domain+"/"

        self.processs     = []
        self.free_maxtime = 3600
        self.delaytime    = 5

        self.filter_rule    = '^http://blog.csdn.net/([\d\_\w]+)/?$'

        M0                  = multiprocessing.Manager()
        self.loop_marked    = M0.dict()

        M1 = multiprocessing.Manager()
        self.html_a_md5       = M1.dict()
        self.html_a_md5_count = multiprocessing.Value('i',0)

        self.html_a           = multiprocessing.Queue(10000)
        self.html_a_count     = multiprocessing.Value('i',0)

        M2 = multiprocessing.Manager()
        self.htmlblog_a_md5       = M2.dict()
        self.htmlblog_a_md5_count = multiprocessing.Value('i',0)

        self.htmlblog_a       = multiprocessing.Queue(1200)
        self.htmlblog_a_count = multiprocessing.Value('i',0)

        self.pageurl        = multiprocessing.Queue(120)
        self.pageurl_count  = multiprocessing.Value('i',0)

        self.blogurl        = multiprocessing.Queue(120) 
        self.blogurl_count  = multiprocessing.Value('i',0)
        self.insert_count   = multiprocessing.Value('i',0) 

        self.console        = multiprocessing.Queue(1200)
        self.console_count  = multiprocessing.Value('i',0)

        self.debug          = multiprocessing.Queue(1200)
        self.debug_count    = multiprocessing.Value('i',0)
        
        self.logs           = multiprocessing.Queue(1200)
        self.logs_count     = multiprocessing.Value('i',0)

        self.errs           = multiprocessing.Queue(1200)
        self.errs_count     = multiprocessing.Value('i',0)

        self.iskill         = multiprocessing.Value('i',0)

        self.dumper         = multiprocessing.Value('i',0)
        self.dumper_lock    = multiprocessing.Lock()

        self.loader         = multiprocessing.Value('i',0)
        self.loader_lock    = multiprocessing.Lock()

        self.wdebug_lock    = multiprocessing.Lock()
        self.wlog_lock      = multiprocessing.Lock()
        self.werr_lock      = multiprocessing.Lock()
        self.wconsole_lock  = multiprocessing.Lock()

        self.cj         = cookielib.CookieJar()
        self.proxy      = urllib2.ProxyHandler({'http':'http://122.96.59.104:80'})  
        #self.proxy      = urllib2.ProxyHandler({'http':'http://211.144.76.58:9000'})  
        self.opener     = urllib2.build_opener(
                self.proxy,
                SpiderDefaultErrorHandler(),
                urllib2.HTTPHandler(),
                urllib2.HTTPSHandler(),
                urllib2.HTTPCookieProcessor(self.cj),
        )
        urllib2.install_opener(self.opener)
        #urllib2.socket.setdefaulttimeout(60)

    def set_header(self,req):
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Accept','*/*')
        req.add_header('Accept-Language', 'zh-CN,zh;q=0.8,en;q=0.6')
        req.add_header('Cache-Control', 'max-age=0')
        req.add_header('Connection', 'keep-alive')
        #req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
        return req

    def Post(self,url,data):
         try:
            postdata = urllib.urlencode(data)
            req      = urllib2.Request(url, postdata)
            header   = self.set_header(req)
            resp     = urllib2.urlopen(header,postdata)
            if resp.code == 200:
                return resp.read()
            else:
                return None
         except Exception,e:
            self.push_err("geturl:%s"% url         )
            self.push_err("error :%s"% str(e)      )
            self.push_err("\n\n")
            return None

    def url_test(self,url):
        try:
            req      = urllib2.Request(url)
            header   = self.set_header(req)
            resp     = urllib2.urlopen(header)
            if resp.code == 200 :
                return True
            else:
                return None
        except Exception,e:
            self.push_err("geturl:%s"% url         )
            self.push_err("error :%s"% str(e)      )
            self.push_err("\n\n")
            return None

    @Get_decorator()
    def Get(self,url):
        try:
            req      = urllib2.Request(url)
            header   = self.set_header(req)
            resp     = urllib2.urlopen(req)
            if resp.code == 200 :
                return resp.read()
            else:
                return resp.code
        except Exception,e:
            self.push_debug("geturl:%s"% url   ,'geterr.log')
            self.push_debug("error :%s"% str(e),'geterr.log')
            self.push_debug("\n\n",'geterr.log')
            return None

    def SendGet(self,url,data):
        try:
            postdata = urllib.urlencode(data)
            req      = urllib2.Request(url+"?"+postdata)
            header   = self.set_header(req)
            resp     = urllib2.urlopen(header)
            if resp.code == 200 :
                return resp.read()
            else:
                return None
        except Exception,e:
            self.push_err("geturl:%s"% url         )
            self.push_err("error :%s"% str(e)      )
            self.push_err("\n\n")
            return None

    def put_console(self,msg):
        funcname=sys._getframe().f_code.co_name
        pid=os.getpid()

        self.console.put(msg)
        qsize=self.console.qsize()
        if qsize > 10:
            self.wconsole_lock.acquire()
            for i in range(qsize) :
                msg=self.console.get()
                print("[%s] : %s\n"%(time.strftime('%Y-%m-%d %H:%M:%S'),msg) )
            self.wconsole_lock.release()


    def save_err(self):
        funcname=sys._getframe().f_code.co_name
        free_timer = 0
        pid=os.getpid()

        while True:
            if self.errs.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.errs.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            self.errs_count.value+=1
            free_timer = 0

            qsize=self.errs.qsize()
            if qsize > 10 :
                with open(self.workdir+'/logs/error.log','a') as d:
                    self.werr_lock.acquire()
                    for i in range(qsize):
                        d.write(self.errs.get())
                    self.werr_lock.release()
            time.sleep(self.delaytime)

    def push_log(self,msg,pconso=True):
        mesg="[%s] : %s\n"%(time.strftime('%Y-%m-%d %H:%M:%S'),msg)
        if pconso :
            self.logs.put(mesg)
            self.put_console(mesg)
        else:
            self.logs.put(mesg)

    def push_debug(self,msg,file='debug.log'):
        mesg="[%s] : %s\n"%(time.strftime('%Y-%m-%d %H:%M:%S'),msg)
        tmp={'m':mesg,'f':file}
        self.debug.put(tmp)

    def push_err(self,msg):
        msg="[%s] : %s\n"%(time.strftime('%Y-%m-%d %H:%M:%S'),msg)
        self.errs.put(msg)

    def __cat_debug(self):
        qsize=self.debug.qsize()
        for i in range(qsize):
            data=self.debug.get()
            self.wdebug_lock.acquire()
            with open('%s/logs/%s'%(self.workdir,data['f']),'a') as de:
                de.write(data['m'])
            self.wdebug_lock.release()
                
    def save_debug(self):
        funcname=sys._getframe().f_code.co_name
        free_timer = 0
        pid=os.getpid()

        while True:
            if self.debug.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.debug.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            self.debug_count.value+=1
            free_timer = 0

            self.__cat_debug()
            time.sleep(self.delaytime)            

    def save_log(self):
        funcname=sys._getframe().f_code.co_name
        free_timer = 0
        pid=os.getpid()

        while True:
            if self.logs.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.logs.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            self.logs_count.value+=1
            free_timer = 0

            qsize=self.logs.qsize()
            if qsize > 10 :
                with open(self.workdir+'/logs/data.log','a') as d:
                    self.wlog_lock.acquire()
                    for i in range(qsize):
                        d.write(self.logs.get())
                    self.wlog_lock.release()
            time.sleep(self.delaytime)

    def __insert_to_mongo(self):
        funcname=sys._getframe().f_code.co_name
        free_timer = 0
        pid=os.getpid()

        while True:
            if self.blogurl.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.blogurl.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            free_timer = 0
            self.insert_count.value+=1

            try :
                row = self.blogurl.get()
                mongo_ins=mongodb.mongo_crud()
                mongo=mongo_ins.get_crud('csdn_all')
                mongo.insert_one(row)
                self.push_log('insert to mongo')
            except Exception ,e:
                self.push_err( "process-%s-%d,insert to mongo,error_info=%s\n"%(funcname,pid,str(e)) )

            time.sleep(self.delaytime)


    def __get_blog_content(self,url,pid):
        funcname=sys._getframe().f_code.co_name

        self.push_log("process-%s-%d,geturl=%s\n"%(funcname,pid,url) ,False)

        html    = self.Get(url)
        if html == None:
            return False

        soup    = BeautifulSoup(html,'html5lib')
        if soup == None:
            return False

        blog    = soup.find("div",{"id":"article_details","class":"details"})
        if blog == None:
            return False

        try:
            reading_num = blog.find("span",{"class":"link_view"}).text.strip()
            reading_num = re.search('(\d+)',reading_num).groups()[0]
        except Exception,e2_reading_num:
            self.push_err("process-%s-%d-e2_reading_num:error=%s,url=%s  \n" %(funcname,pid,str(e2_reading_num),url))
            self.push_err("process-%s-%d-e2_reading_num:error,skip url:%s\n" %(funcname,pid,url))

        try:
            comments_num    = blog.find("span",{"class":"link_comments"}).text.strip()
            comments_num    = re.search('(\d+)',comments_num).groups()[0]
        except Exception,e2_comments_num:
            self.push_err("process-%s-%d-e2_comments_num:error=%s,url=%s  " %(funcname,pid,str(e2_comments_num),url))
            self.push_err("process-%s-%d-e2_comments_num:error,skip url:%s" %(funcname,pid,url))

        try:
            postdate    = blog.find("span",{"class":"link_postdate"}).text.strip()
        except Exception,e2_postdata:
            self.push_err("process-%s-%d-e2_postdata:error=%s,url=%s  " %(funcname,pid,str(e2_postdata),url))
            self.push_err("process-%s-%d-e2_postdata:error,skip url:%s" %(funcname,pid,url))

        try:
            title       = blog.find("div","article_title").find("span",{"class":"link_title"}).text.strip()
        except Exception,e2_title:
            self.push_err("process-%s-%d-e2_title:error=%s,url=%s  " %(funcname,pid,str(e2_title),url))
            self.push_err("process-%s-%d-e2_title:error,skip url:%s" %(funcname,pid,url))

        try:
            content     = blog.find("div","article_content").encode("utf8")
        except Exception,e2_content:
            self.push_err("process-%s-%d-e2_content:error=%s,url=%s  " %(funcname,pid,str(e2_content),url))
            self.push_err("process-%s-%d-e2_content:error,skip url:%s" %(funcname,pid,url))

        try:
            category    = blog.find("div","category_r").find("span").text
            category    = re.search('^(.+)（\d+）',str(category)).groups()[0].strip()
        except Exception,e2_category:
            self.push_err("process-%s-%d-e2_category:error=%s,url=%s  " %(funcname,pid,str(e2_category),url))
            self.push_err("process-%s-%d-e2_category:error,skip url:%s" %(funcname,pid,url))

        try:
            tags    = blog.find("span","link_categories").find("a").text.strip()
        except Exception,e2_tags:
            self.push_err("process-%s-%d-e2_category:error=%s,url=%s  " %(funcname,pid,str(e2_tags),url))
            self.push_err("process-%s-%d-e2_category:error,skip url:%s" %(funcname,pid,url))

        reading_num     = 'reading_num'   in locals().keys() and reading_num   or ''
        comments_num    = 'comments_num'  in locals().keys() and comments_num  or ''
        postdate        = 'postdate'      in locals().keys() and postdate      or ''
        title           = 'title'         in locals().keys() and title         or ''
        category        = 'category'      in locals().keys() and category      or '其他'
        content         = 'content'       in locals().keys() and content       or ''
        tags            = 'tags'          in locals().keys() and tags          or ''
        urlmd5          = md5(url)

        data={
            'reading_num'   :reading_num,
            'comments_num'  :comments_num,
            'postdate'      :postdate,
            'title'         :title,
            'category'      :word_correct(category.lower()),
            'content'       :content,
            'tags'          :word_correct(tags.lower()),
            'urlmd5'        :urlmd5,
        }
        return data
 

    def __get_article_list(self,dom,pid,pageurl):
        funcname=sys._getframe().f_code.co_name
        try :
            link=dom.find('span',{'class':'link_title'}).find('a')

            href = "http://blog.csdn.net%s"%(link['href']).strip()
            title= link.text.strip()
            desc = dom.find('div',{'class':'article_description'}).text.strip()

            self.push_log("process-%s-%d:url=%s\n"%(funcname,pid,href),False)

            if not href :
                return None
            else:
                return {'href':href,'title2':title,'desc':desc}
        except Exception,e1:
            title = 'title' in dir() and title or ''
            desc  = 'desc'  in dir() and desc  or ''
            if not 'href' in dir() :
                self.push_err("process-%s-%d-e1:href is not exists!,skip,pagelist url=%s,error data=%s\n"%(funcname,pid,pageurl,str(e1)) )
                return None
            else:
                self.push_err("process-%s-%d-e1:url=%s,error data=%s\n"%(funcname,pid,href,str(e1)) )
                return {'href':href,'title2':title,'desc':desc}



    def get_blog(self):
        funcname=sys._getframe().f_code.co_name
        free_timer = 0
        pid=os.getpid()

        while True:
            if self.pageurl.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.pageurl.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            free_timer = 0
            self.blogurl_count.value+=1

            
            if self.dumper.value == 1 :
                while(self.dumper.value == 1):
                    self.push_debug('%s-pid=%d,正在dumper，暂停执行'%(funcname,pid))
                    time.sleep(2)
                
            try :
                counter1=0
                url = self.pageurl.get()
                user_all_blogs = []
                for i in url['content_pagelist']:
                    self.push_log("process-%s-%d,geturl=%s\n"%(funcname,pid,i['href']),False)

                    html    = self.Get(i['href'])
                    if html == None:
                        continue

                    soup = BeautifulSoup(html,'html5lib')
                    if soup == None:
                        continue

                    article1 = soup.select('div#article_list    > div ')
                    article2 = soup.select('div#article_toplist > div ')
                    for ii in article1 + article2:

                        result=self.__get_article_list(ii,pid,i['href'])
                        if result == None :
                            continue

                        counter1+=1
                        href_md5=md5(result['href'])
                        if self.Get('http://shuipfcms.ouchaonihao.com/content/insertData/content_only/md5/%s'%href_md5) == '1' :
                            self.push_log("url:%s,md5:%s is existsing,skip\n"%(result['href'],href_md5))
                            continue

                        with open(self.workdir+'/logs/blogmd5.log','a') as m:
                            m.write("url:%s,md5:%s,page_url:%s\n"%(result['href'],href_md5,i['href']))
                            m.write("result=%s\n"%json.dumps(result,ensure_ascii=False,indent=4) )
                            m.flush()


                        if self.dumper.value == 1 :
                            while(self.dumper.value == 1):
                                self.push_debug('%s-pid=%d,正在dumper，暂停执行'%(funcname,pid))
                                time.sleep(2)

                        self.htmlblog_a_md5[href_md5]=self.htmlblog_a_md5.get(href_md5,0)+1
                        del(href_md5)

                        content=self.__get_blog_content(result['href'],pid)
                        if content == None :
                            self.push_err("process-%s-%d:url=%s,content is void\n"%(funcname,pid,result['href']) )
                            content=''

                        if content :
                            category_data=postdata_category_encap(content)
                            catid=self.insert_category(category_data)
                            content_data=postdata_content_encap(content,result,catid,url['userinfo'])
                            self.insert_content(content_data)

                        x={
                            'index_url' :i['href'],
                            'header'    :result,
                            'datas'     :content,
                            'pageid'    :i['listid']
                        }
                        user_all_blogs.append(x)
                        del(result)
                        del(content)
                        del(x)

                counter2=len(user_all_blogs)
                tmps={
                    'user_all_blogs':user_all_blogs,
                    'page_index'    :url['content_pagelist'],
                    'user'          :url['userinfo'],
                    'counter1'      :counter1,
                    'counter2'      :counter2
                }

                tmps=json.dumps(tmps,ensure_ascii=False,indent=4)
                save_path='%s/users/data-%s.json'%(self.workdir,url['userinfo']['user'])
                with open(save_path,'a') as j:
                    j.write(tmps)

                if self.blogurl.put(eval(tmps)) :
                    self.push_log( "put to blogurl suaccess" )

            except Exception,e:
                self.push_err("%s-e:error1=%s,error2=%s,page_url=%s;end\n"%(funcname,str(Exception),str(e),i['href']))
                continue

    def insert_category(self,data):
        url='http://shuipfcms.ouchaonihao.com/index.php?m=InsertData&a=add_category'
        with open('%s/postlogs/category_jdata'%self.workdir,'a') as j:
            j.write(json.dumps(data,ensure_ascii=False,indent=4))
    
        log_data=self.Post(url,data)
        with open('%s/postlogs/category_post.log'%self.workdir,'a') as j:
            j.write(str(log_data)+",\n")
        if log_data : 
            cat=eval(log_data)
            return cat['catid']
        else:
            return 2

    
    def insert_content(self,data):
        url='http://shuipfcms.ouchaonihao.com/index.php?m=InsertData&a=add_content&catid=1'
        with open('%s/postlogs/content_jdata'%self.workdir,'a') as j:
            j.write(json.dumps(data,ensure_ascii=False,indent=4)+",\n")
    
        log_data=self.Post(url,data)
        with open('%s/postlogs/content_post.log'%self.workdir,'a') as j:
            j.write(log_data+",\n")
    

    def Start(self):
        try:
            os.makedirs('%s/logs'%self.workdir)
            os.makedirs('%s/postlogs'%self.workdir)
            os.makedirs('%s/users'%self.workdir)
            os.makedirs('%s/data'%self.workdir)
        except Exception,e:
            print str(e)


        check_queue = multiprocessing.Process(target=self.check_queue,name='check_queue')
        self.processs.append(check_queue)
        
        save_debug = multiprocessing.Process(target=self.save_debug,name='save_debug')
        self.processs.append(save_debug)
        
        logs = multiprocessing.Process(target=self.save_log,name='logs')
        self.processs.append(logs)

        errs = multiprocessing.Process(target=self.save_err,name='errs')
        self.processs.append(errs)

        #insert_to_mongo = multiprocessing.Process(target=self.__insert_to_mongo)
        #self.processs.append(insert_to_mongo)

        self.html_a.put(self.urls)
        for i in range(2):
            get_html_a = multiprocessing.Process(target=self.get_html_a,name='get_html_a')
            self.processs.append(get_html_a)

        for i in range(5):
            contents=multiprocessing.Process(target=self.get_pagelist,name='get_pagelist')
            self.processs.append(contents)

        for i in range(7):
            blog=multiprocessing.Process(target=self.get_blog,name='get_blog')
            self.processs.append(blog)

        pids=[]
        for i in self.processs:
            self.put_console( "process=%s is start\n"%(i.name) )
            i.start()
            pids.append({'pid':i.pid,'name':i.name})

        pid_datas=serializer('%s/data/pids.json'%self.workdir)
        pid_datas.dumper(pids)

        for i in self.processs:
            self.put_console( "process=%s is exit \n"%(i.name) )
            i.join()

    def check_queue(self):
        free_timer1 = 0
        free_timer2 = 0
        free_timer3 = 0
        while True:
            self.wconsole_lock.acquire()
            print "\n\n\n"
            print "free_timer1:%d,free_timer2:%d,free_timer3:%d"%(free_timer1,free_timer2,free_timer3)

            print "html_a         : %-4d,html_a_count        : %-4d"%(self.html_a.qsize()          ,self.html_a_count.value     )
            print "html_a_md5     : %-4d,html_a_md5_count    : %-4d"%(self.html_a_md5.__len__()    ,self.html_a_md5_count.value )

            print "htmlblog_a     : %-4d,htmlblog_a_count    : %-4d"%(self.htmlblog_a.qsize()      ,self.htmlblog_a_count.value )
            print "htmlblog_a_md5 : %-4d,htmlbloga_md5_count : %-4d"%(self.htmlblog_a_md5.__len__(),0                           )

            print "pageurl      : %-4d,pageurl_count        : %-4d"%(self.pageurl.qsize(),self.pageurl_count.value )
            print "blogurl      : %-4d,blogurl_count        : %-4d"%(self.blogurl.qsize(),self.blogurl_count.value )
            print "blogurl      : %-4d,insert_mgo_count     : %-4d"%(self.blogurl.qsize(),self.insert_count.value  )

            print "savelog      : %-4d,savelog_count        : %-4d"%(self.logs.qsize()   ,self.logs_count.value )
            print "saverrs      : %-4d,saverrs_count        : %-4d"%(self.errs.qsize()   ,self.errs_count.value )
            print "\n\n\n"
            self.wconsole_lock.release()

            if self.htmlblog_a.qsize()  == 0 and free_timer1 < self.free_maxtime:
                free_timer1+=1

            if self.pageurl.qsize() == 0 and free_timer2 < self.free_maxtime:
                free_timer2+=1

            if self.blogurl.qsize() == 0 and free_timer3 < self.free_maxtime:
                free_timer3+=1

            if free_timer1 >= self.free_maxtime and free_timer2 >= self.free_maxtime and free_timer3 >= self.free_maxtime :
                sys.exit()

            time.sleep(self.delaytime)

    def __filter_blog_url(self,url):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
    
        if re.search(self.filter_rule,url) :
            test_url="%s?viewmode=list"%(url)
            if self.url_test(test_url) :
                self.htmlblog_a.put(test_url)
                self.htmlblog_a_count.value+=1
                self.push_log("process-%s-%d,put url=%s to htmlblog_a queue"%(funcname,pid,test_url))

    def __onsignal_kill(self,signo='',ff=''):
        funcname=sys._getframe().f_code.co_name
        curr_pid=os.getpid()

        self.push_debug('%s-%d:start'%(funcname,curr_pid))
        self.iskill.value=1
        self.__htmla_onsignal_dumper() 
        #self.push_debug('%s-%d:dumper已经被其他进程执行完毕'%(funcname,curr_pid))
        #self.push_debug('%s-%d:dumper完毕'%(funcname,curr_pid))

        pid_datas=serializer('%s/data/pids.json'%self.workdir)
        pids=pid_datas.loader()
        
        for p in pids:
            if p['pid'] == curr_pid :
                del(p['pid'])
            else:
                self.push_debug('结束进程%s'%str(p))
                os.kill(p['pid'],signal.SIGKILL)
            
        pid_datas.dumper({})
        sys.exit()
        
    def __save_pageurl(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        try:
            pageurl=[]
            qsize=self.pageurl.qsize()
            for i in range(qsize):
                self.push_debug('serializer dumper pageurl,is %d'%i,'dumper_queue.log')
                pageurl.append(self.pageurl.get_nowait())
            
            pageurl_data=serializer('%s/data/pageurl.json'%self.workdir)
            pageurl_data.dumper(pageurl)
            
            if self.iskill.value == 1 :
                self.debug('is kill opener,skip rewrite')
                return True
                
            for l in range(len(pageurl)):
                self.push_debug('rewrite pageurl queue,is %d'%l,'dumper_queue.log')
                self.pageurl.put_nowait(pageurl[l])
           
        except Exception,e:
            self.push_err("process-%s-%d-e:error info:%s\n"%(funcname,pid,str(e)) )
        
    def __save_blogurl(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        try:
            blogurl=[]
            qsize=self.blogurl.qsize()
            for i in range(qsize):
                self.push_debug('serializer dumper blogurl,is %d'%i,'dumper_queue.log')
                blogurl.append(self.blogurl.get_nowait())
            
            blogurl_data=serializer('%s/data/blogurl.json'%self.workdir)
            blogurl_data.dumper(blogurl)
            
            if self.iskill.value == 1 :
                self.debug('is kill opener,skip rewrite')
                return True
                
            for l in range(len(blogurl)):
                self.push_debug('rewrite blogurl queue,is %d'%l,'dumper_queue.log')
                self.blogurl.put_nowait(blogurl[l])
           
        except Exception,e:
            self.push_err("process-%s-%d-e:error info:%s\n"%(funcname,pid,str(e)) )
             
    def __save_htmlblog_a(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        try:
            htmlblog_a=[]
            qsize=self.htmlblog_a.qsize()
            for i in range(qsize):
                self.push_debug('serializer dumper htmlblog_a,is %d'%i,'dumper_queue.log')
                htmlblog_a.append(self.htmlblog_a.get_nowait())
            
            htmlblog_a_data=serializer('%s/data/htmlblog_a.json'%self.workdir)
            htmlblog_a_data.dumper(htmlblog_a)
            
            if self.iskill.value == 1 :
                self.debug('is kill opener,skip rewrite')
                return True
            
            for l in range(len(htmlblog_a)):
                self.push_debug('rewrite htmlblog_a queue,is %d'%l,'dumper_queue.log')
                self.htmlblog_a.put_nowait(htmlblog_a[l])
               
        except Exception,e:
            self.push_err("process-%s-%d-e:error info:%s\n"%(funcname,pid,str(e)) )

    def __save_html_a(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        try:
            html_a=[]
            qsize=self.html_a.qsize()
            for i in range(qsize):
                self.push_debug('serializer dumper html_a,is %d'%i,'dumper_queue.log')
                html_a.append(self.html_a.get_nowait())
            
            html_a_data=serializer('%s/data/html_a.json'%self.workdir)
            html_a_data.dumper(html_a)

            if self.iskill.value == 1 :
                self.debug('is kill opener,skip rewrite')
                return True
                
            for l in range(len(html_a)):
                self.push_debug('rewrite html_a queue,is %d'%l,'dumper_queue.log')
                self.html_a.put_nowait(html_a[l])
                
        except Exception,e:
            self.push_err("process-%s-%d-e:error info:%s\n"%(funcname,pid,str(e)) )
            
    def __save_html_a_md5(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        self.push_debug('serializer dumper html_a_md5','dumper_queue.log')
        html_a_md5_data=serializer('%s/data/html_a_md5.json'%self.workdir)
        html_a_md5_data.dumper(self.html_a_md5.copy(),merge=True)

    def __save_htmlblog_a_md5(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        self.push_debug('serializer dumper htmlblog_a_md5','dumper_queue.log')
        htmlblog_a_md5_data=serializer('%s/data/htmlblog_a_md5.json'%self.workdir)
        htmlblog_a_md5_data.dumper(self.htmlblog_a_md5.copy(),merge=True)            

    
    def __htmla_onsignal_dumper(self,signo='',ff=''):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name

        if self.dumper.value == 1 :
            while(self.dumper.value == 1):
                self.push_debug('%s-%d跳过dumper,已经有进程在dumper,'%(funcname,pid))
                time.sleep(2)
            return False

        self.dumper_lock.acquire()
        self.dumper.value = 1

        self.push_debug('程序%s,pid=%d,start dumper'%(funcname,pid))
        self.push_debug(signo)
        
        self.__save_html_a()
        self.__save_html_a_md5()
        
        self.__save_htmlblog_a()
        self.__save_htmlblog_a_md5()
        
        self.__save_pageurl()
        self.__save_blogurl()
        
        self.dumper.value = 0
        self.dumper_lock.release()
        
        self.push_debug('程序%s,pid=%d,end dumper'%(funcname,pid))
        return True


    def __restore_html_a(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        
        try:
            htmla_data=serializer('%s/data/html_a.json'%self.workdir)
            list=htmla_data.loader()
            for htmla in list:
                i='i' in dir() and i+1 or 1
                self.push_debug('serializer loader html_a:%d'%i,'loader_queue.log')
                self.html_a.put_nowait(htmla)
        except Exception,e1:
            self.push_err("process-%s-%d-e1:error info:%s\n"%(funcname,pid,str(e1)) )
            
    def __restore_html_a_md5(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name 

        try:
            self.push_debug('serializer loader html_a_md5','loader_queue.log')
            html_a_md5_data=serializer('%s/data/html_a_md5.json'%self.workdir)
            self.html_a_md5.update(html_a_md5_data.loader())
        except Exception,e2:
            self.push_err("process-%s-%d-e2:error info:%s\n"%(funcname,pid,str(e2)) )
        
    def __restore_htmlblog_a(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name 
        
        try:
            htmlblog_a_data=serializer('%s/data/htmlblog_a.json'%self.workdir)
            list=htmlblog_a_data.loader()
            for htmlblog_a in list:
                i='i' in dir() and i+1 or 1
                self.push_debug('serializer loader htmlblog_a:%d'%i,'loader_queue.log')
                self.htmlblog_a.put_nowait(htmlblog_a)
        except Exception,e3:
            self.push_err("process-%s-%d-e3:error info:%s\n"%(funcname,pid,str(e3)) )   

    def __restore_htmlblog_a_md5(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name 
        
        try:
            self.push_debug('serializer loader htmlblog_a_md5','loader_queue.log')
            htmlblog_a_md5_data=serializer('%s/data/htmlblog_a_md5.json'%self.workdir)
            self.htmlblog_a_md5.update(htmlblog_a_md5_data.loader())
        except Exception,e4:
            self.push_err("process-%s-%d-e4:error info:%s\n"%(funcname,pid,str(e4)) )     

    def __restore_pageurl(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name 
        
        try:
            pageurl_data=serializer('%s/data/pageurl.json'%self.workdir)
            list=pageurl_data.loader()
            for pageurl in list:
                i='i' in dir() and i+1 or 1
                self.push_debug('serializer loader pageurl:%d'%i,'loader_queue.log')
                self.pageurl.put_nowait(pageurl)
        except Exception,e3:
            self.push_err("process-%s-%d-e3:error info:%s\n"%(funcname,pid,str(e3)) )               
        
    def __restore_blogurl(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name 
        
        try:
            blogurl_data=serializer('%s/data/blogurl.json'%self.workdir)
            list=blogurl_data.loader()
            for blogurl in list:
                i='i' in dir() and i+1 or 1
                self.push_debug('serializer loader blogurl:%d'%i,'loader_queue.log')
                self.blogurl.put_nowait(blogurl)
        except Exception,e3:
            self.push_err("process-%s-%d-e3:error info:%s\n"%(funcname,pid,str(e3)) )    
            
    def __loader_data(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
      
        if self.loader.value == 1 :
            while(self.loader.value == 1):
                self.push_debug('%s-%d跳过loader,已经有进程在loader,'%(funcname,pid))
                time.sleep(2)
            return False
         
        self.loader_lock.acquire()    
        self.loader.value=1
        self.push_debug('程序%s,pid=%d,start loader'%(funcname,pid))

        self.__restore_html_a()
        self.__restore_html_a_md5()
        
        self.__restore_htmlblog_a()
        self.__restore_htmlblog_a_md5()
        
        self.__restore_pageurl()
        self.__restore_blogurl()

        self.loader.value=0        
        self.loader_lock.release()
        
        return True



    def get_html_a(self):
        pid=os.getpid()
        funcname=sys._getframe().f_code.co_name
        free_timer=0
        stop_put_queue  = False
        loop_marked     = {}

        if not self.__loader_data() :
            self.push_debug('%s-%d,skip loader data,run %s'%(funcname,pid,funcname))
        else:
            self.push_debug('%s-%d,loader data end,run %s'%(funcname,pid,funcname))

        signal.signal(signal.SIGUSR1,self.__htmla_onsignal_dumper)
        #signal.signal(signal.SIGTERM,self.__onsignal_kill)

        while True:
            if self.html_a.qsize() == 0 and free_timer < self.free_maxtime:
                time.sleep(5)
                free_timer+=5
                self.put_console( "process-%s-%d,free_timer=%d\n"     %(funcname,pid,free_timer) )
                continue
            elif self.html_a.qsize() == 0 :
                self.put_console( "process-%s-%d,free_timer=%d,exit\n"%(funcname,pid,free_timer) )
                sys.exit()

            free_timer=0

            try:
                url = self.html_a.get()
                html= self.Get(url)
                if html==None:
                    continue
                
                soup=BeautifulSoup(html,'html5lib')
                data_a=soup.findAll('a')            
                if not data_a :
                    continue
                    
                for u in data_a:
                    if not u.has_attr('href'):
                        self.push_log("process-%s-%d,is not href key"%(funcname,pid),False )
                        continue

                    if re.search('^/(.*)',u['href']):
                        url1=self.domain+u['href']
                    elif re.search(self.domain,u['href']):
                        url1=u['href']

                    md5url=md5(url1)
                    if self.html_a_md5.has_key(md5url) :
                        self.html_a_md5[md5url]+=1

                        t=time.strftime("%Y-%m-%d %H:%M:%S")
                        if self.html_a_md5[md5url] > 100 :
                            with open(self.workdir+'/logs/repeat_url.log','a') as rr:
                                rr.write("[%s] : process-%s-%d,url:%s md5_key:%s,count:%d,gt 100,Marked as loop!\n"%(t,funcname,pid,url1,md5url,self.html_a_md5[md5url]) )
                                rr.write("[%s] : process-%s-%d,loop_marked:%d!\n"%(t,funcname,pid,loop_marked[md5url]) )
                                rr.flush()

                            loop_marked[md5url]=loop_marked.get(md5url,0)+1
                            if len(loop_marked) > 100 :
                                with open(self.workdir+'/logs/repeat_url.log','a') as rr:
                                    rr.write("[%s] : process-%s-%d,loop_marked:%d,is ge 100,is loop,exit!\n"%(t,funcname,pid,loop_marked) )
                                if self.html_a.qsize() == 0 : 
                                    sys.exit()
                                else:
                                    stop_put_queue=True
                        else:
                            with open(self.workdir+'/logs/repeat_url.log','a') as rr:
                                rr.write("[%s] : process-%s-%d,url:%s,md5_key:%s,count:%d\n"%(t,funcname,pid,url1,md5url,self.html_a_md5[md5url]) )
                            continue
                    elif stop_put_queue :
                        #不再往html_a队列插入数据，消耗完html_a队列后将退出
                        self.push_log("process-%s-%d,url=%s,url_md5=%s\n"%(funcname,pid,url1,md5url),False)
                        self.__filter_blog_url(url1)
                        if self.html_a.empty():
                            sys.exit()
                    else:
                        self.html_a.put(url1)
                        self.html_a_md5[md5url]=1

                        self.html_a_count.value+=1
                        self.html_a_md5_count.value+=1

                        self.push_log("process-%s-%d,url=%s,url_md5=%s\n"%(funcname,pid,url1,md5url),False)
                        self.__filter_blog_url(url1)
            except Exception,e:
                self.push_err("process-%s-%d-e:error info:%s\n"%(funcname,pid,str(e)) )
                continue

    def get_pagelist(self):
        funcname=sys._getframe().f_code.co_name
        pid=os.getpid()
        free_timer = 0

        while True:
            try :
                if self.htmlblog_a.qsize() == 0 and free_timer < self.free_maxtime:
                    time.sleep(5)
                    free_timer+=5
                    self.put_console( "process-%s-%d,free_timer=%d\n"       %(funcname,pid,free_timer))
                    continue
                elif self.htmlblog_a.qsize() == 0 :
                    self.put_console( "process-%s-%d,free_timer=%d,exit!\n" %(funcname,pid,free_timer))
                    sys.exit()

                free_timer = 0
                self.pageurl_count.value+=1

                url = self.htmlblog_a.get()
                if not url :
                    continue

                self.push_log("process-%s-%d,geturl=%s\n"     %(funcname,pid,url), False)
                if not self.__get_pageurl(url,pid) :
                    continue
            except Exception,e:
                self.push_err("process-%s-%d-e:url=%s error info:%s\n"%(funcname,pid,url,str(e)) )
                continue

    def __get_userinfo(self,html,url):
        try :
            soup     = BeautifulSoup(html,'html5lib')

            user_html= soup.find("a",{"class":"user_name"})

            name     = user_html.text
            href     = user_html['href']
            user     = re.search('\/([\w\d\_]+)\?viewmode=list',url).groups()[0]

            if not user :
                return None
            else:
                d1={'name':name,'user':user,'user_href':href}
                return d1
        except Exception,e:
            if not 'user' in dir() or not user :
                self.push_err(str(e))
                return Nane
            else:
                self.push_err(str(e))
                name   = 'name' in dir() and name or ''
                href   = 'href' in dir() and href or ''
                d1={'name':name,'user':user,'user_href':href}
                return d1


    def __get_pageurl(self,url,pid):
        funcname=sys._getframe().f_code.co_name

        if self.dumper.value == 1 :
            while(self.dumper.value == 1):
                self.push_debug('%s-pid=%d,正在dumper，暂停执行'%(funcname,pid))
                time.sleep(2)

        html = self.Get(url)

        href_md5=md5(url)
        #self.dumper_lock.acquire()
        self.htmlblog_a_md5[href_md5]=self.htmlblog_a_md5.get(href_md5,0)+1
        #self.dumper_lock.release()

        if html==None:
            return False

        userinfo = self.__get_userinfo(html,url)
        if userinfo == None :
            return False

        alist=[];
        try :
            soup     = BeautifulSoup(html,'html5lib')
            page_html= soup.select("div[class=pagelist] > a")
            for p in page_html:
                url1=p.attrs['href']
                a=re.search('/article/list/(\d+)',url1)
                alist.append(int(a.groups()[0]))
        except Exception,e1:
            self.push_err('process-%s-%d-e1,get page list error!error=%s,data=%s\n'%(funcname,pid,str(e1),str(p) ) )

        try :
            alist=alist and alist or [1]
            max1=max(alist) 
            tmp=[]
            for i in range(1,max1+1):
                 base=self.urls+userinfo['user']
                 lll="%s/article/list/%d"%(base,i)
                 tmp.append({'href':lll,'listid':i})
            d1={'content_pagelist':tmp,'page_index':url,'userinfo':userinfo}
            self.pageurl.put(d1)
            self.push_log(json.dumps(d1,ensure_ascii=False,indent=4),False)
        except Exception,e2:
            self.push_err('process-%s-%d-e2,url=%s,get page list error,error_info=%s\n'%(funcname,pid,url,str(e2)) )


def daemonize(stdout='/dev/null',stdin='/dev/null',stderr=None,pidfile=None, startmsg='started with pid %s' ):
    '''    
         This forks the current process into a daemon. 
         The stdin, stdout, and stderr arguments are file names that 
         will be opened and be used to replace the standard file descriptors 
         in sys.stdin, sys.stdout, and sys.stderr. 
         These arguments are optional and default to /dev/null. 
        Note that stderr is opened unbuffered, so 
        if it shares a file with stdout then interleaved output 
         may not appear in the order that you expect. 
     '''
    # flush io  
    sys.stdout.flush() 
    sys.stderr.flush()   
    
    # Do first fork.  
    try:
        pid = os.fork()  
        if pid > 0: sys.exit(0) # Exit first parent. 
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment. 
    os.chdir("/")
    os.umask(0)
    os.setsid()

    # Do second fork. 
    #try:
    #    pid = os.fork()
    #    if pid > 0: sys.exit(0) # Exit second parent. 
    #except OSError, e:
    #    sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
    #    sys.exit(1)

    # Open file descriptors and self.put_console start message 
    if not stderr:
        stderr = stdout

    si  = file(stdin,   'r' )
    so  = file(stdout,  'a+')
    se  = file(stderr,  'a+',0)  #unbuffered 

    pid = str(os.getpid())
    sys.stderr.write("\n%s\n" % startmsg % pid)
    sys.stderr.flush()

    if pidfile:
        fdpid=file(pidfile,'w+')
        fdpid.write("%s" % pid)
        fdpid.close()

    # Redirect standard file descriptors. 
    os.dup2(si.fileno(), sys.stdin.fileno() )
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    blog=BlogRoobt()
    blog.Start()

if __name__ == '__main__':
    current_dir=os.getcwd();
    daemonize(
        stdout  =   current_dir+'/stdout.log',
        stderr  =   current_dir+'/stderr.log',
        pidfile =   current_dir+'/BlogRoobt.pid'
    )

#blog=BlogRoobt()
#blog.Start()
