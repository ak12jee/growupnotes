import os
import sys
import chardet
import codecs
import platform
import re
# encoding: utf-8
#coding:utf-8
#pip install chardet
if 'Windows' in platform.platform():
    spilt='\\'
elif 'Linux' in platform.platform():
    spilt='/'
print (spilt )
def Print(str):
    #print str.encode(sys.stdout.encoding) + "\n"
    print( unicode(str,'utf8'))
    return
def convert( filename, out_enc="UTF-8-sig"):
    #print(filename)
    if not re.match(r'.*\.(h|hpp|c|cpp)$', str(filename), flags=0):
        return
    try:
        content=codecs.open(filename,'r').read()
        source_encode=chardet.detect(content)['encoding']
        print (filename, " is ", source_encode)
        if( source_encode != out_enc ):
            content = content.decode(source_encode).encode(out_enc)
            codecs.open(filename, 'w').write(content)
    except IOError  as err:
        print( "I/O error:{0}".format(err))
        exit()

def search(dir):
    file_list=[]
    if not os.path.exists(dir):
        print( dir , 'is not exist ')
        return file_list
    for item in os.listdir(dir):
        #print (item )
        basename=os.path.basename(item)
        if os.path.isdir(dir+spilt+item ):
            sub_file_list = search(dir+spilt+item)
            #file_list.append(sub_file_list)
            file_list = file_list+sub_file_list
        else:
            try:
                decode_str=basename.decode("GB2312")
                #print( dir, decode_str )
            except UnicodeDecodeError:
                decode_str=basename.decode("utf-8")
            convert(os.path.join(dir,basename))
            file_list.append(decode_str)
    return file_list

def main():
    search(os.getcwd())
if __name__=="__main__":
    main()
