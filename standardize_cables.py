#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电缆型号标准化工具 (v2.0 - 严格固化版)
基于 GB/T 19666, GB/T 12706, GB/T 9330 等标准
"""

import re
import sys

# ================= 配置区域：硬编码规则 =================

# 1. 电压等级白名单 (强制覆盖输入中的错误电压)
STANDARD_VOLTAGE_MAP = {
    'YJV': '0.6/1kV',
    'YJV22': '0.6/1kV',
    'YJV32': '0.6/1kV',
    'YJY': '0.6/1kV',
    'WDZ-YJY': '0.6/1kV',
    'WDZC-YJY': '0.6/1kV',
    'WDZB-YJY': '0.6/1kV',
    'WDZA-YJY': '0.6/1kV',
    'VV': '0.6/1kV',
    'KVV': '450/750V',
    'KVVP': '450/750V',
    'KVV22': '450/750V',
    'RVV': '300/500V',
    'RVVP': '300/300V',
    'RVSP': '300/300V',
    'RVS': '300/300V',
    'RVB': '300/300V',
    'BV': '450/750V',
    'BVR': '450/750V',
    'BYJ': '450/750V',
    'WDZ-BYJ': '450/750V',
    'N-BV': '450/750V',
    'N-BVR': '450/750V',
    'N-RVS': '300/300V',
    'ZCN-RVS': '300/300V',
    'ZC-RVS': '300/300V',
}

# 2. 前缀映射规则 (严禁降级)
PREFIX_MAP = {
    'ZR': 'ZC',
    'ZRA': 'ZA',
    'ZRB': 'ZB',
    'ZRC': 'ZC',
    'NH': 'N',
    'NHBV': 'N-BV', # 特殊处理连写
    'NHYJV': 'N-YJV',
    'ZN': 'ZCN', # 阻燃+耐火 -> ZCN
    'NZ': 'ZCN', # 错误写法修正
    'ZRNH': 'ZCN',
    'ZRN': 'ZCN',
    'DZC': '', # DZC 可能是笔误或特定前缀，暂按空处理或保留？这里按去除处理，因为标准中无DZC，通常是WDZC漏了W
}

# 3. 需要补全 WDZ 前缀的型号
WDZ_REQUIRED_MODELS = ['BYJ']

# ================= 核心逻辑函数 =================

def clean_text(text):
    """清洗无关文本，提取核心型号串"""
    # 移除中英文描述，只保留类似型号的部分
    # 简单策略：提取包含字母、数字、x, *, -, /, + 的连续串
    # 更好的策略：针对本案例，移除 "including...", "包括..." 等
    text = re.sub(r'\s*including.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*包括.*$', '', text)
    text = text.strip()
    return text

def normalize_prefix(model_str):
    """标准化前缀 (阻燃/耐火)"""
    original = model_str
    
    # 处理 WDZ(B1) / WDZ(B2) 特殊情况 -> 保留 B1/B2
    b_match = re.match(r'WDZ\(B([12])\)-?', model_str)
    if b_match:
        level = b_match.group(1)
        rest = model_str[b_match.end():]
        return f"WDZ-B{level}-{rest}"

    # 处理常规前缀映射
    for old, new in PREFIX_MAP.items():
        if model_str.startswith(old + '-') or model_str.startswith(old):
            # 精确匹配前缀
            if model_str.startswith(old + '-'):
                suffix = model_str[len(old)+1:]
            else:
                # 检查是否是连写 (如 NHBV)
                if model_str.startswith(old) and len(model_str) > len(old) and model_str[len(old)].isalpha():
                     suffix = model_str[len(old):]
                else:
                    continue
            
            if new == '': 
                # 空映射 (如 DZC->空)
                return suffix
            elif '-' in new or new.endswith('V'): 
                # 新前缀自带连字符或完整前缀 (如 N-BV)
                # 如果 suffix 已经是 BV，则避免 N-BV-BV
                if suffix.startswith(new.split('-')[-1]) and '-' in new:
                     return new + suffix[len(new.split('-')[-1]):]
                return new + '-' + suffix if '-' not in new else new + suffix
            else:
                return new + '-' + suffix
                
    return model_str

def unify_format(model_str):
    """统一格式符号"""
    # 乘号统一
    s = re.sub(r'[xX×*]', '×', model_str)
    # 移除空格
    s = s.replace(' ', '')
    # 移除 mm2, mm²
    s = re.sub(r'mm[2²]?', '', s)
    # 处理连字符重复
    s = re.sub(r'-+', '-', s)
    return s

def extract_base_model(model_str):
    """提取基础型号用于查电压表"""
    # 尝试匹配 YJV, KVV, BV 等
    match = re.match(r'^([A-Z]+(?:-[A-Z]+)?)', model_str)
    if match:
        base = match.group(1)
        # 特殊处理 WDZC-YJY -> 查 YJY 或 WDZC-YJY
        if base in STANDARD_VOLTAGE_MAP:
            return base
        # 尝试去掉前缀查
        if '-' in base:
            parts = base.split('-')
            for i in range(len(parts)):
                sub = '-'.join(parts[i:])
                if sub in STANDARD_VOLTAGE_MAP:
                    return sub
    return None

def add_voltage(model_str):
    """注入标准电压等级"""
    base = extract_base_model(model_str)
    if base and base in STANDARD_VOLTAGE_MAP:
        voltage = STANDARD_VOLTAGE_MAP[base]
        # 检查是否已有电压
        if re.search(r'\d+/\d+', model_str):
            return model_str # 已有电压，不覆盖 (理论上不会发生，因为前面清洗了)
        
        # 插入电压位置：型号后，规格前
        # 格式：PREFIX-MODEL-VOLTAGE-SPEC
        # 找到第一个数字出现的位置
        match = re.search(r'(\d+)', model_str)
        if match:
            idx = match.start()
            # 在数字前插入 -电压-
            # 需确保前面有连字符
            prefix_part = model_str[:idx]
            spec_part = model_str[idx:]
            if not prefix_part.endswith('-'):
                prefix_part += '-'
            return f"{prefix_part}{voltage}-{spec_part}"
    return model_str

def check_neutral_pe(model_str):
    """简单的中性线/地线校验 (仅提示)"""
    # 解析芯数结构
    match = re.search(r'(\d+)×(\d+)(?:\+(\d+)×(\d+))?', model_str)
    if match:
        main_cores = int(match.group(1))
        main_sec = float(match.group(2))
        if match.group(3):
            n_sec = float(match.group(4))
            # 规则：S<=16 -> N=S; 16<S<=35 -> N>=16; S>35 -> N>=S/2
            required_n = 16
            if main_sec <= 16:
                required_n = main_sec
            elif main_sec > 35:
                required_n = main_sec * 0.5
            
            if n_sec < required_n:
                return f"⚠️ 警告：{model_str} 中性线/地线({n_sec})可能偏小 (建议≥{required_n})"
    return ""

def standardize(raw_line):
    """主处理流程"""
    # 1. 清洗
    cleaned = clean_text(raw_line)
    if not cleaned:
        return None
    
    # 2. 预处理前缀 (处理 DZC->WDZC 这种可能的笔误)
    if cleaned.startswith('DZC-'):
        cleaned = 'WDZC-' + cleaned[4:]
    
    # 3. 标准化前缀
    normalized = normalize_prefix(cleaned)
    
    # 4. 统一格式
    formatted = unify_format(normalized)
    
    # 5. 补全 BYJ -> WDZ-BYJ
    for model in WDZ_REQUIRED_MODELS:
        if formatted.startswith(model + '-') or formatted == model:
             if not formatted.startswith('WDZ-'):
                 formatted = 'WDZ-' + formatted
                 break
    
    # 6. 注入电压
    final_model = add_voltage(formatted)
    
    # 7. 校验
    warning = check_neutral_pe(final_model)
    
    result = final_model
    if warning:
        result += f" {warning}"
        
    return result

if __name__ == '__main__':
    # 测试数据
    test_data = [
        "DZC-YJY-4x2.5 including wiring...",
        "WDZC-YJY-4*25+1*16, including...",
        "WDZC-YJY-5x6, including...",
        "WDZC-YJY-5x4, including...",
        "WDZC-YJY-5x16, including...",
        "WDZC-YJY-5*4, including...",
        "WDZC-YJY-5x2.5, including...",
        "YJV 4×35+1×16, including...",
        "YJV 4×70+1×35, including...",
        "YJV 4×150+1×70, including...",
        "YJV 4×120+1×70, including...",
        "YJV 4×95+1×50, including...",
        "YJV 4×185+1×95, including...",
        "YJV 4×50+1×25, including...",
        "YJV 5*16, including...",
        "YJV 5×6, including...",
        "YJV 5*4, including...",
        "WDZC-YJY-5x10 including..."
    ]
    
    print(f"{'序号':<5} | {'原始输入 (截取)':<30} | {'标准化型号':<40}")
    print("-" * 85)
    
    for i, line in enumerate(test_data, 1):
        res = standardize(line)
        short_raw = line[:28] + "..." if len(line) > 30 else line
        if res:
            # 分离警告信息
            if "⚠️" in res:
                model, warn = res.split(" ⚠️")
                print(f"{i:<5} | {short_raw:<30} | {model:<40} {warn}")
            else:
                print(f"{i:<5} | {short_raw:<30} | {res:<40}")
