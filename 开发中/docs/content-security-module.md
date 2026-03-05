# 内容安全与审核模块文档

## 概述

内容安全与审核模块是知域平台的核心安全保障系统，包括敏感词管理、内容审核引擎和举报处理系统。

## 模块组成

### 1. 敏感词管理（任务 3.1）✅
- 敏感词 CRUD 操作
- 批量导入功能
- Redis 缓存机制
- 按级别和分类管理

### 2. 内容审核引擎（任务 3.2）✅
- 文本内容审核
- 图片内容审核（预留接口）
- 混合内容审核
- DFA 算法实现
- 批量审核功能

### 3. 举报处理系统（任务 3.4）✅
- 用户举报提交
- 举报审核队列
- 举报处理流程
- 统计分析功能

## 功能特性

### 敏感词管理

**支持的敏感级别：**
- `low`: 低敏感度
- `medium`: 中等敏感度
- `high`: 高敏感度

**处理动作：**
- `replace`: 替换为 ***
- `block`: 阻止发布
- `review`: 人工审核

**API 端点：**
```
POST   /api/v1/sensitive-words              创建敏感词
GET    /api/v1/sensitive-words              获取列表
GET    /api/v1/sensitive-words/{id}         获取详情
PUT    /api/v1/sensitive-words/{id}         更新
DELETE /api/v1/sensitive-words/{id}         删除
POST   /api/v1/sensitive-words/bulk-import  批量导入
POST   /api/v1/sensitive-words/check        检测内容
GET    /api/v1/sensitive-words/statistics/summary  统计信息
```

### 内容审核引擎

**审核策略：**
1. 简单匹配：快速检测敏感词
2. DFA 算法：高效过滤大量敏感词
3. 严格模式：发现任何敏感词即拦截
4. 普通模式：根据敏感词数量决定动作

**审核结果：**
- `approve`: 通过审核
- `block`: 拦截发布
- `review`: 需要人工审核

**API 端点：**
```
POST /api/v1/audit/content    审核混合内容
POST /api/v1/audit/text       审核文本
POST /api/v1/audit/batch      批量审核
POST /api/v1/audit/filter     过滤敏感词
```

### 举报处理系统

**举报对象类型：**
- `post`: 帖子
- `comment`: 评论
- `user`: 用户
- `item`: 二手商品
- `order`: 订单

**举报状态：**
- `pending`: 待处理
- `processing`: 处理中
- `resolved`: 已解决
- `rejected`: 已驳回

**限制规则：**
- 每日举报次数上限：10 次
- 举报间隔：60 秒

**API 端点：**
```
POST /api/v1/reports                    提交举报
GET  /api/v1/reports                    获取举报列表
GET  /api/v1/reports/{id}               获取举报详情
POST /api/v1/reports/{id}/process       处理举报（管理员）
GET  /api/v1/reports/statistics/summary 统计信息（管理员）
GET  /api/v1/reports/target/{type}/{id}/count  查询对象举报次数
```

## 使用示例

### 1. 创建敏感词

```python
import httpx

async def create_sensitive_word():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/sensitive-words",
            headers={"Authorization": "Bearer ADMIN_TOKEN"},
            json={
                "word": "违规词",
                "level": "high",
                "category": "暴力",
                "action": "block"
            }
        )
        return response.json()
```

### 2. 审核内容

```python
async def audit_content(text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/audit/text",
            params={"text": text, "strict_mode": False}
        )
        result = response.json()
        
        if result["data"]["passed"]:
            print("内容通过审核")
        else:
            print(f"内容被{result['data']['action']}")
            print(f"发现敏感词: {result['data']['found_words']}")
```

### 3. 提交举报

```python
async def submit_report(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "target_type": "post",
                "target_id": 123,
                "reason": "包含违规内容",
                "description": "该帖子包含不当言论",
                "evidence": {
                    "screenshots": ["url1", "url2"]
                }
            }
        )
        return response.json()
```

### 4. 过滤敏感词

```python
async def filter_text(text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/audit/filter",
            json={
                "text": text,
                "replace_char": "*"
            }
        )
        result = response.json()
        print(f"原文: {result['data']['original_text']}")
        print(f"过滤后: {result['data']['filtered_text']}")
```

## DFA 算法说明

DFA (Deterministic Finite Automaton) 是一种高效的字符串匹配算法，特别适合大量敏感词的检测。

**优势：**
- 时间复杂度：O(n)，n 为文本长度
- 不受敏感词数量影响
- 支持一次扫描检测所有敏感词

**实现原理：**
1. 构建字典树（Trie）
2. 遍历文本，匹配树节点
3. 记录所有匹配位置

**使用场景：**
- 敏感词数量 > 100
- 需要实时过滤
- 高并发场景

## 数据库表结构

### sensitive_words 表

```sql
CREATE TABLE sensitive_words (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  word VARCHAR(100) NOT NULL UNIQUE,
  level ENUM('low', 'medium', 'high') NOT NULL,
  category VARCHAR(50),
  action ENUM('replace', 'block', 'review') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_level (level)
);
```

### reports 表

```sql
CREATE TABLE reports (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  reporter_id BIGINT NOT NULL,
  target_type ENUM('post', 'comment', 'user', 'item', 'order') NOT NULL,
  target_id BIGINT NOT NULL,
  reason VARCHAR(255),
  description TEXT,
  evidence JSON,
  status ENUM('pending', 'processing', 'resolved', 'rejected') NOT NULL,
  handler_id BIGINT,
  handle_result TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (reporter_id) REFERENCES users(id),
  FOREIGN KEY (handler_id) REFERENCES users(id),
  INDEX idx_status (status),
  INDEX idx_target (target_type, target_id),
  INDEX idx_reporter_id (reporter_id),
  INDEX idx_created_at (created_at)
);
```

## 权限控制

### 敏感词管理
- 创建/更新/删除：需要管理员权限
- 查询列表：需要管理员权限
- 检测内容：所有用户可用

### 内容审核
- 所有审核接口：所有用户可用
- 用于内容发布前的自检

### 举报管理
- 提交举报：需要登录
- 查看自己的举报：需要登录
- 查看所有举报：需要管理员权限
- 处理举报：需要管理员权限

## 性能优化

### 1. Redis 缓存
- 敏感词列表缓存 1 小时
- 减少数据库查询
- 提高检测速度

### 2. DFA 算法
- 一次扫描检测所有敏感词
- 时间复杂度 O(n)
- 适合大规模敏感词库

### 3. 批量审核
- 支持一次审核多个内容
- 减少网络往返
- 提高吞吐量

## 测试

### 运行测试

```bash
# 敏感词管理测试
pytest tests/services/test_sensitive_word.py -v

# 内容审核测试
pytest tests/services/test_content_audit.py -v

# 举报系统测试
pytest tests/services/test_report.py -v

# 所有测试
pytest tests/services/test_sensitive_word.py tests/services/test_content_audit.py tests/services/test_report.py -v
```

## 数据库迁移

```bash
# 应用所有迁移
alembic upgrade head

# 查看迁移历史
alembic history

# 回滚
alembic downgrade -1
```

**迁移文件：**
- `002_create_sensitive_words_table.py`
- `003_create_reports_table.py`

## 文件结构

```
app/
├── models/
│   ├── sensitive_word.py
│   └── report.py
├── repositories/
│   ├── sensitive_word.py
│   └── report.py
├── services/
│   ├── sensitive_word.py
│   ├── content_audit.py
│   └── report.py
├── schemas/
│   ├── sensitive_word.py
│   ├── audit.py
│   └── report.py
└── api/v1/endpoints/
    ├── sensitive_words.py
    ├── audit.py
    └── reports.py

tests/services/
├── test_sensitive_word.py
├── test_content_audit.py
└── test_report.py

alembic/versions/
├── 002_create_sensitive_words_table.py
└── 003_create_reports_table.py
```

## 相关需求

- 需求 4.1: 内容敏感词检测
- 需求 4.2: 内容审核通过发布
- 需求 4.3: 高危内容人工审核
- 需求 4.4: 举报功能
- 需求 4.5: 举报审核
- 需求 4.6: 违规内容处理
- 需求 4.7: 敏感词库管理

## 下一步

第三部分（内容安全与审核模块）已完成！接下来可以：

1. ✅ 继续第四部分：校园圈子与内容社交
2. ✅ 集成审核引擎到帖子发布流程
3. ✅ 实现图片审核（腾讯云内容安全 API）
4. ✅ 优化 DFA 算法性能
5. ✅ 添加更多审核规则

## 注意事项

1. 敏感词库需要定期更新
2. 审核规则需要根据实际情况调整
3. 举报处理需要及时响应（24小时内）
4. 缓存失效时间可根据需求调整
5. DFA 算法适合大规模敏感词库（>100个）
6. 建议定期备份敏感词和举报数据
