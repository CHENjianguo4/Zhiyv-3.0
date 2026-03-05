"""应用启动脚本

用于本地开发环境启动应用
"""

import uvicorn

from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
