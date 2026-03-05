import streamlit as st
from openai import OpenAI

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI热量与健康助手", 
    page_icon="🥑",
    layout="wide"  # 设置为宽屏模式，显示效果更好
)

# --- 侧边栏导航 ---
st.sidebar.title("🥑 功能菜单")
app_mode = st.sidebar.radio("请选择功能:", ["🔍 AI查食物热量", "🏃‍♂️ 算每日所需热量"])

# --- 获取 API Key (用于功能1) ---
try:
    api_key = st.secrets["SILICONFLOW_API_KEY"]
    base_url = "https://api.siliconflow.cn/v1"
    client = OpenAI(api_key=api_key, base_url=base_url)
except Exception:
    # 即使在功能2不需要Key，为了防止报错，给个空值或跳过
    client = None

# ==========================================
# 功能 1: AI 查食物热量
# ==========================================
if app_mode == "🔍 查食物热量":
    st.title("🔍 智能食物热量查询")
    st.caption("基于 DeepSeek-V3 大模型 · 硅基流动提供支持")

    if not client:
        st.error("⚠️ 未检测到 API Key，请检查 secrets.toml 配置！")
        st.stop()

    with st.form("food_query_form"):
        user_input = st.text_area(
            "今天吃了什么？(支持语音输入转文字)", 
            height=120,
            placeholder="例如：早上吃了两个肉包子（大概150克），喝了一杯无糖豆浆，中午吃了一份宫保鸡丁盖饭，稍微有点油。"
        )
        submitted = st.form_submit_button("开始计算 🔥")

    if submitted and user_input:
        system_prompt = """
        你是一个专业的营养师。请分析用户的饮食输入，并计算热量。
        
        输出要求：
        1. 使用Markdown表格列出每样食物的估算重量(g)和热量(kcal)。
        2. 计算总热量，并用三级标题加粗显示（例如：### 总热量：500 kcal）。
        3. 给出简短的营养建议（如：碳水过高，建议晚餐少吃主食）。
        """
        
        with st.spinner("AI 正在分析食物成分..."):
            try:
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V3", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                    stream=False
                )
                result = response.choices[0].message.content
                
                # 结果展示区
                st.markdown("---")
                st.success("✅ 分析完成！")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"连接 AI 失败: {e}")

# ==========================================
# 功能 2: 计算每日所需热量 (TDEE)
# ==========================================
elif app_mode == "🏃‍♂️ 算每日所需热量":
    st.title("🏃‍♂️ 每日热量需求计算器 (TDEE)")
    st.write("输入你的身体数据，计算维持体重、减肥或增重需要多少热量。")
    st.markdown("---")

    # 输入区域 - 分两列显示比较好看
    col1, col2 = st.columns(2)
    
    with col1:
        gender = st.radio("你的性别", ["男", "女"], horizontal=True)
        age = st.number_input("年龄 (岁)", min_value=10, max_value=100, value=25)
        height = st.number_input("身高 (cm)", min_value=100, max_value=250, value=170)
    
    with col2:
        weight = st.number_input("体重 (kg)", min_value=30, max_value=200, value=65)
        activity_level = st.selectbox(
            "日常活动量",
            options=[
                "久坐不动 (几乎不运动)",
                "轻度活动 (每周运动 1-3 次)",
                "中度活动 (每周运动 3-5 次)",
                "高度活动 (每周运动 6-7 次)",
                "专业运动 (体力工作或双倍训练)"
            ]
        )

    # 映射活动系数
    activity_multipliers = {
        "久坐不动 (几乎不运动)": 1.2,
        "轻度活动 (每周运动 1-3 次)": 1.375,
        "中度活动 (每周运动 3-5 次)": 1.55,
        "高度活动 (每周运动 6-7 次)": 1.725,
        "专业运动 (体力工作或双倍训练)": 1.9
    }

    # 提交按钮
    if st.button("计算我的热量需求 📊"):
        # 1. 计算 BMR (Mifflin-St Jeor 公式)
        if gender == "男":
            # BMR = 10W + 6.25H - 5A + 5
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            # BMR = 10W + 6.25H - 5A - 161
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
        # 2. 计算 TDEE (每日总消耗)
        tdee = bmr * activity_multipliers[activity_level]

        # 3. 计算不同目标的热量
        maintain = int(tdee)
        lose_slow = int(tdee * 0.85)  # 减少 15%
        lose_fast = int(tdee * 0.75)  # 减少 25%
        gain_weight = int(tdee * 1.15) # 增加 15%

        st.markdown("---")
        st.subheader("📊 你的专属热量报告")
        
        # 显示 BMR 和 TDEE
        st.info(f"你的基础代谢率 (BMR): **{int(bmr)} kcal** (躺着不动消耗的热量)")
        
        # 使用卡片式布局展示四个结果
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        
        with res_col1:
            st.metric(label="🟢 保持体重", value=f"{maintain} kcal", delta="推荐")
            st.caption("维持当前体重的摄入量")
            
        with res_col2:
            st.metric(label="🟡 慢慢减肥", value=f"{lose_slow} kcal", delta="-15%", delta_color="inverse")
            st.caption("每周约减 0.3-0.5 kg")
            
        with res_col3:
            st.metric(label="🔴 快速减肥", value=f"{lose_fast} kcal", delta="-25%", delta_color="inverse")
            st.caption("每周约减 0.5-0.8 kg (较辛苦)")
            
        with res_col4:
            st.metric(label="💪 增肌/增重", value=f"{gain_weight} kcal", delta="+15%")
            st.caption("配合力量训练效果最佳")

# --- 底部版权 ---
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 个人健康助手")