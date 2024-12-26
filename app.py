##############################################
# 업비트 코인 추천 프로그램 개발_2024.12.27    #
##############################################

import streamlit as st
import pyupbit
import pandas as pd

# 서비스 제목 입력
st.markdown("<h2 style='font-size: 24px; text-align: center;'>다빈치 업비트 코인 추천기 </h2>", unsafe_allow_html=True)

# 모든 코인 목록 가져오기
def get_all_tickers():
    excluded_tickers = {"KRW-USDT", "KRW-USDC"}
    tickers = pyupbit.get_tickers(fiat="KRW")
    return [ticker for ticker in tickers if ticker not in excluded_tickers]

# 차트 데이터 가져오기
def get_chart_data(ticker, interval, count):
    try:
        data = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
        return data
    except Exception as e:
        st.warning(f"Error fetching data for {ticker}: {e}")
        return None

# 최근 분석 기간 동안의 최저, 평균, 최고 가격 및 거래량 분석
def analyze_ticker(ticker, time_frame, lookback_days):
    data = get_chart_data(ticker, time_frame, lookback_days)
    
    if data is None or data.empty:
        st.warning(f"{ticker}: 데이터가 비어있어 분석에서 제외됩니다.")
        return None

    try:
        lowest_price = data['close'].min()
        average_price = data['close'].mean()
        highest_price = data['close'].max()

        if average_price is None or average_price == 0:
            st.warning(f"{ticker}: 평균가가 0이거나 None입니다. 분석에서 제외됩니다.")
            return None

        avg_volume = data['volume'].mean()
        avg_daily_trade_amount = avg_volume * average_price
        ratio_high_avg = round(highest_price / average_price, 4)

        return {
            "코인": ticker,
            "점핑율": ratio_high_avg,
            "일평균 거래금액": avg_daily_trade_amount,
            "최저가": lowest_price,
            "평균가": average_price,
            "최고가": highest_price,
            "평균 거래량": avg_volume,
        }
    except ZeroDivisionError:
        st.warning(f"{ticker}: 평균가가 0으로 인해 ZeroDivisionError 발생. 데이터 제외.")
        return None
    except Exception as e:
        st.warning(f"{ticker}: 처리 중 예외 발생 - {e}")
        return None

# 상장된 모든 코인 분석
def analyze_all_tickers(time_frame, lookback_days):
    tickers = get_all_tickers()
    results = []
    for ticker in tickers:
        analysis = analyze_ticker(ticker, time_frame, lookback_days)
        if analysis:
            results.append(analysis)
    return results

# 포맷팅 함수
def format_average_price(value):
    return f"{value:.2f}"  # 소수점 2자리까지 유지

def format_number(value):
    if value > 1:
        return f"{int(value):,}"  # 정수로 변환 및 천단위 구분
    return f"{value:.4f}"  # 소수점 4자리 유지

# 추천 1: 바닥 다지기 + 상승 여력이 있는 코인
def recommend_low_rise_ratio(results, top_n):
    sorted_results = sorted(results, key=lambda x: x["점핑율"])
    return sorted_results[:top_n]

# 추천 2: 점핑율이 높은 코인
def recommend_high_avg_ratio(results, top_n):
    sorted_results = sorted(results, key=lambda x: x["점핑율"], reverse=True)
    return sorted_results[:top_n]

# Streamlit 앱
def main():
    st.markdown("<h2 style='font-size: 24px; text-align: left;'>코인 분석 및 추천</h2>", unsafe_allow_html=True)
    st.markdown("분석 주기는 일별 종가로 고정됩니다.")

    # 사용자 입력
    lookback_days = st.number_input(
        "분석 기간 (일 단위)", min_value=1, max_value=365, value=90, step=1
    )
    top_n = st.number_input(
        "추천할 코인 수", min_value=1, max_value=50, value=10, step=1
    )

    if st.button("분석 시작"):
        st.info("분석을 시작합니다...")
        all_results = analyze_all_tickers("day", lookback_days)
        if not all_results:
            st.error("코인 데이터를 분석하지 못했습니다.")
            return

        # 추천 1
        st.markdown("<h2 style='font-size: 24px; text-align: left;'>추천 : 상승 여력 있는 코인</h2>", unsafe_allow_html=True)
        low_rise_recommendation = recommend_low_rise_ratio(all_results, top_n)
        df_low_rise = pd.DataFrame(low_rise_recommendation)
        # 포맷팅 적용
        df_low_rise["평균가"] = df_low_rise["평균가"].apply(format_average_price)
        for col in ["평균 거래량", "일평균 거래금액"]:
            df_low_rise[col] = df_low_rise[col].apply(format_number)
        # 열 순서 변경
        cols = ["코인", "점핑율", "일평균 거래금액", "최저가", "평균가", "최고가", "평균 거래량"]
        df_low_rise = df_low_rise[cols]
        st.dataframe(df_low_rise)

        # 추천 2
        st.markdown("<h2 style='font-size: 24px; text-align: left;'>비추천 : 최근 급등한 코인</h2>", unsafe_allow_html=True)
        high_rise_recommendation = recommend_high_avg_ratio(all_results, top_n)
        df_high_rise = pd.DataFrame(high_rise_recommendation)
        # 포맷팅 적용
        df_high_rise["평균가"] = df_high_rise["평균가"].apply(format_average_price)
        for col in ["평균 거래량", "일평균 거래금액"]:
            df_high_rise[col] = df_high_rise[col].apply(format_number)
        # 열 순서 변경
        df_high_rise = df_high_rise[cols]
        st.dataframe(df_high_rise)

        st.success("분석이 완료되었습니다!")

if __name__ == "__main__":
    main()
