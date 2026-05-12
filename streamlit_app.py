# =========================================================
# CIME 유튜브 기반 영입후보 대시보드 - 경량본
#
# 저장 위치 추천:
#   project_root/07_code/streamlit_app.py
#
# 실행:
#   cd project_root/07_code
#   streamlit run streamlit_app.py
#
# 전제:
# - 파이프라인 실행 후 아래 파일 중 하나 이상 존재
#   10_dashboard/data/dashboard_candidate_table.csv
#   11_final/core_output/candidate_scored_final.csv
#   09_intermediate/snapshots/candidate_scored_snapshot.csv
# =========================================================

from pathlib import Path
import random
import textwrap
import html as html_lib
import time

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64

# =========================================================
# 0. 기본 설정 / 상수
# =========================================================

st.set_page_config(
    page_title="STAR SEED | CIME STREAM PLANET",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

MIN_TRACKING_DATE = pd.Timestamp("2026-05-01")
MIN_TRACKING_DATE_LABEL = MIN_TRACKING_DATE.strftime("%Y-%m-%d")
COSMIC_COLORS = ["#8b5cf6", "#5b7cfa", "#c94ea2", "#33c7b1", "#f09a4a", "#8fb4ff", "#b48cff"]

# =========================================================
# 성능 메모
# - 이미지 base64 변환은 파일 mtime 기준으로 캐싱한다.
# - 배경 별 DOM 노드는 64개로 제한해 화면 전환 초기 렌더링 부담을 줄인다.
# - 기존 페이지 구조와 디자인 클래스명은 유지한다.
# =========================================================

# =========================================================
# 1. 세션 상태 / 홈 카드 데이터
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "대시보드 홈"

if "card" not in st.session_state:
    st.session_state.card = None

# =========================================================
# 페이지별 버튼 primary 색상 사전 주입
# - 버튼이 렌더링되기 전에 먼저 CSS를 넣어 빨강 → 초록 플래시 방지
# - 홈: 보라
# - 스타시드: 초록
# - 스타트레일: 보라/골드
# =========================================================

def inject_button_theme_by_page():
    current_page = st.session_state.get("page", "대시보드 홈")

    if current_page == "스타시드":
        primary_bg = "linear-gradient(135deg, rgba(32, 165, 92, 0.98), rgba(12, 104, 72, 0.98))"
        primary_bg_hover = "linear-gradient(135deg, rgba(44, 190, 112, 1), rgba(16, 124, 84, 1))"
        primary_border = "rgba(131, 246, 160, 0.56)"
        primary_border_hover = "rgba(152, 255, 171, 0.74)"
        primary_shadow = "0 0 14px rgba(131, 246, 160, 0.18), inset 0 1px 0 rgba(255,255,255,0.14)"
        secondary_border = "rgba(131, 246, 160, 0.22)"
        secondary_hover_border = "rgba(131, 246, 160, 0.42)"

    elif current_page == "스타트레일":
        primary_bg = "linear-gradient(135deg, rgba(222, 167, 38, 0.98), rgba(176, 122, 20, 0.98))"
        primary_bg_hover = "linear-gradient(135deg, rgba(245, 195, 76, 1), rgba(198, 142, 30, 1))"
        primary_border = "rgba(255, 225, 126, 0.72)"
        primary_border_hover = "rgba(255, 240, 176, 0.88)"
        primary_shadow = "0 0 18px rgba(255, 212, 93, 0.26), inset 0 1px 0 rgba(255,255,255,0.18)"
        secondary_border = "rgba(255, 212, 93, 0.24)"
        secondary_hover_border = "rgba(255, 226, 135, 0.52)"

    else:
        primary_bg = "linear-gradient(135deg, #8B4DFF 0%, #6D38E8 52%, #7D42FF 100%)"
        primary_bg_hover = "linear-gradient(135deg, #9B65FF 0%, #7D42FF 56%, #8B4DFF 100%)"
        primary_border = "rgba(229, 155, 255, 0.68)"
        primary_border_hover = "rgba(240, 190, 255, 0.82)"
        primary_shadow = "0 0 20px rgba(125, 66, 255, 0.34), inset 0 1px 0 rgba(255,255,255,0.13)"
        secondary_border = "rgba(196, 143, 255, 0.28)"
        secondary_hover_border = "rgba(228, 205, 255, 0.58)"
