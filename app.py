import streamlit as st
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="健康助手Debug版", page_icon="🛠️", layout="wide")

st.title("🛠️ 调试模式：正在检测系统...")

# --- 2. 侧边栏 ---
st.sidebar.title("功能菜单")
app_mode = st.sidebar.radio("选择功能:", ["🔍 AI查食物热量", "🏃‍♂️ 每日热量计算"])

# --- 3. 尝试导入 OpenAI ---
try:
    from openai import OpenAI
    st.success("✅ 步骤1: OpenAI 库导入成功")
    print("LOG: OpenAI imported successfully")
except Exception as e:
    st.error(f"❌ 步骤1 失败: 无法导入 OpenAI。原因: {e}")
    st.stop()

# ==========================================
# 功能 1: AI 查食物热量
# ==========================================
if app_mode == "🔍 AI查食物热量":
    st.header("正在初始化 AI 服务...")
    
    # --- 4. 检查密钥是否存在 ---
    api_key = None
    
    # 方法A: 尝试从 st.secrets 读取
    if "SILICONFLOW_API_KEY" in st.secrets:
        st.info("✅ 步骤2: 在 Secrets 中找到了密钥配置")
        api_key = st.secrets["SILICONFLOW_API_KEY"]
    else:
        st.warning("⚠️ 步骤2: Secrets 里没找到 SILICONFLOW_API_KEY")
    
    # --- 5. 尝试连接硅基流动 ---
    if api_key:
        try:
            st.write("🔄 步骤3: 正在连接云端模型...")
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            # 测试一下客户端是否存活
            st.success("✅ 步骤3: 客户端连接对象创建成功！")
            
            # --- 6. 显示输入框 ---
            with st.form("debug_form"):
                text = st.text_area("输入测试内容", "一个苹果")
                btn = st.form_submit_button("测试连接")
                
            if btn:
                st.write("🚀 正在发送请求给 DeepSeek...")
                try:
                    response = client.chat.completions.create(
                        model="deepseek-ai/DeepSeek-V3",
                        messages=[{"role": "user", "content": f"查热量：{text}"}],
                        stream=False
                    )
                    st.balloons()
                    st.markdown("### 🎉 成功收到回复：")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"❌ 请求失败: {e}")
                    
        except Exception as e:
            st.error(f"❌ 客户端初始化失败: {e}")
    else:
        st.error("❌ 无法继续：没有有效的 API Key。")

# ==========================================
# 功能 2: 纯计算 (对照组)
# ==========================================
elif app_mode == "🏃‍♂️ 每日热量计算":
    st.success("✅ 本地计算模块运行正常")
    st.write("这里不需要联网，应该能直接显示。")
