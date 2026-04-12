"""
建设工程预算定额查询系统 - Streamlit 前端
调用后端 FastAPI 进行 AI 语义搜索
"""
import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="建设工程预算定额查询系统", page_icon="📊", layout="wide")

API_BASE = "http://localhost:8001"
PAGE_SIZE = 5

# ---- Dark theme CSS ----
st.html("""
<style>
/* 工程类网站配色：深蓝主色(#1a365d) + 建筑橙强调(#f97316) + 天蓝辅助(#38bdf8) */
section[data-testid="stMainBlockContainer"] { background: #ffffff !important; }
iframe { background: #ffffff !important; }
.stApp { background: #ffffff !important; }
body { background: #ffffff !important; }
.stSidebar > div:first-child { background: #1e3a5f !important; }

/* 卡片 */
.card-result { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
.card-result:hover { border-color: #f97316; box-shadow: 0 2px 8px rgba(249,115,22,0.1); }

/* 费用区 */
.fee-highlight { color: #f97316; font-size: 22px; font-weight: 700; }
.fee-label { color: #64748b; font-size: 13px; }
.fee-value { color: #1e293b; font-weight: 600; }

/* 状态色 */
.sim-hi { color: #16a34a; } .sim-md { color: #d97706; } .sim-lo { color: #dc2626; }
.success-val { color: #16a34a; font-weight: 600; }

/* 计算结果 */
.calc-result { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 10px 14px; margin: 8px 0; }
.calc-result .label { color: #92400e; font-size: 12px; }
.calc-result .value { color: #ea580c; font-size: 20px; font-weight: 700; }
.calc-row { display: flex; justify-content: space-between; align-items: center; }

/* 侧边栏文字 */
.stSidebar h1, .stSidebar h2, .stSidebar p, .stSidebar span { color: #e2e8f0 !important; }

/* 通用 */
.stCaption { color: #64748b !important; font-size: 12px; }
.stDivider { border-color: #e2e8f0 !important; }
.stMetric { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }
.stMetric label { color: #64748b !important; }
.stMetric [data-testid="stMetricValue"] { color: #1e293b !important; }

/* 表格去深色背景 */
.stDataFrame, .stDataFrame [data-testid="stTable"], div[data-testid="stDataFrame"] > div {
    background: #ffffff !important;
}
.stDataFrame table { background: #ffffff !important; color: #1e293b !important; }
.stDataFrame th { background: #f1f5f9 !important; color: #1e293b !important; border-bottom: 1px solid #e2e8f0 !important; }
.stDataFrame td { background: #ffffff !important; color: #1e293b !important; border-color: #f1f5f9 !important; }

/* 指标卡白底 */
.stHorizontalBlock > div { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; }

/* 标题栏白底 */
.stApp > header { background: #ffffff !important; }

/* 全局表格 */
table { background: #ffffff !important; color: #1e293b !important; }
thead th { background: #f8fafc !important; color: #1e293b !important; }
tbody td { background: #ffffff !important; }

/* 自定义材料明细表格 */
.mat-table { width: 100%; border-collapse: collapse; font-size: 13px; background: #ffffff; }
.mat-table th { background: #f1f5f9; color: #1e293b; padding: 6px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; font-weight: 600; }
.mat-table td { background: #ffffff; color: #1e293b; padding: 5px 10px; border-bottom: 1px solid #f1f5f9; }
.mat-table tr:hover td { background: #f8fafc; }

/* 复选框居中于其容器 */
[data-testid="stCheckbox"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 0 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
[data-testid="stCheckbox"] > div {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: none !important;
    box-shadow: none !important;
}

/* 清除所有边框和轮廓 */
.stHorizontalBlock,
div[data-testid="stHorizontalBlock"] > div {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
section[data-testid="stMainBlockContainer"] {
    border: none !important;
    outline: none !important;
}

/* Selectbox 下拉框白底 */
section[data-testid="stMainBlockContainer"] .stSelectbox > div > div { background: #ffffff !important; }
[data-testid="stSelectbox"] { background: #ffffff !important; }
.stSelectbox div[data-baseweb="select"] { background: #ffffff !important; border-color: #e2e8f0 !important; }
.stSelectbox .css-1q8j07d { background: #ffffff !important; }
div[data-testid="stSelectbox"] > div > div { background: #ffffff !important; color: #1e293b !important; }


/* 输入框 */
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: #ffffff !important; color: #1e293b !important;
    border: 1px solid #cbd5e1 !important; border-radius: 6px;
}
.stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
    border-color: #f97316 !important; box-shadow: 0 0 0 2px rgba(249,115,22,0.15);
}

/* 按钮 */
.stButton > button { background: #1e3a5f !important; color: #ffffff !important; border: none; border-radius: 6px; font-weight: 600; }
.stButton > button:hover { background: #f97316 !important; }

/* 展开卡片标题 - 毛玻璃效果 */
.result-title {
    background: rgba(200, 220, 255, 0.25);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    color: #1e3a5f;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 14px;
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,0.3);
    border-bottom: 1px solid rgba(30,58,95,0.15);
}
.result-title .quota-id { color: #ea580c; font-weight: 700; }
.result-title .similarity { color: #0369a1; font-size: 12px; float: right; }

/* 工作内容 */
.work-content { color: #475569; font-size: 13px; line-height: 1.6; padding: 8px 0; }

/* 分隔线 */
.section-sep { border-color: #e2e8f0; }
</style>
""")

# ---- Session state init ----
for key, default in [("search_results", None), ("materials_cache", {}), ("last_query", ""), ("card_expanded", {}), ("current_page", 1)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---- Sidebar ----
with st.sidebar:
    st.title("📖 使用说明")
    st.markdown("""
    **操作步骤：**
    1. 输入工程描述（如"内墙抹灰"）
    2. 点击「搜索」按钮
    3. 点击结果卡片展开详情
    4. 输入工程量，自动计算总价

    **数据来源：** 湖北省房屋建筑与装饰工程消耗量定额（2024）
    """)
    st.divider()

# ---- Title ----
st.title("📊 建设工程预算定额查询系统")
st.caption("基于湖北 2024 定额库的 AI 智能定额匹配")
st.divider()

# ---- Search bar ----
# Session state for min_similarity
if "min_similarity" not in st.session_state:
    st.session_state.min_similarity = 0.5

# ---- Threshold options ----
THRESHOLD_OPTIONS = [
    (0.3, "宽松"),
    (0.4, "较宽松"),
    (0.5, "中等"),
    (0.6, "较严格"),
    (0.7, "严格"),
    (0.8, "极严格"),
    (1.0, "精确匹配"),
]
THRESHOLD_LABELS = {k: f"{k:.2f} ({label})" for k, label in THRESHOLD_OPTIONS}
THRESHOLD_DISPLAY = {k: f"阈值: {k:.2f} ({label})" for k, label in THRESHOLD_OPTIONS}

# Normalize session state to known threshold
if st.session_state.min_similarity not in [k for k, _ in THRESHOLD_OPTIONS]:
    st.session_state.min_similarity = 0.5

col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
with col1:
    query = st.text_input("输入工程描述", placeholder="例如：内墙抹灰、铝合金门窗...", label_visibility="collapsed")
with col2:
    top_k = st.selectbox("返回", [3, 5, 10, 15], index=0, label_visibility="collapsed")
with col3:
    # Selectbox for threshold
    sim_idx = [i for i, (k, _) in enumerate(THRESHOLD_OPTIONS) if k == st.session_state.min_similarity]
    sim_idx = sim_idx[0] if sim_idx else 2  # default to 0.5
    selected_sim = st.selectbox(
        "相似度阈值",
        [k for k, _ in THRESHOLD_OPTIONS],
        index=sim_idx,
        format_func=lambda x: THRESHOLD_LABELS[x],
        label_visibility="collapsed"
    )
    min_sim = selected_sim
with col4:
    search_clicked = st.button("🔍 搜索", type="primary", use_container_width=True)

if search_clicked and query:
    st.session_state.min_similarity = min_sim
    st.session_state.current_page = 1
    with st.spinner("正在搜索..."):
        try:
            resp = requests.post(
                f"{API_BASE}/api/v1/ai/search",
                json={"query": query, "top_k": top_k, "min_similarity": min_sim},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.search_results = data.get("results", [])
                st.session_state.last_query = query
                st.session_state.materials_cache = {}
                st.session_state.card_expanded = {}
                st.session_state.filtered_count = data.get("filtered_count", 0)
            else:
                st.error(f"请求失败: {resp.status_code}")
                st.session_state.search_results = None
        except Exception as e:
            st.error(f"请求异常: {e}")
            st.session_state.search_results = None

# ---- Helper: unit divisor ----
def parse_unit_divisor(unit_str: str) -> float:
    if not unit_str: return 1.0
    m = re.match(r"^(\d+\.?\d*)", unit_str.strip())
    return float(m.group(1)) if m else 1.0

def get_display_unit(unit_str: str) -> str:
    if not unit_str: return ""
    m = re.match(r"^(\d+\.?\d*)(.*)", unit_str.strip())
    suffix = m.group(2).strip() if m.group(2) else unit_str.strip()
    return suffix if suffix else unit_str.strip()


def normalize_text(text: str) -> str:
    """将全角字符转换为半角，用于显示"""
    if not text:
        return text
    fw_digits = str.maketrans('０１２３４５６７８９', '0123456789')
    fw_letters = str.maketrans(
        'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ'
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ',
        'abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    fw_punct = str.maketrans(
        '（），．：；？！＂''［］｛｝＋－×÷＝＜＞｜～',
        '(),.:;?!"''[]{}+-*/=<>|~')
    text = text.translate(fw_digits).translate(fw_letters).translate(fw_punct)
    text = text.replace('\uff0a', '^')  # fullwidth asterisk
    text = text.replace('\u3000', ' ')  # ideographic space
    return text


# ---- Results as checkbox-toggle cards ----
if st.session_state.search_results is None:
    st.info("👆 请输入工程描述后点击搜索")
elif not st.session_state.search_results:
    st.warning("未找到匹配结果")
else:
    results = st.session_state.search_results
    total_pages = (len(results) + PAGE_SIZE - 1) // PAGE_SIZE if results else 1
    current_page = st.session_state.get("current_page", 1)
    start_idx = (current_page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_results = results[start_idx:end_idx]

    for r in page_results:
        quota_id = r.get("quota_id", "")
        section = normalize_text(r.get("section", "") or "")
        unit = normalize_text(r.get("unit", ""))
        total_cost = r.get("total_cost") or 0
        labor_fee = r.get("labor_fee") or 0
        material_fee = r.get("material_fee") or 0
        machinery_fee = r.get("machinery_fee") or 0
        tax = r.get("tax") or 0
        sim = r.get("similarity") or 0
        project_name = normalize_text(r.get("project_name") or "")
        if not project_name and section:
            project_name = section.split("/")[-1].strip()

        sim_cls = "sim-hi" if sim >= 0.9 else ("sim-md" if sim >= 0.7 else "sim-lo")
        sim_str = f"<span class='{sim_cls}'>{sim:.4f}</span>"

        hdr_col1, hdr_col2 = st.columns([0.5, 19.5])
        with hdr_col1:
            is_open = st.session_state.card_expanded.get(quota_id, False)
            opened = st.checkbox("", value=is_open, key=f"toggle_{quota_id}", label_visibility="collapsed")
            st.session_state.card_expanded[quota_id] = opened
        with hdr_col2:
            border_color = "#f97316" if opened else "transparent"
            header_html = (
                f"<div class='result-title' style='border-left:4px solid #f97316; border:1px solid {border_color};'>"
                f"<span class='quota-id'>{quota_id}</span>"
                f"<span style='color:#64748b;font-size:13px'> | {project_name} | {unit}</span>"
                f"<span class='similarity'>相似度 {sim_str}</span>"
                f"</div>"
            )
            st.html(header_html)

        if opened:
            if section:
                st.caption(f"📂 {section}")

            # Fee table: 全费用 + 5项明细
            fee_html = (
                f"<span class='fee-label'>全费用:</span> "
                f"<span class='fee-highlight'>{total_cost:.2f}元</span><br/>"
                f"<span class='fee-label'>人工费</span> <span class='fee-value'>{labor_fee:.2f}</span> | "
                f"<span class='fee-label'>材料费</span> <span class='fee-value'>{material_fee:.2f}</span> | "
                f"<span class='fee-label'>机械费</span> <span class='fee-value'>{machinery_fee:.2f}</span> | "
                f"<span class='fee-label'>管理费</span> <span class='fee-value'>{(r.get('management_fee') or 0):.2f}</span> | "
                f"<span class='fee-label'>增值税</span> <span class='fee-value'>{tax:.2f}</span>"
            )
            st.html(fee_html)

            # Work content
            work_content = normalize_text(r.get("work_content") or "")
            if work_content:
                wc_html = f"<span class='fee-label'>工作内容:</span> <span class='work-content'>{work_content}</span>"
                st.html(wc_html)

            st.divider()

            # Quantity input
            base_unit = get_display_unit(unit)
            divisor = parse_unit_divisor(unit)
            unit_price = total_cost / divisor if divisor else total_cost

            st.caption(f"📐 单位: {base_unit}（定额单位: {unit}）")
            qty = st.number_input("输入工程量", min_value=0.0, step=1.0, format="%.2f", key=f"qty_{quota_id}")

            if qty > 0:
                calc_total = qty * unit_price
                calc_html = (
                    f"<div class='calc-result'>"
                    f"<div class='calc-row'><span class='label'>输入工程量</span>"
                    f"<span class='value'>{qty:.2f} {base_unit}</span></div>"
                    f"<div class='calc-row'><span class='label'>定额单价</span>"
                    f"<span class='value'>{unit_price:.4f} 元/{base_unit}</span></div>"
                    f"<div class='calc-row'><span class='label'>计算总价</span>"
                    f"<span class='value' style='color:#ea580c'>{calc_total:.2f} 元</span></div>"
                    f"</div>"
                )
                st.html(calc_html)

            st.divider()

            # Materials
            st.markdown("**材料明细**")
            if quota_id in st.session_state.materials_cache:
                mats = st.session_state.materials_cache[quota_id]
            else:
                try:
                    mr = requests.get(f"{API_BASE}/api/v1/quota/{quota_id}/materials", timeout=10)
                    mats = mr.json() if mr.status_code == 200 else []
                    st.session_state.materials_cache[quota_id] = mats
                except:
                    mats = []

            if mats:
                mat_data = [
                    {
                        "材料名称": normalize_text(m.get("name","")),
                        "类型": normalize_text(m.get("mat_type","")),
                        "单位": normalize_text(m.get("unit","")),
                        "单价(元)": m.get("unit_price",""),
                        "消耗量": normalize_text(str(m.get("consumption",""))),
                    }
                    for m in mats
                ]
                # Use custom HTML table instead of st.dataframe to avoid dark shadow DOM
                table_html = "<table class='mat-table'><thead><tr><th>材料名称</th><th>类型</th><th>单位</th><th>单价(元)</th><th>消耗量</th></tr></thead><tbody>"
                for m in mat_data:
                    table_html += f"<tr><td>{m['材料名称']}</td><td>{m['类型']}</td><td>{m['单位']}</td><td>{m['单价(元)']}</td><td>{m['消耗量']}</td></tr>"
                table_html += "</tbody></table>"
                st.html(table_html)
            else:
                st.info("无材料明细")

            st.divider()

    # Pagination
    if len(results) > PAGE_SIZE:
        total_pages = (len(results) + PAGE_SIZE - 1) // PAGE_SIZE
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ 上一页", key="prev_page", disabled=(st.session_state.get("current_page", 1) <= 1)):
                st.session_state.current_page -= 1
        with col_page:
            st.write(f"第 {st.session_state.get('current_page', 1)} / {total_pages} 页")
        with col_next:
            if st.button("下一页 ▶", key="next_page", disabled=(st.session_state.get("current_page", 1) >= total_pages)):
                st.session_state.current_page += 1

# ---- Footer ----
