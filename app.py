import streamlit as st
import google.generativeai as genai

st.title("API 모델 확인 모드")
gemini_key = st.secrets["gemini_api_key"]
genai.configure(api_key=gemini_key)

try:
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    st.write("### 사용 가능한 모델 목록:")
    st.write(models)
    st.info("위 목록에 있는 이름을 코드에 써야 합니다.")
except Exception as e:
    st.error(f"모델 목록을 가져오지 못했습니다. API 키나 설정 문제입니다: {e}")
