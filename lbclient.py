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
    a_recode = dns.resolver.resolve(domain, 'A') 
    addr_list = []
    for i in a_recode.response.answer:
        for j in i.items:
            addr_list.append(j.address)
    return addr_list

def update_dns():
    global domain_str, token_queue, res, main_thread_end_flag
    while not main_thread_end_flag:
        time.sleep(2)
        token_queue.update_token(get_dns_ip(domain_str))

def get_url(url):
    try:
        global res, req_line, total_int_lock
        key = 'fail'
        skt = socket.socket(ipvx, socket.SOCK_STREAM)
        skt.connect((url, 80))
        skt.send(req_line)
        response_code = int(skt.recv(20).split()[1]) # just http resp code
        skt.close()
        if 200 <= response_code <= 500:
            key = 'success'
    except socket.timeout:
        pass
    except Exception as err:
        raise err
    finally:
        global token_queue
        res[url][key] += 1
        total_int_lock.acquire()
        res['total'][key] += 1
        total_int_lock.release()
        token_queue.produce_token(url)

def main():
    global token_queue, res
    threading.Thread(target=update_dns).start()
    count = 0
    while True:
        count += 1
        if count % 30 == 0:
            print('res: ', res)
        while len(token_queue) == 0:
            time.sleep(0.1)
        if count - res['total']['fail'] > 100:
            break
        threading.Thread(target=get_url, args=(token_queue.get_token(),)).start()
        
    while len(threading.enumerate()) > 2:
        time.sleep(0.1)
    # the last req must be success
    while res['total']['success'] < 100:
        get_url(token_queue.get_token())
    print('res: ', res)

if __name__ == "__main__":
    domain_str = sys.argv[1]
    req_line = "GET / HTTP/1.0\r\nhost: %s\r\n\r\n" % domain_str
    req_line = req_line.encode('utf-8')
    socket.setdefaulttimeout(1)
    ipvx = socket.AF_INET if '.' in domain_str else socket.AF_INET6
    
    iplist = get_dns_ip(domain_str)
    token_queue = TokenDueqe(iplist)
    res = {}
    for ip_str in iplist:
        res[ip_str] = {'success': 0, 'fail': 0}
    total_int_lock = threading.Lock()
    res['total'] = {'success': 0, 'fail': 0}
    
    main_thread_end_flag = False
    print('main() start, token_queue: ', token_queue)
    main()
    main_thread_end_flag = True

