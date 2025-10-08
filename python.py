import streamlit as st
# Nhập các thư viện cần thiết từ google-genai
from google import genai
from google.genai import types

# --- CẤU HÌNH & KHỞI TẠO ---
# Chú ý: Streamlit sẽ tự động lấy khóa API từ biến môi trường
# `GEMINI_API_KEY` nếu bạn đã thiết lập.
client = genai.Client()

# Sử dụng mô hình chat (phù hợp cho hội thoại)
MODEL_NAME = "gemini-2.5-flash"

# --- KHỞI TẠO TRẠNG THÁI CUỘC TRÒ CHUYỆN ---
# Sử dụng st.session_state để lưu trữ lịch sử chat giữa các lần tương tác
if "chat_history" not in st.session_state:
    # Lịch sử chat lưu dưới dạng list các dict
    st.session_state.chat_history = []
    
# Khởi tạo đối tượng Chat của Gemini nếu chưa có
# Việc này giúp duy trì ngữ cảnh cuộc trò chuyện (conversation context)
if "gemini_chat" not in st.session_state:
    try:
        st.session_state.gemini_chat = client.chats.create(model=MODEL_NAME)
    except Exception as e:
        st.error(f"Lỗi khởi tạo Gemini Client: Vui lòng kiểm tra khóa API. Chi tiết: {e}")
        st.stop()


# --- HÀM XỬ LÝ CHAT ---
def generate_response(prompt):
    """Gửi prompt đến Gemini và cập nhật lịch sử chat."""
    try:
        # Gửi tin nhắn đến API Gemini
        # Vì đã dùng client.chats.create, mỗi lần send_message sẽ tự động
        # kế thừa ngữ cảnh từ các tin nhắn trước.
        response = st.session_state.gemini_chat.send_message(prompt)
        
        # Thêm prompt của người dùng và phản hồi của Gemini vào lịch sử
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "model", "content": response.text})
        
    except Exception as e:
        # Xử lý lỗi API và hiển thị cho người dùng
        error_message = f"Đã xảy ra lỗi khi gọi Gemini API: {e}"
        st.session_state.chat_history.append({"role": "model", "content": error_message})


# --- GIAO DIỆN STREAMLIT ---

st.set_page_config(page_title="Gemini Chat App", layout="centered")

# Giữ nguyên tiêu đề và nội dung ban đầu
st.title("Ứng dụng Hỏi đáp với Gemini ✨")
st.write("Chào mừng bạn đến với ứng dụng Python Streamlit được tích hợp mô hình AI Gemini. Hãy bắt đầu cuộc trò chuyện của bạn ở khung chat bên dưới!")

# Thêm một đường kẻ ngang để phân biệt các phần
st.divider()

## KHUNG CHAT (CHAT INTERFACE)

# 1. Hiển thị lịch sử cuộc trò chuyện
# Duyệt qua các tin nhắn đã lưu trong session_state và hiển thị chúng
for message in st.session_state.chat_history:
    # Dùng st.chat_message để hiển thị tin nhắn với avatar phù hợp
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. Khung nhập liệu cho người dùng
user_prompt = st.chat_input("Hỏi Gemini bất cứ điều gì...")

# 3. Xử lý khi người dùng nhập prompt
if user_prompt:
    # Ngay lập tức gọi hàm xử lý
    generate_response(user_prompt)
    
    # Tự động làm mới giao diện (rerun) để hiển thị tin nhắn mới ngay lập tức
    # Đây là bước cần thiết trong Streamlit để cập nhật UI sau khi session_state thay đổi
    st.rerun()
