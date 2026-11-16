# 服务器部署与更新指南

本文记录本项目在腾讯云 Ubuntu 服务器上的部署、更新、Nginx 转发、端口排查和智谱 API 排错流程。下次本地改完代码后，可以直接按这份文档操作。

当前约定：

- 服务器项目路径：/opt/IOT_project
- systemd 服务名：iot-ballot
- 应用内部端口：8010
- Nginx 对外端口：80
- 对外访问地址：http://150.109.71.218
- Python 虚拟环境：/opt/IOT_project/.venv
- 运行数据目录：/opt/IOT_project/webapp_data

## 1. 本地更新后上传哪些文件

用 WinSCP 上传到服务器目录：

~~~text
/opt/IOT_project
~~~

通常需要上传：

~~~text
README.md
requirements.txt
run_web_app.py
ballot_recognition/
webapp/
webapp_frontend/
~~~

如果新增或修改了测试，也可以上传：

~~~text
tests/
~~~

不要上传或覆盖：

~~~text
.venv/
webapp_data/
.env
__pycache__/
*.pyc
~~~

原因：

- .venv 是服务器自己的 Linux 虚拟环境，不能用 Windows 本地环境覆盖。
- webapp_data 是服务器上的活动、图片、识别结果、复核记录和模板数据，覆盖会丢数据。
- .env 包含 API Key 和服务器配置，不要用本地文件随意覆盖。

## 2. 更新代码后的标准操作

上传完成后 SSH 登录服务器：

~~~bash
cd /opt/IOT_project
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart iot-ballot
sudo systemctl status iot-ballot
~~~

看到下面状态说明服务正常：

~~~text
Active: active (running)
~~~

查看实时日志：

~~~bash
sudo journalctl -u iot-ballot -f
~~~

查看最近日志：

~~~bash
sudo journalctl -u iot-ballot -n 80 --no-pager
~~~

## 3. .env 环境变量配置

服务器环境变量文件：

~~~bash
/opt/IOT_project/.env
~~~

推荐内容：

~~~env
APP_ENV=production
UVICORN_RELOAD=false
HOST=127.0.0.1
PORT=8010
APP_DATA_DIR=/opt/IOT_project/webapp_data
PUBLIC_BASE_URL=http://150.109.71.218

VISION_MODEL_PROVIDER=zhipu
VISION_MODEL_API_KEY=你的真实智谱API_KEY
VISION_MODEL_NAME=glm-4.6v
VISION_MODEL_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
VISION_MODEL_THINKING=false
VISION_MODEL_TIMEOUT_SECONDS=90
~~~

注意：

- 不要给环境变量值加引号。
- VISION_MODEL_API_KEY 不要留空，不要写中文占位说明，不要多复制空格。
- 修改 .env 后必须重启服务。

~~~bash
sudo systemctl restart iot-ballot
~~~

如果 .env 是从 Windows 上传的，检查是否有 Windows 换行符：

~~~bash
sudo cat -A /opt/IOT_project/.env
~~~

如果行尾出现 ^M$，执行：

~~~bash
sudo sed -i 's/\r$//' /opt/IOT_project/.env
sudo systemctl restart iot-ballot
~~~

## 4. systemd 服务配置

服务文件路径：

~~~bash
/etc/systemd/system/iot-ballot.service
~~~

推荐内容：

~~~ini
[Unit]
Description=IOT Ballot Recognition Web App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/IOT_project
EnvironmentFile=/opt/IOT_project/.env
ExecStart=/opt/IOT_project/.venv/bin/python /opt/IOT_project/run_web_app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
~~~

编辑服务文件：

~~~bash
sudo nano /etc/systemd/system/iot-ballot.service
~~~

修改服务文件后必须执行：

~~~bash
sudo systemctl daemon-reload
sudo systemctl restart iot-ballot
~~~

设置开机自启：

~~~bash
sudo systemctl enable iot-ballot
~~~

排查问题时，如果不希望它一直自动重启，可以临时改成：

~~~ini
Restart=no
~~~

排查结束后建议改回：

~~~ini
Restart=always
RestartSec=5
~~~

## 5. Nginx 反向代理

目标是让用户只访问：

~~~text
http://150.109.71.218
~~~

实际转发到服务器内部应用：

~~~text
http://127.0.0.1:8010
~~~

安装 Nginx：

~~~bash
sudo apt update
sudo apt install -y nginx
~~~

创建配置文件：

~~~bash
sudo nano /etc/nginx/sites-available/iot-ballot
~~~

写入：

~~~nginx
server {
    listen 80;
    server_name 150.109.71.218;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 180s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;
    }
}
~~~

启用配置：

~~~bash
sudo ln -s /etc/nginx/sites-available/iot-ballot /etc/nginx/sites-enabled/iot-ballot
sudo nginx -t
sudo systemctl restart nginx
~~~

如果出现冲突警告：

~~~text
conflicting server name "150.109.71.218" on 0.0.0.0:80, ignored
~~~

查重复配置：

~~~bash
sudo grep -R "server_name 150.109.71.218" -n /etc/nginx/sites-enabled /etc/nginx/conf.d
~~~

如果看到旧配置，例如 sites-enabled/iot_project 和 sites-enabled/iot-ballot 同时存在，保留 iot-ballot，删除旧链接：

~~~bash
sudo rm -f /etc/nginx/sites-enabled/iot_project
sudo nginx -t
sudo systemctl restart nginx
~~~

腾讯云安全组建议：

- 保留 22 端口，用于 SSH。
- 保留 80 端口，用于网页访问。
- 如果已经通过 Nginx 访问，可以不再对外放行 8010。

## 6. 端口被占用怎么办

典型错误：

~~~text
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8000): address already in use
~~~

查看端口占用：

~~~bash
sudo ss -ltnp | grep :8000
sudo ss -ltnp | grep :8010
~~~

查看项目进程：

~~~bash
ps -ef | grep run_web_app.py | grep -v grep
~~~

如果之前手动启动过很多个 python run_web_app.py，先停 systemd，再杀残留：

~~~bash
sudo systemctl stop iot-ballot
sudo pkill -f run_web_app.py
sudo ss -ltnp | grep :8010
sudo systemctl start iot-ballot
sudo systemctl status iot-ballot
~~~

如果只想杀某个 PID：

~~~bash
sudo kill PID
~~~

如果还杀不掉：

~~~bash
sudo kill -9 PID
~~~

正式运行时只用 systemctl 管理服务，不要同时手动运行 python run_web_app.py，否则会抢端口。

## 7. 智谱 401 排查

典型错误：

~~~text
Error code: 401, with error text {"error":{"code":"1000","message":"身份验证失败。"}}
~~~

先确认服务进程是否真的读取到了 .env：

~~~bash
PID=$(sudo systemctl show -p MainPID --value iot-ballot)
echo "PID=$PID"
sudo tr '\0' '\n' < /proc/$PID/environ | grep -E '^(VISION_MODEL_PROVIDER|VISION_MODEL_NAME|VISION_MODEL_API_URL|VISION_MODEL_API_KEY|OPENAI_API_KEY)=' | sed -E 's/(VISION_MODEL_API_KEY=).*/\1***MASKED***/; s/(OPENAI_API_KEY=).*/\1***MASKED***/'
~~~

正常应看到：

~~~text
VISION_MODEL_PROVIDER=zhipu
VISION_MODEL_API_KEY=***MASKED***
VISION_MODEL_NAME=glm-4.6v
VISION_MODEL_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
~~~

检查 key 是否为空，不显示 key 内容：

~~~bash
sudo awk -F= '/^VISION_MODEL_API_KEY=/{print "API_KEY length:", length($2)}' /opt/IOT_project/.env
~~~

如果环境变量正常但还是 401，用 curl 绕开项目代码测试：

~~~bash
source /opt/IOT_project/.env

curl -sS -i https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer $VISION_MODEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$VISION_MODEL_NAME"'",
    "messages": [
      {"role": "user", "content": "你好，请只回复 ok"}
    ]
  }'
~~~

判断：

- curl 也是 401：API Key、账号权限或额度问题，和项目代码无关。
- curl 是 200：Key 可用，再查项目调用方式。
- 返回模型不存在或无权限：修改 VISION_MODEL_NAME 或检查智谱控制台权限。

## 8. 重新部署的安全流程

如果服务器状态很乱，可以重头部署，但先备份。

停止服务并清进程：

~~~bash
sudo systemctl stop iot-ballot
sudo systemctl disable iot-ballot
sudo pkill -f run_web_app.py
~~~

备份项目：

~~~bash
cd /opt
sudo tar -czf IOT_project_backup_$(date +%Y%m%d_%H%M%S).tar.gz IOT_project
~~~

重建目录：

~~~bash
sudo rm -rf /opt/IOT_project
sudo mkdir -p /opt/IOT_project
sudo chown -R ubuntu:ubuntu /opt/IOT_project
~~~

用 WinSCP 重新上传代码后，服务器重新创建虚拟环境：

~~~bash
cd /opt/IOT_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

重新创建 .env 和 systemd 服务后启动：

~~~bash
sudo systemctl daemon-reload
sudo systemctl enable iot-ballot
sudo systemctl start iot-ballot
sudo systemctl status iot-ballot
~~~

## 9. 常用检查命令

应用状态：

~~~bash
sudo systemctl status iot-ballot
~~~

应用日志：

~~~bash
sudo journalctl -u iot-ballot -n 80 --no-pager
~~~

Nginx 状态：

~~~bash
sudo systemctl status nginx
~~~

Nginx 配置检查：

~~~bash
sudo nginx -t
~~~

端口监听：

~~~bash
sudo ss -ltnp | grep -E ':80|:8010|:8000'
~~~

项目进程：

~~~bash
ps -ef | grep run_web_app.py | grep -v grep
~~~

## 10. 日常更新 checklist

每次本地修改代码后：

1. 本地先确认能运行，必要时跑测试。
2. 用 WinSCP 上传代码文件，不覆盖 .env、.venv、webapp_data。
3. 服务器执行 pip install -r requirements.txt。
4. 重启 iot-ballot。
5. 检查 systemctl status。
6. 检查 nginx -t。
7. 浏览器访问 http://150.109.71.218。
8. 上传一张测试投票单，确认识别、人工复核、统计页和导出功能正常。
