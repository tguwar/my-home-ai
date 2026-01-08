import streamlit as st
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials

# 1. 보안 설정 (Streamlit Cloud Secrets에서 불러옴)
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
sheet = client.open("home-finder").sheet1
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-pro')

# 3. 화면 구성
st.title("🏠 우리 집 물건 위치 비서")
user_input = st.text_input("질문하거나 위치를 알려주세요", placeholder="예: '망치 어디 있어?' 또는 '침대 밑에 상자 둠'")

if st.button("보내기") and user_input:
    data = sheet.get_all_records()
    prompt = f"현재 데이터: {data}\n사용자 입력: {user_input}\n질문이면 답변하고, 저장 요청이면 'SAVE|물건|위치'라고만 답해줘."
    
    response = model.generate_content(prompt).text
    
    if "SAVE|" in response:
        _, item, loc = response.split("|")
        sheet.append_row([item, loc.strip()])
        st.success(f"✅ '{item}' 위치를 '{loc}'로 저장했습니다!")
    else:
        st.info(response)
