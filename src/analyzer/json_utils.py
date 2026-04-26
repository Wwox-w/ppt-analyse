"""JSON 解析工具函数"""

import json
import re


def clean_json_string(json_str: str) -> str:
    """清理 JSON 字符串中的常见格式问题"""
    # 替换中文智能引号为标准英文引号
    json_str = json_str.replace('\u201c', '"').replace('\u201d', '"')
    json_str = json_str.replace('\u2018', "'").replace('\u2019', "'")
    # 替换中文逗号为英文逗号
    json_str = json_str.replace('，', ',')
    # 替换中文冒号为英文冒号
    json_str = json_str.replace('：', ':')
    return json_str


def extract_json_from_response(response: str) -> str:
    """从 LLM 响应中提取 JSON 字符串"""
    # 尝试提取 markdown 代码块中的 JSON
    if "```json" in response:
        json_str = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response:
        json_str = response.split("```")[1].split("```")[0].strip()
    else:
        # 尝试直接找到 JSON 对象
        json_str = response.strip()
        # 如果响应以 { 开头，直接使用
        if json_str.startswith("{"):
            pass
        # 否则尝试查找第一个 { 到最后一个 }
        elif "{" in json_str:
            start = json_str.index("{")
            end = json_str.rindex("}") + 1
            json_str = json_str[start:end]
    
    return clean_json_string(json_str)


def _repair_json_string(json_str: str) -> str:
    """修复 JSON 字符串中的常见格式问题
    
    LLM 有时会在 JSON 字符串值中包含未转义的双引号（如 "存储程序"），
    这会导致 json.loads 解析失败。此函数尝试修复这类问题。
    """
    result = []
    i = 0
    in_string = False
    string_char = None
    escape_next = False
    
    while i < len(json_str):
        c = json_str[i]
        
        if escape_next:
            result.append(c)
            escape_next = False
            i += 1
            continue
        
        if c == '\\':
            result.append(c)
            escape_next = True
            i += 1
            continue
        
        if c in '"\'':
            if not in_string:
                in_string = True
                string_char = c
                result.append(c)
            elif c == string_char:
                # 检查这个引号是否真的是字符串结束
                # 如果后面跟着结构字符（,:}] 或空白+结构字符），则是结束
                rest = json_str[i+1:].lstrip()
                if rest and rest[0] in ',:}]':
                    in_string = False
                    result.append(c)
                else:
                    # 这是字符串内部的未转义引号，转义它
                    result.append('\\"')
            else:
                result.append(c)
        else:
            result.append(c)
        
        i += 1
    
    return ''.join(result)


def parse_json_response(response: str):
    """解析 LLM 返回的 JSON 响应"""
    json_str = extract_json_from_response(response)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 尝试修复后重新解析
        repaired = _repair_json_string(json_str)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            # 最后尝试：使用更激进的修复
            # 替换所有字符串值中的未转义引号
            repaired = re.sub(
                r'(?<=[：:])\s*"([^"]*?)"([^"]*?)"(?=[^"]*?"\s*[,}\]])',
                r'"\1\\"\2\\""',
                json_str
            )
            return json.loads(repaired)
