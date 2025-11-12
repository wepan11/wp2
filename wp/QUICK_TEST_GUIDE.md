# 测试快速指南

## 运行测试

### 运行所有测试
```bash
cd wp
python -m unittest discover tests -v
python3 -m pytest tests/integration -v
```

### 运行知识库模块测试
```bash
python -m unittest tests.test_knowledge_module -v
```

### 运行集成测试（后端API）
```bash
python3 -m pytest tests/integration -v
```

### 运行特定测试类
```bash
# 存储层测试
python -m unittest tests.test_knowledge_module.TestKnowledgeRepository -v

# API测试
python -m unittest tests.test_knowledge_module.TestKnowledgeAPI -v
```

### 运行单个测试
```bash
python -m unittest tests.test_knowledge_module.TestKnowledgeRepository.test_tag_derivation -v
```

## 测试覆盖

### 存储层测试 (17个)
- ✅ 标签提取 (6种场景)
- ✅ 基础列表功能
- ✅ 分页功能
- ✅ 全文搜索 (标题/ID/URL/链接)
- ✅ 状态过滤 (pending/completed/transferred/failed)
- ✅ 标签过滤
- ✅ 日期范围过滤
- ✅ 排序功能 (4个字段 × 2个方向)
- ✅ 非法参数处理
- ✅ 组合过滤
- ✅ 边缘情况 (空值、null)
- ✅ 标签列表
- ✅ 状态统计
- ✅ 导出功能 (全字段/选择字段/过滤/验证)

### API测试 (15个)
- ✅ 认证机制 (有/无API密钥)
- ✅ 分页参数
- ✅ 过滤参数
- ✅ 参数验证 (非法排序/方向/日期)
- ✅ CSV导出 (基础/自定义字段/过滤/验证)
- ✅ 标签端点
- ✅ 状态端点
- ✅ 详情页 (404测试)
- ✅ 静态路由

### 后端控制API集成测试 (26个)
- ✅ 健康检查和系统信息端点
- ✅ 认证流程 (有/无API密钥)
- ✅ 文件管理 (列表/搜索)
- ✅ 转存操作 (状态/队列)
- ✅ 分享操作 (状态/队列)
- ✅ 账户参数处理
- ✅ 错误传播和处理
- ✅ 无真实网络调用 (使用FakeCoreService)

## 测试特点

### 完全隔离
- ✨ 使用临时数据库
- ✨ 不影响生产数据
- ✨ 自动清理

### 标准化
- ✨ 使用Python unittest框架
- ✨ 可集成CI/CD
- ✨ 支持测试发现

### 全面覆盖
- ✨ 功能测试
- ✨ 边缘情况
- ✨ 错误处理
- ✨ 集成测试

## 预期结果

### 单元测试 (unittest)
```
test_entries_invalid_date_format ... ok
test_entries_invalid_sort_field ... ok
test_entries_invalid_sort_order ... ok
...
test_tag_derivation ... ok

----------------------------------------------------------------------
Ran 32 tests in ~2s

OK
```

### 集成测试 (pytest)
```
tests/integration/test_backend_endpoints.py::TestHealthAndInfo::test_health_no_auth_required PASSED
tests/integration/test_backend_endpoints.py::TestHealthAndInfo::test_info_requires_auth PASSED
tests/integration/test_backend_endpoints.py::TestFileManagement::test_list_files_happy_path PASSED
...
tests/integration/test_backend_endpoints.py::TestErrorPropagation::test_search_files_returns_empty_on_error PASSED

======================== 26 passed in ~1s ========================
```

## 故障排查

### 测试失败
1. 检查数据库是否被锁定
2. 确认所有依赖已安装
3. 查看详细错误输出

### 导入错误
1. 确保在wp目录下运行
2. 检查Python路径设置
3. 验证模块存在

### 数据库错误
1. 删除临时测试文件
2. 重新运行测试
3. 检查权限设置

## 详细文档

- [完整测试文档](docs/KNOWLEDGE_TESTING.md)
- [测试实施总结](TESTING_SUMMARY.md)
- [知识库API文档](README_KNOWLEDGE_API.md)
- [知识库存储层文档](README_KNOWLEDGE_REPO.md)
- [集成测试文档](tests/integration/README.md)
