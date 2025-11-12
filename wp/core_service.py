"""
核心业务服务类
提供转存和分享的核心功能
"""
import os
import time
import random
import threading
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Callable

from baidu_pan_adapter import BaiduPanAdapter, ERROR_CODES, generate_random_password


# 定义应该直接跳过的错误码（不重试，直接标记为跳过）
SKIP_ON_ERRORS = {
    -1,   # 链接错误，链接失效或缺少提取码
    -62,  # 转存失败，链接访问次数过多（超过限制）
    -4,   # 转存失败，无效登录
    -8,   # 转存失败，目录中已有同名文件
    -10,  # 转存失败，容量不足
    2,    # 分享失败，参数错误
}


# -------------------------------
# 工具函数
# -------------------------------

def appdata_dir() -> str:
    """获取应用数据目录"""
    base = os.getenv('APPDATA') or os.path.expanduser('~')
    d = os.path.join(base, 'BaiduPanTool')
    os.makedirs(d, exist_ok=True)
    return d


def safe_int(v, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(v)
    except Exception:
        return default


def now_str() -> str:
    """返回当前时间字符串"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def parse_pwd_from_link(link: str) -> Tuple[str, str]:
    """
    从链接中提取 ?pwd= 参数，返回 (base_url, pwd)
    - 若包含其他参数，保留其余参数顺序，仅移除 pwd 参数
    - 如果没有 pwd，则返回 (link, '')
    """
    try:
        if '?pwd=' in link or '&pwd=' in link:
            if '?' in link:
                base, query = link.split('?', 1)
                params = query.split('&') if query else []
                new_params = []
                code = ''
                for p in params:
                    if p.startswith('pwd='):
                        code = p[4:]
                    elif p:
                        new_params.append(p)
                new_query = '&'.join(new_params)
                new_link = base
                if new_query:
                    new_link = f"{base}?{new_query}"
                return new_link, code
        return link, ''
    except Exception:
        return link, ''


def build_link_with_pwd(base_url: str, pwd: str) -> str:
    """
    组合链接和密码
    - 如果链接已有?pwd=参数，直接返回
    - 如果有密码，添加?pwd=参数
    - 如果没有密码，返回原链接
    """
    if not pwd:
        return base_url

    # 检查是否已有pwd参数
    if '?pwd=' in base_url or '&pwd=' in base_url:
        return base_url

    # 如果已有其他查询参数，用&连接，否则用?
    sep = '&' if '?' in base_url else '?'
    return f"{base_url}{sep}pwd={pwd}"


# -------------------------------
# 节流策略
# -------------------------------

class Throttler:
    """API调用节流控制器"""
    def __init__(self, cfg: Dict[str, Any]):
        t = cfg.get('throttle', {})
        self.jitter_min = safe_int(t.get('jitter_ms_min', 500))
        self.jitter_max = safe_int(t.get('jitter_ms_max', 1500))
        self.ops_per_window = safe_int(t.get('ops_per_window', 50))
        self.window_sec = safe_int(t.get('window_sec', 60))
        self.window_rest_sec = safe_int(t.get('window_rest_sec', 20))
        self.max_consec_fail = safe_int(t.get('max_consecutive_failures', 5))
        self.pause_sec_on_failure = safe_int(t.get('pause_sec_on_failure', 60))
        self.backoff_factor = float(t.get('backoff_factor', 1.5))
        self.cooldown_on_62 = safe_int(t.get('cooldown_on_errno_-62_sec', 120))

        self.ops_in_window = 0
        self.window_start = time.time()
        self.consec_fail = 0

    def jitter(self):
        """添加随机延迟"""
        delay = random.uniform(self.jitter_min/1000.0, self.jitter_max/1000.0)
        time.sleep(delay)

    def tick(self):
        """执行操作前调用"""
        now = time.time()
        if now - self.window_start > self.window_sec:
            self.window_start = now
            self.ops_in_window = 0
        if self.ops_in_window >= self.ops_per_window:
            time.sleep(self.window_rest_sec)
            self.window_start = time.time()
            self.ops_in_window = 0
        self.jitter()
        self.ops_in_window += 1

    def on_success(self):
        """操作成功时调用"""
        self.consec_fail = 0

    def on_failure(self, errno: int):
        """操作失败时调用"""
        self.consec_fail += 1
        if errno == -62:
            time.sleep(self.cooldown_on_62)
        if self.consec_fail >= self.max_consec_fail:
            time.sleep(self.pause_sec_on_failure)
            self.consec_fail = 0


# -------------------------------
# 转存工作线程（无GUI版本）
# -------------------------------

class TransferWorker(threading.Thread):
    """转存任务工作线程"""

    def __init__(self,
                 transfer_queue: List[Dict[str, Any]],
                 adapter: BaiduPanAdapter,
                 throttler: Throttler,
                 on_progress: Optional[Callable] = None,
                 on_completed: Optional[Callable] = None,
                 on_failed: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.transfer_queue = transfer_queue
        self.adapter = adapter
        self.throttler = throttler
        self.on_progress = on_progress
        self.on_completed = on_completed
        self.on_failed = on_failed
        self.log_callback = log_callback

        self.is_running = False
        self.is_paused = False
        self._state_lock = threading.Lock()
        self._queue_lock = threading.Lock()

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)

    def run(self):
        """执行转存任务"""
        with self._state_lock:
            self.is_running = True

        while True:
            with self._state_lock:
                if not self.is_running:
                    break
                if self.is_paused:
                    time.sleep(0.1)
                    continue

            # 查找待处理的任务
            pending_task = None
            pending_index = -1

            with self._queue_lock:
                for i, task in enumerate(self.transfer_queue):
                    if task['status'] == 'pending':
                        pending_task = task
                        pending_index = i
                        break

            if not pending_task:
                time.sleep(0.5)
                continue

            try:
                # 更新状态为运行中
                with self._queue_lock:
                    if pending_index < len(self.transfer_queue):
                        self.transfer_queue[pending_index]['status'] = 'running'

                if self.on_progress:
                    self.on_progress(pending_index, 'running')

                # 获取转存参数
                share_link = pending_task.get('share_link', '')
                share_password = pending_task.get('share_password', '')
                target_path = pending_task.get('target_path', '/批量转存')

                if not share_link:
                    raise Exception("分享链接为空")

                # 解析链接和密码
                base_url, pwd = parse_pwd_from_link(share_link)
                if not pwd and share_password:
                    pwd = share_password

                # 转存前先获取文件名（用于后续匹配title）
                filename = None
                try:
                    from baidu_pan_adapter import normalize_link, parse_url_and_code
                    normalized = normalize_link(f'{base_url} {pwd}')
                    url, _ = parse_url_and_code(normalized)

                    # 如果有密码，先验证
                    if pwd:
                        randsk = self.adapter._verify_pass_code(url, pwd)
                        if not isinstance(randsk, int):
                            # 验证成功，更新Cookie
                            from baidu_pan_adapter import update_cookie
                            old_cookie = self.adapter.session.headers.get('Cookie', '')
                            new_cookie = update_cookie(randsk, old_cookie)
                            self.adapter.session.headers['Cookie'] = new_cookie

                    # 获取HTML并解析文件名
                    html = self.adapter._get_transfer_params(url)
                    from baidu_pan_adapter import parse_response
                    params = parse_response(html)
                    if params and not isinstance(params, int) and len(params) >= 4:
                        filename_list = params[3]
                        if filename_list and len(filename_list) > 0:
                            filename = filename_list[0]  # 取第一个文件名
                except Exception as e:
                    # 获取文件名失败，不影响转存
                    pass

                # 执行转存
                self.throttler.tick()
                errno = self.adapter.transfer(base_url, pwd, target_path)

                if errno == 0:
                    # 转存成功
                    self.throttler.on_success()
                    with self._queue_lock:
                        if pending_index < len(self.transfer_queue):
                            self.transfer_queue[pending_index]['status'] = 'completed'
                            self.transfer_queue[pending_index]['target_path'] = target_path
                            # 保存文件名，用于匹配title
                            if filename:
                                self.transfer_queue[pending_index]['filename'] = filename

                            # 日志：记录转存成功的信息
                            task_title = self.transfer_queue[pending_index].get('title', '')
                            self.log(f"✅ 转存成功 #{pending_index}: 标题='{task_title}', 文件名='{filename}', 目标={target_path}")

                    if self.on_completed:
                        self.on_completed(pending_index, target_path)
                else:
                    # 转存失败
                    error_msg = f"转存失败 (错误码: {errno}) - {ERROR_CODES.get(errno, '未知错误')}"

                    # 检查是否应该跳过（不重试）
                    if errno in SKIP_ON_ERRORS:
                        # 直接跳过，不计入连续失败
                        with self._queue_lock:
                            if pending_index < len(self.transfer_queue):
                                self.transfer_queue[pending_index]['status'] = 'skipped'
                                self.transfer_queue[pending_index]['error_message'] = error_msg

                        self.log(f"⏭️ 跳过任务 #{pending_index}: {error_msg}")
                        if self.on_failed:
                            self.on_failed(pending_index, f"已跳过 - {error_msg}")
                    else:
                        # 正常失败，计入throttler
                        self.throttler.on_failure(errno)
                        with self._queue_lock:
                            if pending_index < len(self.transfer_queue):
                                self.transfer_queue[pending_index]['status'] = 'failed'
                                self.transfer_queue[pending_index]['error_message'] = error_msg

                        if self.on_failed:
                            self.on_failed(pending_index, error_msg)

            except Exception as e:
                # 异常处理
                error_msg = f"转存异常: {str(e)}\n链接: {pending_task.get('share_link', 'N/A')}\n目标路径: {pending_task.get('target_path', 'N/A')}"
                with self._queue_lock:
                    if pending_index < len(self.transfer_queue):
                        self.transfer_queue[pending_index]['status'] = 'failed'
                        self.transfer_queue[pending_index]['error_message'] = error_msg

                if self.on_failed:
                    self.on_failed(pending_index, error_msg)

    def pause(self):
        """暂停转存"""
        with self._state_lock:
            self.is_paused = True

    def resume(self):
        """继续转存"""
        with self._state_lock:
            self.is_paused = False

    def stop(self):
        """停止转存"""
        with self._state_lock:
            self.is_running = False


# -------------------------------
# 分享工作线程（无GUI版本）
# -------------------------------

class ShareWorker(threading.Thread):
    """分享任务工作线程"""

    def __init__(self,
                 share_queue: List[Dict[str, Any]],
                 adapter: BaiduPanAdapter,
                 throttler: Throttler,
                 on_progress: Optional[Callable] = None,
                 on_completed: Optional[Callable] = None,
                 on_failed: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        super().__init__(daemon=True)
        self.share_queue = share_queue
        self.adapter = adapter
        self.throttler = throttler
        self.on_progress = on_progress
        self.on_completed = on_completed
        self.on_failed = on_failed
        self.log_callback = log_callback

        self.is_running = False
        self.is_paused = False
        self._state_lock = threading.Lock()
        self._queue_lock = threading.Lock()

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)

    def run(self):
        """执行分享任务"""
        with self._state_lock:
            self.is_running = True

        while True:
            with self._state_lock:
                if not self.is_running:
                    break
                if self.is_paused:
                    time.sleep(0.1)
                    continue

            # 查找待处理的任务
            pending_task = None
            pending_index = -1

            with self._queue_lock:
                for i, task in enumerate(self.share_queue):
                    if task['status'] == 'pending':
                        pending_task = task
                        pending_index = i
                        break

            if not pending_task:
                time.sleep(0.5)
                continue

            try:
                # 更新状态为运行中
                with self._queue_lock:
                    if pending_index < len(self.share_queue):
                        self.share_queue[pending_index]['status'] = 'running'

                if self.on_progress:
                    self.on_progress(pending_index, 'running')

                # 获取分享参数
                fs_id = pending_task['file_info']['fs_id']
                expiry = pending_task.get('expiry', 7)  # 默认7天
                password_mode = pending_task.get('password_mode', 'random')

                # 生成密码
                if password_mode == 'fixed':
                    # 使用固定密码
                    password = pending_task.get('share_password', '')
                elif password_mode == 'random':
                    # 随机生成密码
                    password = generate_random_password()
                else:
                    # 无密码
                    password = ''

                # 执行分享
                self.throttler.tick()
                result = self.adapter.create_share(fs_id, expiry=expiry, password=password)

                if isinstance(result, str):
                    # 分享成功
                    self.throttler.on_success()
                    share_link = result
                    with self._queue_lock:
                        if pending_index < len(self.share_queue):
                            self.share_queue[pending_index]['status'] = 'completed'
                            self.share_queue[pending_index]['share_link'] = share_link
                            self.share_queue[pending_index]['share_password'] = password

                            # 日志：记录分享成功的信息
                            task_title = self.share_queue[pending_index].get('title', '')
                            task_filename = self.share_queue[pending_index]['file_info'].get('name', '')
                            self.log(f"🎉 分享成功 #{pending_index}: 标题='{task_title}', 文件名='{task_filename}', 链接={share_link[:40]}...")

                    if self.on_completed:
                        self.on_completed(pending_index, share_link, password)
                else:
                    # 分享失败
                    error_msg = f"分享失败 (错误码: {result})"

                    # 检查是否应该跳过（不重试）
                    if result in SKIP_ON_ERRORS:
                        # 直接跳过，不计入连续失败
                        with self._queue_lock:
                            if pending_index < len(self.share_queue):
                                self.share_queue[pending_index]['status'] = 'skipped'
                                self.share_queue[pending_index]['error_message'] = error_msg

                        self.log(f"⏭️ 跳过任务 #{pending_index}: {error_msg}")
                        if self.on_failed:
                            self.on_failed(pending_index, f"已跳过 - {error_msg}")
                    else:
                        # 正常失败，计入throttler
                        self.throttler.on_failure(result)
                        with self._queue_lock:
                            if pending_index < len(self.share_queue):
                                self.share_queue[pending_index]['status'] = 'failed'
                                self.share_queue[pending_index]['error_message'] = error_msg

                        if self.on_failed:
                            self.on_failed(pending_index, error_msg)

            except Exception as e:
                # 异常处理
                error_msg = f"分享异常: {str(e)}\n文件: {pending_task['file_info'].get('name', 'N/A')}"
                with self._queue_lock:
                    if pending_index < len(self.share_queue):
                        self.share_queue[pending_index]['status'] = 'failed'
                        self.share_queue[pending_index]['error_message'] = error_msg

                if self.on_failed:
                    self.on_failed(pending_index, error_msg)

    def pause(self):
        """暂停分享"""
        with self._state_lock:
            self.is_paused = True

    def resume(self):
        """继续分享"""
        with self._state_lock:
            self.is_paused = False

    def stop(self):
        """停止分享"""
        with self._state_lock:
            self.is_running = False


# -------------------------------
# 核心业务服务类
# -------------------------------

class CoreService:
    """核心业务服务 - 管理转存和分享队列"""

    def __init__(self, cookie: str = None, config: Dict[str, Any] = None):
        self.cookie = cookie
        self.config = config or {}
        self.adapter = None
        self.throttler = Throttler(self.config)

        self.transfer_queue: List[Dict[str, Any]] = []
        self.share_queue: List[Dict[str, Any]] = []

        self.transfer_worker: Optional[TransferWorker] = None
        self.share_worker: Optional[ShareWorker] = None

        self.session_tag = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 回调函数
        self.log_callback: Optional[Callable] = None
        
        # 默认设置
        self.share_defaults = {
            'expiry': 7,
            'auto_password': True,
            'fixed_password': ''
        }
        self.transfer_defaults = {
            'target_path': '/批量转存'
        }

    def set_log_callback(self, callback: Callable):
        """设置日志回调函数"""
        self.log_callback = callback

    def log(self, message: str):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[{now_str()}] {message}")

    def login(self, cookie: str) -> Tuple[bool, str]:
        """
        登录百度网盘
        返回: (成功/失败, 错误信息)
        """
        try:
            self.cookie = cookie
            # 正确的初始化方式
            self.adapter = BaiduPanAdapter(debug=False)

            # 使用init方法初始化（传入cookie）
            success = self.adapter.init(cookie)

            if success:
                self.log("登录成功")
                return True, ""
            else:
                error_msg = "登录失败，Cookie无效或已过期"
                self.log(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            self.log(error_msg)
            return False, error_msg

    def add_transfer_tasks_from_csv(self, csv_data: List[Dict[str, str]], default_target_path: str = '/批量转存') -> int:
        """
        从CSV数据添加转存任务
        参数:
            csv_data: CSV数据列表，每项包含 {'标题', '链接', '提取码', '保存位置'}
            default_target_path: 默认保存路径
        返回: 添加的任务数量
        """
        imported_count = 0
        for row in csv_data:
            title = row.get('标题', '').strip()  # 标题可以为空
            share_link = row.get('链接', '').strip()
            share_password = row.get('提取码', '').strip()
            target_path = row.get('保存位置', '').strip()

            # 验证必填字段（只有链接是必填的）
            if not share_link:
                continue  # 跳过空链接

            # 如果链接中有pwd参数，提取出来
            if not share_password:
                base_link, pwd = parse_pwd_from_link(share_link)
                if pwd:
                    share_password = pwd

            # 添加到转存队列
            transfer_task = {
                'title': title,  # 保存标题（可以为空，为空时后续用文件名）
                'share_link': share_link,
                'share_password': share_password,
                'target_path': target_path or default_target_path,
                'status': 'pending',
                'created_at': now_str(),
                'session_tag': self.session_tag,
                'retry_count': 0,
                'error_message': ''
            }

            self.transfer_queue.append(transfer_task)
            imported_count += 1

            # 日志：记录导入的title
            self.log(f"📥 导入任务 #{imported_count}: 标题='{title}', 链接={share_link[:30]}...")

        self.log(f"已导入 {imported_count} 个转存任务")
        return imported_count

    def add_transfer_task(self, share_link: str, share_password: str = '', target_path: str = '/批量转存') -> bool:
        """
        添加单个转存任务
        """
        if not share_link:
            return False

        # 如果链接中有pwd参数，提取出来
        if not share_password:
            base_link, pwd = parse_pwd_from_link(share_link)
            if pwd:
                share_password = pwd

        transfer_task = {
            'share_link': share_link,
            'share_password': share_password,
            'target_path': target_path,
            'status': 'pending',
            'created_at': now_str(),
            'session_tag': self.session_tag,
            'retry_count': 0,
            'error_message': ''
        }

        self.transfer_queue.append(transfer_task)
        self.log(f"已添加转存任务: {share_link[:50]}...")
        return True

    def start_transfer(self) -> Tuple[bool, str]:
        """
        开始执行转存任务
        返回: (成功/失败, 错误信息)
        """
        if not self.adapter:
            return False, "请先登录"

        if self.transfer_worker and self.transfer_worker.is_alive():
            return False, "转存任务正在运行中"

        # 创建并启动转存工作线程
        self.transfer_worker = TransferWorker(
            self.transfer_queue,
            self.adapter,
            self.throttler,
            on_progress=lambda idx, status: self.log(f"转存进度: 任务{idx} - {status}"),
            on_completed=lambda idx, path: self.log(f"转存成功: 任务{idx} -> {path}"),
            on_failed=lambda idx, error: self.log(f"转存失败: 任务{idx} - {error}"),
            log_callback=self.log
        )
        self.transfer_worker.start()
        self.log("转存任务已启动")
        return True, ""

    def pause_transfer(self):
        """暂停转存"""
        if self.transfer_worker:
            self.transfer_worker.pause()
            self.log("转存已暂停")

    def resume_transfer(self):
        """继续转存"""
        if self.transfer_worker:
            self.transfer_worker.resume()
            self.log("转存已继续")

    def stop_transfer(self):
        """停止转存"""
        if self.transfer_worker:
            self.transfer_worker.stop()
            self.transfer_worker = None
            self.log("转存已停止")

    def get_transfer_status(self) -> Dict[str, Any]:
        """获取转存状态"""
        total = len(self.transfer_queue)
        pending = sum(1 for t in self.transfer_queue if t['status'] == 'pending')
        running = sum(1 for t in self.transfer_queue if t['status'] == 'running')
        completed = sum(1 for t in self.transfer_queue if t['status'] == 'completed')
        failed = sum(1 for t in self.transfer_queue if t['status'] == 'failed')
        skipped = sum(1 for t in self.transfer_queue if t['status'] == 'skipped')

        is_running = self.transfer_worker and self.transfer_worker.is_alive()
        is_paused = self.transfer_worker.is_paused if self.transfer_worker else False

        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'skipped': skipped,
            'is_running': is_running,
            'is_paused': is_paused,
            'tasks': self.transfer_queue
        }

    def add_share_tasks_from_path(self, path: str, expiry: int = 7, password: str = None) -> int:
        """
        从指定路径添加分享任务
        参数:
            path: 网盘路径
            expiry: 有效期（0=永久, 1=1天, 7=7天, 30=30天）
            password: 固定提取码，None则随机生成
        """
        if not self.adapter:
            self.log("请先登录")
            return 0

        # 列出目录文件
        items = self.adapter.list_dir(path)
        if isinstance(items, int):
            self.log(f"列目录失败: {path} (错误码: {items})")
            return 0

        # 创建转存队列的标题映射（通过文件名匹配）
        title_map = {}
        for task in self.transfer_queue:
            if task.get('status') == 'completed':
                # 使用文件名作为key进行匹配
                filename = task.get('filename', '')
                title = task.get('title', '')
                if filename and title:
                    title_map[filename] = title
                    self.log(f"🔗 标题映射: '{filename}' -> '{title}'")
                elif filename:
                    # 有文件名但没有title，记录一下
                    self.log(f"⚠️ 转存任务有文件名但无标题: '{filename}'")

        self.log(f"📋 共建立 {len(title_map)} 个标题映射")

        added_count = 0
        for item in items:
            file_path = item['path']
            file_name = item['server_filename']

            # 通过文件名精确匹配标题
            title = title_map.get(file_name, file_name)  # 如果没匹配到，使用文件名作为标题

            # 日志：记录匹配结果
            if file_name in title_map:
                self.log(f"✅ 匹配成功: '{file_name}' -> 标题='{title}'")
            else:
                self.log(f"⚠️ 未匹配到标题，使用文件名: '{file_name}'")


            share_task = {
                'title': title,  # 保存标题
                'file_info': {
                    'fs_id': item['fs_id'],
                    'name': file_name,
                    'path': file_path
                },
                'status': 'pending',
                'created_at': now_str(),
                'session_tag': self.session_tag,
                'share_link': '',
                'share_password': password if password else '',  # 如果指定了密码就用固定的
                'error_message': '',
                'expiry': expiry,  # 使用传入的有效期
                'password_mode': 'fixed' if password else 'random'  # 固定密码或随机
            }
            self.share_queue.append(share_task)
            added_count += 1

        self.log(f"已从 {path} 添加 {added_count} 个分享任务 (有效期: {expiry}天, 提取码: {'固定' if password else '随机'})")
        return added_count

    def start_share(self) -> Tuple[bool, str]:
        """
        开始执行分享任务
        返回: (成功/失败, 错误信息)
        """
        if not self.adapter:
            return False, "请先登录"

        if self.share_worker and self.share_worker.is_alive():
            return False, "分享任务正在运行中"

        # 创建并启动分享工作线程
        self.share_worker = ShareWorker(
            self.share_queue,
            self.adapter,
            self.throttler,
            on_progress=lambda idx, status: self.log(f"分享进度: 任务{idx} - {status}"),
            on_completed=lambda idx, link, pwd: self.log(f"分享成功: 任务{idx} - {link} (密码: {pwd})"),
            on_failed=lambda idx, error: self.log(f"分享失败: 任务{idx} - {error}"),
            log_callback=self.log
        )
        self.share_worker.start()
        self.log("分享任务已启动")
        return True, ""

    def get_share_status(self) -> Dict[str, Any]:
        """获取分享状态"""
        total = len(self.share_queue)
        pending = sum(1 for t in self.share_queue if t['status'] == 'pending')
        running = sum(1 for t in self.share_queue if t['status'] == 'running')
        completed = sum(1 for t in self.share_queue if t['status'] == 'completed')
        failed = sum(1 for t in self.share_queue if t['status'] == 'failed')
        skipped = sum(1 for t in self.share_queue if t['status'] == 'skipped')

        is_running = self.share_worker and self.share_worker.is_alive()
        is_paused = self.share_worker.is_paused if self.share_worker else False

        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'skipped': skipped,
            'is_running': is_running,
            'is_paused': is_paused,
            'tasks': self.share_queue
        }

    def pause_share(self):
        """暂停分享"""
        if self.share_worker:
            self.share_worker.pause()
            self.log("分享已暂停")

    def resume_share(self):
        """继续分享"""
        if self.share_worker:
            self.share_worker.resume()
            self.log("分享已继续")

    def stop_share(self):
        """停止分享"""
        if self.share_worker:
            self.share_worker.stop()
            self.share_worker = None
            self.log("分享已停止")

    def get_share_results(self) -> List[Dict[str, str]]:
        """
        获取分享结果（已完成的任务）
        返回格式：标题 + 完整链接（包含密码）
        """
        results = []
        for task in self.share_queue:
            if task['status'] == 'completed':
                # 组合链接和密码
                share_link = task.get('share_link', '')
                share_password = task.get('share_password', '')
                complete_link = build_link_with_pwd(share_link, share_password)

                # 获取标题
                title = task.get('title', '')
                filename = task['file_info']['name']
                final_title = title if title else filename

                # 日志：记录最终输出
                self.log(f"📤 输出结果: 标题='{final_title}' (原始title='{title}', 文件名='{filename}')")

                results.append({
                    '标题': final_title,  # 优先使用标题，否则使用文件名
                    '分享链接': complete_link  # 完整链接（包含pwd参数）
                })
        return results

    def get_transfer_queue(self) -> List[Dict[str, Any]]:
        """获取转存队列"""
        return self.transfer_queue

    def get_share_queue(self) -> List[Dict[str, Any]]:
        """获取分享队列"""
        return self.share_queue

    def list_dir(self, path: str):
        """
        列出指定路径的文件
        委托给adapter的list_dir方法
        """
        if not self.adapter:
            return -4  # 未登录错误码
        return self.adapter.list_dir(path)

    def search_files(self, keyword: str, path: str = '/'):
        """
        搜索文件
        委托给adapter的search方法
        """
        if not self.adapter:
            return []
        # BaiduPanAdapter的search方法
        return self.adapter.search(keyword, path)

    def update_throttle(self, throttle_config: Dict[str, Any]):
        """
        Update throttler configuration and apply to active workers.
        
        Args:
            throttle_config: New throttle configuration dictionary
        """
        # Create new throttler with updated config
        new_config = self.config.copy()
        new_config['throttle'] = throttle_config
        self.throttler = Throttler(new_config)
        
        # Update throttler reference in active workers
        if self.transfer_worker and self.transfer_worker.is_alive():
            self.transfer_worker.throttler = self.throttler
            self.log("转存工作线程的节流配置已更新")
        
        if self.share_worker and self.share_worker.is_alive():
            self.share_worker.throttler = self.throttler
            self.log("分享工作线程的节流配置已更新")
        
        self.log("节流配置已更新")
    
    def apply_settings(self, settings: Dict[str, Any]):
        """
        Apply full settings bundle to the service.
        
        Args:
            settings: Full settings dictionary including throttle, share_defaults, transfer_defaults
        """
        # Apply throttle settings if present
        if 'throttle' in settings:
            self.update_throttle(settings['throttle'])
        
        # Apply share defaults if present
        if 'share_defaults' in settings:
            self.share_defaults = settings['share_defaults'].copy()
            self.log(f"分享默认设置已更新: 有效期={self.share_defaults.get('expiry')}天")
        
        # Apply transfer defaults if present
        if 'transfer_defaults' in settings:
            self.transfer_defaults = settings['transfer_defaults'].copy()
            self.log(f"转存默认设置已更新: 目标路径={self.transfer_defaults.get('target_path')}")
        
        self.log("服务设置已完全更新")

    def clear_transfer_queue(self):
        """清空转存队列"""
        self.transfer_queue.clear()
        self.log("转存队列已清空")

    def clear_share_queue(self):
        """清空分享队列"""
        self.share_queue.clear()
        self.log("分享队列已清空")

    def export_transfer_results(self) -> List[Dict[str, Any]]:
        """
        导出转存结果
        返回所有已完成的转存任务
        """
        results = []
        for task in self.transfer_queue:
            if task['status'] == 'completed':
                results.append({
                    'share_link': task.get('share_link', ''),
                    'target_path': task.get('target_path', ''),
                    'filename': task.get('filename', ''),
                    'status': task['status'],
                    'created_at': task.get('created_at', ''),
                    'completed_at': task.get('completed_at', '')
                })
        return results

    def export_share_results(self) -> List[Dict[str, Any]]:
        """
        导出分享结果
        返回所有已完成的分享任务
        """
        results = []
        for task in self.share_queue:
            if task['status'] == 'completed':
                results.append({
                    'title': task.get('title', task['file_info']['name']),
                    'share_link': task.get('share_link', ''),
                    'share_password': task.get('share_password', ''),
                    'file_path': task['file_info']['path'],
                    'status': task['status'],
                    'created_at': task.get('created_at', ''),
                    'completed_at': task.get('completed_at', '')
                })
        return results
