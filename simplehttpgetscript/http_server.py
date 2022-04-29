#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import BaseHTTPServer
import SocketServer
import logging
import time
import socket
import argparse
import ssl

parser = argparse.ArgumentParser(description='Manual to this server.py')
parser.add_argument('-6','--ipv6', default=False, help="ipv6 Switch", action='store_true')
parser.add_argument('-s','--https', default=False, help="HTTPS Switch", action='store_true')
parser.add_argument('-p','--port', type=int, help="server port")
args = parser.parse_args()
PORT = args.port
SERVER_INFO = "port {}, ipv6: {}, https: {}".format(PORT, args.ipv6, args.https)
CUR_TIME = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
FILENAME = "server_{}_{}.log".format(PORT, CUR_TIME)

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
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(FILENAME, mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    def getloger(self):
        return self.logger
logger = elblogging().getloger()


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    session_id = 0
    req_id = 0
    def do_GET(self):
        self.send_response(200)
        MyHandler.req_id += 1
        if not self.headers.has_key('cookie'):
            MyHandler.session_id += 1
            cookie = 'session_id={}_{}'.format(PORT, MyHandler.session_id)
            self.send_header('Set-Cookie', cookie)
        self.send_header("client_address", "{}".format(self.client_address))
        self.end_headers()
        self.wfile.write("{}, [{}]\n".format(SERVER_INFO, self.requestline))
        loginfo = {}
        loginfo["req_id"] = MyHandler.req_id
        loginfo["client_addr"] = self.client_address
        loginfo["HTTP_INFO"] = [self.requestline, self.headers.headers]
        logger.info("{}".format(loginfo))


if __name__ == "__main__":
    while True:
        try:
            if args.ipv6:
                SocketServer.TCPServer.address_family=socket.AF_INET6
            httpd = SocketServer.ThreadingTCPServer(("", PORT), MyHandler)
            if args.https:
                httpd.socket = ssl.wrap_socket(httpd.socket, certfile='server.pem', server_side=True)
            logger.info("Start serving on port {}, ipv6: {}, https: {}"\
                        .format(PORT, args.ipv6, args.https))
            print("Start listen on port {}. \nSee {} for more details".format(PORT, FILENAME))
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("stop server success! closing the server...")
            break
        except Exception as e:
            logger.error(e, "> ERROR closing the server...")
        finally:
            httpd.server_close()
