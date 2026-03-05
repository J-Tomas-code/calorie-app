import streamlit as st
import os

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="热量与健康助手", 
    page_icon="🥑",
    layout="wide"
)

# --- 2. 侧边栏导航 ---
st.sidebar.title("🥑 功能菜单")
app_mode = st.sidebar.radio("请选择功能:", ["🔍 查食物热量", "🏃‍♂️ 算每日所需热量"])

# --- 3. 尝试导入 OpenAI (带错误捕获) ---
client = None
try:
    from openai import OpenAI
    # 尝试读取 Key
    if "SILICONFLOW_API_KEY" in st.secrets:
        api_key = st.secrets["SILICONFLOW_API_KEY"]
        base_url = "https://api.siliconflow.cn/v1"
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        # 如果本地运行没有配置 secrets，给个提示但不要崩溃
        pass
except Exception as e:
    st.error(f"❌ 系统初始化失败: {e}")

# ==========================================
# 功能 1: AI 查食物热量
# ==========================================
if app_mode == "🔍 AI查食物热量":
    st.title("🔍 AI 智能食物热量查询")
    st.caption("基于 DeepSeek-V3 大模型 · 硅基流动提供支持")

    # 检查客户端是否准备好
    if not client:
        st.warning("⚠️ 未检测到 API Key，请检查 Secrets 配置！")
        st.info("如果你是开发者，请去 Streamlit Cloud -> Settings -> Secrets 填入 SILICONFLOW_API_KEY")
        st.stop()

    with st.form("food_query_form"):
        user_input = st.text_area(
            "今天吃了什么？(支持语音输入转文字)", 
            height=120,
            placeholder="例如：早上吃了两个肉包子（大概150克），喝了一杯无糖豆浆..."
        )
        submitted = st.form_submit_button("开始计算 🔥")

    if submitted and user_input:
        # 提示词
        system_prompt = """
        你是一个专业的营养师。请分析用户的饮食输入，并计算热量。
        
        输出要求：
        1. 使用Markdown表格列出每样食物的估算重量(g)和热量(kcal)。
        2. 计算总热量，并用三级标题加粗显示（例如：### 总热量：500 kcal）。
        3. 给出简短的营养建议。
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
                st.error("可能原因：Key 余额不足、网络波动或模型暂时繁忙。")

# ==========================================
# 功能 2: 计算每日所需热量 (TDEE) - 纯数学版
# ==========================================
elif app_mode == "🏃‍♂️ 算每日所需热量":
    st.title("🏃‍♂️ 每日热量需求计算器 (TDEE)")
    st.write("输入你的身体数据，计算维持体重、减肥或增重需要多少热量。")
    st.markdown("---")

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

    activity_multipliers = {
        "久坐不动 (几乎不运动)": 1.2,
        "轻度活动 (每周运动 1-3 次)": 1.375,
        "中度活动 (每周运动 3-5 次)": 1.55,
        "高度活动 (每周运动 6-7 次)": 1.725,
        "专业运动 (体力工作或双倍训练)": 1.9
    }

    if st.button("计算我的热量需求 📊"):
        if gender == "男":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
        tdee = bmr * activity_multipliers[activity_level]
        maintain = int(tdee)
        lose_slow = int(tdee * 0.85)
        lose_fast = int(tdee * 0.75)
        gain_weight = int(tdee * 1.15)

        st.markdown("---")
        st.subheader("📊 你的专属热量报告")
        st.info(f"你的基础代谢率 (BMR): **{int(bmr)} kcal**")
        
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        with res_col1:
            st.metric(label="🟢 保持体重", value=f"{maintain} kcal", delta="推荐")
        with res_col2:
            st.metric(label="🟡 慢慢减肥", value=f"{lose_slow} kcal", delta="-15%", delta_color="inverse")
        with res_col3:
            st.metric(label="🔴 快速减肥", value=f"{lose_fast} kcal", delta="-25%", delta_color="inverse")
        with res_col4:
            st.metric(label="💪 增肌/增重", value=f"{gain_weight} kcal", delta="+15%")

# --- 底部版权 ---
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 冲哥健康助手")

