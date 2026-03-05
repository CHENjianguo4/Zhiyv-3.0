# 知域平台开发环境启动脚本
# 用于 Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  知域校园互动社交平台 - 开发环境启动  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否运行
Write-Host "[1/5] 检查 Docker 状态..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker 未安装或未运行" -ForegroundColor Red
        Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Docker 已就绪: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装或未运行" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# 检查 Python 是否安装
Write-Host ""
Write-Host "[2/5] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python 未安装" -ForegroundColor Red
        Write-Host "请先安装 Python 3.11+: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 未安装" -ForegroundColor Red
    exit 1
}

# 启动数据库容器
Write-Host ""
Write-Host "[3/5] 启动数据库服务..." -ForegroundColor Yellow
Write-Host "正在启动 MySQL 和 Redis 容器..." -ForegroundColor Gray

docker compose up -d mysql redis 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据库容器启动成功" -ForegroundColor Green
    
    # 等待数据库就绪
    Write-Host "等待数据库初始化（约 30 秒）..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    $maxRetries = 12
    $retryCount = 0
    $dbReady = $false
    
    while ($retryCount -lt $maxRetries -and -not $dbReady) {
        $retryCount++
        Write-Host "检查数据库状态... ($retryCount/$maxRetries)" -ForegroundColor Gray
        
        $result = docker compose exec -T mysql mysqladmin ping -h localhost -uzhiyu -pzhiyu_password 2>&1
        if ($result -match "mysqld is alive") {
            $dbReady = $true
            Write-Host "✅ 数据库已就绪" -ForegroundColor Green
        } else {
            Start-Sleep -Seconds 3
        }
    }
    
    if (-not $dbReady) {
        Write-Host "⚠️  数据库启动超时，但将继续..." -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ 数据库容器启动失败" -ForegroundColor Red
    Write-Host "请检查 Docker Desktop 是否正在运行" -ForegroundColor Yellow
    exit 1
}

# 运行数据库迁移
Write-Host ""
Write-Host "[4/5] 运行数据库迁移..." -ForegroundColor Yellow

# 检查虚拟环境
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "激活虚拟环境..." -ForegroundColor Gray
    & "venv\Scripts\Activate.ps1"
}

$migrationResult = alembic upgrade head 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据库迁移完成" -ForegroundColor Green
} else {
    Write-Host "⚠️  数据库迁移失败，可能已经是最新版本" -ForegroundColor Yellow
    Write-Host $migrationResult -ForegroundColor Gray
}

# 启动开发服务器
Write-Host ""
Write-Host "[5/5] 启动开发服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🚀 服务器启动中...                    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 API 文档地址：" -ForegroundColor Green
Write-Host "   Swagger UI: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   ReDoc:      http://localhost:8000/redoc" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示：按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

python run.py
