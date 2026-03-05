-- MySQL初始化脚本
-- 创建数据库并设置字符集

-- 确保使用utf8mb4字符集
ALTER DATABASE zhiyu CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 创建测试数据库
CREATE DATABASE IF NOT EXISTS zhiyu_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 授予权限
GRANT ALL PRIVILEGES ON zhiyu.* TO 'zhiyu'@'%';
GRANT ALL PRIVILEGES ON zhiyu_test.* TO 'zhiyu'@'%';
FLUSH PRIVILEGES;

-- 显示数据库
SHOW DATABASES;
