"""
百度网盘适配器 - 独立可复用版本
====================================

特点：
1. 完全独立，只依赖 requests 库
2. 基于网页行为模拟，不使用百度网盘API
3. 详细的注释说明每一步操作
4. 完整的错误处理和错误码映射
5. 支持：目录遍历、文件分享、链接转存

⚠️ 重要警告：
- 百度网盘官方API是收费的，本代码不使用任何官方API
- 所有操作都是基于模拟用户网页行为实现
- 如未来百度网盘开放免费API，建议修改源码以使用官方API

作者：基于 hxz393/BaiduPanFilesTransfers 改编
版本：1.0.0
许可：MIT License

使用示例：
----------
from baidu_pan_adapter import BaiduPanAdapter

# 初始化
adapter = BaiduPanAdapter()
if not adapter.init(cookie="你的Cookie"):
    print("初始化失败")
    exit()

# 列出目录
files = adapter.list_dir("/我的文档")

# 创建分享
link = adapter.create_share(files[0]['fs_id'], expiry=7, password="1234")

# 转存文件
result = adapter.transfer("https://pan.baidu.com/s/xxxxx", "1234", "/目标目录")
"""

import re
import time
import random
from typing import Union, List, Dict, Any, Tuple, Optional
import requests


# ============================================================================
# 常量定义
# ============================================================================

BASE_URL = 'https://pan.baidu.com'

# 请求头 - 模拟浏览器访问
HEADERS = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

# 错误码映射 - 百度网盘网页操作返回的错误码及其含义
ERROR_CODES = {
    -1: '链接错误，链接失效或缺少提取码',
    -4: '转存失败，无效登录。请退出账号在其他地方的登录',
    -6: '转存失败，请用浏览器无痕模式获取 Cookie 后再试',
    -7: '转存失败，转存文件夹名有非法字符，不能包含 < > | * ? \\ :',
    -8: '转存失败，目录中已有同名文件或文件夹存在',
    -9: '链接错误，提取码错误',
    -10: '转存失败，容量不足',
    -12: '链接错误，提取码错误',
    -62: '转存失败，链接访问次数过多，请手动转存或稍后再试',
    0: '成功',
    2: '转存失败，目标目录不存在',
    4: '转存失败，目录中存在同名文件',
    12: '转存失败，转存文件数超过限制',
    20: '转存失败，容量不足',
    105: '链接错误，所访问的页面不存在',
    404: '转存失败，秒传无效',
}

# 有效期映射 - 将天数转换为网页操作所需的格式
EXPIRY_MAP = {
    1: 1,      # 1天
    7: 7,      # 7天
    30: 30,    # 30天
    0: 0       # 永久
}


# ============================================================================
# 正则表达式 - 用于从 HTML 页面解析必要参数
# ============================================================================

# 从分享页面提取 shareid（分享ID）
SHARE_ID_REGEX = re.compile(r'"shareid":(\d+?),')

# 从分享页面提取 share_uk（分享者的用户ID）
USER_ID_REGEX = re.compile(r'"share_uk":"(\d+?)",')

# 从分享页面提取 fs_id（文件/目录的唯一ID列表）
FS_ID_REGEX = re.compile(r'"fs_id":(\d+?),')

# 从分享页面提取文件名
SERVER_FILENAME_REGEX = re.compile(r'"server_filename":"(.+?)",')

# 从分享页面提取是否为目录的标志（1=目录，0=文件）
ISDIR_REGEX = re.compile(r'"isdir":(\d+?),')


# ============================================================================
# 工具函数
# ============================================================================

def normalize_link(url_code: str) -> str:
    """
    标准化百度网盘分享链接格式
    
    处理步骤：
    1. 将旧格式链接转换为新格式
    2. 统一提取码的分隔方式
    3. 统一使用 https 协议
    4. 规范化空格
    
    参数：
        url_code: 原始链接字符串，可能包含提取码
        
    返回：
        标准格式：链接 + 空格 + 提取码
        
    示例：
        输入: "链接: https://pan.baidu.com/s/1xxx?pwd=1234 提取码: 1234"
        输出: "https://pan.baidu.com/s/1xxx 1234"
    """
    # 1. 升级旧链接格式：share/init?surl= -> s/1
    normalized = url_code.replace("share/init?surl=", "s/1")
    
    # 2. 将 ?pwd= 或 &pwd= 替换为空格，统一提取码的分隔方式
    normalized = re.sub(r'[?&]pwd=', ' ', normalized)
    
    # 3. 将"提取码："或"提取码:"替换为空格
    normalized = re.sub(r'提取码*[：:]', ' ', normalized)
    
    # 4. 统一使用 https 协议，并去除开头的无关文字
    normalized = re.sub(r'^.*?(https?://)', 'https://', normalized)
    
    # 5. 将连续的空格替换为单个空格
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def parse_url_and_code(url_code: str) -> Tuple[str, str]:
    """
    从标准化的链接字符串中分离出 URL 和提取码
    
    参数：
        url_code: 标准格式的链接字符串（链接 + 空格 + 提取码）
        
    返回：
        (url, code) 元组
        - url: 完整的分享链接（截取前47个字符以规范化）
        - code: 4位提取码（从末尾截取）
        
    示例：
        输入: "https://pan.baidu.com/s/1xxx 1234"
        输出: ("https://pan.baidu.com/s/1xxx", "1234")
    """
    # 使用空格分割字符串，最多分割1次
    parts = url_code.split(' ', 1)
    url = parts[0].strip() if parts else ''
    code = parts[1].strip() if len(parts) > 1 else ''
    
    # 标准化 URL 长度（百度网盘分享链接标准长度为47字符）
    # 例如: https://pan.baidu.com/s/1xxxxxxxxxxxxx (25+22=47)
    if len(url) > 47:
        url = url[:47]
    
    # 提取码固定为4位，从末尾截取
    if len(code) >= 4:
        code = code[-4:]
    
    return url, code


def parse_response(response: str) -> Union[List[str], int]:
    """
    解析分享页面的 HTML 内容，提取转存所需的参数
    
    该函数从百度网盘分享页面的源码中提取：
    - shareid: 分享ID
    - share_uk: 分享者的用户ID
    - fs_id_list: 文件/目录ID列表（一个分享可能包含多个文件）
    - server_filename_list: 文件名列表
    - isdir_list: 是否为目录的标志列表
    
    参数：
        response: 分享页面的 HTML 源码
        
    返回：
        成功: [shareid, share_uk, fs_id_list, filename_list, isdir_list]
        失败: -1 (表示无法解析页面，可能链接失效)
        
    注意：
        - shareid 和 share_uk 只有一个值
        - fs_id_list 可能有多个值（一个分享包含多个文件）
        - 所有值都是字符串类型
    """
    # 使用正则表达式从 HTML 中提取各个参数
    shareid_list = SHARE_ID_REGEX.findall(response)
    user_id_list = USER_ID_REGEX.findall(response)
    fs_id_list = FS_ID_REGEX.findall(response)
    server_filename_list = SERVER_FILENAME_REGEX.findall(response)
    isdir_list = ISDIR_REGEX.findall(response)
    
    # 验证所有必需参数都已提取到
    if not all([shareid_list, user_id_list, fs_id_list, server_filename_list, isdir_list]):
        return -1  # 返回错误码，表示解析失败
    
    # 返回参数列表：
    # [0]: shareid (字符串)
    # [1]: share_uk (字符串)
    # [2]: fs_id_list (列表)
    # [3]: server_filename_list (去重后的列表)
    # [4]: isdir_list (列表)
    return [
        shareid_list[0],
        user_id_list[0],
        fs_id_list,
        list(dict.fromkeys(server_filename_list)),  # 去重
        isdir_list
    ]


def update_cookie(bdclnd: str, cookie: str) -> str:
    """
    更新 Cookie 中的 BDCLND 值
    
    BDCLND 是验证提取码后获得的临时令牌，必须添加到 Cookie 中才能访问需要提取码的分享
    
    警告：这是基于网页行为模拟的实现，不是百度网盘官方API
    1. 字段名必须是大写 "BDCLND"（百度网页操作大小写敏感）
    2. 如果已存在 BDCLND，需要先删除旧值
    3. Cookie 格式为: key1=value1; key2=value2; ...
    
    参数：
        bdclnd: 新的 BDCLND 值（从 verify_pass_code 接口获取的 randsk）
        cookie: 当前的 Cookie 字符串
        
    返回：
        更新后的 Cookie 字符串
        
    示例：
        输入: 
            bdclnd = "abc123"
            cookie = "BAIDUID=xxx; STOKEN=yyy"
        输出: 
            "BAIDUID=xxx; STOKEN=yyy; BDCLND=abc123"
    """
    if not cookie:
        return f'BDCLND={bdclnd}'
    
    # 1. 将 Cookie 字符串拆分为字典
    # 先用分号分割，再用等号分割出键值对
    cookie_parts = [part.strip() for part in cookie.split(';') if part.strip()]
    cookies_dict = {}
    
    for part in cookie_parts:
        if '=' in part:
            key, value = part.split('=', 1)
            cookies_dict[key.strip()] = value.strip()
    
    # 2. 更新或添加 BDCLND（必须大写）
    cookies_dict['BDCLND'] = bdclnd
    
    # 3. 重新构建 Cookie 字符串
    updated_cookie = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
    
    return updated_cookie


def generate_random_password() -> str:
    """
    生成随机4位提取码
    
    提取码规则：
    - 4位字符
    - 包含大小写字母和数字
    
    返回：
        4位随机提取码
        
    示例：
        "a8Kp", "3xYz", "M9nB"
    """
    import string
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(4))


# ============================================================================
# 重试装饰器 - 简化版（不依赖 retrying 库）
# ============================================================================

def simple_retry(max_attempts: int = 3, delay_range: Tuple[float, float] = (1.0, 2.0)):
    """
    简单的重试装饰器
    
    参数：
        max_attempts: 最大重试次数
        delay_range: 重试间隔的随机范围（秒）
        
    说明：
        - 发生 requests 相关异常时自动重试
        - 重试间隔为随机值，避免请求过于密集
        - 达到最大次数后抛出异常
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, requests.Timeout, requests.ConnectionError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        # 随机延迟后重试
                        delay = random.uniform(delay_range[0], delay_range[1])
                        time.sleep(delay)
                    else:
                        # 最后一次尝试也失败，抛出异常
                        raise last_exception
                except Exception as e:
                    # 非网络异常直接抛出
                    raise e
            # 理论上不会到达这里，但为了类型安全
            raise last_exception if last_exception else Exception("Unknown error")
        return wrapper
    return decorator


# ============================================================================
# 主适配器类
# ============================================================================

class BaiduPanAdapter:
    """
    百度网盘适配器主类
    
    功能：
    1. 初始化和身份验证
    2. 列出目录内容
    3. 创建分享链接
    4. 转存分享链接
    5. 创建目录
    
    使用流程：
    1. 创建实例
    2. 调用 init() 初始化（传入 Cookie）
    3. 调用其他方法进行操作
    
    注意：
    - 所有网络请求方法都带有自动重试机制
    - 返回错误码时，可以使用 get_error_message() 获取错误描述
    """
    
    def __init__(self, debug: bool = False):
        """
        初始化适配器
        
        参数：
            debug: 是否开启调试模式（打印详细日志）
        """
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.bdstoken = ''  # 百度网盘的访问令牌，所有操作都需要
        self.debug = debug
        
        # 禁用 SSL 警告（百度网盘证书验证可能有问题）
        requests.packages.urllib3.disable_warnings()
        
        if self.debug:
            print("[DEBUG] 适配器初始化完成")
    
    def _log(self, message: str):
        """调试日志输出"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def init(self, cookie: str, trust_env: bool = False) -> bool:
        """
        初始化适配器（必须首先调用）
        
        该方法执行以下操作：
        1. 设置 Cookie 到请求头
        2. 获取 bdstoken（所有操作的前置条件）
        
        参数：
            cookie: 百度网盘的完整 Cookie 字符串
                   如何获取：
                   1. 浏览器打开 https://pan.baidu.com
                   2. 登录账号
                   3. 按 F12 打开开发者工具
                   4. 切换到 Network 标签
                   5. 刷新页面
                   6. 找到任意请求，查看 Request Headers
                   7. 复制完整的 Cookie 值
            
            trust_env: 是否使用系统代理（默认 False）
        
        返回：
            True: 初始化成功
            False: 初始化失败（Cookie 无效或网络问题）
        
        示例：
            adapter = BaiduPanAdapter()
            cookie = "BAIDUID=xxx; STOKEN=yyy; ..."
            if adapter.init(cookie):
                print("初始化成功")
            else:
                print("初始化失败，请检查 Cookie")
        """
        try:
            # 1. 设置系统代理选项
            self.session.trust_env = trust_env
            
            # 2. 设置 Cookie
            self.session.headers['Cookie'] = cookie
            self._log(f"Cookie 已设置: {cookie[:50]}...")
            
            # 3. 获取 bdstoken
            result = self._get_bdstoken()
            
            if isinstance(result, str) and result:
                self.bdstoken = result
                self._log(f"bdstoken 获取成功: {self.bdstoken}")
                return True
            else:
                self._log(f"bdstoken 获取失败，错误码: {result}")
                return False
                
        except Exception as e:
            self._log(f"初始化异常: {e}")
            return False
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def _get_bdstoken(self) -> Union[str, int]:
        """
        获取 bdstoken
        
        bdstoken 是百度网盘网页操作的访问令牌，类似于 access_token
        所有需要身份验证的操作都必须携带此 token
        
        返回：
            成功: bdstoken 字符串
            失败: 错误码（整数）
        
        注意：
            - 该方法会自动重试3次
            - 尝试使用新旧两个 app_id（兼容性更好）
        """
        url = f'{BASE_URL}/api/gettemplatevariable'
        
        # 尝试两个不同的 app_id（新旧版本兼容）
        for app_id in ['38824127', '250528']:
            params = {
                'clienttype': '0',
                'app_id': app_id,
                'web': '1',
                'fields': '["bdstoken","token","uk","isdocuser","servertime"]'
            }
            
            self._log(f"尝试获取 bdstoken，app_id={app_id}")
            
            try:
                r = self.session.get(
                    url=url,
                    params=params,
                    timeout=10,
                    allow_redirects=False,
                    verify=False
                )
                
                if r.status_code != 200:
                    continue
                
                data = r.json()
                self._log(f"bdstoken 响应: {data}")
                
                if data.get('errno') == 0:
                    token = data.get('result', {}).get('bdstoken', '')
                    if token:
                        return token
                else:
                    return data.get('errno', -1)
                    
            except Exception as e:
                self._log(f"获取 bdstoken 异常: {e}")
                continue
        
        return -6  # 所有尝试都失败，返回"Cookie无效"错误码
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def list_dir(self, path: str, page: int = 1, num: int = 1000) -> Union[List[Dict[str, Any]], int]:
        """
        列出指定目录下的文件和子目录
        
        参数：
            path: 目录路径
                  - 根目录: "/"
                  - 子目录: "/我的文档"
                  - 深层目录: "/我的文档/子目录"
            page: 页码（从1开始）
            num: 每页数量（最大1000）
        
        返回：
            成功: 文件/目录列表，每项包含：
                  {
                      'fs_id': 文件/目录ID,
                      'path': 完整路径,
                      'server_filename': 文件名,
                      'isdir': 是否为目录（1=目录, 0=文件）,
                      'size': 文件大小（字节）
                  }
            失败: 错误码（整数）
        
        示例：
            files = adapter.list_dir("/")
            for file in files:
                print(f"{'[DIR]' if file['isdir'] else '[FILE]'} {file['server_filename']}")
        """
        if not self.bdstoken:
            return -6  # 未初始化
        
        # 确保路径以 / 开头
        if not path.startswith('/'):
            path = '/' + path
        
        url = f'{BASE_URL}/api/list'
        params = {
            'order': 'time',      # 按时间排序
            'desc': '1',          # 降序
            'showempty': '0',     # 不显示空目录
            'web': '1',
            'page': str(page),
            'num': str(num),
            'dir': path,
            'bdstoken': self.bdstoken
        }
        
        self._log(f"列出目录: {path}")
        
        r = self.session.get(
            url=url,
            params=params,
            timeout=15,
            allow_redirects=False,
            verify=False
        )
        
        if r.status_code != 200:
            return -1
        
        data = r.json()
        self._log(f"列出目录响应: errno={data.get('errno')}, 文件数={len(data.get('list', []))}")
        
        if data.get('errno') != 0:
            return data.get('errno', -1)
        
        return data.get('list', [])
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def create_dir(self, path: str) -> int:
        """
        创建目录
        
        参数：
            path: 目录路径（必须以 / 开头）
                  例如: "/新建目录"
        
        返回：
            0: 创建成功
            其他: 错误码
        
        注意：
            - 如果目录已存在，会返回错误码
            - 不支持递归创建（父目录必须存在）
        
        示例：
            result = adapter.create_dir("/测试目录")
            if result == 0:
                print("目录创建成功")
            else:
                print(f"创建失败: {adapter.get_error_message(result)}")
        """
        if not self.bdstoken:
            return -6
        
        # 确保路径以 / 开头
        if not path.startswith('/'):
            path = '/' + path
        
        url = f'{BASE_URL}/api/create'
        params = {
            'a': 'commit',
            'bdstoken': self.bdstoken
        }
        data = {
            'path': path,
            'isdir': '1',           # 1表示创建目录
            'block_list': '[]',
        }
        
        self._log(f"创建目录: {path}")
        
        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )
        
        if r.status_code != 200:
            return -1
        
        result = r.json()
        errno = result.get('errno', -1)
        self._log(f"创建目录响应: errno={errno}")
        
        return errno
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def delete(self, fs_id: int) -> int:
        """
        删除文件或目录

        参数：
            fs_id: 文件或目录的 ID（从 list_dir 获取）

        返回：
            0: 删除成功
            其他: 错误码
        """
        if not self.bdstoken:
            return -6

        url = f'{BASE_URL}/api/filemanager'
        params = {
            'opera': 'delete',
            'bdstoken': self.bdstoken
        }
        data = {
            'fid_list': f'[{fs_id}]'
        }

        self._log(f"删除文件/目录: fs_id={fs_id}")

        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        if r.status_code != 200:
            return -1

        result = r.json()
        errno = result.get('errno', -1)
        self._log(f"删除响应: errno={errno}")

        return errno

    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def rename(self, fs_id: int, new_name: str) -> int:
        """
        重命名文件或目录

        参数：
            fs_id: 文件或目录的 ID（从 list_dir 获取）
            new_name: 新的名称

        返回：
            0: 重命名成功
            其他: 错误码
        """
        if not self.bdstoken:
            return -6

        url = f'{BASE_URL}/api/filemanager'
        params = {
            'opera': 'rename',
            'bdstoken': self.bdstoken
        }
        data = {
            'fid_list': f'[{fs_id}]',
            'new_name': new_name
        }

        self._log(f"重命名: fs_id={fs_id}, new_name={new_name}")

        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        if r.status_code != 200:
            return -1

        result = r.json()
        errno = result.get('errno', -1)
        self._log(f"重命名响应: errno={errno}")

        return errno

    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def move(self, fs_id: int, dest_path: str) -> int:
        """
        移动文件或目录

        参数：
            fs_id: 文件或目录的 ID（从 list_dir 获取）
            dest_path: 目标目录路径（必须以 / 开头）

        返回：
            0: 移动成功
            其他: 错误码
        """
        if not self.bdstoken:
            return -6

        # 确保目标路径以 / 开头
        if not dest_path.startswith('/'):
            dest_path = '/' + dest_path

        url = f'{BASE_URL}/api/filemanager'
        params = {
            'opera': 'move',
            'bdstoken': self.bdstoken
        }
        data = {
            'fid_list': f'[{fs_id}]',
            'dest_path': dest_path
        }

        self._log(f"移动: fs_id={fs_id}, dest={dest_path}")

        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )

        if r.status_code != 200:
            return -1

        result = r.json()
        errno = result.get('errno', -1)
        self._log(f"移动响应: errno={errno}")

        return errno

    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def copy(self, fs_id: int, dest_path: str) -> int:
        """
        复制文件或目录

        参数：
            fs_id: 文件或目录的 ID（从 list_dir 获取）
            dest_path: 目标目录路径（必须以 / 开头）

        返回：
            0: 复制成功
            其他: 错误码
        """
        if not self.bdstoken:
            return -6

        # 确保目标路径以 / 开头
        if not dest_path.startswith('/'):
            dest_path = '/' + dest_path

        url = f'{BASE_URL}/api/filemanager'
        params = {
            'opera': 'copy',
            'bdstoken': self.bdstoken
        }
        data = {
            'fid_list': f'[{fs_id}]',
            'dest_path': dest_path
        }

        self._log(f"复制: fs_id={fs_id}, dest={dest_path}")

        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=30,
            allow_redirects=False,
            verify=False
        )

        if r.status_code != 200:
            return -1

        result = r.json()
        errno = result.get('errno', -1)
        self._log(f"复制响应: errno={errno}")

        return errno

    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def create_share(self, fs_id: int, expiry: int = 7, password: str = '') -> Union[str, int]:
        """
        创建分享链接
        
        参数：
            fs_id: 文件或目录的 ID（从 list_dir 获取）
            expiry: 有效期（天）
                    - 1: 1天
                    - 7: 7天（默认）
                    - 30: 30天
                    - 0: 永久
            password: 提取码（4位字符，留空则不设置）
                      - 留空: 无提取码
                      - 指定: 例如 "1234"
                      - 随机: 使用 generate_random_password()
        
        返回：
            成功: 分享链接（字符串）
                  格式: "https://pan.baidu.com/s/xxxxxx"
            失败: 错误码（整数）
        
        示例：
            # 创建7天有效、提取码为1234的分享
            link = adapter.create_share(123456, expiry=7, password="1234")
            if isinstance(link, str):
                print(f"分享链接: {link}")
                print(f"提取码: 1234")
            else:
                print(f"创建失败: {adapter.get_error_message(link)}")
        """
        if not self.bdstoken:
            return -6
        
        # 验证有效期参数
        if expiry not in EXPIRY_MAP:
            expiry = 7  # 默认7天
        
        url = f'{BASE_URL}/share/set'
        params = {
            'channel': 'chunlei',
            'bdstoken': self.bdstoken,
            'clienttype': '0',
            'app_id': '250528',
            'web': '1'
        }
        data = {
            'period': str(expiry),      # 有效期
            'pwd': password or '',       # 提取码（可为空）
            'eflag_disable': 'true',
            'channel_list': '[]',
            'schannel': '4',
            'fid_list': f'[{fs_id}]'    # 文件ID列表
        }
        
        self._log(f"创建分享: fs_id={fs_id}, expiry={expiry}, password={password}")
        
        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=15,
            allow_redirects=False,
            verify=False
        )
        
        if r.status_code != 200:
            return -1
        
        result = r.json()
        self._log(f"创建分享响应: {result}")

        if result.get('errno') != 0:
            errno = result.get('errno', -1)
            # 输出详细错误信息用于调试
            print(f"[分享失败] errno={errno}, 完整响应: {result}, 参数: expiry={expiry}, pwd={password}, fs_id={fs_id}")
            return errno
        
        link = result.get('link', '')
        if not link:
            return -1  # 未获取到链接
        
        return link
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def _verify_pass_code(self, share_url: str, password: str) -> Union[str, int]:
        """
        验证分享链接的提取码
        
        内部方法，由 transfer 调用
        
        参数：
            share_url: 分享链接
            password: 提取码
        
        返回：
            成功: randsk 字符串（临时令牌，需要添加到 Cookie 中）
            失败: 错误码
                  -9 或 -12: 提取码错误
                  其他: 其他错误
        """
        # 提取 surl（链接标识）
        # 格式: https://pan.baidu.com/s/1xxxxxx
        # surl = 链接中第25位到第48位的字符
        if 'pan.baidu.com/s/' in share_url:
            surl = share_url[25:48]
        elif 'pan.baidu.com/e/' in share_url:
            surl = share_url[25:48]
        else:
            return -1  # 不支持的链接格式
        
        url = f'{BASE_URL}/share/verify'
        params = {
            'surl': surl,
            'bdstoken': self.bdstoken,
            't': str(int(time.time() * 1000)),  # 当前时间戳（毫秒）
            'channel': 'chunlei',
            'web': '1',
            'clienttype': '0'
        }
        data = {
            'pwd': password,
            'vcode': '',      # 验证码（通常不需要）
            'vcode_str': ''
        }
        
        self._log(f"验证提取码: surl={surl}, password={password}")
        
        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=10,
            allow_redirects=False,
            verify=False
        )
        
        if r.status_code != 200:
            return -1
        
        result = r.json()
        self._log(f"验证提取码响应: {result}")
        
        errno = result.get('errno', -1)
        if errno != 0:
            return errno  # 返回错误码（-9表示提取码错误）
        
        # 重要：返回的字段名是 'randsk'，不是 'bdclnd'！
        randsk = result.get('randsk', '')
        if not randsk:
            return -1  # 未获取到令牌
        
        return randsk
    
    @simple_retry(max_attempts=3, delay_range=(1.0, 2.0))
    def _get_transfer_params(self, share_url: str) -> str:
        """
        获取分享页面的 HTML 内容
        
        内部方法，由 transfer 调用
        
        参数：
            share_url: 分享链接
        
        返回：
            页面的 HTML 源码
        
        注意：
            - 必须在验证提取码后调用（如果有提取码）
            - Cookie 中必须包含 BDCLND（通过 _verify_pass_code 获取）
        """
        self._log(f"获取分享页面: {share_url}")
        
        r = self.session.get(
            url=share_url,
            timeout=15,
            verify=False,
            allow_redirects=True  # 允许重定向
        )
        
        if r.status_code != 200:
            raise Exception(f"获取分享页面失败: HTTP {r.status_code}")
        
        return r.content.decode("utf-8", errors='ignore')
    
    @simple_retry(max_attempts=5, delay_range=(1.0, 2.0))
    def _do_transfer(self, params_list: List[str], dest_folder: str) -> int:
        """
        执行转存操作
        
        内部方法，由 transfer 调用
        
        参数：
            params_list: 转存参数列表
                        [0]: shareid
                        [1]: share_uk
                        [2]: fs_id_list
            dest_folder: 目标目录
        
        返回：
            0: 转存成功
            其他: 错误码
        """
        # 确保目录路径以 / 开头
        if not dest_folder.startswith('/'):
            dest_folder = '/' + dest_folder
        
        url = f'{BASE_URL}/share/transfer'
        params = {
            'shareid': params_list[0],
            'from': params_list[1],
            'bdstoken': self.bdstoken,
            'channel': 'chunlei',
            'web': '1',
            'clienttype': '0'
        }
        data = {
            # 重要：参数名是 'fsidlist'，不是 'fid_list'！
            'fsidlist': f"[{','.join(params_list[2])}]",
            # 重要：参数名是 'path'，不是 'to'！
            'path': dest_folder
        }
        
        self._log(f"执行转存: dest={dest_folder}, fs_ids={params_list[2]}")
        
        r = self.session.post(
            url=url,
            params=params,
            data=data,
            timeout=30,  # 转存可能较慢，超时时间设长一些
            allow_redirects=False,
            verify=False
        )
        
        if r.status_code != 200:
            return -1
        
        result = r.json()
        errno = result.get('errno', -1)
        
        self._log(f"转存响应: errno={errno}")
        
        return errno
    
    def transfer(self, share_url: str, password: str, dest_folder: str) -> int:
        """
        转存分享链接到指定目录
        
        这是最复杂的操作，完整流程：
        1. 标准化链接格式
        2. 如果有提取码，验证提取码并更新 Cookie
        3. 获取分享页面的 HTML
        4. 从 HTML 中解析转存所需的参数
        5. 执行转存操作
        
        参数：
            share_url: 分享链接（支持多种格式）
                      - https://pan.baidu.com/s/1xxxxx
                      - https://pan.baidu.com/s/1xxxxx?pwd=1234
                      - http://pan.baidu.com/e/1xxxxx
            password: 提取码（4位字符，无提取码则传空字符串）
            dest_folder: 目标目录（会自动创建）
                        - "/" 表示根目录
                        - "/我的文档" 表示根目录下的子目录
        
        返回：
            0: 转存成功
            -1: 链接无效或解析失败
            -9 或 -12: 提取码错误
            -8: 目标目录已有同名文件
            -10 或 20: 容量不足
            其他: 其他错误码（参考 ERROR_CODES）
        
        示例：
            # 转存到根目录
            result = adapter.transfer(
                "https://pan.baidu.com/s/1xxxxx",
                "1234",
                "/"
            )
            
            # 转存到指定目录
            result = adapter.transfer(
                "https://pan.baidu.com/s/1xxxxx",
                "1234",
                "/我的资源/新目录"
            )
            
            if result == 0:
                print("转存成功")
            else:
                print(f"转存失败: {adapter.get_error_message(result)}")
        """
        if not self.bdstoken:
            return -6  # 未初始化
        
        try:
            # 第1步：标准化链接格式
            normalized = normalize_link(f'{share_url} {password}')
            url, pwd = parse_url_and_code(normalized)
            
            self._log(f"开始转存: url={url}, password={pwd}, dest={dest_folder}")
            
            # 第2步：如果有提取码，验证并更新 Cookie
            if pwd:
                randsk = self._verify_pass_code(url, pwd)
                
                # 验证失败（返回错误码）
                if isinstance(randsk, int):
                    return randsk
                
                # 验证成功，更新 Cookie
                # 重要：必须将 randsk 作为 BDCLND 添加到 Cookie 中
                old_cookie = self.session.headers.get('Cookie', '')
                new_cookie = update_cookie(randsk, old_cookie)
                self.session.headers['Cookie'] = new_cookie
                
                self._log(f"提取码验证成功，Cookie 已更新")
            
            # 第3步：获取分享页面内容
            html = self._get_transfer_params(url)
            
            # 第4步：解析页面，提取转存参数
            params = parse_response(html)
            
            if isinstance(params, int):
                # 解析失败（链接可能失效）
                return params
            
            self._log(f"解析成功: shareid={params[0]}, uk={params[1]}, files={len(params[2])}")
            
            # 第5步：执行转存
            result = self._do_transfer(params, dest_folder)
            
            return result
            
        except Exception as e:
            self._log(f"转存异常: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    def close(self):
        """
        关闭会话，释放资源
        
        在程序结束时调用，清理网络连接
        """
        self.session.close()
        self._log("会话已关闭")
    
    @staticmethod
    def get_error_message(errno: int) -> str:
        """
        获取错误码对应的错误信息
        
        参数：
            errno: 错误码
        
        返回：
            错误描述字符串
        
        示例：
            result = adapter.transfer(...)
            if result != 0:
                print(adapter.get_error_message(result))
        """
        return ERROR_CODES.get(errno, f'未知错误: {errno}')


# ============================================================================
# 便捷函数（可选）
# ============================================================================

def create_adapter(cookie: str, debug: bool = False) -> Optional[BaiduPanAdapter]:
    """
    快速创建并初始化适配器
    
    参数：
        cookie: 百度网盘 Cookie
        debug: 是否开启调试模式
    
    返回：
        成功: BaiduPanAdapter 实例
        失败: None
    
    示例：
        adapter = create_adapter("你的Cookie")
        if adapter:
            files = adapter.list_dir("/")
    """
    adapter = BaiduPanAdapter(debug=debug)
    if adapter.init(cookie):
        return adapter
    else:
        return None


# ============================================================================
# 模块信息
# ============================================================================

__version__ = '1.0.0'
__author__ = 'Based on hxz393/BaiduPanFilesTransfers'
__all__ = [
    'BaiduPanAdapter',
    'create_adapter',
    'generate_random_password',
    'normalize_link',
    'ERROR_CODES'
]


if __name__ == '__main__':
    print("""
百度网盘适配器 v1.0.0
===================

这是一个独立的百度网盘操作适配器，支持：
✓ 列出目录
✓ 创建分享
✓ 转存文件
✓ 创建目录

使用示例请参考 test_adapter.py
使用文档请参考 README_ADAPTER.md
    """)
