"""
english_parser.py — 英文电缆型号解析器

将英文描述的电缆型号转换为中国国标格式。
"""

import re
from typing import Optional

CONDUCTOR_MAP = {'CU': '铜', 'AL': '铝'}
INSULATION_MAP = {'XLPE': 'YJ', 'PVC': 'V', 'EPR': 'Y', 'HEPR': 'Y'}
SHEATH_MAP = {'PVC': 'V', 'PE': 'Y', 'FRPVC': 'V', 'LSZH': 'Y'}
ARMOR_MAP = {'DSTA': '22', 'SWA': '32', 'AWA': '33', 'STA': '23'}

def parse_english_model(raw: str) -> Optional[str]:
    s = raw.strip().upper()
    # 清理中文前缀（如"接地线 "、"接地裸铜线 "）
    s = re.sub(r'^接地线\s*', '', s)
    s = re.sub(r'^接地裸铜线\s*', '', s)
    
    spec_match = re.search(r'(\d+(?:[xX×*]\d+(?:\.\d+)?)?(?:\+\d+[xX×*]\d+(?:\.\d+)?)?)(?:MM2)?$', s)
    if not spec_match:
        return None
    
    spec_str = spec_match.group(1)
    s = s[:spec_match.start()].strip()
    
    materials = re.split(r'[/\s]+', s)
    materials = [m.strip() for m in materials if m.strip()]
    
    if not materials:
        return None
    
    conductor = None
    insulation = None
    sheath = None
    armor = None
    is_fire_resistant = False
    has_voltage = False
    voltage_str = '0.6/1kV'
    
    material_role = ['insulation', 'sheath']
    role_index = 0
    
    for mat in materials:
        mat_orig = mat
        mat = mat.strip()
        
        # 检测并提取电压（如 PVCW24KV → PVC + 24KV）
        voltage_match = re.search(r'([Ww]?)\d+(?:\.?\d+)?/?\d*(?:kV|KV)', mat)
        if voltage_match:
            has_voltage = True
            v_full = voltage_match.group(0)
            v_num = re.search(r'(\d+(?:\.?\d+)?/?\d*)kV', v_full, re.IGNORECASE)
            if v_num:
                v_str = v_num.group(1).upper()
                if '24' in v_str or '15' in v_str:
                    voltage_str = '8.7/15kV'
                elif '1' in v_str:
                    voltage_str = '0.6/1kV'
            # 去除电压部分，保留材料
            mat = re.sub(r'[Ww]?\d+(?:\.?\d+)?/?\d*(?:kV|KV)', '', mat)
        
        if not mat:
            continue
        
        if mat == 'CU':
            conductor = '铜'
            continue
        if mat == 'AL':
            conductor = '铝'
            continue
        
        if mat in ('MICA', 'FR'):
            is_fire_resistant = True
            continue
        
        # 特殊情况：FRPVC 应视为 PVC（阻燃 PVC 护套）
        if mat == 'FRPVC':
            mat = 'PVC'
        
        # 绝缘/护套：按顺序分配
        if mat in INSULATION_MAP and role_index < len(material_role):
            role = material_role[role_index]
            if role == 'insulation':
                insulation = INSULATION_MAP[mat]
            elif role == 'sheath':
                sheath = SHEATH_MAP.get(mat, INSULATION_MAP[mat])
            role_index += 1
            continue
        
        if mat in SHEATH_MAP and role_index < len(material_role):
            role = material_role[role_index]
            if role == 'sheath':
                sheath = SHEATH_MAP[mat]
            role_index += 1
            continue
        
        if mat in ARMOR_MAP:
            armor = ARMOR_MAP[mat]
            continue
    
    # 特殊情况处理
    # 1. CU/FRPVC 只有护套材料，需要推断绝缘
    if not insulation and sheath and len(materials) == 2 and 'FRPVC' in [m.upper() for m in materials]:
        # FRPVC 通常用于护套，绝缘默认也是 PVC
        insulation = 'V'
    
    # 2. 如果只有一个材料且既是绝缘又是护套（如 PVC 在 CU/PVC 中）
    if insulation and not sheath and insulation in SHEATH_MAP.values():
        sheath = insulation
    if not insulation and sheath and sheath in INSULATION_MAP.values():
        insulation = sheath
    
    if not insulation or not sheath:
        return None
    
    base = ''
    if is_fire_resistant:
        base += 'N-'
    if conductor == '铝':
        base += 'L'
    base += insulation + sheath
    if armor:
        base += armor
    
    spec_str = re.sub(r'[xX*]', '×', spec_str)
    result = f'{base}-{voltage_str}-{spec_str}'
    return result.lstrip('-')

if __name__ == '__main__':
    tests = [
        ('CU/XLPE/PVC 4x25+1x16', 'YJV-0.6/1kV-4×25+1×16'),
        ('CU/XLPE/PVC 1x120', 'YJV-0.6/1kV-1×120'),
        ('CU/PVC 3x2.5', 'VV-0.6/1kV-3×2.5'),
        ('CU/Mica/XLPE/FRPVC 1x120', 'N-YJV-0.6/1kV-1×120'),
        ('CU/XLPE/DSTA/PVCW24kV  3x70', 'YJV22-8.7/15kV-3×70'),
        ('接地线 CU/PVC 1x95mm2', 'VV-0.6/1kV-1×95'),
    ]
    for inp, exp in tests:
        res = parse_english_model(inp)
        status = '✓' if res == exp else '✗'
        print(f'{status} {inp}')
        print(f'  期望：{exp}')
        print(f'  实际：{res}')
