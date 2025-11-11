# API 文档

本文档详细说明所有REST API接口的使用方法。

## 基础信息

- **Base URL**: `http://your-server:5000`
- **认证方式**: API Key（请求头）
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

## 认证

所有需要认证的接口都需要在请求头中添加API密钥：

```
X-API-Key: your_secret_key_here
```

示例：
```bash
curl -H "X-API-Key: your_secret_key" http://localhost:5000/api/health
```

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 失败响应

```json
{
  "success": false,
  "error": "Error message",
  "message": "错误消息"
}
```

## API接口列表

### 系统接口

#### 1. 健康检查

获取服务健康状态。

**请求：**
- **URL**: `/api/health`
- **方法**: `GET`
- **认证**: 不需要

**响应示例：**
```json
{
  "status": "ok",
  "message": "服务运行正常",
  "version": "1.0.0",
  "accounts": ["main", "backup"],
  "timestamp": "2024-01-01 12:00:00"
}
```

**cURL示例：**
```bash
curl http://localhost:5000/api/health
```

---

#### 2. 获取系统信息

获取系统配置和运行信息。

**请求：**
- **URL**: `/api/info`
- **方法**: `GET`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "data": {
    "app_name": "BaiduPan Automation Server",
    "version": "1.0.0",
    "environment": "production",
    "accounts": ["main", "backup"],
    "active_services": ["main"],
    "config": {
      "rate_limit_enabled": true,
      "log_level": "INFO",
      "database_type": "sqlite"
    }
  }
}
```

**cURL示例：**
```bash
curl -H "X-API-Key: your_secret_key" \
  http://localhost:5000/api/info
```

---

#### 3. 获取统计信息

获取任务统计信息。

**请求：**
- **URL**: `/api/stats`
- **方法**: `GET`
- **认证**: 需要
- **查询参数**:
  - `account` (可选): 账户名，不填则返回所有账户

**响应示例：**
```json
{
  "success": true,
  "data": {
    "main": {
      "transfer": {
        "total": 100,
        "completed": 80,
        "failed": 10,
        "pending": 10
      },
      "share": {
        "total": 50,
        "completed": 45,
        "failed": 5,
        "pending": 0
      }
    }
  }
}
```

**cURL示例：**
```bash
# 获取所有账户统计
curl -H "X-API-Key: your_secret_key" \
  http://localhost:5000/api/stats

# 获取指定账户统计
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/stats?account=main"
```

---

### 转存接口

#### 4. 批量导入转存任务

从CSV文件或JSON数据导入多个转存任务。

**请求：**
- **URL**: `/api/transfer/import`
- **方法**: `POST`
- **认证**: 需要
- **内容类型**: `multipart/form-data` 或 `application/json`

**方式1：上传CSV文件**

**请求参数（表单）**:
- `file`: CSV文件
- `account` (可选): 账户名
- `default_target_path` (可选): 默认保存路径，默认为 `/批量转存`

CSV文件格式：
```csv
链接,提取码,保存位置
https://pan.baidu.com/s/xxx,abcd,/目标目录1
https://pan.baidu.com/s/yyy,efgh,/目标目录2
https://pan.baidu.com/s/zzz,,/目标目录3
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -F "file=@links.csv" \
  -F "default_target_path=/批量转存" \
  http://localhost:5000/api/transfer/import
```

**方式2：JSON数据**

**请求体：**
```json
{
  "account": "main",
  "csv_data": [
    {
      "链接": "https://pan.baidu.com/s/xxx",
      "提取码": "abcd",
      "保存位置": "/目标目录1"
    },
    {
      "链接": "https://pan.baidu.com/s/yyy",
      "提取码": "efgh",
      "保存位置": "/目标目录2"
    }
  ],
  "default_target_path": "/批量转存"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "已导入 10 个转存任务",
  "count": 10
}
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_data": [
      {"链接": "https://pan.baidu.com/s/xxx", "提取码": "abcd", "保存位置": "/目标"}
    ]
  }' \
  http://localhost:5000/api/transfer/import
```

---

#### 5. 添加单个转存任务

添加一个转存任务。

**请求：**
- **URL**: `/api/transfer/add`
- **方法**: `POST`
- **认证**: 需要
- **内容类型**: `application/json`

**请求体：**
```json
{
  "account": "main",
  "share_link": "https://pan.baidu.com/s/xxxxx",
  "share_password": "1234",
  "target_path": "/我的文件"
}
```

**请求参数说明**:
- `account` (可选): 账户名
- `share_link` (必需): 分享链接
- `share_password` (可选): 提取码
- `target_path` (可选): 目标路径，默认为 `/批量转存`

**响应示例：**
```json
{
  "success": true,
  "message": "已添加转存任务"
}
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "share_link": "https://pan.baidu.com/s/xxxxx",
    "share_password": "1234",
    "target_path": "/我的文件"
  }' \
  http://localhost:5000/api/transfer/add
```

---

#### 6. 开始转存任务

启动转存任务队列。

**请求：**
- **URL**: `/api/transfer/start`
- **方法**: `POST`
- **认证**: 需要

**请求体：**
```json
{
  "account": "main"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "转存任务已启动"
}
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"account": "main"}' \
  http://localhost:5000/api/transfer/start
```

---

#### 7. 暂停转存任务

暂停正在运行的转存任务。

**请求：**
- **URL**: `/api/transfer/pause`
- **方法**: `POST`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "message": "转存已暂停"
}
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"account": "main"}' \
  http://localhost:5000/api/transfer/pause
```

---

#### 8. 继续转存任务

继续已暂停的转存任务。

**请求：**
- **URL**: `/api/transfer/resume`
- **方法**: `POST`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "message": "转存已继续"
}
```

---

#### 9. 停止转存任务

停止转存任务（无法继续，需重新开始）。

**请求：**
- **URL**: `/api/transfer/stop`
- **方法**: `POST`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "message": "转存已停止"
}
```

---

#### 10. 获取转存状态

获取转存任务的当前状态。

**请求：**
- **URL**: `/api/transfer/status`
- **方法**: `GET`
- **认证**: 需要
- **查询参数**:
  - `account` (可选): 账户名

**响应示例：**
```json
{
  "success": true,
  "data": {
    "is_running": true,
    "is_paused": false,
    "total": 100,
    "completed": 50,
    "failed": 5,
    "pending": 45,
    "current_index": 50
  }
}
```

**cURL示例：**
```bash
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/transfer/status?account=main"
```

---

#### 11. 获取转存队列

获取转存任务队列详情。

**请求：**
- **URL**: `/api/transfer/queue`
- **方法**: `GET`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "share_link": "https://pan.baidu.com/s/xxx",
      "share_password": "abcd",
      "target_path": "/目标",
      "status": "completed",
      "filename": "文件名.zip"
    },
    {
      "id": 2,
      "share_link": "https://pan.baidu.com/s/yyy",
      "status": "pending"
    }
  ]
}
```

---

#### 12. 清空转存队列

清空所有转存任务。

**请求：**
- **URL**: `/api/transfer/clear`
- **方法**: `POST`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "message": "转存队列已清空"
}
```

---

#### 13. 导出转存结果

导出转存结果为JSON或CSV格式。

**请求：**
- **URL**: `/api/transfer/export`
- **方法**: `GET`
- **认证**: 需要
- **查询参数**:
  - `account` (可选): 账户名
  - `format` (可选): 导出格式，`json` 或 `csv`，默认为 `json`

**响应**:
- JSON格式：返回JSON数据
- CSV格式：返回CSV文件下载

**cURL示例：**
```bash
# 导出为JSON
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/transfer/export?format=json"

# 导出为CSV
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/transfer/export?format=csv" \
  -o results.csv
```

---

### 分享接口

#### 14. 从路径添加分享任务

从指定路径的文件/文件夹创建分享任务。

**请求：**
- **URL**: `/api/share/add_from_path`
- **方法**: `POST`
- **认证**: 需要
- **内容类型**: `application/json`

**请求体：**
```json
{
  "account": "main",
  "path": "/要分享的目录",
  "expiry": 7,
  "password": "1234"
}
```

**请求参数说明**:
- `account` (可选): 账户名
- `path` (必需): 文件或文件夹路径
- `expiry` (可选): 有效期，`0`=永久, `1`=1天, `7`=7天, `30`=30天，默认为 `7`
- `password` (可选): 固定提取码，不填则随机生成

**响应示例：**
```json
{
  "success": true,
  "message": "已添加 5 个分享任务",
  "count": 5
}
```

**cURL示例：**
```bash
curl -X POST \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/要分享的目录",
    "expiry": 7,
    "password": "1234"
  }' \
  http://localhost:5000/api/share/add_from_path
```

---

#### 15-20. 分享任务控制接口

与转存任务类似，分享任务也有以下控制接口：

- `/api/share/start` - 开始分享任务
- `/api/share/pause` - 暂停分享任务
- `/api/share/resume` - 继续分享任务
- `/api/share/stop` - 停止分享任务
- `/api/share/status` - 获取分享状态
- `/api/share/queue` - 获取分享队列
- `/api/share/clear` - 清空分享队列
- `/api/share/export` - 导出分享结果

使用方法与转存接口相同。

---

### 文件管理接口

#### 21. 列出文件

列出指定路径的文件和文件夹。

**请求：**
- **URL**: `/api/files/list`
- **方法**: `GET`
- **认证**: 需要
- **查询参数**:
  - `account` (可选): 账户名
  - `path` (必需): 文件路径，默认为 `/`

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "fs_id": "123456789",
      "path": "/文档/文件.pdf",
      "name": "文件.pdf",
      "size": 1024000,
      "isdir": 0,
      "category": 1,
      "server_mtime": 1640000000
    },
    {
      "fs_id": "987654321",
      "path": "/文档/子目录",
      "name": "子目录",
      "isdir": 1
    }
  ]
}
```

**cURL示例：**
```bash
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/files/list?path=/文档"
```

---

#### 22. 搜索文件

搜索文件。

**请求：**
- **URL**: `/api/files/search`
- **方法**: `GET`
- **认证**: 需要
- **查询参数**:
  - `account` (可选): 账户名
  - `keyword` (必需): 搜索关键词
  - `path` (可选): 搜索路径，默认为 `/`

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "fs_id": "123456789",
      "path": "/文档/搜索结果.pdf",
      "name": "搜索结果.pdf",
      "size": 1024000
    }
  ]
}
```

**cURL示例：**
```bash
curl -H "X-API-Key: your_secret_key" \
  "http://localhost:5000/api/files/search?keyword=文档&path=/"
```

---

### 账户管理接口

#### 23. 列出所有账户

列出所有配置的账户。

**请求：**
- **URL**: `/api/accounts`
- **方法**: `GET`
- **认证**: 需要

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "name": "main",
      "is_active": true
    },
    {
      "name": "backup",
      "is_active": false
    }
  ]
}
```

**cURL示例：**
```bash
curl -H "X-API-Key: your_secret_key" \
  http://localhost:5000/api/accounts
```

---

## 错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（API密钥无效或账户登录失败） |
| 404 | 资源不存在 |
| 429 | 请求过于频繁（速率限制） |
| 500 | 服务器内部错误 |

## 速率限制

默认速率限制：每小时100次请求

响应头会包含速率限制信息：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640000000
```

超过速率限制会返回429错误：
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "请求过于频繁，请稍后再试"
}
```

## 完整示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:5000"
API_KEY = "your_secret_key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. 健康检查
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# 2. 添加转存任务
data = {
    "share_link": "https://pan.baidu.com/s/xxxxx",
    "share_password": "1234",
    "target_path": "/我的文件"
}
response = requests.post(f"{BASE_URL}/api/transfer/add", 
                        headers=headers, json=data)
print(response.json())

# 3. 开始转存
response = requests.post(f"{BASE_URL}/api/transfer/start", 
                        headers=headers)
print(response.json())

# 4. 查看状态
response = requests.get(f"{BASE_URL}/api/transfer/status", 
                       headers=headers)
print(response.json())
```

### JavaScript示例

```javascript
const BASE_URL = "http://localhost:5000";
const API_KEY = "your_secret_key";

const headers = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json"
};

// 添加转存任务
fetch(`${BASE_URL}/api/transfer/add`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    share_link: "https://pan.baidu.com/s/xxxxx",
    share_password: "1234",
    target_path: "/我的文件"
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 查看状态
fetch(`${BASE_URL}/api/transfer/status`, {
  method: "GET",
  headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
```

## Swagger UI

访问 `http://your-server:5000/docs` 可以使用交互式API文档（Swagger UI），可以直接在浏览器中测试所有API接口。

## Postman导入

可以使用以下URL导入OpenAPI规范到Postman：
```
http://your-server:5000/apispec.json
```

## 相关文档

- [README.md](README.md) - 项目说明
- [CONFIG.md](CONFIG.md) - 配置说明
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
