"""隐私信息脱敏工具

提供学号、手机号、身份证号等敏感信息的脱敏处理函数
"""

import re
from typing import Optional


def mask_student_id(student_id: Optional[str]) -> Optional[str]:
    """脱敏学号
    
    格式：保留前3位和后3-4位，中间用****替换
    示例：2021001234 -> 202****234
    
    Args:
        student_id: 原始学号
        
    Returns:
        Optional[str]: 脱敏后的学号，如果输入为None则返回None
    """
    if not student_id:
        return None
    
    # 如果学号长度小于7，不进行脱敏（避免信息过少）
    if len(student_id) < 7:
        return student_id
    
    # 保留前3位和后3-4位
    if len(student_id) <= 10:
        # 短学号：前3位 + **** + 后3位
        return f"{student_id[:3]}****{student_id[-3:]}"
    else:
        # 长学号：前3位 + **** + 后4位
        return f"{student_id[:3]}****{student_id[-4:]}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """脱敏手机号
    
    格式：保留前3位和后4位，中间用****替换
    示例：13812345678 -> 138****5678
    
    Args:
        phone: 原始手机号
        
    Returns:
        Optional[str]: 脱敏后的手机号，如果输入为None则返回None
    """
    if not phone:
        return None
    
    # 移除所有非数字字符
    phone_digits = re.sub(r'\D', '', phone)
    
    # 如果不是11位手机号，不进行脱敏
    if len(phone_digits) != 11:
        return phone
    
    # 保留前3位和后4位
    return f"{phone_digits[:3]}****{phone_digits[-4:]}"


def mask_id_card(id_card: Optional[str]) -> Optional[str]:
    """脱敏身份证号
    
    格式：保留前6位和后4位，中间用********替换
    示例：110101199001011234 -> 110101********1234
    
    Args:
        id_card: 原始身份证号
        
    Returns:
        Optional[str]: 脱敏后的身份证号，如果输入为None则返回None
    """
    if not id_card:
        return None
    
    # 移除所有非字母数字字符
    id_card_clean = re.sub(r'[^0-9Xx]', '', id_card)
    
    # 如果不是15位或18位身份证号，不进行脱敏
    if len(id_card_clean) not in [15, 18]:
        return id_card
    
    # 保留前6位和后4位
    return f"{id_card_clean[:6]}********{id_card_clean[-4:]}"


def mask_email(email: Optional[str]) -> Optional[str]:
    """脱敏邮箱地址
    
    格式：保留邮箱用户名的第一个字符和@后的域名，中间用***替换
    示例：zhangsan@university.edu.cn -> z***@university.edu.cn
    
    Args:
        email: 原始邮箱地址
        
    Returns:
        Optional[str]: 脱敏后的邮箱地址，如果输入为None则返回None
    """
    if not email:
        return None
    
    # 检查邮箱格式
    if '@' not in email:
        return email
    
    parts = email.split('@')
    if len(parts) != 2:
        return email
    
    username, domain = parts
    
    # 如果用户名太短，只保留第一个字符
    if len(username) <= 1:
        return f"{username}***@{domain}"
    
    # 保留第一个字符和最后一个字符
    if len(username) == 2:
        return f"{username[0]}***@{domain}"
    
    return f"{username[0]}***{username[-1]}@{domain}"


def mask_real_name(real_name: Optional[str]) -> Optional[str]:
    """脱敏真实姓名
    
    格式：保留姓氏，名字用*替换
    示例：张三 -> 张*
          欧阳修 -> 欧阳*
    
    Args:
        real_name: 原始姓名
        
    Returns:
        Optional[str]: 脱敏后的姓名，如果输入为None则返回None
    """
    if not real_name:
        return None
    
    # 移除空格
    name = real_name.strip()
    
    if len(name) <= 1:
        return name
    
    # 中文姓名处理
    # 常见复姓列表
    compound_surnames = [
        '欧阳', '太史', '端木', '上官', '司马', '东方', '独孤', '南宫',
        '万俟', '闻人', '夏侯', '诸葛', '尉迟', '公羊', '赫连', '澹台',
        '皇甫', '宗政', '濮阳', '公冶', '太叔', '申屠', '公孙', '慕容',
        '仲孙', '钟离', '长孙', '宇文', '司徒', '鲜于', '司空', '闾丘',
        '子车', '亓官', '司寇', '巫马', '公西', '颛孙', '壤驷', '公良',
        '漆雕', '乐正', '宰父', '谷梁', '拓跋', '夹谷', '轩辕', '令狐',
        '段干', '百里', '呼延', '东郭', '南门', '羊舌', '微生', '公户',
        '公玉', '公仪', '梁丘', '公仲', '公上', '公门', '公山', '公坚',
    ]
    
    # 检查是否是复姓
    for surname in compound_surnames:
        if name.startswith(surname):
            return f"{surname}*"
    
    # 单姓处理：保留第一个字符
    return f"{name[0]}*"
