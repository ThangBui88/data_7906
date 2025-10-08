import streamlit as st
import pandas as pd
from google import genai
from google.genai.errors import APIError

# --- Cấu hình Trang Streamlit ---
st.set_page_config(
    page_title="App Phân Tích Báo Cáo Tài Chính",
    layout="wide"
)

st.title("Ứng dụng Phân Tích Báo Cáo Tài chính 📊")

# Lấy API Key
api_key = st.secrets.get("GEMINI_API_KEY")

# --- Khởi tạo Client Gemini duy trì qua các lần chạy (SỬA LỖI CLIENT CLOSED) ---
@st.cache_resource(show_spinner=False)
def get_gemini_client(api_key):
    """Khởi tạo và lưu trữ đối tượng genai.Client."""
    if not api_key:
        st.error("Lỗi: Không tìm thấy Khóa API. Vui lòng cấu hình Khóa 'GEMINI_API_KEY' trong Streamlit Secrets.")
        return None
    try:
        # Tắt logging mặc định nếu cần
        # genai.set_logging('error') 
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi khởi tạo Gemini Client: {e}")
        return None

# Lấy đối tượng client đã được cache
client = get_gemini_client(api_key)

# --- Hàm tính toán chính (Sử dụng Caching để Tối ưu hiệu suất) ---
@st.cache_data
def process_financial_data(df):
    """Thực hiện các phép tính Tăng trưởng và Tỷ trọng."""
    
    # Đảm bảo các giá trị là số để tính toán
    numeric_cols = ['Năm trước', 'Năm sau']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 1. Tính Tốc độ Tăng trưởng
    # Dùng .replace(0, 1e-9) cho Series Pandas để tránh lỗi chia cho 0
    df['Tốc độ tăng trưởng (%)'] = (
        (df['Năm sau'] - df['Năm trước']) / df['Năm trước'].replace(0, 1e-9)
    ) * 100

    # 2. Tính Tỷ trọng theo Tổng Tài sản
    # Lọc chỉ tiêu "TỔNG CỘNG TÀI SẢN"
    tong_tai_san_row = df[df['Chỉ tiêu'].str.contains('TỔNG CỘNG TÀI SẢN', case=False, na=False)]
    
    if tong_tai_san_row.empty:
        raise ValueError("Không tìm thấy chỉ tiêu 'TỔNG CỘNG TÀI SẢN'.")

    tong_tai_san_N_1 = tong_tai_san_row['Năm trước'].iloc[0]
    tong_tai_san_N = tong_tai_san_row['Năm sau'].iloc[0]

    # Xử lý giá trị 0 thủ công cho mẫu số để tránh lỗi chia cho 0 trên giá trị đơn lẻ.
    divisor_N_1 = tong_tai_san_N_1 if tong_tai_san_N_1 != 0 else 1e-9
    divisor_N = tong_tai_san_N if tong_tai_san_N != 0 else 1e-9

    # Tính tỷ trọng với mẫu số đã được xử lý
    df['Tỷ trọng Năm trước (%)'] = (df['Năm trước'] / divisor_N_1) * 100
    df['Tỷ trọng Năm sau (%)'] = (df['Năm sau'] / divisor_N) * 100
    
    return df

# --- Hàm gọi API Gemini cho Nhận xét Tự động (Chức năng 5) ---
def get_ai_analysis(data_for_ai, client):
    """Gửi dữ liệu phân tích đến Gemini API và nhận nhận xét."""
    if not client:
        return "Lỗi: Gemini Client không được khởi tạo. Vui lòng kiểm tra Khóa API."
        
    try:
        model_name = 'gemini-2.5-flash' 

        prompt = f"""
        Bạn là một chuyên gia phân tích tài chính chuyên nghiệp. Dựa trên các chỉ số tài chính sau, hãy đưa ra một nhận xét khách quan, ngắn gọn (khoảng 3-4 đoạn) về tình hình tài chính của doanh nghiệp. Đánh giá tập trung vào tốc độ tăng trưởng, thay đổi cơ cấu tài sản và khả năng thanh toán hiện hành.
        
        Dữ liệu thô và chỉ số:
        {data_for_ai}
        """

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text

    except APIError as e:
        return f"Lỗi gọi Gemini API: Vui lòng kiểm tra Khóa API hoặc giới hạn sử dụng. Chi tiết lỗi: {e}"
    except Exception as e:
        return f"Đã xảy ra lỗi không xác định: {e}"


# --- Chức năng 1: Tải File ---
uploaded_file = st.file_uploader(
    "1. Tải file Excel Báo cáo Tài chính (Chỉ tiêu | Năm trước | Năm sau)",
    type=['xlsx', 'xls']
)


if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file)
        
        # Tiền xử lý: Đảm bảo chỉ có 3 cột quan trọng
        df_raw.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        
        # Xử lý dữ liệu
        df_processed = process_financial_data(df_raw.copy())

        if df_processed is not None:
            
            # --- Chức năng 2 & 3: Hiển thị Kết quả ---
            st.subheader("2. Tốc độ Tăng trưởng & 3. Tỷ trọng Cơ cấu Tài sản")
            st.dataframe(df_processed.style.format({
                'Năm trước': '{:,.0f}',
                'Năm sau': '{:,.0f}',
                'Tốc độ tăng trưởng (%)': '{:.2f}%',
                'Tỷ trọng Năm trước (%)': '{:.2f}%',
                'Tỷ trọng Năm sau (%)': '{:.2f}%'
            }), use_container_width=True)
            
            # --- Chức năng 4: Tính Chỉ số Tài chính ---
            st.subheader("4. Các Chỉ số Tài chính Cơ bản")
            
            try:
                # Lấy Tài sản ngắn hạn
                tsnh_row = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]
                tsnh_n = tsnh_row['Năm sau'].iloc[0]
                tsnh_n_1 = tsnh_row['Năm trước'].iloc[0]

                # Lấy Nợ ngắn hạn
                no_ngan_han_row = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)] 
                no_ngan_han_N = no_ngan_han_row['Năm sau'].iloc[0] 
                no_ngan_han_N_1 = no_ngan_han_row['Năm trước'].iloc[0]

                # Tính toán, xử lý chia cho 0
                thanh_toan_hien_hanh_N = tsnh_n / no_ngan_han_N if no_ngan_han_N != 0 else float('inf')
                thanh_toan_hien_hanh_N_1 = tsnh_n_1 / no_ngan_han_N_1 if no_ngan_han_N_1 != 0 else float('inf')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="Chỉ số Thanh toán Hiện hành (Năm trước)",
                        value=f"{thanh_toan_hien_hanh_N_1:.2f} lần" if thanh_toan_hien_hanh_N_1 != float('inf') else "Không xác định"
                    )
                with col2:
                    st.metric(
                        label="Chỉ số Thanh toán Hiện hành (Năm sau)",
                        value=f"{thanh_toan_hien_hanh_N:.2f} lần" if thanh_toan_hien_hanh_N != float('inf') else "Không xác định",
                        delta=f"{thanh_toan_hien_hanh_N - thanh_toan_hien_hanh_N_1:.2f}" if thanh_toan_hien_hanh_N != float('inf') and thanh_toan_hien_hanh_N_1 != float('inf') else None
                    )
                    
            except IndexError:
                st.warning("Thiếu chỉ tiêu 'TÀI SẢN NGẮN HẠN' hoặc 'NỢ NGẮN HẠN' để tính chỉ số.")
                thanh_toan_hien_hanh_N = "N/A" # Dùng để tránh lỗi ở Chức năng 5
                thanh_toan_hien_hanh_N_1 = "N/A"
            except Exception as e:
                 st.error(f"Lỗi tính toán chỉ số: {e}")
                 thanh_toan_hien_hanh_N = "N/A" 
                 thanh_toan_hien_hanh_N_1 = "N/A"
            
            # --- Chức năng 5: Nhận xét AI ---
            st.subheader("5. Nhận xét Tình hình Tài chính (AI)")
            
            # Chuẩn bị dữ liệu để gửi cho AI
            data_for_ai = pd.DataFrame({
                'Chỉ tiêu': [
                    'Toàn bộ Bảng phân tích (dữ liệu thô)', 
                    'Tăng trưởng Tài sản ngắn hạn (%)', 
                    'Thanh toán hiện hành (N-1)', 
                    'Thanh toán hiện hành (N)'
                ],
                'Giá trị': [
                    df_processed.to_markdown(index=False),
                    f"{df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Tốc độ tăng trưởng (%)'].iloc[0]:.2f}%" if 'TÀI SẢN NGẮN HẠN' in df_processed['Chỉ tiêu'].str.upper().values else "N/A", 
                    f"{thanh_toan_hien_hanh_N_1}", 
                    f"{thanh_toan_hien_hanh_N}"
                ]
            }).to_markdown(index=False) 

            if st.button("Yêu cầu AI Phân tích"):
                if client:
                    with st.spinner('Đang gửi dữ liệu và chờ Gemini phân tích...'):
                        ai_result = get_ai_analysis(data_for_ai, client)
                        st.markdown("**Kết quả Phân tích từ Gemini AI:**")
                        st.info(ai_result)
                else:
                    st.error("Lỗi: Không tìm thấy Khóa API. Vui lòng cấu hình Khóa 'GEMINI_API_KEY' trong Streamlit Secrets.")

    except ValueError as ve:
        st.error(f"Lỗi cấu trúc dữ liệu: {ve}")
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi đọc hoặc xử lý file: {e}. Vui lòng kiểm tra định dạng file và đảm bảo cột đầu tiên là 'Chỉ tiêu'.")

else:
    st.info("Vui lòng tải lên file Excel để bắt đầu phân tích.")
    
# =========================================================================
# --- Chức năng MỚI: Khung Chat Hỏi Đáp Gemini (Chức năng 6) ---
# =========================================================================

st.divider()
st.subheader("6. Khung Chat Hỏi Đáp Gemini AI (Chuyên viên Tài chính)")

if not client:
    st.error("Để sử dụng khung chat, vui lòng cấu hình Khóa 'GEMINI_API_KEY' trong Streamlit Secrets.")
else:
    # Cấu hình chat
    MODEL_NAME = 'gemini-2.5-flash'
    SYSTEM_PROMPT = "Bạn là một chuyên gia phân tích tài chính thân thiện và giàu kinh nghiệm. Hãy trả lời các câu hỏi về tài chính, kinh tế, và các chỉ số. Hãy giữ câu trả lời ngắn gọn và chính xác. Nếu có dữ liệu Báo cáo Tài chính đã tải lên, hãy sử dụng thông tin đó để hỗ trợ trả lời các câu hỏi cụ thể."
    
    # 1. Khởi tạo đối tượng Chat và Lịch sử tin nhắn (Sử dụng client đã được cache)
    if "chat_session" not in st.session_state:
        try:
            # Thêm dữ liệu đã xử lý vào ngữ cảnh chat ban đầu
            initial_prompt = ""
            if 'df_processed' in locals() and df_processed is not None:
                initial_prompt = f"Dữ liệu Báo cáo Tài chính hiện tại (đã phân tích):\n{df_processed.to_markdown(index=False)}"
            
            st.session_state["chat_session"] = client.chats.create(
                model=MODEL_NAME,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            # Gửi initial_prompt không hiển thị
            if initial_prompt:
                st.session_state["chat_session"].send_message(initial_prompt)

            # Bổ sung tin nhắn chào mừng
            st.session_state.messages = [{"role": "model", "content": "Xin chào! Tôi là Chuyên viên Tài chính AI. Bạn có câu hỏi nào về các chỉ số tài chính hay tình hình kinh tế không?"}]

        except Exception as e:
            st.error(f"Lỗi khởi tạo Chat Session: {e}")
            st.session_state.messages = [{"role": "model", "content": "Lỗi: Không thể kết nối với Gemini AI."}]
            
    # 2. Hiển thị lịch sử trò chuyện
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Xử lý đầu vào từ người dùng
    if prompt := st.chat_input("Hỏi Gemini AI về tài chính..."):
        
        # Thêm tin nhắn của người dùng vào lịch sử và hiển thị
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Gửi tin nhắn đến mô hình Gemini và nhận phản hồi
            with st.spinner("Đang xử lý..."):
                response = st.session_state.chat_session.send_message(prompt)
                ai_response = response.text

            # Thêm phản hồi của AI vào lịch sử và hiển thị
            st.session_state.messages.append({"role": "model", "content": ai_response})
            with st.chat_message("model"):
                st.markdown(ai_response)
                
        except APIError as e:
            error_message = f"Lỗi Gemini API: {e}. Vui lòng kiểm tra khóa API và giới hạn sử dụng."
            st.error(error_message)
            st.session_state.messages.append({"role": "model", "content": error_message})
        except Exception as e:
            error_message = f"Đã xảy ra lỗi không xác định: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "model", "content": error_message})


# Nếu file chưa được tải lên, hiển thị khung chat với tin nhắn hướng dẫn
if uploaded_file is None:
    st.markdown("""
        <p style='margin-top: 1rem; color: #888;'>
        *Mẹo: Sau khi bạn tải file Báo cáo Tài chính, bạn có thể hỏi AI các câu hỏi chi tiết về dữ liệu đã tải lên trong khung chat này.*
        </p>
    """, unsafe_allow_html=True)
