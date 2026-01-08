import streamlit as st
import fitz  # PyMuPDF
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
import io

# 기존에 만드신 전처리 클래스 (거의 동일합니다)
class PDFChatbotPreprocessor:
    def __init__(self, chunk_size=600, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def extract_text_from_pdf(self, pdf_file):
        # 업로드된 파일 객체에서 직접 읽기
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'-\s*\d+\s*-', '', text)
        return text.strip()

    def process(self, pdf_file):
        raw_text = self.extract_text_from_pdf(pdf_file)
        cleaned_text = self.clean_text(raw_text)
        chunks = self.text_splitter.split_text(cleaned_text)
        
        return {
            "source": pdf_file.name,
            "total_chunks": len(chunks),
            "content": [{"id": i, "text": chunk} for i, chunk in enumerate(chunks)]
        }

# --- 웹 화면 구성 ---
st.set_page_config(page_title="PDF 챗봇 데이터 생성기", page_icon="📄")

st.title("📄 PDF 업무 자동화 전처리 도구")
st.write("PDF 파일을 업로드하면 챗봇 학습용 JSON 파일로 변환해드립니다.")

# 설정 옵션 (사이드바)
st.sidebar.header("설정")
chunk_size = st.sidebar.slider("글자 자르기 단위(Chunk Size)", 100, 2000, 600)
chunk_overlap = st.sidebar.slider("중복 허용 범위(Overlap)", 0, 500, 100)

# 파일 업로더
uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type="pdf")

if uploaded_file is not None:
    st.success(f"파일 '{uploaded_file.name}' 업로드 완료!")
    
    if st.button("전처리 시작하기"):
        with st.spinner('데이터를 분석 중입니다...'):
            preprocessor = PDFChatbotPreprocessor(chunk_size, chunk_overlap)
            result_data = preprocessor.process(uploaded_file)
            
            # JSON 변환
            json_string = json.dumps(result_data, ensure_ascii=False, indent=4)
            
            st.info("전처리가 완료되었습니다!")
            
            # 다운로드 버튼 생성
            st.download_button(
                label="결과 파일(.json) 다운로드",
                data=json_string,
                file_name=f"processed_{uploaded_file.name.replace('.pdf', '')}.json",
                mime="application/json"
            )
            
            # 미리보기
            with st.expander("데이터 미리보기"):
                st.json(result_data)