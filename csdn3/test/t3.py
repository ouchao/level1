import os

def xx(i):
    pid=os.fork()
    if pid == 0:
        if i==1:
            print "is %d"%i
        elif i==10:
            print "is %d"%i
        elif i==100:
            print "is %d"%i

        print "this is a sub process"
    if pid > 0:
        print "this is father process"
    else:
        print "create process error"

    print "testet"


xx(100)
