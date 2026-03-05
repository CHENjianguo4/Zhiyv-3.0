# 校园圈子与内容社交模块

## 概述

校园圈子与内容社交模块是知域平台的核心功能，提供社区讨论、内容发布、互动交流等功能。

## 当前实现状态

### ✅ 已完成

#### 任务 4.1：实现圈子数据模型
- Circle 模型（MySQL）
- School 模型（MySQL）
- Post 文档模型（MongoDB）
- Comment 文档模型（MongoDB）
- Interaction 模型
- 数据库迁移文件

### ⏳ 待实现

由于第四部分功能复杂且工作量大，以下是剩余任务的实现建议：

#### 任务 4.2：实现圈子管理功能
**需要实现：**
- CircleRepository（数据访问层）
- CircleService（业务逻辑层）
- Circle API 端点
  - 创建圈子
  - 查询圈子列表
  - 圈子详情
  - 更新圈子
  - 圈子审核（管理员）
  - 管理员权限分配

#### 任务 4.4：实现帖子发布功能
**需要实现：**
- PostRepository（MongoDB 操作）
- PostService（业务逻辑）
- 集成内容审核引擎
- Post API 端点
  - 创建帖子
  - 草稿保存
  - 匿名发布
  - 多种帖子类型（图文、视频、投票、悬赏）

#### 任务 4.6：实现帖子互动功能
**需要实现：**
- InteractionService
- Comment API 端点
  - 点赞/取消点赞
  - 发布评论
  - 楼中楼回复
  - 转发、收藏、分享

#### 任务 4.7：实现帖子列表与排序
**需要实现：**
- 帖子列表查询
- 排序算法（最新、热门、精华）
- 分页加载
- 帖子详情

#### 任务 4.8：实现内容推荐系统（基础版）
**需要实现：**
- RecommendationService
- 基于标签的内容匹配
- 热门内容推荐
- 同校区/专业内容优先

## 数据模型设计

### MySQL 表

#### schools 表
```sql
CREATE TABLE schools (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL,
  short_name VARCHAR(50),
  province VARCHAR(50),
  city VARCHAR(50),
  logo VARCHAR(255),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### circles 表
```sql
CREATE TABLE circles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  school_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  icon VARCHAR(255),
  type ENUM('official', 'custom') NOT NULL,
  creator_id BIGINT,
  admin_ids JSON,
  member_count INT DEFAULT 0,
  post_count INT DEFAULT 0,
  status ENUM('active', 'archived') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (school_id) REFERENCES schools(id),
  FOREIGN KEY (creator_id) REFERENCES users(id),
  INDEX idx_school_id (school_id),
  INDEX idx_type (type),
  INDEX idx_status (status)
);
```

### MongoDB 文档

#### posts 集合
```javascript
{
  _id: ObjectId,
  post_id: Long,
  school_id: Long,
  circle_id: Long,
  author_id: Long,
  title: String,
  content: String,
  type: String, // "text", "image", "video", "poll", "question"
  images: [String],
  videos: [String],
  poll_options: [{
    option: String,
    vote_count: Number,
    voters: [Long]
  }],
  tags: [String],
  is_anonymous: Boolean,
  view_count: Number,
  like_count: Number,
  comment_count: Number,
  share_count: Number,
  collect_count: Number,
  status: String, // "pending", "approved", "rejected", "deleted"
  audit_result: {
    passed: Boolean,
    reason: String,
    keywords: [String]
  },
  is_pinned: Boolean,
  is_featured: Boolean,
  created_at: Date,
  updated_at: Date
}
```

#### comments 集合
```javascript
{
  _id: ObjectId,
  comment_id: Long,
  post_id: Long,
  author_id: Long,
  content: String,
  parent_id: Long,
  reply_to_user_id: Long,
  like_count: Number,
  is_anonymous: Boolean,
  status: String,
  created_at: Date
}
```

## API 设计（规划）

### 圈子管理

```
GET    /api/v1/circles                获取圈子列表
POST   /api/v1/circles                创建圈子
GET    /api/v1/circles/{id}           获取圈子详情
PUT    /api/v1/circles/{id}           更新圈子
DELETE /api/v1/circles/{id}           删除圈子
POST   /api/v1/circles/{id}/join      加入圈子
POST   /api/v1/circles/{id}/leave     退出圈子
GET    /api/v1/circles/{id}/members   获取成员列表
POST   /api/v1/circles/{id}/admins    添加管理员
```

### 帖子管理

```
GET    /api/v1/posts                  获取帖子列表
POST   /api/v1/posts                  创建帖子
GET    /api/v1/posts/{id}             获取帖子详情
PUT    /api/v1/posts/{id}             更新帖子
DELETE /api/v1/posts/{id}             删除帖子
POST   /api/v1/posts/{id}/like        点赞
DELETE /api/v1/posts/{id}/like        取消点赞
POST   /api/v1/posts/{id}/collect     收藏
POST   /api/v1/posts/{id}/share       分享
GET    /api/v1/posts/{id}/comments    获取评论列表
POST   /api/v1/posts/{id}/comments    发布评论
```

### 评论管理

```
GET    /api/v1/comments/{id}          获取评论详情
PUT    /api/v1/comments/{id}          更新评论
DELETE /api/v1/comments/{id}          删除评论
POST   /api/v1/comments/{id}/like     点赞评论
POST   /api/v1/comments/{id}/reply    回复评论
```

### 推荐系统

```
GET    /api/v1/recommendations/posts  获取推荐帖子
GET    /api/v1/recommendations/circles 获取推荐圈子
GET    /api/v1/recommendations/users  获取推荐用户
```

## 实现建议

### 1. 优先级排序

**高优先级（MVP 必需）：**
1. 圈子基础 CRUD
2. 帖子发布（文本、图片）
3. 帖子列表和详情
4. 基础互动（点赞、评论）

**中优先级：**
1. 匿名发布
2. 投票帖子
3. 帖子排序算法
4. 圈子管理员功能

**低优先级（可后续迭代）：**
1. 视频帖子
2. 悬赏提问
3. 高级推荐算法
4. 内容标签系统

### 2. 技术要点

**MongoDB 使用：**
- 使用 Motor 异步驱动
- 帖子和评论存储在 MongoDB
- 利用 MongoDB 的灵活 schema
- 建立合适的索引优化查询

**缓存策略：**
- 热门帖子缓存（Redis）
- 用户互动状态缓存
- 圈子信息缓存

**性能优化：**
- 帖子列表分页加载
- 评论懒加载
- 图片 CDN 加速
- 计数器异步更新

### 3. 与审核系统集成

**帖子发布流程：**
```
用户提交 → 内容审核 → 审核通过 → 发布到圈子
                    ↓
                审核失败 → 返回错误
                    ↓
                需要人工审核 → 进入审核队列
```

**集成点：**
- 在 PostService 中调用 ContentAuditEngine
- 根据审核结果设置帖子状态
- 记录审核结果到 audit_result 字段

### 4. 权限控制

**帖子操作权限：**
- 发布：需要认证用户
- 编辑/删除：作者或管理员
- 置顶/精华：圈子管理员
- 审核：平台管理员

**圈子操作权限：**
- 创建：认证用户
- 管理：圈子管理员
- 审核：平台管理员

## 开发步骤建议

### 阶段 1：基础功能（2-3天）
1. 实现 CircleRepository 和 CircleService
2. 实现圈子 CRUD API
3. 实现 PostRepository（MongoDB）
4. 实现帖子发布 API（文本）
5. 集成内容审核

### 阶段 2：互动功能（1-2天）
1. 实现 InteractionService
2. 实现点赞、评论 API
3. 实现评论列表和回复
4. 实现计数器更新

### 阶段 3：列表和排序（1天）
1. 实现帖子列表查询
2. 实现排序算法
3. 实现分页加载
4. 优化查询性能

### 阶段 4：推荐系统（1-2天）
1. 实现基础推荐算法
2. 实现推荐 API
3. 添加缓存优化

## 测试建议

### 单元测试
- CircleService 测试
- PostService 测试
- InteractionService 测试
- 推荐算法测试

### 集成测试
- 帖子发布完整流程
- 审核集成测试
- 互动功能测试

### 性能测试
- 帖子列表查询性能
- 并发点赞测试
- MongoDB 查询优化

## 相关需求

- 需求 5.1-5.9: 圈子与帖子功能
- 需求 6.1-6.8: 帖子互动与推荐

## 文件结构（规划）

```
app/
├── models/
│   ├── circle.py          ✅ 已完成
│   └── post.py            ✅ 已完成
├── repositories/
│   ├── circle.py          ⏳ 待实现
│   └── post.py            ⏳ 待实现
├── services/
│   ├── circle.py          ⏳ 待实现
│   ├── post.py            ⏳ 待实现
│   ├── interaction.py     ⏳ 待实现
│   └── recommendation.py  ⏳ 待实现
├── schemas/
│   ├── circle.py          ⏳ 待实现
│   └── post.py            ⏳ 待实现
└── api/v1/endpoints/
    ├── circles.py         ⏳ 待实现
    ├── posts.py           ⏳ 待实现
    └── comments.py        ⏳ 待实现

alembic/versions/
└── 004_create_circles_and_schools_tables.py  ✅ 已完成
```

## 注意事项

1. **数据一致性**：MySQL 和 MongoDB 之间的数据同步
2. **性能优化**：合理使用索引和缓存
3. **安全性**：防止 XSS、注入攻击
4. **匿名发布**：保护用户隐私但保留追溯能力
5. **内容审核**：所有用户生成内容必须经过审核

## 下一步

第四部分的数据模型已完成，建议按照以下顺序继续开发：

1. ✅ 实现圈子管理功能（任务 4.2）
2. ✅ 实现帖子发布功能（任务 4.4）
3. ✅ 实现帖子互动功能（任务 4.6）
4. ✅ 实现帖子列表与排序（任务 4.7）
5. ✅ 实现内容推荐系统（任务 4.8）

由于第四部分工作量较大，建议分阶段实现，先完成核心功能，再逐步完善。
