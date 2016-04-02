import threading
import time,os

class test:
    def write(self,key, value):
        self.d[key]=value

    def read(self,key):
        print "pid=%d,d[%s]:%s"%(os.getpid(),key,self.d[key])
        self.d[key]=11

    def run(self):
        self.d = {}

        jobs = [] 
        for i in range(20):
            jobs.append(threading.Thread(target=self.write,args=(i, str(i*20))) )

        for i in range(20):
            jobs.append(threading.Thread(target=self.read,args=(i,) ) )

        for j in jobs:
            j.start()
        for j in jobs:
            j.join()

        print ('Results:' )
        print self.d

        for key, value in enumerate(dict(self.d)):
            print("%s=%s" % (key, value))

a=test()
a.run()
