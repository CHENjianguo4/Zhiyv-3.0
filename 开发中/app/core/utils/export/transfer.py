"""数据导入导出工具

提供CSV/Excel文件的导入导出功能
"""

import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataTransfer:
    """数据转换工具类"""

    @staticmethod
    def export_csv(headers: List[str], data: List[Dict[str, Any]]) -> str:
        """导出为CSV字符串"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        
        writer.writeheader()
        for row in data:
            # 处理特殊类型
            processed_row = {}
            for k, v in row.items():
                if isinstance(v, datetime):
                    processed_row[k] = v.strftime("%Y-%m-%d %H:%M:%S")
                elif v is None:
                    processed_row[k] = ""
                else:
                    processed_row[k] = str(v)
            writer.writerow(processed_row)
            
        return output.getvalue()

    @staticmethod
    def import_csv(content: str) -> List[Dict[str, str]]:
        """从CSV字符串导入"""
        input_file = io.StringIO(content)
        reader = csv.DictReader(input_file)
        return list(reader)
