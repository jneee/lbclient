# -*- coding: utf-8 -*-
import urllib2
import logging
import logging.handlers
import time
from threading import Timer, Event
import argparse

parser = argparse.ArgumentParser(description='Manual to this elb_client.py')
parser.add_argument('-e','--elb_url', help="elb_url")
parser.add_argument('-m','--member_url', help="member_url")
args = parser.parse_args()
ELB_URL = "http://%s/" % args.elb_url 
MEMBER_URL = "http://" + args.member_url if args.member_url else False
log_cont = {"ELB":{}, "SERVER":{}}
event = Event()

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

@singleton
class elblogging(object):
    def __init__(self):
        cur_time = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
        filename = "client_{}_{}.log".format(args.elb_url.replace(":", "_"), cur_time)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        fh = logging.handlers.RotatingFileHandler(filename, maxBytes=52428800, backupCount=10)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    def getloger(self):
        return self.logger

def get_url(url, req_type):
    Timer(1, get_url, (url, req_type)).start()
    try:
        start_time = time.time()
        ok_flag = False
        if req_type == 'ELB':
            url += str(int(start_time))
            log_cont[req_type]['reqid'] = str(int(start_time))
        response = urllib2.urlopen(url, timeout=0.9)
        if response.headers.get("Server") == "elb":
            log_cont[req_type]["nginx_ip"] = response.headers.get("client_address")
        ok_flag = True
        log_cont[req_type]["response"] = response.code
    except urllib2.HTTPError as err:
        log_cont[req_type]["response"] = err.code
    except Exception as err:
        log_cont[req_type]["other_err"] = str(err)
    finally:
        log_cont[req_type]["cost_time"] = round((time.time() - start_time), 4)
        if req_type == 'SERVER':
            event.set()
        if req_type == 'ELB':
            event.wait()
            if ok_flag:
                logger.info(log_cont)
            else:
                logger.error(log_cont)
            global log_cont 
            log_cont = {"ELB":{}, "SERVER":{}}
            event.clear()

if __name__ == "__main__":
    logger = elblogging().getloger()
    logger.info("start check ELB:{}, server_url:{}".format(ELB_URL, MEMBER_URL))
    Timer(0.1, get_url, (ELB_URL, "ELB")).start()
    if MEMBER_URL:
        Timer(0.1, get_url, (MEMBER_URL, "SERVER")).start()
