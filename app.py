import streamlit as st
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials

# 1. 보안 설정
try:
    creds_dict = st.secrets["gcp_service_account"]
    gemini_key = st.secrets["gemini_api_key"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

# 2. 구글 시트 및 제미나이 연결
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# 시트 이름 확인! "home-finder"가 맞는지 꼭 확인하세요.
try:
    sheet = client.open("home-finder").sheet1
except Exception as e:
    st.error(f"구글 시트를 열 수 없습니다. 이름을 확인해주세요: {e}")
    st.stop()

genai.configure(api_key=gemini_key)
#model = genai.GenerativeModel('models/gemini-2.5-flash')
model = genai.GenerativeModel('models/gemini-2.0-flash-lite')

# 3. 화면 구성 (스마트폰 최적화 버전)
st.markdown("""
    <style>
    .main-title {
        font-size: 22px !important; 
        font-weight: bold;
        color: #BBBBBB;
        padding-top: 5px;
        padding-bottom: 5px;
    }
    </style>
    <div class="main-title">🏠 우리 집 물건 위치 비서</div>
    """, unsafe_allow_html=True)

st.write("물건의 위치를 알려주거나 물어보세요.")

# --- 폼(Form)을 사용한 전송 방지 로직 시작 ---
with st.form("input_form", clear_on_submit=False):
    user_input = st.text_input("질문하거나 위치를 알려주세요", placeholder="예: '망치 어디 있어?'")
    submit_button = st.form_submit_button("보내기")

    if submit_button and user_input:
        # 1. 시트 데이터 읽기
        all_values = sheet.get_all_values()
        
        inventory_list = []
        for row in all_values:
            if len(row) >= 2:
                inventory_list.append(f"- 물건: {row[0]}, 위치: {row[1]}")
        
        context_data = "\n".join(inventory_list)
        
        # 2. AI 지시문
        prompt = f"""
        너는 우리 집 물건 위치를 관리하는 전문 비서야. 
        아래 [목록]을 정독하고 사용자의 질문에 답해줘.

        [우리 집 물건 목록]
        {context_data}

        [사용자 입력]
        {user_input}

        [규칙]
        1. 위치 질문에는 목록을 확인하여 해당 위치만 정확히 답변해.
        2. 새로운 위치 저장 요청이면 반드시 'SAVE|물건|위치' 형식으로만 답해.
        3. 목록에 없는 물건은 "아직 위치 정보가 없어요"라고 답해줘.
        """
        
        with st.spinner('정보 확인 중...'):
            try:
                # API 호출
                response = model.generate_content(prompt).text.strip()
                
                # 3. 결과 처리
                if "SAVE|" in response:
                    parts = response.split("|")
                    if len(parts) == 3:
                        _, item, loc = parts
                        sheet.append_row([item.strip(), loc.strip()])
                        st.success(f"✅ '{item.strip()}' -> '{loc.strip()}' 저장 완료!")
                    else:
                        st.info(response)
                else:
                    st.info(response)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# --- 폼 끝 ---

# 저장된 데이터 미리보기
if st.checkbox("저장된 데이터 전체 보기"):
    st.write(sheet.get_all_records())
