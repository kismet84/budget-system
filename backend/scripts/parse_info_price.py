#!/usr/bin/env python3
"""
超快 xlsx 解析器 - 直接解析 xlsx 内部 XML
支持两种调用方式：
1. 脚本模式：扫描 DATA_DIR 批量处理
2. 函数模式：parse_xlsx(path, month, city_cols) 解析单个文件
"""
import zipfile, xml.etree.ElementTree as ET, os, json, re, re as _re

DATA_DIR = "/Users/kis/.hermes/memory/projects/budget-system/data/信息价/raw/"
OUT_DIR  = "/Users/kis/.hermes/memory/projects/budget-system/data/信息价/indexed/"
os.makedirs(OUT_DIR, exist_ok=True)

def get_month(f):
    m = re.search(r"(\d{4})年(\d{1,2})月", f)
    return f"{m.group(1)}-{int(m.group(2)):02d}" if m else f

def col_letter_to_num(letters):
    num = 0
    for c in letters.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num

def cell_ref_to_col(ref):
    m = _re.match(r"([A-Z]+)(\d+)", ref)
    if m:
        return col_letter_to_num(m.group(1))
    return None

NS = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def parse_xlsx(path: str, month: str = None, city_cols = None):
    """
    解析单个 xlsx 文件，返回记录列表
    
    Args:
        path: 文件路径（支持 /tmp 路径或本地路径）
        month: 月份字符串，默认为 None（自动从文件名提取）
        city_cols: 城市列配置，默认为 None（自动根据文件名选择）
    
    Returns:
        list[dict]: 解析后的记录列表
    """
    records = []
    
    if month is None:
        month = get_month(os.path.basename(path))
    
    if city_cols is None:
        filename = os.path.basename(path)
        if "2025年8月" in filename:
            city_cols = [("仙桃市", 5)]
        elif "2026年" in filename:
            city_cols = [("武汉市",6),("黄石市",8),("鄂州市",10),("黄冈市",12),
                         ("荆州市",14),("宜昌市",16),("襄阳市",18),("十堰市",20),
                         ("孝感市",22),("荆门市",24),("咸宁市",26),("随州市",28),
                         ("恩施州",30),("神农架林区",32),("天门市",34),("潜江市",36),("仙桃市",38)]
        else:
            city_cols = [("武汉市",5),("襄阳市",7),("宜昌市",9),("黄石市",11),
                         ("十堰市",13),("荆州市",15),("荆门市",17),("鄂州市",19),
                         ("孝感市",21),("黄冈市",23),("咸宁市",25),("随州市",27),
                         ("恩施市",29),("神农架林区",31)]
    
    try:
        with zipfile.ZipFile(path) as z:
            try:
                with z.open("xl/worksheets/sheet1.xml") as f:
                    tree = ET.parse(f)
            except:
                return records
            root = tree.getroot()
            ns = NS['ns']
            
            # Get shared strings
            strings = []
            try:
                with z.open("xl/sharedStrings.xml") as sf:
                    ss_tree = ET.parse(sf)
                ss_root = ss_tree.getroot()
                for si in ss_root.findall(f".//{{{ns}}}si"):
                    t = si.find(f".//{{{ns}}}t")
                    strings.append(t.text if t is not None else "")
            except:
                pass
            
            def get_val(cell, strings):
                t_attr = cell.get("t", "")
                v_el = cell.find(f"{{{ns}}}v")
                if v_el is None: return None
                v = v_el.text
                if v is None: return None
                if t_attr == "s":
                    try: return strings[int(v)]
                    except: return None
                else:
                    try: return float(v) if v else None
                    except: return v
            
            for row in root.findall(f".//{{{ns}}}row"):
                row_idx = int(row.get("r", 0))
                if row_idx < 6: continue
                
                cells = {}
                for c in row.findall(f"{{{ns}}}c"):
                    col = cell_ref_to_col(c.get("r", ""))
                    if col:
                        cells[col] = c
                
                seq_cell = cells.get(1)
                if not seq_cell: continue
                seq = get_val(seq_cell, strings)
                if not isinstance(seq, (int, float)): continue
                
                code = get_val(cells.get(2), strings) or ""
                name = get_val(cells.get(3), strings) or ""
                spec = get_val(cells.get(4), strings) or ""
                unit = get_val(cells.get(5), strings) or ""
                
                if not name: continue
                
                for city, col_idx in city_cols:
                    tax = get_val(cells.get(col_idx), strings)
                    notax = get_val(cells.get(col_idx + 1), strings)
                    try:
                        tax_f = float(tax) if tax else None
                        notax_f = float(notax) if notax else None
                    except:
                        tax_f, notax_f = None, None
                    
                    if tax_f and notax_f and tax_f > 0 and notax_f > 0:
                        records.append({
                            "月份": month,
                            "材料编号": str(code).strip() if code else "",
                            "材料名称": str(name).strip(),
                            "规格及型号": str(spec).strip() if spec else "",
                            "单位": str(unit).strip() if unit else "",
                            "城市": city,
                            "含税价": tax_f,
                            "除税价": notax_f,
                        })
    except Exception as e:
        print(f"Error parsing {path}: {e}")
    
    return records


# 脚本模式入口
if __name__ == "__main__":
    files = sorted(os.listdir(DATA_DIR))
    total = 0

    for f in files:
        path = os.path.join(DATA_DIR, f)
        month = get_month(f)
        out_path = os.path.join(OUT_DIR, f"{month}.json")
        
        if os.path.exists(out_path):
            with open(out_path) as fp:
                existing = json.load(fp)
            print(f"[SKIP] {f[:28]} ({len(existing)} 条)", flush=True)
            total += len(existing)
            continue
        
        print(f"[处理] {f[:28]}...", end=" ", flush=True)
        
        if "2025年8月" in f:
            records = parse_xlsx(path, month, [("仙桃市", 5)])
        elif "2026年" in f:
            city_cols = [("武汉市",6),("黄石市",8),("鄂州市",10),("黄冈市",12),
                         ("荆州市",14),("宜昌市",16),("襄阳市",18),("十堰市",20),
                         ("孝感市",22),("荆门市",24),("咸宁市",26),("随州市",28),
                         ("恩施州",30),("神农架林区",32),("天门市",34),("潜江市",36),("仙桃市",38)]
            records = parse_xlsx(path, month, city_cols)
        else:
            city_cols = [("武汉市",5),("襄阳市",7),("宜昌市",9),("黄石市",11),
                         ("十堰市",13),("荆州市",15),("荆门市",17),("鄂州市",19),
                         ("孝感市",21),("黄冈市",23),("咸宁市",25),("随州市",27),
                         ("恩施市",29),("神农架林区",31)]
            records = parse_xlsx(path, month, city_cols)
        
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(records, fp, ensure_ascii=False)
        print(f"{len(records)} 条", flush=True)
        total += len(records)

    print(f"\n总计: {total} 条")
