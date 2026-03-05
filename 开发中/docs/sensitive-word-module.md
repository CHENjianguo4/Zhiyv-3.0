# 敏感词管理模块文档

## 概述

敏感词管理模块用于内容审核，支持敏感词的 CRUD 操作、批量导入和 Redis 缓存机制。

## 功能特性

### ✅ 已实现功能

1. **敏感词 CRUD**
   - 创建敏感词
   - 查询敏感词（单个/列表）
   - 更新敏感词
   - 删除敏感词

2. **批量导入**
   - 支持批量导入敏感词
   - 自动去重检测
   - 返回导入结果统计

3. **Redis 缓存**
   - 敏感词列表缓存（1小时）
   - 自动缓存更新
   - 高性能内容检测

4. **内容检测**
   - 检测文本是否包含敏感词
   - 返回发现的敏感词列表
   - 支持所有用户调用

5. **统计功能**
   - 总数统计
   - 按级别统计

## 数据模型

### SensitiveWord 表

```sql
CREATE TABLE sensitive_words (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  word VARCHAR(100) NOT NULL UNIQUE,
  level ENUM('low', 'medium', 'high') NOT NULL,
  category VARCHAR(50),
  action ENUM('replace', 'block', 'review') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 字段说明

- `id`: 主键
- `word`: 敏感词内容（唯一）
- `level`: 敏感级别
  - `low`: 低敏感度
  - `medium`: 中等敏感度
  - `high`: 高敏感度
- `category`: 分类（可选）
- `action`: 处理动作
  - `replace`: 替换为 ***
  - `block`: 阻止发布
  - `review`: 人工审核
- `created_at`: 创建时间

## API 接口

### 1. 创建敏感词

```http
POST /api/v1/sensitive-words
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "word": "测试敏感词",
  "level": "high",
  "category": "政治",
  "action": "block"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "word": "测试敏感词",
    "level": "high",
    "category": "政治",
    "action": "block",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

### 2. 获取敏感词列表

```http
GET /api/v1/sensitive-words?level=high&limit=100&offset=0
Authorization: Bearer {admin_token}
```

**查询参数：**
- `level`: 敏感级别筛选（可选）
- `category`: 分类筛选（可选）
- `limit`: 每页数量（默认 100，最大 1000）
- `offset`: 偏移量（默认 0）

### 3. 获取单个敏感词

```http
GET /api/v1/sensitive-words/{word_id}
Authorization: Bearer {admin_token}
```

### 4. 更新敏感词

```http
PUT /api/v1/sensitive-words/{word_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "level": "medium",
  "category": "暴力",
  "action": "review"
}
```

### 5. 删除敏感词

```http
DELETE /api/v1/sensitive-words/{word_id}
Authorization: Bearer {admin_token}
```

### 6. 批量导入敏感词

```http
POST /api/v1/sensitive-words/bulk-import
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "words": [
    {
      "word": "敏感词1",
      "level": "high",
      "action": "block"
    },
    {
      "word": "敏感词2",
      "level": "medium",
      "action": "review"
    }
  ]
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success_count": 2,
    "failed_count": 0,
    "errors": []
  }
}
```

### 7. 检测内容

```http
POST /api/v1/sensitive-words/check
Content-Type: application/json

{
  "content": "这是一段需要检测的文本内容"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "has_sensitive_words": true,
    "found_words": ["敏感词1", "敏感词2"],
    "count": 2
  }
}
```

**注意：** 此接口不需要管理员权限，所有用户可用。

### 8. 获取统计信息

```http
GET /api/v1/sensitive-words/statistics/summary
Authorization: Bearer {admin_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 150,
    "by_level": {
      "high": 50,
      "medium": 70,
      "low": 30
    }
  }
}
```

## 权限要求

### 管理员权限（需要）
- 创建敏感词
- 查询敏感词列表
- 更新敏感词
- 删除敏感词
- 批量导入
- 查看统计信息

### 所有用户（无需认证）
- 检测内容是否包含敏感词

## 缓存机制

### Redis 缓存策略

1. **缓存键：** `sensitive_words:all`
2. **缓存时间：** 1 小时（3600 秒）
3. **缓存内容：** 所有敏感词的列表
4. **更新策略：** 
   - 创建/更新/删除敏感词时自动清除缓存
   - 下次查询时重新加载到缓存

### 性能优化

- 内容检测使用 Set 数据结构，O(1) 查找复杂度
- 缓存命中时无需查询数据库
- 支持高并发内容检测

## 使用示例

### Python 示例

```python
import httpx

# 创建敏感词
async def create_sensitive_word(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/sensitive-words",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "word": "测试词",
                "level": "high",
                "action": "block"
            }
        )
        return response.json()

# 检测内容
async def check_content(content: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/sensitive-words/check",
            json={"content": content}
        )
        return response.json()
```

### curl 示例

```bash
# 创建敏感词
curl -X POST http://localhost:8000/api/v1/sensitive-words \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"word":"测试词","level":"high","action":"block"}'

# 检测内容
curl -X POST http://localhost:8000/api/v1/sensitive-words/check \
  -H "Content-Type: application/json" \
  -d '{"content":"这是测试内容"}'
```

## 测试

### 运行测试

```bash
# 运行敏感词模块测试
pytest tests/services/test_sensitive_word.py -v

# 查看测试覆盖率
pytest tests/services/test_sensitive_word.py --cov=app/services/sensitive_word
```

### 测试用例

- ✅ 创建敏感词成功
- ✅ 创建重复敏感词失败
- ✅ 查询敏感词成功
- ✅ 查询不存在的敏感词失败
- ✅ 检测包含敏感词的内容
- ✅ 检测不包含敏感词的内容
- ✅ 批量导入成功
- ✅ 删除敏感词成功
- ✅ 获取统计信息

## 数据库迁移

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 查看迁移历史
alembic history

# 回滚一个版本
alembic downgrade -1
```

### 迁移文件

- `alembic/versions/002_create_sensitive_words_table.py`

## 文件结构

```
app/
├── models/
│   └── sensitive_word.py          # 数据模型
├── repositories/
│   └── sensitive_word.py          # 数据访问层
├── services/
│   └── sensitive_word.py          # 业务逻辑层
├── schemas/
│   └── sensitive_word.py          # API Schema
└── api/v1/endpoints/
    └── sensitive_words.py         # API 端点

tests/
└── services/
    └── test_sensitive_word.py     # 单元测试

alembic/versions/
└── 002_create_sensitive_words_table.py  # 数据库迁移
```

## 下一步

任务 3.1 已完成，接下来可以：

1. ✅ 继续任务 3.2：实现内容审核引擎
2. ✅ 集成敏感词检测到帖子发布流程
3. ✅ 实现更高级的检测算法（AC 自动机、DFA）
4. ✅ 添加图片内容审核（腾讯云内容安全 API）

## 相关需求

- 需求 4.7: 敏感词库管理功能

## 注意事项

1. 敏感词管理接口需要管理员权限
2. 内容检测接口对所有用户开放
3. 缓存会在敏感词变更时自动清除
4. 批量导入时会自动去重
5. 建议定期备份敏感词数据
