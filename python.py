import streamlit as st
from google import genai # Hoặc: from google import gemini
from google.genai import types # Hoặc: from google.gemini import types
import os

# --- Thiết lập API Key và Mô hình Gemini ---
# Đảm bảo bạn đã đặt biến môi trường GEMINI_API_KEY hoặc sử dụng st.secrets
# st.secrets["GEMINI_API_KEY"]
try:
    # Lấy API Key từ Streamlit secrets hoặc biến môi trường
    api_key = os.environ.get("GEMINI_API_KEY") # Ưu tiên dùng biến môi trường khi deploy
    if not api_key:
        # Thử lấy từ st.secrets nếu có
        api_key = st.secrets["GEMINI_API_KEY"]

    if api_key:
        client = genai.Client(api_key=api_key) # Khởi tạo Client
    else:
        st.error("⚠️ Vui lòng cung cấp GEMINI_API_KEY thông qua biến môi trường hoặc st.secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Lỗi khi khởi tạo Gemini Client: {e}. Vui lòng kiểm tra API Key.")
    st.stop()


# --- Cấu hình Mô hình ---
MODEL_NAME = "gemini-2.5-flash" # Chọn mô hình phù hợp

# --- Khởi tạo Streamlit Chat (Giữ nguyên các đoạn mã khác) ---

st.title("🤖 Ứng dụng Streamlit Hỏi Đáp với Gemini")
# st.write("Các đoạn mã khác của ứng dụng nằm ở đây...")

# --- LOGIC KHUNG CHAT MỚI ---

# 1. Khởi tạo Lịch sử Chat trong Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Thêm tin nhắn chào mừng ban đầu
    st.session_state.messages.append({"role": "model", "content": "Xin chào! Tôi là trợ lý AI được cung cấp bởi Gemini. Bạn cần tôi giúp gì?"})

# 2. Khởi tạo Phiên Chat (Chat Session)
# Sử dụng một hàm để khởi tạo hoặc lấy phiên chat hiện tại
@st.cache_resource
def get_chat_session():
    # Khởi tạo một phiên chat với lịch sử ban đầu (nếu có)
    # Cần chuyển định dạng lịch sử của st.session_state sang định dạng của Gemini API
    history_for_gemini = [
        types.Content(role=msg["role"], parts=[types.Part.from_text(msg["content"])])
        for msg in st.session_state.messages
        if msg["role"] != "system" # Bỏ qua các tin nhắn role "system" nếu có
    ]

    return client.chats.create(
        model=MODEL_NAME,
        history=history_for_gemini
    )

chat = get_chat_session()

# 3. Hiển thị Lịch sử Chat
for message in st.session_state.messages:
    # Bỏ qua tin nhắn chào mừng (role model đầu tiên) khi hiển thị nếu bạn muốn
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Xử lý Input của Người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn vào đây..."):
    # Thêm tin nhắn của người dùng vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Hiển thị tin nhắn của người dùng
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gửi câu hỏi đến Gemini và hiển thị phản hồi
    with st.chat_message("model"):
        with st.spinner("Gemini đang suy nghĩ..."):
            try:
                # Sử dụng send_message để duy trì ngữ cảnh chat
                response = chat.send_message(prompt)
                full_response = response.text

                # Hiển thị phản hồi và thêm vào lịch sử
                st.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})

            except Exception as e:
                error_msg = f"Đã xảy ra lỗi khi gọi Gemini API: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "model", "content": error_msg})


# --- KẾT THÚC LOGIC KHUNG CHAT ---
