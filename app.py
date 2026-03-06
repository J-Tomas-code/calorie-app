import streamlit as st
import base64
from openai import OpenAI

# --- 1. 页面全局配置 ---
st.set_page_config(page_title="AI热量拍立得", page_icon="🥑", layout="wide")

# --- 2. 侧边栏导航 ---
st.sidebar.title("🥑 功能菜单")
app_mode = st.sidebar.radio("选择功能:", [
    "📸 拍照/文本查热量", 
    "📝 今日热量记账本", 
    "🏃‍♂️ 每日热量计算(TDEE)"
])

# --- 3. 初始化 AI 客户端 ---
client = None
try:
    if "SILICONFLOW_API_KEY" in st.secrets:
        client = OpenAI(
            api_key=st.secrets["SILICONFLOW_API_KEY"],
            base_url="https://api.siliconflow.cn/v1"
        )
except Exception as e:
    st.error(f"❌ 系统初始化失败: {e}")

# --- 辅助函数：图片转Base64 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# ==========================================
# 功能 1: 拍照/文本查热量
# ==========================================
if app_mode == "📸 拍照/文本查热量":
    st.title("📸 AI 智能食物热量查询")
    st.caption("支持 📝文字描述 和 📷拍照识别")

    if not client:
        st.warning("⚠️ 请先配置 API Key")
        st.stop()

    with st.container():
        uploaded_file = st.file_uploader("上传食物照片", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, caption="已上传", width=300)
        
        text_input = st.text_input("补充描述", placeholder="例如：一碗牛肉面，不加香菜")
        submit_btn = st.button("开始分析 🔥", type="primary")

    if submit_btn:
        if not uploaded_file and not text_input:
            st.warning("请至少上传图片或输入文字！")
            st.stop()

        with st.spinner("AI 正在识别中..."):
            try:
                messages = []
                if uploaded_file:
                    base64_image = encode_image(uploaded_file)
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"分析图片食物热量。{text_input}。输出表格：食物名、重量、热量。"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }]
                    model_name = "Qwen/Qwen2-VL-72B-Instruct" 
                else:
                    messages = [
                        {"role": "system", "content": "你是营养师。计算食物热量，输出表格和总热量。"},
                        {"role": "user", "content": text_input}
                    ]
                    model_name = "deepseek-ai/DeepSeek-V3"

                response = client.chat.completions.create(
                    model=model_name, messages=messages, stream=False
                )
                
                st.markdown("---")
                st.success("✅ 识别结果")
                st.markdown(response.choices[0].message.content)

            except Exception as e:
                st.error(f"分析失败: {e}")

# ==========================================
# 功能 2: 今日热量记账本
# ==========================================
elif app_mode == "📝 今日热量记账本":
    st.title("📝 今日热量记账本")
    st.caption("⚠️ 注意：刷新网页后记录会清空")

    if 'food_log' not in st.session_state:
        st.session_state.food_log = []

    with st.expander("🎯 设置今日目标", expanded=True):
        # 这里的 step=50 表示按一下加减号变 50
        target_cal = st.number_input("今日目标摄入 (kcal)", min_value=1000, max_value=5000, value=2000, step=50)

    st.markdown("### ➕ 记一笔")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        food_name = st.text_input("食物名称", placeholder="例如：早餐面包")
    with col2:
        food_cal = st.number_input("热量 (kcal)", min_value=0, max_value=2000, value=0, step=10)
    with col3:
        st.write("")
        st.write("")
        add_btn = st.button("添加记录")

    if add_btn:
        if food_name and food_cal > 0:
            st.session_state.food_log.append({"name": food_name, "cal": food_cal})
            st.success(f"已添加: {food_name}")
        else:
            st.warning("请输入名称和大于0的热量")

    st.markdown("---")
    total_intake = sum(item['cal'] for item in st.session_state.food_log)
    remaining = target_cal - total_intake
    progress = min(total_intake / target_cal, 1.0)
    
    st.subheader("📊 今日统计")
    m1, m2, m3 = st.columns(3)
    m1.metric("目标热量", f"{target_cal} kcal")
    m2.metric("已摄入", f"{total_intake} kcal", delta=f"{total_intake} kcal", delta_color="inverse")
    m3.metric("还能吃", f"{remaining} kcal", delta=f"{remaining} kcal")

    if remaining < 0:
        st.error(f"🚨 警告：你已经超标 {abs(remaining)} kcal 了！")
        st.progress(1.0)
    else:
        st.progress(progress)

    st.markdown("### 🧾 详细清单")
    if len(st.session_state.food_log) > 0:
        for i, item in enumerate(st.session_state.food_log):
            st.text(f"{i+1}. {item['name']} —— {item['cal']} kcal")
        if st.button("🗑️ 清空所有记录"):
            st.session_state.food_log = []
            st.rerun()
    else:
        st.info("今天还没有记录哦")

# ==========================================
# 功能 3: 每日热量计算(TDEE) - 修复版
# ==========================================
elif app_mode == "🏃‍♂️ 每日热量计算(TDEE)":
    st.title("🏃‍♂️ 每日热量需求计算器")
    st.write("输入你的身体数据，计算维持体重、减肥或增重需要多少热量。")
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        gender = st.radio("你的性别", ["男", "女"], horizontal=True)
        # 修复点：设置 min_value 为 10，这样你就可以从 25 减到 10 了
        # step=1 表示点一下按钮增减 1 岁
        age = st.number_input("年龄 (岁)", min_value=10, max_value=100, value=25, step=1)
        
        # 修复点：身高同理
        height = st.number_input("身高 (cm)", min_value=100, max_value=250, value=170, step=1)
    
    with col2:
        # 修复点：体重设置 step=0.5，允许输入小数（例如 65.5 kg）
        weight = st.number_input("体重 (kg)", min_value=30.0, max_value=200.0, value=65.0, step=0.5)
        
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

    # 活动系数
    activity_multipliers = {
        "久坐不动 (几乎不运动)": 1.2,
        "轻度活动 (每周运动 1-3 次)": 1.375,
        "中度活动 (每周运动 3-5 次)": 1.55,
        "高度活动 (每周运动 6-7 次)": 1.725,
        "专业运动 (体力工作或双倍训练)": 1.9
    }

    if st.button("计算我的热量需求 📊"):
        # 计算 BMR (Mifflin-St Jeor 公式)
        if gender == "男":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
        tdee = bmr * activity_multipliers[activity_level]

        # 计算结果
        maintain = int(tdee)
        lose_slow = int(tdee * 0.85)
        lose_fast = int(tdee * 0.75)
        gain_weight = int(tdee * 1.15)

        st.markdown("---")
        st.subheader("📊 你的专属热量报告")
        st.info(f"你的基础代谢率 (BMR): **{int(bmr)} kcal**")
        
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        
        with res_col1:
            st.metric(label="🟢 保持体重", value=f"{maintain}", delta="推荐")
        with res_col2:
            st.metric(label="🟡 慢慢减肥", value=f"{lose_slow}", delta="-15%", delta_color="inverse")
        with res_col3:
            st.metric(label="🔴 快速减肥", value=f"{lose_fast}", delta="-25%", delta_color="inverse")
        with res_col4:
            st.metric(label="💪 增肌/增重", value=f"{gain_weight}", delta="+15%")

# --- 底部版权 ---
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 冲哥健康助手")
