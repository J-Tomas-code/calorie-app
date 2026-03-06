import streamlit as st
import base64
from openai import OpenAI

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI热量拍立得", page_icon="📸", layout="wide")

# --- 2. 侧边栏 ---
st.sidebar.title("🥑 功能菜单")
app_mode = st.sidebar.radio("选择功能:", ["📸 拍照/文本查热量", "🏃‍♂️ 每日热量计算"])

# --- 3. 初始化客户端 ---
client = None
try:
    if "SILICONFLOW_API_KEY" in st.secrets:
        # 这里我们继续用硅基流动，因为它有免费的 Qwen-VL 模型
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
# 功能 1: 拍照/文本查热量 (升级版)
# ==========================================
if app_mode == "📸 拍照/文本查热量":
    st.title("📸 AI 智能食物热量查询")
    st.caption("支持 📝文字描述 和 📷拍照识别 (模型: Qwen2-VL)")

    if not client:
        st.warning("⚠️ 请先配置 API Key")
        st.stop()

    # --- 输入区 ---
    with st.container():
        # 1. 图片上传组件
        uploaded_file = st.file_uploader("上传食物照片 (或点击手机相机图标拍摄)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, caption="已上传图片", width=300)
        
        # 2. 文字补充组件
        text_input = st.text_input("补充描述 (可选)", placeholder="例如：这碗面大概200克，微辣")
        
        # 3. 提交按钮
        submit_btn = st.button("开始分析 🔥", type="primary")

    # --- 处理逻辑 ---
    if submit_btn:
        if not uploaded_file and not text_input:
            st.warning("请至少上传一张图片或输入一段文字！")
            st.stop()

        with st.spinner("AI 正在观察你的食物..."):
            try:
                messages = []
                
                # 情况 A: 有图片 (使用 Qwen-VL 视觉模型)
                if uploaded_file:
                    base64_image = encode_image(uploaded_file)
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"请分析这张图片里的食物。{text_input if text_input else ''}。请列出食物名称、估算重量(g)和热量(kcal)，并计算总热量。请用Markdown表格展示。"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ]
                    # 注意：这里换成了支持图片的 Qwen 模型
                    # 如果硅基流动这个模型不可用，可以换成 "Qwen/Qwen2-VL-72B-Instruct"
                    model_name = "Qwen/Qwen2-VL-72B-Instruct" 

                # 情况 B: 只有文字 (继续用 DeepSeek-V3)
                else:
                    messages = [
                        {"role": "system", "content": "你是专业营养师。请计算食物热量，输出表格和总热量。"},
                        {"role": "user", "content": text_input}
                    ]
                    model_name = "deepseek-ai/DeepSeek-V3"

                # 发送请求
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=False
                )
                
                # 展示结果
                result = response.choices[0].message.content
                st.markdown("---")
                st.success("✅ 识别完成！")
                st.markdown(result)

            except Exception as e:
                st.error(f"分析失败: {e}")
                st.info("如果是图片识别失败，可能是该免费模型暂时繁忙，请稍后再试或仅使用文字模式。")

# ==========================================
# 功能 2: 每日热量计算 (保持不变)
# ==========================================
elif app_mode == "🏃‍♂️ 每日热量计算":
    # ... (这里保留你之前的计算器代码，为了节省篇幅我省略了，你自己要把之前的粘回来) ...
    st.title("🏃‍♂️ 每日热量需求计算器 (TDEE)")
    # (把之前那段计算身高的代码复制粘贴在下面)
    st.write("请把之前 app.py 里功能2的代码完整复制回这里")
