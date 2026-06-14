import streamlit as st
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from io import StringIO

# Playwright 브라우저 자동 설치 (스팀릿 클라우드 환경 대응)
import os
os.system("playwright install chromium")

async def fetch_revenue(co_id):
    url = f"https://emops.twse.com.tw/server-java/t05st10_ifrs_e?step=3&caption_id=000001&co_id={co_id}&TYPEK=sii"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_selector("table", timeout=10000)
            html_content = await page.content()
        except Exception:
            await browser.close()
            return None
        
        await browser.close()
        
        tables = pd.read_html(StringIO(html_content))
        for df in tables:
            if df.shape[1] >= 2:
                df_str = str(df.values)
                if "Month" in df_str or "Revenue" in df_str or "Net Sales" in df_str:
                    return df
    return None

# --- 스팀릿 웹 UI 디자인 ---
st.title("📊 대만 기업 월별 매출 조회기")
st.write("대만 공개정보관측참(MOPS)의 실시간 데이터를 가져옵니다.")

# 기업 코드 입력창 (기본값: 1560)
company_code = st.text_input("기업 코드를 입력하세요:", value="1560")

if st.button("매출 데이터 가져오기"):
    with st.spinner("대만 서버에서 데이터를 읽어오는 중입니다. 잠시만 기다려주세요..."):
        # 비동기 함수 실행
        result_df = asyncio.run(fetch_revenue(company_code))
        
        if result_df is not None:
            st.success("데이터를 성공적으로 가져왔습니다!")
            
            # 웹 화면에 표 출력
            st.dataframe(result_df, use_container_width=True)
            
            # 엑셀 다운로드 버튼 만들기
            @st.cache_data
            def convert_df(df):
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                return output.getvalue()
                
            excel_data = convert_df(result_df)
            st.download_button(
                label="📥 엑셀 파일로 다운로드",
                data=excel_data,
                file_name=f"revenue_{company_code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("데이터를 가져오는데 실패했습니다. 기업 코드가 정확한지 확인해 주세요.")
