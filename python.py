import streamlit as st
from google import genai
from google.genai import types

# --- CẤU HÌNH & KHỞI TẠO ---
# Chú ý: Streamlit sẽ tự động lấy khóa API từ biến môi trường
# `GEMINI_API_KEY` nếu bạn đã thiết lập.
# Nếu không, bạn cần thay thế None bằng khóa API của bạn
# client = genai.Client(api_key="YOUR_API_KEY") 
client = genai.Client()

# Sử dụng mô hình chat (phù hợp cho hội thoại)
MODEL_NAME = "gemini-2.5-flash"

# --- KHỞI TẠO TRẠNG THÁI CUỘC TRÒ CHUYỆN ---
# Sử dụng st.session_state để lưu trữ lịch sử chat giữa các lần tương tác
if "chat_history" not in st.session_state:
    # Bắt đầu với một tin nhắn hệ thống nếu cần, hoặc để trống
    st.session_state.chat_history = []
    
# Khởi tạo đối tượng Chat của Gemini nếu chưa có
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = client.chats.create(model=MODEL_NAME)


# --- HÀM XỬ LÝ CHAT ---
def generate_response(prompt):
    """Gửi prompt đến Gemini và cập nhật lịch sử chat."""
    try:
        # Gửi tin nhắn đến API Gemini
        response = st.session_state.gemini_chat.send_message(prompt)
        
        # Thêm prompt của người dùng và phản hồi của Gemini vào lịch sử
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "model", "content": response.text})
        
    except Exception as e:
        error_message = f"Đã xảy ra lỗi khi gọi Gemini API: {e}"
        st.session_state.chat_history.append({"role": "model", "content": error_message})


# --- GIAO DIỆN STREAMLIT ---

# Giữ nguyên tiêu đề và nội dung ban đầu (đoạn mã khác)
st.title("Ứng dụng Hỏi đáp với Gemini ✨")
st.write("Chào mừng bạn đến với ứng dụng Python Streamlit được tích hợp mô hình AI Gemini. Hãy bắt đầu cuộc trò chuyện của bạn ở khung chat bên dưới!")

# Thêm một đường kẻ ngang để phân biệt các phần
st.divider()

## KHUNG CHAT

# Hiển thị lịch sử cuộc trò chuyện
for message in st.session_state.chat_history:
    # Dùng st.chat_message để hiển thị tin nhắn với avatar phù hợp
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Khung nhập liệu cho người dùng
user_prompt = st.chat_input("Hỏi Gemini bất cứ điều gì...")

# Xử lý khi người dùng nhập prompt
if user_prompt:
    # Gọi hàm xử lý và hiển thị phản hồi
    generate_response(user_prompt)
    
    # Tự động làm mới giao diện để hiển thị tin nhắn mới ngay lập tức
    # (vì lịch sử đã được cập nhật trong st.session_state)
    st.rerun()
