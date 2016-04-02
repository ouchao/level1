import sys
import os
import json
import types

class serializer():

    def __init__(self,file):
        if not os.path.exists(file):
            with open(file,'a') as f:
                f.write('')

        self.file=file

    def __clear(self):
        try:
            os.remove(self.file)
        except Exception,e:
            print str(e)

    def dumper(self,data,merge=False):
        if merge :
            d1=self.loader()
            if   type(d1) is types.ListType  and type(data) is types.ListType:
                data=data+d1
            elif type(d1) is types.TupleType and type(data) is types.TupleType:
                data=list(data+d1)
            elif type(d1) is types.DictType  and type(data) is types.DictType:
                data=dict(data,**d1)
            elif not d1 and data:
                print "file data is empty"
            else:
                print "dumper error,data merge error"
                return False

        self.__clear()

        with open(self.file,'a') as s:
            tmp=json.dumps(data,ensure_ascii=False,indent=4)
            s.write(tmp)
            
    def loader(self):
        with open(self.file,'r+') as s:
            xx=s.read()
        xx='xx' in dir() and xx or {}
        if xx :
            return eval(xx)
        else:
            return xx
'''
print sys.argv
if len(sys.argv) < 2:
    sys.exit()

xx=[]
#d=dict(name='Bob', age=20, score=88)
d={'name11ss':'Bob'}

data=serializer('working/data/htmla_md5.json');
if sys.argv[1] == 'dumper':
    data.dumper(d,merge=True)
elif sys.argv[1] == 'loader':
    print data.loader()
'''
