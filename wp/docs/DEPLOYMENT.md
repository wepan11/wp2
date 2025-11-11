# 部署指南

本文档提供详细的部署指南，包括各种部署方式和环境配置。

## 目录

- [系统要求](#系统要求)
- [部署方式](#部署方式)
  - [方式1: Docker部署（推荐）](#方式1-docker部署推荐)
  - [方式2: 直接部署](#方式2-直接部署)
  - [方式3: Systemd服务](#方式3-systemd服务)
- [生产环境优化](#生产环境优化)
- [安全加固](#安全加固)
- [监控和维护](#监控和维护)
- [故障排查](#故障排查)
- [升级和回滚](#升级和回滚)

## 系统要求

### 最低要求

- **CPU**: 1核
- **内存**: 512MB
- **存储**: 1GB（不包括数据）
- **操作系统**: Linux/Windows/MacOS
- **Python**: 3.8+

### 推荐配置

- **CPU**: 2核
- **内存**: 2GB
- **存储**: 10GB SSD
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **Python**: 3.11+

## 部署方式

### 方式1: Docker部署（推荐）

Docker部署是最简单、最可靠的部署方式，适合所有环境。

#### 1.1 安装Docker

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 安装Docker Compose
sudo apt-get install docker-compose

# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录以使组更改生效
```

**CentOS/RHEL:**
```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 1.2 准备项目文件

```bash
# 克隆或上传项目代码
cd /opt
git clone <your-repo-url> baidu-pan-server
# 或者上传zip包并解压

cd baidu-pan-server/wp
```

#### 1.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env

# 必须配置的参数：
# - API_SECRET_KEY (生成强密钥)
# - ACCOUNT_MAIN_COOKIE (百度网盘Cookie)
```

生成强密钥：
```bash
openssl rand -hex 32
```

#### 1.4 启动服务

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查状态
docker-compose ps
```

#### 1.5 验证部署

```bash
# 健康检查
curl http://localhost:5000/api/health

# 应该返回：
# {"status":"ok","message":"服务运行正常",...}
```

#### 1.6 Docker命令参考

```bash
# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 更新并重启
docker-compose pull
docker-compose up -d

# 进入容器
docker-compose exec baidu-pan-server bash
```

---

### 方式2: 直接部署

适合开发环境或不使用Docker的生产环境。

#### 2.1 安装Python

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip
```

#### 2.2 准备项目

```bash
# 进入项目目录
cd /opt/baidu-pan-server/wp

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

#### 2.3 配置环境

```bash
# 复制并编辑配置
cp .env.example .env
nano .env

# 初始化数据库
python3 init_db.py
```

#### 2.4 启动服务

**开发模式：**
```bash
python3 server.py
```

**生产模式（Gunicorn）：**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --daemon \
  server:app
```

**使用启动脚本：**
```bash
chmod +x start.sh
./start.sh
```

---

### 方式3: Systemd服务

适合Linux生产环境，实现开机自启和服务管理。

#### 3.1 准备部署目录

```bash
# 创建部署目录
sudo mkdir -p /opt/baidu-pan-server
sudo chown $USER:$USER /opt/baidu-pan-server

# 复制项目文件
cp -r wp/* /opt/baidu-pan-server/

# 创建虚拟环境
cd /opt/baidu-pan-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env

# 初始化数据库
python3 init_db.py
```

#### 3.2 创建Systemd服务

```bash
# 编辑服务文件（如果需要修改配置）
nano baidu-pan-server.service

# 复制服务文件
sudo cp baidu-pan-server.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable baidu-pan-server

# 启动服务
sudo systemctl start baidu-pan-server

# 检查状态
sudo systemctl status baidu-pan-server
```

#### 3.3 服务管理命令

```bash
# 启动服务
sudo systemctl start baidu-pan-server

# 停止服务
sudo systemctl stop baidu-pan-server

# 重启服务
sudo systemctl restart baidu-pan-server

# 查看状态
sudo systemctl status baidu-pan-server

# 查看日志
sudo journalctl -u baidu-pan-server -f

# 禁用开机自启
sudo systemctl disable baidu-pan-server
```

---

## 生产环境优化

### 使用Nginx反向代理

#### 安装Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 配置Nginx

创建 `/etc/nginx/sites-available/baidu-pan-server`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日志
    access_log /var/log/nginx/baidu-pan-access.log;
    error_log /var/log/nginx/baidu-pan-error.log;

    # 客户端最大请求体大小（用于文件上传）
    client_max_body_size 100M;

    # 代理设置
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # API文档路径
    location /docs {
        proxy_pass http://127.0.0.1:5000/docs;
        proxy_set_header Host $host;
    }

    # 静态文件缓存
    location /static {
        proxy_pass http://127.0.0.1:5000/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/baidu-pan-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 使用MySQL/PostgreSQL

对于生产环境，推荐使用MySQL或PostgreSQL替代SQLite。

#### MySQL配置

```bash
# 安装MySQL
sudo apt-get install mysql-server

# 创建数据库和用户
sudo mysql -e "
CREATE DATABASE baidu_pan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'baidu_pan'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON baidu_pan.* TO 'baidu_pan'@'localhost';
FLUSH PRIVILEGES;
"

# 安装Python驱动
source venv/bin/activate
pip install pymysql

# 修改.env配置
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=baidu_pan
MYSQL_PASSWORD=strong_password
MYSQL_DATABASE=baidu_pan

# 初始化数据库
python3 init_db.py
```

#### PostgreSQL配置

```bash
# 安装PostgreSQL
sudo apt-get install postgresql

# 创建数据库和用户
sudo -u postgres psql -c "
CREATE DATABASE baidu_pan;
CREATE USER baidu_pan WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE baidu_pan TO baidu_pan;
"

# 安装Python驱动
pip install psycopg2-binary

# 修改.env配置
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=baidu_pan
POSTGRES_PASSWORD=strong_password
POSTGRES_DATABASE=baidu_pan

# 初始化数据库
python3 init_db.py
```

### 使用Redis进行速率限制

```bash
# 安装Redis
sudo apt-get install redis-server

# 修改.env配置
RATE_LIMIT_STORAGE_URL=redis://localhost:6379

# 重启服务
sudo systemctl restart baidu-pan-server
```

---

## 安全加固

### 1. 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. 使用强密钥

```bash
# 生成强API密钥
openssl rand -hex 32

# 在.env中配置
API_SECRET_KEY=<生成的密钥>
```

### 3. 限制IP访问

在Nginx配置中添加：
```nginx
location / {
    # 只允许特定IP访问
    allow 192.168.1.0/24;
    deny all;
    
    proxy_pass http://127.0.0.1:5000;
    ...
}
```

### 4. 文件权限

```bash
# 设置正确的文件权限
chmod 600 .env
chmod 700 data/
chmod 700 logs/

# 设置所有者
sudo chown -R www-data:www-data /opt/baidu-pan-server
```

### 5. 定期更新

```bash
# 更新系统包
sudo apt-get update && sudo apt-get upgrade

# 更新Python依赖
pip install --upgrade -r requirements.txt
```

---

## 监控和维护

### 日志管理

```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# 查看systemd日志
sudo journalctl -u baidu-pan-server -f

# 日志轮转（logrotate）
sudo nano /etc/logrotate.d/baidu-pan-server
```

logrotate配置：
```
/opt/baidu-pan-server/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### 数据备份

```bash
# SQLite备份
cp data/baidu_pan.db data/baidu_pan.db.backup.$(date +%Y%m%d)

# MySQL备份
mysqldump -u baidu_pan -p baidu_pan > backup_$(date +%Y%m%d).sql

# PostgreSQL备份
pg_dump -U baidu_pan baidu_pan > backup_$(date +%Y%m%d).sql

# 定期备份脚本
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/baidu-pan-server/data/baidu_pan.db $BACKUP_DIR/db_$DATE.db

# 备份配置
cp /opt/baidu-pan-server/.env $BACKUP_DIR/env_$DATE

# 删除7天前的备份
find $BACKUP_DIR -name "db_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "env_*" -mtime +7 -delete
EOF

chmod +x /opt/backup.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup.sh") | crontab -
```

### 健康检查

```bash
# 创建健康检查脚本
cat > /opt/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:5000/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    # 可以添加告警逻辑
    # 例如：发送邮件或重启服务
    exit 1
fi
EOF

chmod +x /opt/health_check.sh

# 添加到crontab（每5分钟检查一次）
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/health_check.sh") | crontab -
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查日志
sudo journalctl -u baidu-pan-server -n 100

# 检查端口占用
sudo netstat -tlnp | grep 5000
sudo lsof -i :5000

# 检查Python进程
ps aux | grep python

# 检查配置文件
python3 -c "from config import get_config; print(get_config().__dict__)"
```

#### 2. Cookie失效

```bash
# 重新获取Cookie并更新.env
nano .env

# 重启服务
sudo systemctl restart baidu-pan-server
```

#### 3. 数据库连接失败

```bash
# 测试数据库连接
python3 -c "import sqlite3; conn = sqlite3.connect('data/baidu_pan.db'); print('OK')"

# MySQL
python3 -c "import pymysql; conn = pymysql.connect(host='localhost', user='baidu_pan', password='xxx', database='baidu_pan'); print('OK')"

# 检查数据库服务
sudo systemctl status mysql
sudo systemctl status postgresql
```

#### 4. 内存不足

```bash
# 查看内存使用
free -h

# 查看进程内存
ps aux --sort=-%mem | head -10

# 减少worker数量
# 在.env中设置
MAX_TRANSFER_WORKERS=1
MAX_SHARE_WORKERS=1
```

#### 5. 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 查找大文件
du -sh /* | sort -rh | head -10

# 清理日志
rm -f logs/*.log.*
```

---

## 升级和回滚

### 升级步骤

```bash
# 1. 备份当前版本
cd /opt/baidu-pan-server
tar -czf ../backup_$(date +%Y%m%d).tar.gz .

# 2. 停止服务
sudo systemctl stop baidu-pan-server

# 3. 拉取新代码
git pull

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 5. 运行数据库迁移（如果有）
python3 init_db.py

# 6. 启动服务
sudo systemctl start baidu-pan-server

# 7. 验证
curl http://localhost:5000/api/health

# 8. 查看日志
sudo journalctl -u baidu-pan-server -f
```

### Docker升级

```bash
# 1. 备份数据
docker-compose exec baidu-pan-server tar -czf /tmp/backup.tar.gz /app/data

# 2. 拉取新镜像
docker-compose pull

# 3. 重新构建并启动
docker-compose up -d --build

# 4. 验证
docker-compose logs -f
```

### 回滚

```bash
# 停止服务
sudo systemctl stop baidu-pan-server

# 恢复备份
cd /opt
tar -xzf backup_20240101.tar.gz -C baidu-pan-server/

# 启动服务
sudo systemctl start baidu-pan-server
```

---

## 性能优化

### 1. 增加Worker数量

```bash
# Gunicorn
gunicorn -w 8 -b 0.0.0.0:5000 server:app

# 或在启动脚本中设置
export WORKERS=8
```

### 2. 启用HTTP/2

在Nginx配置中：
```nginx
listen 443 ssl http2;
```

### 3. 启用Gzip压缩

在Nginx配置中：
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

### 4. 优化数据库

```bash
# SQLite优化
# 在init_db.py中添加索引

# MySQL优化
# my.cnf配置
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 200
```

---

## 相关文档

- [README.md](README.md) - 项目说明
- [CONFIG.md](CONFIG.md) - 配置说明
- [API.md](API.md) - API文档
