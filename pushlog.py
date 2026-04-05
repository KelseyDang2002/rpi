#encoding:utf-8
################################################################################
# Program:   VSign Real-time Data Transmission (hub to server, server to server)
#
# Authors:   Care Jiang, Lianyu Chu
#
# Functions: Encryption, Compression, Auto single/multiple record(s) transmission,
#            Use RAM as buffer, Timestamp/priority transmission mode,
#            server response requirement
#
# Input:     pushlog.conf
# Output:    pushlog.log (setup in the restart_pushlog.sh or supervisor.conf)
#
# Dependencies: zlib; Two programs, log_server and consume on the server Side
##############################################################################
import os,os.path
import sys
import time
import re
import configparser
import socket
import zlib
import getopt

g_Encryption_Keys=[0x1f, 0x0a, 0x1d, 0x1e, 0x04, 0x08, 0x11]
g_Encryption_Smallest_Char=0x20
g_MaxOpen=500

g_INTP_PSR=61
g_REID_PSR=30
g_INTP_START_Y=0
g_INTP_END_Y=0
g_START_FIRST_DRV=0.5
g_END_FIRST_DRV=0.5
g_HAAR_SIZE=32

g_compress = "0"
g_subfolder = "0"
g_interval = 0.4
g_compressionLevel = 6
g_encrypt = "1"
g_debug = 0
g_filename_header = "1"
g_tempFolder = "/dev/shm/"
g_send_type = 0
g_ramTime = 300
g_serverResponse = 1
g_noResponsePrint = 1
g_moveToBackup = 0
g_sendCountOnce=10
g_sendPSR = 1
g_waitTime = 1

VERSION='3.0.0'

def pause():
    programPause = raw_input("Press the <ENTER> key to continue...")

def encrypt(input):
    keySize=len(g_Encryption_Keys)
    output=''
    for i in range(0,len(input)):
        if ord(input[i]) >= g_Encryption_Smallest_Char:
            output = output+chr(ord(input[i])^g_Encryption_Keys[i % keySize])
        else:
            output = output+input[i]
    return output

def decrypt(input):
    keySize=len(g_Encryption_Keys)
    output=''
    for i in range(0,len(input)):
        if ord(input[i]) >= g_Encryption_Smallest_Char:
            output = output+chr(ord(input[i])^g_Encryption_Keys[i % keySize])
        else:
            output = output+input[i]
    return output

def searchFile(pathname,filename):
    matchedFile =[]
    paths = pathname.split('|')
    for path in paths:
        path = path.strip()
        #print g_subfolder
        for root,dirs,files in os.walk(path):
            if g_subfolder == "1":
                for file in files:
                    if re.match(filename,file):
                        fname = os.path.abspath(os.path.join(root,file))
                        matchedFile.append(fname)
            else:
                if root == path:
                    for file in files:
                        if re.match(filename,file):
                            fname = os.path.abspath(os.path.join(root,file))
                            matchedFile.append(fname)

    return matchedFile

def takeSecond(elem):
    return elem[1]

class ReadLog(object):
    def __init__(self, config_file):
        self.last_run_time = 0
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.pathname = self.config.get("path", "file_path")
        self.filename = self.config.get("path", "log_file")
        self.openfile = 0
        self.maxfilesize = 3145728
        if self.config.has_option("dev_shm_backup", "max_file_size"):
            self.maxfilesize = int(self.config.get("dev_shm_backup", "max_file_size"))
        self.cachesize = 30000000
        if self.config.has_option("dev_shm_backup", "cache_size"):
            self.cachesize = int(self.config.get("dev_shm_backup", "cache_size"))
        self.backuppath = "/media/card"
        self.cachepath = "/media/ram"
        if self.config.has_option("dev_shm_backup", "backup_path"):
            self.backuppath = self.config.get("dev_shm_backup", "backup_path")
        if self.config.has_option("dev_shm_backup", "cache_path"):
            self.cachepath = self.config.get("dev_shm_backup", "cache_path")
        self.cachetimeout = 7200
        if self.config.has_option("dev_shm_backup", "cache_timeout"):
            self.cachetimeout = int(self.config.get("dev_shm_backup", "cache_timeout"))
        self.pushlog_addr = self.config.get("push", "pushlog_addr")
        self.pushlog_port = self.config.get("push", "pushlog_port")
        self.pushlog_addr2 = self.config.get("push", "pushlog_addr2")
        self.pushlog_port2 = self.config.get("push", "pushlog_port2")
        global g_subfolder,g_compress,g_interval,g_compressionLevel,g_encrypt,g_debug,g_filename_header,g_send_type,g_ramTime,g_response,g_noResponsePrint,g_moveToBackup,g_sendCountOnce,g_sendPSR,g_waitTime
        if self.config.has_option("config", "compression"):
            g_compressLevel = int(self.config.get("config", "compression"))
            if g_compressLevel > 0:
                g_compress = "1"
        if self.config.has_option("config", "encryption"):
            g_encrypt = self.config.get("config", "encryption")
        if self.config.has_option("config", "subfolder"):
            g_subfolder = self.config.get("config", "subfolder")
        if self.config.has_option("config", "transmission_interval"):
            g_interval = float(self.config.get("config", "transmission_interval"))
        if self.config.has_option("config", "debug"):
            g_debug = int(self.config.get("config", "debug"))
        if self.config.has_option("config", "filename_header"):
            g_filename_header = self.config.get("config", "filename_header")
        if self.config.has_option("config", "send_type"):
            g_send_type = int(self.config.get("config", "send_type"))
        if self.config.has_option("config", "timeInRam"):
            g_ramTime = int(self.config.get("config", "timeInRam"))
        if self.config.has_option("config", "serverResponse"):
            g_serverResponse = int(self.config.get("config", "serverResponse"))
        if self.config.has_option("config", "noServerResponsePrint"):
            g_noResponsePrint = int(self.config.get("config", "noServerResponsePrint"))
        if self.config.has_option("config", "move_to_backup"):
            g_moveToBackup = int(self.config.get("config", "move_to_backup"))
        if self.config.has_option("config", "send_count_once"):
            g_sendCountOnce = int(self.config.get("config", "send_count_once"))
            if g_sendCountOnce <= 1:
                g_sendCountOnce = 1
        if self.config.has_option("config", "send_psr"):
            g_sendPSR = int(self.config.get("config", "send_psr"))
        if self.config.has_option("config", "wait_time"):
            g_waitTime = int(self.config.get("config", "wait_time"))
        self.socket_idx = 1
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s_connected = False
        self.callback = sys.stdout.write
        #self.files = searchFile(self.pathname,self.filename)
        self.files = []
        self.idx_file = self.config.get("path", "idx_file")
        self.config_idx = configparser.ConfigParser()
        self.config_idx.read(self.idx_file)
        if not self.config_idx.has_section("file_idx"):
            self.config_idx.add_section("file_idx")
        self.file_idx = {}
        for item in self.config_idx.items('file_idx'):
            file = item[0]
            idx = int(item[1])
            self.files.append(file)
            self.file_idx[file]=idx
        self.p_files = {}
        self.check_new_file()
        #print(g_subfolder,g_compress,g_interval,g_compressionLevel,g_encrypt,g_debug,g_filename_header)
        #pause()

    def open_file(self, file):
        pf=open(file)
        if self.openfile > g_MaxOpen:
            for of in self.p_files:
                if not self.p_files[of].closed:
                    self.close_file(self.p_files[of])
        self.openfile+=1
        return pf

    def close_file(self, pfile):
        pfile.close()
        self.openfile-=1

    def remove_file(self, file):
        if file in self.p_files:
            if not self.p_files[file].closed:
                self.close_file(self.p_files[file])
            del self.p_files[file]
        if file in self.file_idx:
            del self.file_idx[file]
        self.files.remove(file)
        if self.config_idx.has_option("file_idx", file):
            self.config_idx.remove_option("file_idx", file)

    def sort_file(self):
        self.files.sort()
        if g_send_type == 0:
            file_dev = []
            file_ram = []
            file_card = []
            for file in self.files:
                pp,ff = os.path.split(file)
                if pp == '/dev/shm':
                    file_dev.append(file)
                elif pp == self.cachepath:
                    file_ram.append(file)
                else:
                    file_card.append(file)
            if g_send_type == 0:
                self.files = file_dev+file_ram+file_card
        else:
            file_list = []
            for file in self.files:
                pp,ff = os.path.split(file)
                file_path = (pp,ff)
                file_list.append(file_path)
            file_list.sort(key=takeSecond)
            self.files = []
            for file in file_list:
                self.files.append(file[0]+'/'+file[1])

    def check_new_file(self):
        for file in self.files:
            if not os.path.exists(file):
                self.remove_file(file)

        new_files = searchFile(self.pathname,self.filename)
        for file in new_files:
            if not (file in self.files):
                self.files.append(file)
                self.file_idx[file]=0
                self.p_files[file] = self.open_file(file)

        cache_dir_size = 0
        for file in self.files:
            #check file size and date
            if not os.path.exists(file):
                self.remove_file(file)
                continue
            pp,ff = os.path.split(file)
            file_type = os.path.splitext(file)[1].upper()
            time3h = time.localtime(time.time()-3600*3)
            file_size = os.path.getsize(file)
            if pp == self.cachepath:
                movefile = False
                cache_dir_size += file_size
                if cache_dir_size>self.cachesize:
                    movefile = True
                mft=os.path.getmtime(file)
                if time.time() - mft > self.cachetimeout:
                    movefile = True
                #move file to backup dir
                if file_size <= self.file_idx[file] and file_type == ".MAGM":
                    #remove file
                    self.remove_file(file)
                    os.system("rm -f "+file)
                elif movefile  and file_type == ".MAGM":
                    new_name = os.path.join(self.backuppath, ff)
                    addn = 1
                    while os.path.exists(new_name):
                        f1,f2 = os.path.splitext(ff)
                        new_name = os.path.join(self.backuppath,f1+"."+str(addn)+f2)
                        addn = addn + 1
                        if addn >= 100:
                            print("max file!!!")
                            break
                    #os.rename(file, new_name)
                    os.system("mv "+file+" "+new_name)
                    self.p_files[new_name] = self.open_file(new_name)
                    if file in self.file_idx:
                        self.file_idx[new_name] = self.file_idx[file]
                        self.config_idx.set("file_idx", new_name, self.file_idx[new_name])
                    self.files.append(new_name)
                    self.remove_file(file)
            elif pp == "/dev/shm":
                movefile = False
                if file_size>self.maxfilesize:
                    movefile = True
                mft=os.path.getmtime(file)
                if time.time() - mft > g_ramTime:
                    movefile = True
                #move file to backup dir
                if movefile and file_size <= self.file_idx[file] and file_type == ".MAGM":
                    #remove file
                    self.remove_file(file)
                    os.system("rm -f "+file)
                elif movefile :
                    new_name = os.path.join(self.cachepath, ff)
                    addn = 1
                    while os.path.exists(new_name):
                        f1,f2 = os.path.splitext(ff)
                        new_name = os.path.join(self.cachepath,f1+"."+str(addn)+f2)
                        addn = addn + 1
                        if addn >= 100:
                            print("max file!!!")
                            break
                    #os.rename(file, new_name)
                    os.system("mv "+file+" "+new_name)
                    self.p_files[new_name] = self.open_file(new_name)
                    if file in self.file_idx:
                        self.file_idx[new_name] = self.file_idx[file]
                        self.config_idx.set("file_idx", new_name, self.file_idx[new_name])
                    self.files.append(new_name)
                    self.remove_file(file)
            else:
                mft1=os.path.getmtime(file)
                if file_size <= self.file_idx[file] and file_type == ".MAGM" and time.time() - mft1 > g_ramTime:
                    #remove file
                    os.system("rm -f "+file)
                    self.remove_file(file)
                else:
                    if time.time() - mft1 > 86400:
                        if g_moveToBackup == 0:
                            os.system("rm -f "+file)
                            self.remove_file(file)
                        elif pp != self.backuppath:
                            new_name = os.path.join(self.backuppath, ff)
                            addn = 1
                            while os.path.exists(new_name):
                                f1,f2 = os.path.splitext(ff)
                                new_name = os.path.join(self.backuppath,f1+"."+str(addn)+f2)
                                addn = addn + 1
                                if addn >= 100:
                                    print("max file!!!")
                                    break
                            os.system("mv "+file+" "+new_name)
                            self.remove_file(file)
        new_files = searchFile(self.pathname,self.filename)
        for file in new_files:
            if not (file in self.files):
                self.files.append(file)
                self.file_idx[file]=0
                self.p_files[file] = self.open_file(file)
        self.sort_file()

    def save_config(self):
        fb = open(self.idx_file,"w")
        self.config_idx.write(fb)
        fb.close()

    def follow(self, s=1, waite=1):
        try:
            all_send = False
            for file in self.files:
                if not os.path.exists(file):
                    continue
                self.p_files[file] = self.open_file(file)
            while True:
                self.check_new_file()
                self.save_config()
                # 当最后一次全部发送，并且当前距离最后一次运行时间未超时，等待10秒
                if waite > 60:
                    if all_send and time.time() - self.last_run_time < waite:
                        time.sleep(10)
                        continue
                    if time.time() - self.last_run_time >= waite:
                        nowTime = time.time()
                        self.last_run_time = nowTime - nowTime%waite
                if not self.s_connected:
                    time.sleep(1)
                    try:
                        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        addr = self.pushlog_addr
                        port = int(self.pushlog_port)
                        if self.socket_idx == 2 and len(self.pushlog_addr2)>3:
                            addr = self.pushlog_addr2
                            port = int(self.pushlog_port2)

                        print("connect to:",addr,port,self.socket_idx)
                        self.s.connect((addr, port))
                        self.s.settimeout(10)
                        self.s_connected = True
                    except Exception as err:
                        print("connect error:",err)
                        if self.socket_idx == 2:
                            self.socket_idx = 1
                        else:
                            self.socket_idx = 2
                        self.s_connected = False
                        continue
                    time.sleep(1)
                send_count = 0
                all_send = True
                self.sort_file()
                for file in self.files:
                    if not os.path.exists(file):
                        continue
                    file_type = os.path.splitext(file)[1].upper()
                    if send_count >= g_sendCountOnce:
                        break
                    if not self.s_connected:
                        break
                    try:
                        file_ = self.p_files[file]
                        if file_.closed:
                            file_ = self.open_file(file)
                        if file_.closed:
                            continue
                        # Go to the end of file
                        if self.file_idx[file] == -1:
                            file_.seek(0, 2)
                        else:
                            file_.seek(self.file_idx[file])
                        sendData = ""
                        fileReadLen = 0
                        while True:
                            if send_count >= g_sendCountOnce:
                                self.file_idx[file] = file_.tell()
                                break
                            line = file_.readline()
                            if not line or line[-1] != '\n':
                                file_.seek(self.file_idx[file]+fileReadLen)
                                break
                            else:
                                all_send = False
                                fileReadLen = fileReadLen + len(line)
                                if g_sendPSR == 0 and file_type == ".MAGM" :
                                    str_p = line.rfind(',')
                                    if str_p > 0:
                                        line = line[0:str_p+1]+'\n'
                                send_count = send_count + 1
                                sendData = sendData + line
                        if len(sendData) > 0:
                            count_index = file_.tell()
                            if self.callback(sendData,file):
                                self.config_idx.set("file_idx", file, count_index)
                                self.file_idx[file] = count_index
                            else:
                                if count_index < fileReadLen:
                                    print("file idx is error!!!")
                                file_.seek(count_index - fileReadLen)
                                self.file_idx[file] = count_index - fileReadLen
                    except IOError as err:
                        pass
                time.sleep(s)
            self.s.shutdown(2)
        except IOError as err:
            print("File error:"+str(err))
        finally:
            self.check_new_file()
            self.save_config()
            self.s.close()
            for file in self.files:
                if not self.p_files[file].closed:
                    # print("close file:", file)
                    self.close_file(self.p_files[file])

    def register_callback(self, func):
        self.callback = func

    def pushlog(self,log,file):
        #print(log)
        str_send = ''
        if g_debug == 1:
            filename = g_tempFolder+"infile0.txt"
            f = open(filename, 'w')
            f.write(log)
            f.close()
        co = 0
        en = 0
        if g_filename_header == "1":
            log  = '['+file+'] '+ log
            if g_debug == 1:
                filename = g_tempFolder+"infileHead.txt"
                f = open(filename, 'w')
                f.write(log)
                f.close()
        if g_compress == "1":
            log = zlib.compress(log, g_compressionLevel)
            co = 1
            if g_debug == 1:
                filename = g_tempFolder+"infileHead_com1.txt"
                f = open(filename, 'w')
                f.write(log)
                f.close()
        if g_encrypt == "1":
            log = encrypt(log)
            en = 1
            if g_debug == 1:
                filename = g_tempFolder+"infileHeadEn2.txt"
                f = open(filename, 'w')
                f.write(log)
                f.close()
        try:
            str_send = log
            data_len = len(str_send)
            send_data = ''
            send_data += chr(0xFF)     #data head
            version = 2
            if co == 1:
                version = version | (1<<7)
            if en == 1:
                version = version | (1<<6)
            send_data += chr(version)     #data version
            send_data += chr(data_len&0xFF) #data lenth low byte
            send_data += chr((data_len>>8)&0xFF)#data lenth middle byte
            #send_data += chr(data_len>>16)
            send_data += chr((data_len>>16)&0xFF)#data lenth high byte (ignore extra data)
            send_data += str_send
            if g_debug == 1:
                filename = g_tempFolder+"infile_send.txt"
                f = open(filename, 'w')
                f.write(send_data)
                f.close()
            self.s.sendall(bytes(send_data))
            res = self.s.recv(2)
            if res != "ok":
                if g_noResponsePrint == 1:
                    from datetime import datetime
                    now = datetime.now() # current date and time
                    time1 = now.strftime("%H:%M:%S")
                    print(file,time1,":no ok from server")
                if g_serverResponse == 1:
                    return False
        except Exception as ex:
            from datetime import datetime
            now = datetime.now() # current date and time
            time1 = now.strftime("%H:%M:%S")
            print("send data error:",file,time1,ex)
            #self.s.connect((self.pushlog_addr, int(self.pushlog_port)))
            if self.socket_idx == 2:
                self.socket_idx = 1
            else:
                self.socket_idx = 2
            self.s_connected = False
            return False
        finally:
            time.sleep(0.01)
        return True

if __name__=='__main__':
    args = sys.argv
    wait_time = 1
    try:
        opts, args = getopt.getopt(args[1:],"vhw:",["version","help","wait="])
    except getopt.GetoptError:
        print('pushlog_v3.py all.conf')
        sys.exit(2)
    t = ReadLog(args[0])
    wait_time = g_waitTime
    for opt, arg in opts:
        if opt in ("-v", "--version"):
            print(VERSION)
            sys.exit(0)
        if opt in ("-h", "--help"):
            print("Usage: pushlog_v3.py all.conf\n-v, --version\t show the version\n-h,  --help\tshow help\n-w,  --wait\tWaiting time after one full run. value by second")
            sys.exit(0)
        if opt in ("-w", "--wait"):
            wait_time = int(arg)
    if len(args)<1:
        print('need one filename parameter')
        exit(1)
    t.register_callback(t.pushlog)
    t.follow(g_interval, wait_time)
