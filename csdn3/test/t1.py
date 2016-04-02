import multiprocessing
import time,os

class test:
    def write(self,key, value):
        self.d.update({key:value})

    def read(self,key):
        #print "pid=%d,d[%s]:%s"%(os.getpid(),key,self.d[key])
        print "pid=%d,%s"%(os.getpid(),str(self.d))
        d=self.d.copy()
        #for key,val in self.d.items():
        #    d[key]=val
        print type(d)
        print d
        print "\n\n"
        #self.d[key]=11

    def run(self):
        mgr = multiprocessing.Manager()
        self.d = mgr.dict()

        jobs = [] 
        for i in range(20):
            jobs.append(multiprocessing.Process(target=self.write,args=(i, str(i*20))) )

        for i in range(20):
            jobs.append(multiprocessing.Process(target=self.read,args=(i,) ) )

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
