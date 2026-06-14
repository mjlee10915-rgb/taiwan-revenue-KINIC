import streamlit as st
import pandas as pd
import requests
from io import StringIO

def fetch_revenue_fast(co_id):
    # 대만 MOPS 서버에 직접 데이터를 요청하는 URL
    url = f"https://emops.twse.com.tw/server-java/t05st10_ifrs_e?step=3&caption_id=000001&co_id={co_id}&TYPEK=sii"
    
    # 일반 브라우저처럼 보이도록 헤더 설정 (차단 방지)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8"
    }
    
    try:
        # 1. 브라우저 없이 서버에 직접 HTML 요청
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            st.error(f"대만 서버 응답 실패 (상태 코드: {response.status_code})")
            return None
            
        # 2. 받아온 HTML에서 테이블 추출
        tables = pd.read_html(StringIO(response.text))
        
        # 3. 매출 데이터가 담긴 테이블 매칭
        for df in tables:
            if df.shape[1] >= 2:
                df_str = str(df.values)
                if "Month" in df_str or "Revenue" in df_str or "Net Sales" in df_str:
                    return df
                    
    except Exception as e:
        st.error(f"데이터 처리 중 에러 발생: {e}")
        return None
    return None

# --- 스팀릿 UI 구성 ---
st.set_page_config(page_title="대만 매출 조회", page_icon="📊", layout="wide")

st.title("📊 대만 기업 월별 매출 조회기")
st.write("대만 공개정보관측참(MOPS)의 실시간 데이터를 가져옵니다.")

company_code = st.text_input("기업 코드를 입력하세요 (예: 1560):", value="1560")

if st.button("매출 데이터 가져오기"):
    with st.spinner("대만 서버에서 데이터를 직접 다운로드 중입니다..."):
        result_df = fetch_revenue_fast(company_code)
        
        if result_df is not None:
            st.success("데이터를 성공적으로 가져왔습니다!")
            st.dataframe(result_df, use_container_width=True)
            
            # 엑셀 다운로드 기능
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                result_df.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 엑셀 파일로 다운로드",
                data=excel_data,
                file_name=f"revenue_{company_code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("데이터 테이블을 찾지 못했습니다. 기업 코드가 정확한지 확인해 주세요.")
