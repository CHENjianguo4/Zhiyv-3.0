@echo off
REM 知域平台开发环境启动脚本
REM 用于 Windows CMD

echo ========================================
echo   知域校园互动社交平台 - 开发环境启动
echo ========================================
echo.

REM 检查 Docker
echo [1/5] 检查 Docker 状态...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker 未安装或未运行
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [OK] Docker 已就绪
echo.

REM 检查 Python
echo [2/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装
    echo 请先安装 Python 3.11+: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已安装
echo.

REM 启动数据库
echo [3/5] 启动数据库服务...
echo 正在启动 MySQL 和 Redis 容器...
docker compose up -d mysql redis
if errorlevel 1 (
    echo [ERROR] 数据库容器启动失败
    echo 请检查 Docker Desktop 是否正在运行
    pause
    exit /b 1
)
echo [OK] 数据库容器启动成功
echo 等待数据库初始化（约 30 秒）...
timeout /t 30 /nobreak >nul
echo.

REM 运行数据库迁移
echo [4/5] 运行数据库迁移...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
alembic upgrade head
echo [OK] 数据库迁移完成
echo.

REM 启动开发服务器
echo [5/5] 启动开发服务器...
echo.
echo ========================================
echo   服务器启动中...
echo ========================================
echo.
echo API 文档地址：
echo    Swagger UI: http://localhost:8000/docs
echo    ReDoc:      http://localhost:8000/redoc
echo.
echo 提示：按 Ctrl+C 停止服务器
echo.

python run.py
