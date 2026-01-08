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
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 3. 화면 구성
st.markdown("""
    <style>
    .main-title {
        font-size: 22px !important;  /* 24px보다 조금 더 줄였습니다 */
        font-weight: bold;
        color: #1E1E1E;
        padding-top: 5px;
        padding-bottom: 5px;
    }
    </style>
    <div class="main-title">🏠 우리 집 물건 위치 비서</div>
    """, unsafe_allow_html=True)

st.write("물건의 위치를 알려주면 저장하고, 물어보면 찾아줍니다.")

user_input = st.text_input("질문하거나 위치를 알려주세요", placeholder="예: '망치 거실 서랍에 둠' 또는 '망치 어디 있어?'")

if st.button("보내기") and user_input:
    # 1. 모든 데이터를 값 형태로 가져옵니다. (get_all_records 대신 get_all_values 사용)
    all_values = sheet.get_all_values()
    
    # 2. 데이터를 AI가 이해하기 쉬운 텍스트 형식으로 변환합니다.
    inventory_list = []
    for row in all_values:
        if len(row) >= 2:
            inventory_list.append(f"- 물건: {row[0]}, 위치: {row[1]}")
    
    context_data = "\n".join(inventory_list)
    
    # 3. AI에게 주는 지시문(프롬프트) 강화
    prompt = f"""
    너는 우리 집 물건 위치를 관리하는 전문 비서야. 
    아래 [우리 집 물건 목록]을 반드시 한 줄씩 정독하고 사용자의 질문에 답해줘.

    [우리 집 물건 목록]
    {context_data}

    [사용자 입력]
    {user_input}

    [규칙]
    1. 사용자가 위치를 물어보면 위 목록에서 해당 물건을 찾아 그 옆에 적힌 위치만 정확히 말해줘. 
    2. 목록에 있는 물건인데 엉뚱한 위치를 말하면 절대 안 돼.
    3. 만약 새로운 위치를 알려주면(예: '~는 ~에 있어') 반드시 'SAVE|물건|위치' 형식으로 답해.
    """
    
    with st.spinner('시트를 확인하며 생각 중...'):
        response = model.generate_content(prompt).text.strip()
    
    # 저장 로직
    if "SAVE|" in response:
        try:
            parts = response.split("|")
            if len(parts) == 3:
                _, item, loc = parts
                sheet.append_row([item.strip(), loc.strip()])
                st.success(f"✅ '{item.strip()}' 위치를 '{loc.strip()}'(으)로 잘 기억해둘게요!")
            else:
                st.info(response) # 형식이 안 맞을 경우 대비
        except:
            st.error("저장 중 오류가 발생했습니다.")
    # 답변 로직
    else:
        st.info(response)

# (선택사항) 저장된 데이터 미리보기 (디버깅용)
if st.checkbox("저장된 데이터 전체 보기"):
    st.write(sheet.get_all_records())
