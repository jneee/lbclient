# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 12:06:16 2021

@author: Administrator
"""
import collections
import dns.resolver
import socket
import sys
import time
import threading
import pdb


class TokenDueqe:
    def __init__(self, token_list):
        self.deque = collections.deque(token_list)
        self.helpset = set(token_list)
    
    def get_token(self):
        return self.deque.popleft()
        
    def produce_token(self, token):
        if token in self.helpset:
            self.deque.append(token)
        
    def update_token(self, token_list):
        newset = set(token_list)
        self.deque.extend(newset - self.helpset)
        self.helpset = newset

    def __len__(self):
        return len(self.deque)
    
    def __str__(self):
        return str(self.deque)


def get_dns_ip(domain):
    a_recode = dns.resolver.resolve(domain, 'A') # 查询类型为A记录
    addr_list = []
    for i in a_recode.response.answer:
        for j in i.items:
            addr_list.append(j.address)
    # print('get_dns_ip() addr_list: ', addr_list)
    return addr_list

def update_dns():
    global domain_str, token_queue
    while True:
        time.sleep(5)
        token_queue.update_token(get_dns_ip(domain_str))

def get_url(url):
    try:
        global res, req_line
        skt = socket.socket(ipvx, socket.SOCK_STREAM)
        skt.connect((url, 80))
        skt.send(req_line)
        response_code = int(skt.recv(20).split()[1]) # just http resp code
        skt.close()
        if response_code >= 500:
            res[url].setdefault('fail', 0)
            res[url]['fail'] += 1
        elif 200 <= response_code < 500:
            res[url].setdefault('success', 0)
            res[url]['success'] += 1
    except Exception as err:
        raise err
        res[url].setdefault('fail', 0)
        res[url]['fail'] += 1
    finally:
        global token_queue
        token_queue.produce_token(url)
        

def main():
    global token_queue, res
    threading.Thread(target=update_dns).start()
    count = 0
    pdb.set_trace()
    while True:
        count += 1
        if count % 10 == 0:
            print ('res: ', res)
            print ('token_queue: ', token_queue)
            if count == 100:
                break
        while len(token_queue) == 0:
            time.sleep(0.1)
        threading.Thread(target=get_url, args=(token_queue.get_token(),)).start()

if __name__ == "__main__":
    domain_str = sys.argv[1]
    req_line = "GET / HTTP/1.0\r\nhost: %s\r\n\r\n" % domain_str
    req_line = req_line.encode('utf-8')
    socket.setdefaulttimeout(1)
    ipvx = socket.AF_INET if '.' in domain_str else socket.AF_INET6
    
    iplist = get_dns_ip(domain_str)
    token_queue = TokenDueqe(iplist)
    
    res = collections.defaultdict(dict)
    print('main() start, token_queue: ', token_queue)
    main()

