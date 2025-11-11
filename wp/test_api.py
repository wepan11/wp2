"""
API测试脚本
用于测试所有API端点
"""
import requests
import json
import sys
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:5000"
API_KEY = "your_secret_key"  # 从.env中获取


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, method: str, endpoint: str, data: Dict = None, 
             params: Dict = None, expected_status: int = 200, auth: bool = True):
        """
        测试单个API端点
        
        Args:
            name: 测试名称
            method: HTTP方法
            endpoint: API端点
            data: 请求体数据
            params: 查询参数
            expected_status: 预期HTTP状态码
            auth: 是否需要认证
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.headers if auth else {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                print(f"✅ PASS: {name}")
                print(f"   Status: {response.status_code}")
                try:
                    print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
                self.passed += 1
            else:
                print(f"❌ FAIL: {name}")
                print(f"   Expected: {expected_status}, Got: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed += 1
        
        except Exception as e:
            print(f"❌ ERROR: {name}")
            print(f"   Exception: {str(e)}")
            self.failed += 1
        
        print()
    
    def summary(self):
        """打印测试摘要"""
        total = self.passed + self.failed
        print("=" * 60)
        print(f"测试完成: {total} 个测试")
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")
        print("=" * 60)
        
        return self.failed == 0


def main():
    """主函数"""
    print("=" * 60)
    print("百度网盘自动化服务器 API 测试")
    print("=" * 60)
    print()
    
    # 获取API密钥
    api_key = input(f"请输入API密钥（默认: {API_KEY}）: ").strip()
    if not api_key:
        api_key = API_KEY
    
    tester = APITester(BASE_URL, api_key)
    
    # 系统接口测试
    print("【系统接口测试】")
    print("-" * 60)
    tester.test("健康检查", "GET", "/api/health", auth=False)
    tester.test("获取系统信息", "GET", "/api/info")
    tester.test("获取统计信息", "GET", "/api/stats")
    
    # 账户接口测试
    print("【账户接口测试】")
    print("-" * 60)
    tester.test("列出所有账户", "GET", "/api/accounts")
    
    # 转存接口测试
    print("【转存接口测试】")
    print("-" * 60)
    tester.test("获取转存状态", "GET", "/api/transfer/status")
    tester.test("获取转存队列", "GET", "/api/transfer/queue")
    
    # 添加转存任务（示例，需要有效链接）
    tester.test(
        "添加转存任务（无效链接测试）",
        "POST",
        "/api/transfer/add",
        data={
            "share_link": "https://pan.baidu.com/s/test",
            "share_password": "1234",
            "target_path": "/测试"
        },
        expected_status=200
    )
    
    # 分享接口测试
    print("【分享接口测试】")
    print("-" * 60)
    tester.test("获取分享状态", "GET", "/api/share/status")
    tester.test("获取分享队列", "GET", "/api/share/queue")
    
    # 文件管理接口测试
    print("【文件管理接口测试】")
    print("-" * 60)
    tester.test("列出根目录文件", "GET", "/api/files/list", params={"path": "/"})
    
    # 错误测试
    print("【错误处理测试】")
    print("-" * 60)
    tester.test("无效API密钥", "GET", "/api/info", auth=False, expected_status=401)
    tester.test("不存在的端点", "GET", "/api/nonexistent", expected_status=404)
    
    # 打印摘要
    print()
    success = tester.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        sys.exit(1)
