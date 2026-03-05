"""测试隐私信息脱敏工具

测试学号、手机号、身份证号、邮箱、姓名等敏感信息的脱敏功能
"""

import pytest

from app.utils.masking import (
    mask_email,
    mask_id_card,
    mask_phone,
    mask_real_name,
    mask_student_id,
)


class TestMaskStudentId:
    """测试学号脱敏"""

    def test_mask_normal_student_id(self):
        """测试正常学号脱敏"""
        # 10位学号
        assert mask_student_id("2021001234") == "202****234"
        
        # 11位学号
        assert mask_student_id("20210012345") == "202****2345"
        
        # 12位学号
        assert mask_student_id("202100123456") == "202****3456"

    def test_mask_short_student_id(self):
        """测试短学号（不脱敏）"""
        # 少于7位的学号不脱敏
        assert mask_student_id("123456") == "123456"
        assert mask_student_id("12345") == "12345"

    def test_mask_none_student_id(self):
        """测试None值"""
        assert mask_student_id(None) is None

    def test_mask_empty_student_id(self):
        """测试空字符串"""
        assert mask_student_id("") is None

    def test_mask_various_lengths(self):
        """测试不同长度的学号"""
        # 7位学号
        assert mask_student_id("2021001") == "202****001"
        
        # 8位学号
        assert mask_student_id("20210012") == "202****012"
        
        # 9位学号
        assert mask_student_id("202100123") == "202****123"


class TestMaskPhone:
    """测试手机号脱敏"""

    def test_mask_normal_phone(self):
        """测试正常手机号脱敏"""
        assert mask_phone("13812345678") == "138****5678"
        assert mask_phone("15912345678") == "159****5678"
        assert mask_phone("18612345678") == "186****5678"

    def test_mask_phone_with_spaces(self):
        """测试带空格的手机号"""
        assert mask_phone("138 1234 5678") == "138****5678"
        assert mask_phone("138-1234-5678") == "138****5678"

    def test_mask_phone_with_country_code(self):
        """测试带国家代码的手机号"""
        # 带+86的手机号，移除非数字字符后应该是13位，不是11位，所以不脱敏
        assert mask_phone("+8613812345678") == "+8613812345678"

    def test_mask_invalid_phone(self):
        """测试无效手机号（不脱敏）"""
        # 不是11位的号码不脱敏
        assert mask_phone("12345") == "12345"
        assert mask_phone("123456789012") == "123456789012"

    def test_mask_none_phone(self):
        """测试None值"""
        assert mask_phone(None) is None

    def test_mask_empty_phone(self):
        """测试空字符串"""
        assert mask_phone("") is None


class TestMaskIdCard:
    """测试身份证号脱敏"""

    def test_mask_18_digit_id_card(self):
        """测试18位身份证号脱敏"""
        assert mask_id_card("110101199001011234") == "110101********1234"
        assert mask_id_card("31010519900101123X") == "310105********123X"

    def test_mask_15_digit_id_card(self):
        """测试15位身份证号脱敏"""
        assert mask_id_card("110101900101123") == "110101********1123"

    def test_mask_id_card_with_spaces(self):
        """测试带空格的身份证号"""
        assert mask_id_card("110101 1990 0101 1234") == "110101********1234"

    def test_mask_invalid_id_card(self):
        """测试无效身份证号（不脱敏）"""
        # 不是15位或18位的不脱敏
        assert mask_id_card("12345") == "12345"
        assert mask_id_card("1234567890123456789") == "1234567890123456789"

    def test_mask_none_id_card(self):
        """测试None值"""
        assert mask_id_card(None) is None

    def test_mask_empty_id_card(self):
        """测试空字符串"""
        assert mask_id_card("") is None


class TestMaskEmail:
    """测试邮箱脱敏"""

    def test_mask_normal_email(self):
        """测试正常邮箱脱敏"""
        assert mask_email("zhangsan@university.edu.cn") == "z***n@university.edu.cn"
        assert mask_email("test@example.com") == "t***t@example.com"

    def test_mask_short_username_email(self):
        """测试短用户名邮箱"""
        # 单字符用户名
        assert mask_email("a@example.com") == "a***@example.com"
        
        # 双字符用户名
        assert mask_email("ab@example.com") == "a***@example.com"

    def test_mask_long_username_email(self):
        """测试长用户名邮箱"""
        assert mask_email("verylongusername@example.com") == "v***e@example.com"

    def test_mask_invalid_email(self):
        """测试无效邮箱（不脱敏）"""
        # 没有@符号
        assert mask_email("notanemail") == "notanemail"
        
        # 多个@符号
        assert mask_email("test@@example.com") == "test@@example.com"

    def test_mask_none_email(self):
        """测试None值"""
        assert mask_email(None) is None

    def test_mask_empty_email(self):
        """测试空字符串"""
        assert mask_email("") is None


class TestMaskRealName:
    """测试真实姓名脱敏"""

    def test_mask_single_surname(self):
        """测试单姓脱敏"""
        assert mask_real_name("张三") == "张*"
        assert mask_real_name("李四") == "李*"
        assert mask_real_name("王五") == "王*"

    def test_mask_compound_surname(self):
        """测试复姓脱敏"""
        assert mask_real_name("欧阳修") == "欧阳*"
        assert mask_real_name("司马懿") == "司马*"
        assert mask_real_name("诸葛亮") == "诸葛*"
        assert mask_real_name("上官婉儿") == "上官*"

    def test_mask_single_character_name(self):
        """测试单字名（不脱敏）"""
        assert mask_real_name("李") == "李"

    def test_mask_name_with_spaces(self):
        """测试带空格的姓名"""
        assert mask_real_name(" 张三 ") == "张*"
        assert mask_real_name("  欧阳修  ") == "欧阳*"

    def test_mask_none_name(self):
        """测试None值"""
        assert mask_real_name(None) is None

    def test_mask_empty_name(self):
        """测试空字符串"""
        assert mask_real_name("") is None


class TestMaskingIntegration:
    """集成测试：测试脱敏功能的整体效果"""

    def test_mask_all_privacy_fields(self):
        """测试所有隐私字段的脱敏"""
        # 模拟用户数据
        user_data = {
            "student_id": "2021001234",
            "phone": "13812345678",
            "id_card": "110101199001011234",
            "email": "zhangsan@university.edu.cn",
            "real_name": "张三",
        }

        # 应用脱敏
        masked_data = {
            "student_id": mask_student_id(user_data["student_id"]),
            "phone": mask_phone(user_data["phone"]),
            "id_card": mask_id_card(user_data["id_card"]),
            "email": mask_email(user_data["email"]),
            "real_name": mask_real_name(user_data["real_name"]),
        }

        # 验证脱敏结果
        assert masked_data["student_id"] == "202****234"
        assert masked_data["phone"] == "138****5678"
        assert masked_data["id_card"] == "110101********1234"
        assert masked_data["email"] == "z***n@university.edu.cn"
        assert masked_data["real_name"] == "张*"

        # 验证脱敏后的数据不等于原始数据
        assert masked_data["student_id"] != user_data["student_id"]
        assert masked_data["phone"] != user_data["phone"]
        assert masked_data["id_card"] != user_data["id_card"]
        assert masked_data["email"] != user_data["email"]
        assert masked_data["real_name"] != user_data["real_name"]

    def test_mask_preserves_format(self):
        """测试脱敏保持格式"""
        # 学号格式
        masked_student_id = mask_student_id("2021001234")
        assert len(masked_student_id) == 10  # 长度不变
        assert masked_student_id.startswith("202")  # 前缀保留
        assert masked_student_id.endswith("234")  # 后缀保留
        assert "****" in masked_student_id  # 包含脱敏标记

        # 手机号格式
        masked_phone = mask_phone("13812345678")
        assert len(masked_phone) == 11  # 长度不变
        assert masked_phone.startswith("138")  # 前缀保留
        assert masked_phone.endswith("5678")  # 后缀保留
        assert "****" in masked_phone  # 包含脱敏标记

    def test_mask_handles_edge_cases(self):
        """测试边界情况"""
        # None值
        assert mask_student_id(None) is None
        assert mask_phone(None) is None
        assert mask_id_card(None) is None
        assert mask_email(None) is None
        assert mask_real_name(None) is None

        # 空字符串
        assert mask_student_id("") is None
        assert mask_phone("") is None
        assert mask_id_card("") is None
        assert mask_email("") is None
        assert mask_real_name("") is None

        # 无效格式（不脱敏）
        assert mask_student_id("123") == "123"
        assert mask_phone("123") == "123"
        assert mask_id_card("123") == "123"
        assert mask_email("invalid") == "invalid"


class TestMaskingReversibility:
    """测试脱敏的不可逆性"""

    def test_masking_is_irreversible(self):
        """测试脱敏后无法还原原始数据"""
        original_student_id = "2021001234"
        masked_student_id = mask_student_id(original_student_id)

        # 脱敏后的数据不应该包含完整的原始数据
        assert masked_student_id != original_student_id

        # 脱敏后的数据应该隐藏了中间部分
        assert "0012" not in masked_student_id

        # 但保留了前后缀用于识别
        assert masked_student_id.startswith("202")
        assert masked_student_id.endswith("234")

    def test_different_inputs_produce_different_outputs(self):
        """测试不同输入产生不同输出"""
        # 相似但不同的学号
        id1 = mask_student_id("2021001234")
        id2 = mask_student_id("2021001235")

        # 脱敏后应该不同（因为后缀不同）
        assert id1 != id2

        # 相似但不同的手机号
        phone1 = mask_phone("13812345678")
        phone2 = mask_phone("13812345679")

        # 脱敏后应该不同（因为后缀不同）
        assert phone1 != phone2
