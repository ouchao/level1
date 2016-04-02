import urllib2

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


def url_test(url):
    try:
        opener = urllib2.build_opener(SpiderDefaultErrorHandler())  
        urllib2.install_opener(opener)

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36')
        #req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)')
        req.add_header('Accept', '*/*')
        req.add_header('Accept-Language', 'zh-CN,zh;q=0.8,en;q=0.6')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        resp = urllib2.urlopen(req)
        if resp.code == 200 :
            return resp.read()
        else:
            return resp.code
    except Exception,e:
        print("Get:error=%s\n"%str(e))

#print url_test('http://www.baidu.com/')
print url_test('http://blog.csdn.net/')
