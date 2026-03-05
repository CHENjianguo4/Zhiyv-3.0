"""图片视频处理工具

提供图片压缩、视频检查等功能
"""

import os
import uuid
from typing import Tuple, Optional
from PIL import Image
from io import BytesIO

class MediaProcessor:
    """媒体处理工具类"""

    @staticmethod
    def compress_image(
        image_data: bytes,
        max_size: int = 1024 * 1024,  # 1MB
        quality: int = 85
    ) -> Tuple[bytes, str]:
        """压缩图片"""
        img = Image.open(BytesIO(image_data))
        
        # 转换格式为RGB（去除透明通道，便于压缩）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality)
        compressed_data = output.getvalue()
        
        # 如果仍然超过大小，降低质量递归压缩
        if len(compressed_data) > max_size and quality > 10:
            return MediaProcessor.compress_image(image_data, max_size, quality - 10)
            
        return compressed_data, "jpeg"

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """生成唯一文件名"""
        ext = os.path.splitext(original_filename)[1].lower()
        return f"{uuid.uuid4().hex}{ext}"

    @staticmethod
    def check_video_constraints(
        file_size: int,
        duration: Optional[int] = None,
        max_size: int = 50 * 1024 * 1024,  # 50MB
        max_duration: int = 60  # 60秒
    ) -> bool:
        """检查视频约束"""
        if file_size > max_size:
            return False
        if duration and duration > max_duration:
            return False
        return True
