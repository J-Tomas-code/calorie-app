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
                # 这里的逻辑：有图用Qwen-VL，没图用DeepSeek
                if uploaded_file:
                    base64_image = encode_image(uploaded_file)
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"分析图片食物热量。{text_input}。输出表格：食物名、重量、热量。"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }]
                    # 注意：如果图片识别报错，请检查硅基流动是否支持 Qwen-VL 免费版
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
# 功能 2: 今日热量记账本 (✨新功能)
# ==========================================
elif app_mode == "📝 今日热量记账本":
    st.title("📝 今日热量记账本")
    st.caption("⚠️ 注意：刷新网页后记录会清空，请及时截图保存。")

    # --- 初始化记账数据 (Session State) ---
    if 'food_log' not in st.session_state:
        st.session_state.food_log = [] # 这是一个列表，存吃过的东西

    # --- 1. 设置目标区域 ---
    with st.expander("🎯 设置今日目标", expanded=True):
        target_cal = st.number_input("今日目标摄入 (kcal)", min_value=1000, max_value=5000, value=2000, step=50)

    # --- 2. 记一笔区域 ---
    st.markdown("### ➕ 记一笔")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        food_name = st.text_input("食物名称", placeholder="例如：早餐面包")
    with col2:
        food_cal = st.number_input("热量 (kcal)", min_value=0, max_value=2000, value=0, step=10)
    with col3:
        st.write("") # 占位
        st.write("") # 占位
        add_btn = st.button("添加记录")

    # 点击添加按钮后的逻辑
    if add_btn:
        if food_name and food_cal > 0:
            # 把数据存到 session_state 里
            st.session_state.food_log.append({"name": food_name, "cal": food_cal})
            st.success(f"已添加: {food_name}")
        else:
            st.warning("请输入名称和大于0的热量")

    # --- 3. 统计展示区域 ---
    st.markdown("---")
    
    # 计算总和
    total_intake = sum(item['cal'] for item in st.session_state.food_log)
    remaining = target_cal - total_intake
    
    # 进度条逻辑
    progress = min(total_intake / target_cal, 1.0)
    
    st.subheader("📊 今日统计")
    
    # 漂亮的指标卡片
    m1, m2, m3 = st.columns(3)
    m1.metric("目标热量", f"{target_cal} kcal")
    m2.metric("已摄入", f"{total_intake} kcal", delta=f"{total_intake} kcal", delta_color="inverse")
    m3.metric("还能吃", f"{remaining} kcal", delta=f"{remaining} kcal")

    # 进度条
    if remaining < 0:
        st.error(f"🚨 警告：你已经超标 {abs(remaining)} kcal 了！")
        st.progress(1.0)
    else:
        st.progress(progress)
        st.caption(f"进度: {int(progress*100)}%")

    # --- 4. 详细列表 ---
    st.markdown("### 🧾 详细清单")
    if len(st.session_state.food_log) > 0:
        for i, item in enumerate(st.session_state.food_log):
            st.text(f"{i+1}. {item['name']} —— {item['cal']} kcal")
            
        # 清空按钮
        if st.button("🗑️ 清空所有记录"):
            st.session_state.food_log = []
            st.rerun() # 重新运行刷新页面
    else:
        st.info("今天还没有记录哦，快去吃点什么吧~")

# ==========================================
# 功能 3: 每日热量计算(TDEE)
# ==========================================
elif app_mode == "🏃‍♂️ 每日热量计算(TDEE)":
    st.title("🏃‍♂️ 每日热量需求计算器")
    # ... (为了节省篇幅，这里请把之前写好的计算器逻辑粘贴回来) ...
    # 简版占位，记得用之前的代码替换这里
    col1, col2 = st.columns(2)
    with col1:
        gender = st.radio("你的性别", ["男", "女"], horizontal=True)
        age = st.number_input("年龄", 25)
        height = st.number_input("身高", 170)
    with col2:
        weight = st.number_input("体重", 65)
        activity = st.selectbox("活动量", ["久坐", "轻度", "中度", "重度"])
        
    if st.button("计算"):
        st.info("这里显示计算结果 (请把之前的逻辑复制过来)")
