## 1. 更新日志

* 2020-9-28 client请求url增加/时间戳，以区分出nginx节点对应的访问日志
* 2020-9-4 client增加回显经过的nginxIP信息，周期改为1s
* 2020-9-3 增加双线程请求server，保证同一时间server可用。 ~~（此功能与server耦合）~~ 改为手动输入（-m）
* 支持ipv6流量预置，查看源地址等；
* Server 增加日志，区分HTTP健康检查和真实请求（tcp健康检查暂无记录），可直接查看七层源地址；
* Client HTTP 502返回码时检出为健康检查不在线； 404 检出为member错误；
* server 支持测试“应用程序会话保持”，可直接在浏览器中测试；~[会话保持测试方法]()~
* 日志时间精度提升 s->ms，记录每次请求的消耗时间
* 支持HTTPS服务，可选参数 [-s]


## 2. 使用方法
### 2.1 流量预置
* http_server71.py : 起服务端，-6 为可选项，即起ipv6服务，加-6则**ipv4 ipv6都能访问**；-s则起HTTPS服务，需配置证书`server.pem`
* elbtimeout71.py : 客户端打流脚本，-e elb地址:端口 -m 对应的member地址:端口。建议-m总是填写member的EIP:port，这样流量一定是跨节点的，和ELB流量一致

使用方法：
```bash
nohup Python http_server.py [-6] [-s] -p port &

nohup Python elb_timeout.py -e ip:port -m ip:port &
#-e elb地址:端口 -m 对应的member地址:端口
tail -f client_xxx_xxx.log #查看流量是否正常
```

![](./z_howtouse.png)

### 2.2 查看日志
日志文件为启动目录下的 server/client_[port]_[time].log 。

#### 2.2.1 server 端日志

* 如果是通过elb的请求，可以直接在server日志上看到源地址，即headers中`X-Forwarded-For`字段。测试7层透传时候，可以用`tail -f server_xxx.log | grep X-Forwarded-For`查看;
* headers 中User-agent为`elb-healthcheck`的为elb的健康检查（仅ELBv3），为`ELB test`的是elb_timeout.py脚本发出的;
* 其他关键词...

#### 2.2.2 client日志

日志前面的时间戳含义是截止时间（如果有timeout, 则是2秒前的请求失败了）。client 日志有如下类型
* INFO: response 200 的请求
* ERROR： 中断
  1. 健康检查不在线（有member，但对应的端口没起服务），关键词 502;
  2. member错误（比如没添加后端），关键词 404;
  3. 其他


## 3. 其他
### 3.1 会话保持测试参考
当前怕影响server打流性能把http_server.py cookie注释掉了，需要就删掉注释
1. 在console上面设置应用程序会话保持 cookie名称：session_id
2. curl ELB_ip:port -i 获得session_id
3. curl ELB_ip:port --cookie 'session_id=xxx' --header 'Connection=keep-alive'
4. 或浏览器刷新访问

### 3.2 生成HTTPS证书
```
# 生成rsa密钥
openssl genrsa -des3 -out server.key 1024
# 去除掉密钥文件保护密码
openssl rsa -in server.key -out server.key
# 生成ca对应的csr文件
openssl req -new -key server.key -out server.csr
# 自签名
openssl x509 -req -days 1024 -in server.csr -signkey server.key -out server.crt
cat server.crt server.key > server.pem
```
