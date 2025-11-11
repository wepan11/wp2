"""
Flask API 服务器
提供HTTP API接口，可在Linux服务器上无头运行
"""
import os
import csv
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any
import io
from dotenv import load_dotenv

from core_service import CoreService, appdata_dir

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局服务实例（多账户）
services: Dict[str, CoreService] = {}
current_account: str = None
config: Dict[str, Any] = {}
api_secret_key: str = None
accounts: Dict[str, str] = {}  # 账户名 -> Cookie


def load_config():
    """加载配置文件"""
    global config
    config_path = os.path.join(appdata_dir(), 'settings.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # 默认配置
        config = {
            'throttle': {
                'jitter_ms_min': 500,
                'jitter_ms_max': 1500,
                'ops_per_window': 50,
                'window_sec': 60,
                'window_rest_sec': 20,
                'max_consecutive_failures': 5,
                'pause_sec_on_failure': 60,
                'backoff_factor': 1.5,
                'cooldown_on_errno_-62_sec': 120
            }
        }
    return config


def save_cookie(cookie: str):
    """保存Cookie到文件"""
    cookie_path = os.path.join(appdata_dir(), 'cookie.txt')
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(cookie)


def load_cookie():
    """从文件加载Cookie"""
    cookie_path = os.path.join(appdata_dir(), 'cookie.txt')
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def load_accounts():
    """从环境变量加载所有账户"""
    global accounts, api_secret_key

    # 加载API密钥
    api_secret_key = os.getenv('API_SECRET_KEY')
    if not api_secret_key:
        print("⚠️ 警告：未设置API_SECRET_KEY，建议设置以增强安全性")
        api_secret_key = "default_insecure_key"

    # 加载账户配置
    # 格式：ACCOUNT_{账户名}_COOKIE
    for key, value in os.environ.items():
        if key.startswith('ACCOUNT_') and key.endswith('_COOKIE'):
            # 提取账户名：ACCOUNT_MAIN_COOKIE -> main
            account_name = key[8:-7].lower()  # 去掉 ACCOUNT_ 和 _COOKIE
            accounts[account_name] = value
            print(f"✅ 加载账户: {account_name}")

    if not accounts:
        print("⚠️ 未找到账户配置，请在.env中配置 ACCOUNT_xxx_COOKIE")

    return len(accounts) > 0


def verify_api_key(request_key: str) -> bool:
    """验证API密钥"""
    return request_key == api_secret_key


def get_service(account: str = None) -> CoreService:
    """获取或创建指定账户的服务实例"""
    global services, current_account

    # 如果没有指定账户，使用默认账户
    if not account:
        account = os.getenv('DEFAULT_ACCOUNT', 'main')

    # 如果该账户的服务已存在且已登录，直接返回
    if account in services and services[account].adapter:
        current_account = account
        return services[account]

    # 获取该账户的Cookie
    if account not in accounts:
        return None

    cookie = accounts[account]

    # 创建并登录服务实例
    service = CoreService(cookie, config)
    success, _ = service.login(cookie)

    if success:
        services[account] = service
        current_account = account
        print(f"✅ 账户 '{account}' 登录成功")
        return service
    else:
        print(f"❌ 账户 '{account}' 登录失败")
        return None


def auto_login():
    """自动登录（从保存的Cookie）- 兼容旧版本"""
    global services

    # 如果已经有服务实例，返回True
    if services:
        return True

    # 尝试登录默认账户
    default_account = os.getenv('DEFAULT_ACCOUNT', 'main')
    service = get_service(default_account)

    return service is not None


def require_auth_and_account(f):
    """装饰器：验证API密钥并获取账户服务"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 验证API密钥
        api_key = request.headers.get('X-API-Key')
        if not api_key or not verify_api_key(api_key):
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key'
            }), 401

        # 2. 获取账户名（支持多种方式）
        account = None
        if request.method in ['POST', 'PUT']:
            # 尝试从JSON获取
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json(silent=True) or {}
                account = data.get('account')
            # 尝试从form data获取
            elif request.form:
                account = request.form.get('account')
            # 尝试从query参数获取
            else:
                account = request.args.get('account')
        else:
            # GET/DELETE等方法从query参数获取
            account = request.args.get('account')

        # 3. 获取服务实例
        service = get_service(account)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Account not found or login failed: {account or "default"}'
            }), 401

        # 4. 将服务实例传递给路由函数
        return f(service, *args, **kwargs)

    return decorated_function


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'BaiduPan API服务运行正常',
        'accounts': list(accounts.keys())
    })


@app.route('/api/login', methods=['POST'])
def login():
    """
    登录接口（可选）
    请求体: {"cookie": "BDUSS=..."} 或 {} (使用已保存的cookie)
    """
    global service

    data = request.get_json() or {}

    # 如果已经登录，直接返回成功
    if service and service.adapter:
        return jsonify({
            'success': True,
            'message': '已登录'
        })

    # 获取cookie（优先使用请求中的，否则尝试自动登录）
    cookie = data.get('cookie')

    if cookie:
        # 使用提供的cookie登录
        service = CoreService(cookie, config)
        success, error_msg = service.login(cookie)

        if success:
            # 保存Cookie到文件，下次自动登录
            save_cookie(cookie)
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 401
    else:
        # 没有提供cookie，尝试自动登录
        if auto_login():
            return jsonify({
                'success': True,
                'message': '自动登录成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '请提供cookie参数或配置环境变量BAIDU_COOKIE'
            }), 400


@app.route('/api/transfer/import', methods=['POST'])
@require_auth_and_account
def import_transfer_tasks(service):
    """
    导入转存任务（CSV格式）
    Headers: X-API-Key: your_secret_key
    请求体:
    {
        "account": "main",  # 可选，不填则使用默认账户
        "csv_data": [
            {"链接": "xxx", "提取码": "abc", "保存位置": "/path"},
            ...
        ],
        "default_target_path": "/批量转存"  # 可选
    }
    或者直接上传CSV文件（multipart/form-data）
    """

    # 支持两种方式：JSON和文件上传
    if request.content_type and 'multipart/form-data' in request.content_type:
        # 文件上传方式
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400

        file = request.files['file']
        default_target_path = request.form.get('default_target_path', '/批量转存')

        # 读取CSV
        try:
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            csv_data = list(reader)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'CSV解析失败: {str(e)}'
            }), 400

    else:
        # JSON方式
        data = request.get_json()
        if not data or 'csv_data' not in data:
            return jsonify({
                'success': False,
                'error': '缺少csv_data参数'
            }), 400

        csv_data = data['csv_data']
        default_target_path = data.get('default_target_path', '/批量转存')

    # 添加任务
    count = service.add_transfer_tasks_from_csv(csv_data, default_target_path)

    if count > 0:
        return jsonify({
            'success': True,
            'message': f'已导入 {count} 个转存任务',
            'count': count
        })
    else:
        return jsonify({
            'success': False,
            'error': '没有有效的转存任务'
        }), 400


@app.route('/api/transfer/add', methods=['POST'])
def add_transfer_task():
    """
    添加单个转存任务
    请求体:
    {
        "share_link": "https://pan.baidu.com/s/xxx",
        "share_password": "abc",  # 可选
        "target_path": "/path"     # 可选
    }
    """
    global service

    # 自动登录检查
    if not service:
        if not auto_login():
            return jsonify({
                'success': False,
                'error': '请先登录'
            }), 401

    data = request.get_json()
    if not data or 'share_link' not in data:
        return jsonify({
            'success': False,
            'error': '缺少share_link参数'
        }), 400

    share_link = data['share_link']
    share_password = data.get('share_password', '')
    target_path = data.get('target_path', '/批量转存')

    success = service.add_transfer_task(share_link, share_password, target_path)

    if success:
        return jsonify({
            'success': True,
            'message': '已添加转存任务'
        })
    else:
        return jsonify({
            'success': False,
            'error': '添加任务失败'
        }), 400


@app.route('/api/transfer/start', methods=['POST'])
@require_auth_and_account
def start_transfer(service):
    """
    开始转存任务
    Headers: X-API-Key: your_secret_key
    Body: {"account": "main"}  # 可选
    """
    success, error_msg = service.start_transfer()

    if success:
        return jsonify({
            'success': True,
            'message': '转存任务已启动'
        })
    else:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400


@app.route('/api/transfer/pause', methods=['POST'])
@require_auth_and_account
def pause_transfer(service):
    """暂停转存任务"""
    service.pause_transfer()
    return jsonify({
        'success': True,
        'message': '转存已暂停'
    })


@app.route('/api/transfer/resume', methods=['POST'])
@require_auth_and_account
def resume_transfer(service):
    """继续转存任务"""
    service.resume_transfer()
    return jsonify({
        'success': True,
        'message': '转存已继续'
    })


@app.route('/api/transfer/stop', methods=['POST'])
@require_auth_and_account
def stop_transfer(service):
    """停止转存任务"""
    service.stop_transfer()
    return jsonify({
        'success': True,
        'message': '转存已停止'
    })


@app.route('/api/transfer/status', methods=['GET'])
@require_auth_and_account
def get_transfer_status(service):
    """获取转存状态"""
    status = service.get_transfer_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/share/add_from_path', methods=['POST'])
@require_auth_and_account
def add_share_from_path(service):
    """
    从指定路径添加分享任务
    Headers: X-API-Key: your_secret_key
    请求体: {
        "account": "main",
        "path": "/批量转存",
        "expiry": 0,           # 可选，有效期：0=永久, 1=1天, 7=7天, 30=30天
        "password": "1234"     # 可选，固定提取码，不填则随机生成
    }
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({
            'success': False,
            'error': '缺少path参数'
        }), 400

    path = data['path']
    expiry = data.get('expiry', 7)  # 默认7天
    password = data.get('password', None)  # 默认随机

    count = service.add_share_tasks_from_path(path, expiry=expiry, password=password)

    if count > 0:
        return jsonify({
            'success': True,
            'message': f'已添加 {count} 个分享任务',
            'count': count
        })
    else:
        return jsonify({
            'success': False,
            'error': '没有找到文件或添加失败'
        }), 400


@app.route('/api/share/start', methods=['POST'])
@require_auth_and_account
def start_share(service):
    """
    开始分享任务
    Headers: X-API-Key: your_secret_key
    Body: {"account": "main"}  # 可选
    """
    success, error_msg = service.start_share()

    if success:
        return jsonify({
            'success': True,
            'message': '分享任务已启动'
        })
    else:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400


@app.route('/api/share/status', methods=['GET'])
@require_auth_and_account
def get_share_status(service):
    """
    获取分享状态
    Headers: X-API-Key: your_secret_key
    Query: ?account=main  # 可选
    """
    status = service.get_share_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/share/results', methods=['GET'])
@require_auth_and_account
def get_share_results(service):
    """
    获取分享结果
    Headers: X-API-Key: your_secret_key
    Query: ?account=main  # 可选
    """
    results = service.get_share_results()
    return jsonify({
        'success': True,
        'data': results,
        'count': len(results)
    })


@app.route('/api/share/pause', methods=['POST'])
@require_auth_and_account
def pause_share(service):
    """暂停分享任务"""
    service.pause_share()
    return jsonify({
        'success': True,
        'message': '分享已暂停'
    })


@app.route('/api/share/resume', methods=['POST'])
@require_auth_and_account
def resume_share(service):
    """继续分享任务"""
    service.resume_share()
    return jsonify({
        'success': True,
        'message': '分享已继续'
    })


@app.route('/api/share/stop', methods=['POST'])
@require_auth_and_account
def stop_share(service):
    """停止分享任务"""
    service.stop_share()
    return jsonify({
        'success': True,
        'message': '分享已停止'
    })


@app.route('/api/process_single', methods=['POST'])
@require_auth_and_account
def process_single(service):
    """
    一次性处理单条记录：转存 + 分享
    用于n8n逐条循环处理

    请求体:
    {
        "account": "main",       # 可选
        "title": "文件标题",
        "link": "https://pan.baidu.com/s/xxx",
        "password": "1234",      # 提取码，可选
        "target_path": "/软件",  # 转存目录，可选，默认 /批量转存
        "share_expiry": 0,       # 分享有效期，可选，默认 7
        "share_password": "abcd" # 分享提取码（4位），可选，默认随机
    }

    返回:
    {
        "success": true,
        "data": {
            "title": "文件标题",
            "share_link": "https://pan.baidu.com/s/xxx?pwd=abcd"
        }
    }
    """
    from baidu_pan_adapter import generate_random_password
    from core_service import parse_pwd_from_link, build_link_with_pwd

    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '缺少请求数据'
        }), 400

    # 获取参数
    title = data.get('title', '').strip()
    link = data.get('link', '').strip()
    password = data.get('password', '').strip()
    target_path = data.get('target_path', '/批量转存').strip()
    share_expiry = data.get('share_expiry', 7)
    share_password = data.get('share_password', '').strip()

    # 验证必填参数
    if not link:
        return jsonify({
            'success': False,
            'error': '缺少必填参数: link'
        }), 200  # 返回200，让n8n可以用IF判断

    # 如果链接中有密码，提取出来
    if not password:
        base_link, pwd = parse_pwd_from_link(link)
        if pwd:
            password = pwd
            link = base_link

    # 验证分享密码长度
    if share_password and len(share_password) != 4:
        return jsonify({
            'success': False,
            'error': '分享密码必须是4个字符'
        }), 200  # 返回200，让n8n可以用IF判断

    try:
        # 步骤1: 转存
        service.log(f"🔄 开始处理: {title or link[:30]}")
        service.throttler.tick()
        errno = service.adapter.transfer(link, password, target_path)

        if errno != 0:
            from baidu_pan_adapter import ERROR_CODES
            error_msg = f"转存失败 (错误码: {errno})"
            error_detail = ERROR_CODES.get(errno, '未知错误')
            service.log(f"❌ {error_msg} - {error_detail}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_detail': error_detail,
                'errno': errno
            }), 200  # 返回200，让n8n可以用IF判断

        service.throttler.on_success()
        service.log(f"✅ 转存成功: {target_path}")

        # 步骤2: 获取转存后的文件信息
        items = service.adapter.list_dir(target_path)
        if isinstance(items, int) or not items:
            return jsonify({
                'success': False,
                'error': f'无法列出目录: {target_path}'
            }), 200  # 返回200，让n8n可以用IF判断

        # 找到最新的文件（假设是刚转存的）
        # 或者根据title匹配
        target_item = None
        if title:
            # 尝试通过标题匹配
            for item in items:
                if title in item.get('server_filename', ''):
                    target_item = item
                    break

        if not target_item:
            # 如果没找到，使用最后一个
            target_item = items[-1]

        fs_id = target_item['fs_id']
        filename = target_item['server_filename']
        service.log(f"📄 找到文件: {filename} (fs_id={fs_id})")

        # 步骤3: 分享
        if not share_password:
            share_password = generate_random_password()

        service.throttler.tick()
        result = service.adapter.create_share(fs_id, expiry=share_expiry, password=share_password)

        if isinstance(result, str):
            # 分享成功
            service.throttler.on_success()
            share_link = result

            # 组合完整链接
            complete_link = build_link_with_pwd(share_link, share_password)

            final_title = title if title else filename
            service.log(f"🎉 处理完成: {final_title}")

            return jsonify({
                'success': True,
                'data': {
                    'title': final_title,
                    'share_link': complete_link
                }
            })
        else:
            # 分享失败
            service.throttler.on_failure(result)
            error_msg = f"分享失败 (错误码: {result})"
            service.log(f"❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'errno': result
            }), 200  # 返回200，让n8n可以用IF判断

    except Exception as e:
        service.log(f"❌ 处理异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'处理异常: {str(e)}'
        }), 500


if __name__ == '__main__':
    # 加载.env文件
    load_dotenv()

    # 加载配置
    load_config()

    # 加载所有账户
    print("="*50)
    print("百度网盘API服务 - 多账户版")
    print("="*50)
    load_accounts()

    # 尝试自动登录默认账户
    default_account = os.getenv('DEFAULT_ACCOUNT')
    if default_account:
        print(f"\n正在自动登录默认账户: {default_account}")
        service = get_service(default_account)
        if service:
            print(f"✅ 默认账户 '{default_account}' 已自动登录")
        else:
            print(f"❌ 默认账户 '{default_account}' 登录失败")

    # 启动服务器
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')

    print(f"\n" + "="*50)
    print(f"启动API服务器...")
    print(f"监听地址: {host}:{port}")
    print(f"健康检查: http://{host}:{port}/api/health")
    print(f"API密钥: {api_secret_key[:10]}...{api_secret_key[-4:]}")
    print(f"可用账户: {', '.join(accounts.keys())}")
    print("="*50 + "\n")

    app.run(host=host, port=port, debug=False)
