# 配置说明

本文档详细说明所有配置项的含义和使用方法。

## 配置文件

项目使用 `.env` 文件进行配置，支持以下配置方式：

1. **环境变量**：直接在系统环境变量中设置
2. **.env文件**：在项目根目录创建 `.env` 文件（推荐）
3. **Docker环境**：通过 `docker-compose.yml` 或 `--env-file` 参数传递

## 完整配置项说明

### 基础配置

#### ENV
- **说明**：运行环境
- **可选值**：`development`、`production`、`testing`
- **默认值**：`development`
- **示例**：`ENV=production`

#### APP_NAME
- **说明**：应用名称
- **默认值**：`BaiduPan Automation Server`
- **示例**：`APP_NAME=我的百度网盘服务器`

#### APP_VERSION
- **说明**：应用版本号
- **默认值**：`1.0.0`
- **示例**：`APP_VERSION=1.0.0`

#### DEBUG
- **说明**：调试模式开关
- **可选值**：`True`、`False`
- **默认值**：`False`
- **注意**：生产环境务必设置为 `False`

### 服务器配置

#### HOST
- **说明**：服务监听地址
- **默认值**：`0.0.0.0`
- **示例**：
  - `0.0.0.0` - 监听所有网卡（Docker/生产环境）
  - `127.0.0.1` - 仅本机访问
  - `192.168.1.100` - 监听指定IP

#### PORT
- **说明**：服务监听端口
- **默认值**：`5000`
- **示例**：`PORT=8080`

### API安全配置

#### API_SECRET_KEY
- **说明**：API密钥，用于验证所有API请求
- **默认值**：`default_insecure_key`
- **重要性**：⭐⭐⭐⭐⭐（必须修改）
- **生成方法**：
  ```bash
  # Linux/Mac
  openssl rand -hex 32
  
  # Python
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- **使用方法**：在所有API请求头中添加 `X-API-Key: your_secret_key`

### CORS配置

#### CORS_ORIGINS
- **说明**：允许跨域访问的源
- **默认值**：`*`（允许所有源）
- **格式**：多个域名用逗号分隔
- **示例**：
  - `CORS_ORIGINS=*` - 允许所有源
  - `CORS_ORIGINS=https://example.com` - 仅允许单个域名
  - `CORS_ORIGINS=https://example.com,https://app.example.com` - 允许多个域名

### 速率限制配置

#### RATE_LIMIT_ENABLED
- **说明**：是否启用速率限制
- **可选值**：`True`、`False`
- **默认值**：`True`
- **建议**：生产环境建议启用

#### RATE_LIMIT_DEFAULT
- **说明**：默认速率限制
- **默认值**：`100 per hour`
- **格式**：`数量 per 时间单位`
- **示例**：
  - `100 per hour` - 每小时100次
  - `1000 per day` - 每天1000次
  - `10 per minute` - 每分钟10次

#### RATE_LIMIT_STORAGE_URL
- **说明**：速率限制存储后端
- **默认值**：`memory://`
- **示例**：
  - `memory://` - 内存存储（单机）
  - `redis://localhost:6379` - Redis存储（分布式）

### 日志配置

#### LOG_LEVEL
- **说明**：日志级别
- **可选值**：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`
- **默认值**：`INFO`
- **说明**：
  - `DEBUG` - 调试信息（开发环境）
  - `INFO` - 一般信息（生产环境推荐）
  - `WARNING` - 警告信息
  - `ERROR` - 错误信息
  - `CRITICAL` - 严重错误

#### LOG_FILE_ENABLED
- **说明**：是否启用文件日志
- **可选值**：`True`、`False`
- **默认值**：`True`

#### LOG_FILE_PATH
- **说明**：日志文件路径
- **默认值**：`logs/app.log`
- **示例**：`LOG_FILE_PATH=/var/log/baidu-pan/app.log`

#### LOG_MAX_BYTES
- **说明**：单个日志文件最大大小（字节）
- **默认值**：`10485760`（10MB）
- **示例**：`LOG_MAX_BYTES=20971520`（20MB）

#### LOG_BACKUP_COUNT
- **说明**：保留的日志文件备份数量
- **默认值**：`5`
- **说明**：日志文件会在达到最大大小后自动轮转，保留最近N个备份

#### LOG_FORMAT
- **说明**：日志格式
- **默认值**：`%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s`
- **格式说明**：
  - `%(asctime)s` - 时间
  - `%(name)s` - 日志记录器名称
  - `%(levelname)s` - 日志级别
  - `%(filename)s` - 文件名
  - `%(lineno)d` - 行号
  - `%(message)s` - 日志消息

### 数据库配置

#### DATABASE_TYPE
- **说明**：数据库类型
- **可选值**：`sqlite`、`mysql`、`postgresql`
- **默认值**：`sqlite`
- **说明**：
  - `sqlite` - SQLite数据库（单机，简单）
  - `mysql` - MySQL数据库（生产环境）
  - `postgresql` - PostgreSQL数据库（生产环境）

#### DATABASE_PATH（SQLite）
- **说明**：SQLite数据库文件路径
- **默认值**：`data/baidu_pan.db`
- **示例**：`DATABASE_PATH=/var/lib/baidu-pan/db.sqlite`

#### MySQL配置

```bash
MYSQL_HOST=localhost      # MySQL服务器地址
MYSQL_PORT=3306           # MySQL端口
MYSQL_USER=root           # MySQL用户名
MYSQL_PASSWORD=password   # MySQL密码
MYSQL_DATABASE=baidu_pan  # 数据库名
```

#### PostgreSQL配置

```bash
POSTGRES_HOST=localhost          # PostgreSQL服务器地址
POSTGRES_PORT=5432               # PostgreSQL端口
POSTGRES_USER=postgres           # PostgreSQL用户名
POSTGRES_PASSWORD=password       # PostgreSQL密码
POSTGRES_DATABASE=baidu_pan      # 数据库名
```

#### DATABASE_URL（通用）
- **说明**：数据库连接字符串（可选，优先级高于单独配置）
- **格式**：
  - MySQL: `mysql://user:password@host:port/database`
  - PostgreSQL: `postgresql://user:password@host:port/database`
- **示例**：`DATABASE_URL=mysql://root:password@localhost:3306/baidu_pan`

### 数据目录配置

#### DATA_DIR
- **说明**：数据存储目录
- **默认值**：`data`
- **示例**：`DATA_DIR=/var/lib/baidu-pan/data`

### 节流配置

节流配置用于控制对百度网盘API的请求频率，避免触发限制。

#### THROTTLE_JITTER_MS_MIN
- **说明**：每次请求的最小随机延迟（毫秒）
- **默认值**：`500`
- **建议**：300-1000

#### THROTTLE_JITTER_MS_MAX
- **说明**：每次请求的最大随机延迟（毫秒）
- **默认值**：`1500`
- **建议**：1000-2000

#### THROTTLE_OPS_PER_WINDOW
- **说明**：时间窗口内最大操作数
- **默认值**：`50`
- **说明**：在指定时间窗口内最多执行多少次操作

#### THROTTLE_WINDOW_SEC
- **说明**：时间窗口大小（秒）
- **默认值**：`60`
- **说明**：配合OPS_PER_WINDOW使用，例如：60秒内最多50次操作

#### THROTTLE_WINDOW_REST_SEC
- **说明**：时间窗口用完后的休息时间（秒）
- **默认值**：`20`
- **说明**：达到速率限制后，等待多久再继续

#### THROTTLE_MAX_CONSECUTIVE_FAILURES
- **说明**：最大连续失败次数
- **默认值**：`5`
- **说明**：连续失败N次后触发暂停机制

#### THROTTLE_PAUSE_SEC_ON_FAILURE
- **说明**：失败后的暂停时间（秒）
- **默认值**：`60`
- **说明**：达到最大连续失败次数后，暂停多久

#### THROTTLE_BACKOFF_FACTOR
- **说明**：退避系数
- **默认值**：`1.5`
- **说明**：每次失败后延迟时间乘以此系数

#### THROTTLE_COOLDOWN_ON_ERRNO_62_SEC
- **说明**：遇到错误码-62时的冷却时间（秒）
- **默认值**：`120`
- **说明**：错误码-62表示访问过于频繁，需要较长冷却时间

### 账户配置

#### DEFAULT_ACCOUNT
- **说明**：默认使用的账户名
- **默认值**：`main`
- **说明**：当API请求未指定账户时使用的默认账户

#### ACCOUNT_{名称}_COOKIE
- **说明**：百度网盘账户Cookie
- **格式**：`ACCOUNT_{账户名}_COOKIE=BDUSS=xxx`
- **示例**：
  ```bash
  ACCOUNT_MAIN_COOKIE=BDUSS=xxxxxxxxxxxxxxxxxx
  ACCOUNT_BACKUP_COOKIE=BDUSS=yyyyyyyyyyyyyyyyyy
  ACCOUNT_TEST_COOKIE=BDUSS=zzzzzzzzzzzzzzzzzz
  ```
- **获取方法**：
  1. 浏览器登录百度网盘
  2. 打开开发者工具（F12）
  3. 切换到"网络"标签
  4. 刷新页面
  5. 找到任意请求，查看请求头中的Cookie
  6. 复制BDUSS部分

### 工作线程配置

#### MAX_TRANSFER_WORKERS
- **说明**：最大转存工作线程数
- **默认值**：`1`
- **建议**：1-2（过多可能触发限制）

#### MAX_SHARE_WORKERS
- **说明**：最大分享工作线程数
- **默认值**：`1`
- **建议**：1-2

### 性能监控配置

#### ENABLE_PERFORMANCE_MONITORING
- **说明**：是否启用性能监控
- **可选值**：`True`、`False`
- **默认值**：`False`
- **说明**：启用后会记录API响应时间等性能指标

## 配置示例

### 开发环境配置

```bash
ENV=development
DEBUG=True
HOST=127.0.0.1
PORT=5000
LOG_LEVEL=DEBUG

API_SECRET_KEY=dev_secret_key_for_testing

DATABASE_TYPE=sqlite
DATABASE_PATH=data/dev.db

ACCOUNT_MAIN_COOKIE=BDUSS=your_cookie_here
```

### 生产环境配置

```bash
ENV=production
DEBUG=False
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO

# 使用强密钥
API_SECRET_KEY=production_strong_secret_key_generated_randomly

# 使用MySQL数据库
DATABASE_TYPE=mysql
MYSQL_HOST=mysql.example.com
MYSQL_PORT=3306
MYSQL_USER=baidu_pan
MYSQL_PASSWORD=strong_password
MYSQL_DATABASE=baidu_pan

# 启用速率限制（使用Redis）
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=1000 per day
RATE_LIMIT_STORAGE_URL=redis://redis.example.com:6379

# 配置多个账户
ACCOUNT_MAIN_COOKIE=BDUSS=xxx
ACCOUNT_BACKUP_COOKIE=BDUSS=yyy

# 节流配置（较保守）
THROTTLE_OPS_PER_WINDOW=30
THROTTLE_WINDOW_SEC=60
```

### Docker环境配置

```bash
ENV=production
HOST=0.0.0.0
PORT=5000

API_SECRET_KEY=docker_secret_key

# 使用容器内路径
DATABASE_TYPE=sqlite
DATABASE_PATH=/app/data/baidu_pan.db
LOG_FILE_PATH=/app/logs/app.log

ACCOUNT_MAIN_COOKIE=BDUSS=xxx
```

## 配置优先级

1. 命令行环境变量（最高）
2. .env文件
3. 默认值（最低）

例如：
```bash
# .env文件中设置
PORT=5000

# 命令行覆盖
PORT=8080 python3 server.py  # 实际使用8080
```

## 配置验证

启动服务时，系统会自动验证配置：

```bash
python3 server.py
```

如果配置有问题，会在启动时提示错误信息。

## 配置热更新

大部分配置需要重启服务才能生效。如果使用Docker：

```bash
# 修改.env文件后
docker-compose restart
```

## 安全建议

1. **API_SECRET_KEY**：使用强随机密钥，至少32字符
2. **Cookie**：定期更新，不要泄露
3. **数据库密码**：使用强密码
4. **文件权限**：.env文件权限设置为600
   ```bash
   chmod 600 .env
   ```
5. **备份配置**：定期备份.env文件（注意安全保存）

## 故障排查

### 配置未生效

1. 检查环境变量名是否正确
2. 检查.env文件格式（不要有多余空格）
3. 检查是否重启了服务
4. 检查日志输出

### Cookie失效

Cookie会定期失效，需要重新获取并更新配置。

### 数据库连接失败

1. 检查数据库服务是否运行
2. 检查连接参数（主机、端口、用户名、密码）
3. 检查网络连接
4. 检查数据库用户权限

## 进阶配置

### 使用环境变量文件的不同环境

```bash
# 开发环境
cp .env.development .env

# 生产环境
cp .env.production .env

# 测试环境
cp .env.testing .env
```

### 使用Docker Secrets

在docker-compose.yml中：

```yaml
version: '3.8'

services:
  app:
    environment:
      API_SECRET_KEY_FILE: /run/secrets/api_key
    secrets:
      - api_key

secrets:
  api_key:
    file: ./secrets/api_key.txt
```

## 相关文档

- [README.md](README.md) - 项目说明
- [API.md](API.md) - API文档
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
