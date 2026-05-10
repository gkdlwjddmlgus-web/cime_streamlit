# =========================================================
# CIME 유튜브 기반 영입후보 대시보드 - Streamlit 통합본
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
#   11_final/core_output/candidate_shortlist_tracking.csv
# =========================================================

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import random
import textwrap
import html as html_lib

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
# =========================================================
# 변화 추적 최소 허용 날짜
# - 2026-05-01 이전 snapshot은 값이 불안정하므로 화면 필터에서 제외
# =========================================================

MIN_TRACKING_DATE = pd.Timestamp("2026-05-01")
MIN_TRACKING_DATE_LABEL = MIN_TRACKING_DATE.strftime("%Y-%m-%d")

# =========================================================
# 0. 페이지 설정
# =========================================================


st.set_page_config(
    page_title="STAR SEED | CIME STREAM PLANET",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 0-0. Streamlit sidebar 안정화 설정
# - 커스텀 JS 토글 제거: MutationObserver/DOM 강제 클릭으로 앱이 대기 상태에 빠지는 문제 방지
# - Streamlit 기본 사이드바 토글을 그대로 사용
# - header/toolbar를 숨기지 않음: 기본 토글 동작 보존
# =========================================================
st.markdown(
    """
    <style>
    header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        overflow: visible !important;
        background: transparent !important;
    }

    /* 기본 사이드바 토글은 숨기지 않는다. 닫힌 뒤 다시 여는 핵심 컨트롤임 */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] *,
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="사이드바 열기"],
    button[aria-label="사이드바 닫기"],
    button[title="Open sidebar"],
    button[title="Close sidebar"],
    button[title="사이드바 열기"],
    button[title="사이드바 닫기"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        overflow: visible !important;
        z-index: 1000000 !important;
    }

    .block-container {
        padding-top: 0.25rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 0-0-1. Streamlit 우측 상단 액션 버튼 숨김 - 토글 보존형
# - header/stToolbar 컨테이너는 절대 숨기지 않음
# - 사이드바 토글은 Streamlit 기본 컨트롤이므로 항상 보존
# - Share / Deploy / GitHub / Star / Fork 등 우측 액션 "개별 버튼"만 숨김
# =========================================================
st.markdown(
    """
    <style>
    /* header는 보존: 사이드바 토글 이벤트가 header 내부 컨트롤에 의존할 수 있음 */
    header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    header [data-testid="stToolbar"],
    [data-testid="stToolbar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background: transparent !important;
        overflow: visible !important;
    }

    /*
      중요:
      stHeaderActionElements / stToolbar / stToolbarActionButton 컨테이너 전체를 숨기면
      Streamlit 버전에 따라 sidebar open/close 토글까지 같이 사라질 수 있음.
      따라서 우측 액션으로 식별 가능한 개별 버튼/링크만 숨긴다.
    */
    header button[title="Share"],
    header button[aria-label="Share"],
    header a[title="Share"],
    header a[aria-label="Share"],
    header button[title*="Share"],
    header button[aria-label*="Share"],
    header a[title*="Share"],
    header a[aria-label*="Share"],
    header button[title="Deploy"],
    header button[aria-label="Deploy"],
    header a[title="Deploy"],
    header a[aria-label="Deploy"],
    header button[title*="Deploy"],
    header button[aria-label*="Deploy"],
    header a[title*="Deploy"],
    header a[aria-label*="Deploy"],
    header button[title*="GitHub"],
    header a[title*="GitHub"],
    header button[aria-label*="GitHub"],
    header a[aria-label*="GitHub"],
    header button[title="Fork"],
    header button[aria-label="Fork"],
    header a[title="Fork"],
    header a[aria-label="Fork"],
    header button[title*="Fork"],
    header button[aria-label*="Fork"],
    header a[title*="Fork"],
    header a[aria-label*="Fork"],
    header button[title="Star"],
    header button[aria-label="Star"],
    header a[title="Star"],
    header a[aria-label="Star"],
    header button[title*="Star"],
    header button[aria-label*="Star"],
    header a[title*="Star"],
    header a[aria-label*="Star"],
    [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"],
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    .stAppDeployButton {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /*
      GitHub/Share/Star 아이콘이 title/aria-label 없이 우측 액션 영역 버튼으로만 잡히는 경우:
      - 사이드바 토글은 보통 left: 0 근처에 렌더링됨
      - 우측 toolbar 버튼만 시각적으로 숨김
      - 단, Open/Close sidebar 라벨이 있는 버튼은 아래 보존 규칙으로 다시 살림
    */
    header button[style*="right"],
    header a[style*="right"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* 좌측 사이드바 토글은 최종적으로 반드시 보존 */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] *,
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="사이드바 열기"],
    button[aria-label="사이드바 닫기"],
    button[title="Open sidebar"],
    button[title="Close sidebar"],
    button[title="사이드바 열기"],
    button[title="사이드바 닫기"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: auto !important;
        min-width: auto !important;
        max-width: none !important;
        height: auto !important;
        min-height: auto !important;
        max-height: none !important;
        padding: initial !important;
        margin: initial !important;
        pointer-events: auto !important;
        overflow: visible !important;
        z-index: 1000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 0-1. CIME STREAM PLANET 네비게이션 상태
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "대시보드 홈"

if "card" not in st.session_state:
    st.session_state.card = None

if "bg_html" not in st.session_state:
    random.seed(42)
    stars = []
    for _ in range(180):
        size = random.uniform(1.2, 4.2)
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        delay = random.uniform(0, 7)
        duration = random.uniform(2.0, 6.0)
        opacity = random.uniform(0.65, 1.0)
        stars.append(
            f'<div class="twinkle-star" style="'
            f'width:{size:.1f}px;height:{size:.1f}px;'
            f'left:{x:.1f}%;top:{y:.1f}%;'
            f'--max-opacity:{opacity:.2f};'
            f'animation-delay:{delay:.1f}s;'
            f'animation-duration:{duration:.1f}s;"></div>'
        )
    st.session_state.bg_html = "".join(stars)

STARTRAIL_SEGMENTS = [
    {
        "num": "01",
        "ko": "성단",
        "en": "Star Cluster",
        "icon": "⭐",
        "icon_class": "icon-cluster",
        "purpose": '팬덤이 함께 이동할 가능성이 높은<br><span class="purpose-key">그룹형 후보군</span>',
        "criteria": "그룹/소속성, 팬덤 결집, 멤버 단위 이동 가능성",
        "point": "여러 스트리머와 팬덤을 함께 유입시켜 초기 트래픽을 빠르게 확보합니다.",
    },
    {
        "num": "02",
        "ko": "프로토스타",
        "en": "Protostar",
        "icon": "🌱",
        "icon_class": "icon-protostar",
        "purpose": '현재 규모는 작지만 방송 반응이 좋은<br><span class="purpose-key">성장형 후보군</span>',
        "criteria": "시청자 반응, 채팅, 뷰어십, 팔로워 대비 성과",
        "point": "성장 가능성이 높은 후보를 조기에 발굴해 CIME의 육성 타깃으로 활용합니다.",
    },
    {
        "num": "03",
        "ko": "위성",
        "en": "Satellite",
        "icon": "🛰️",
        "icon_class": "icon-satellite",
        "purpose": '소속 없이도 방송 성과가 검증된<br><span class="purpose-key">개인형 후보군</span>',
        "criteria": "도네이션, 채팅화력, 평균 시청자, 개인 활동 여부",
        "point": "검증된 개인 방송 화력을 바탕으로 안정적인 콘텐츠와 수익성을 확보합니다.",
    },
    {
        "num": "04",
        "ko": "슈퍼노바",
        "en": "Supernova",
        "icon": "💥",
        "icon_class": "icon-supernova",
        "purpose": '대중성과 팬덤 규모가 큰<br><span class="purpose-key">간판형 후보군</span>',
        "criteria": "팔로워, 최고 시청자, 유튜브 구독자, 팬덤지수, 방송화력",
        "point": "인지도 높은 스트리머를 통해 플랫폼 주목도와 외부 유입을 높입니다.",
    },
    {
        "num": "05",
        "ko": "코멧",
        "en": "Comet",
        "icon": "☄️",
        "icon_class": "icon-comet",
        "purpose": '방송 외 다른곳에서 인지도가 높은<br><span class="purpose-key">발견형 후보군</span>',
        "criteria": "유튜브 구독자, X 팔로워, 유튜브/X 유입지수, 플랫폼 대비 외부 체급",
        "point": "외부 팬덤을 CIME으로 연결해 새로운 이용자 유입을 만듭니다.",
    },
]

TRAIL_ICON_HTML = """
<div class="trail-spark-icon">
    <div class="trail-line trail-line-1"></div>
    <div class="trail-line trail-line-2"></div>
    <div class="trail-line trail-line-3"></div>
    <div class="trail-star trail-star-main">✦</div>
    <div class="trail-star trail-star-small">✦</div>
    <div class="trail-star trail-star-tiny">✦</div>
    <div class="trail-dot trail-dot-1"></div>
    <div class="trail-dot trail-dot-2"></div>
</div>
"""

SEED_ICON_HTML = """
<div class="seed-search-icon">
    <div class="seed-lens"></div>
    <div class="seed-handle"></div>
    <div class="seed-star-core">✦</div>
    <div class="seed-sparkle-1">✦</div>
    <div class="seed-sparkle-2">✦</div>
    <div class="seed-dot-1"></div>
    <div class="seed-dot-2"></div>
</div>
"""


STAR_SEED_CARDS = [
    {
        "num": "01",
        "icon": "search",
        "title": "후보 수집 기준",
        "desc": "유튜브 활동 채널 중<br>영입 검토 가능한 후보를 모읍니다.",
    },
    {
        "num": "02",
        "icon": "chat",
        "title": "팬 반응 밀도",
        "desc": "조회수 대비 좋아요·댓글로<br>팬덤 반응 강도를 봅니다.",
    },
    {
        "num": "03",
        "icon": "live",
        "title": "라이브 전환성",
        "desc": "콘텐츠 유형과 라이브 신호로<br>방송 전환 가능성을 봅니다.",
    },
    {
        "num": "04",
        "icon": "filter",
        "title": "실전 리스크",
        "desc": "기관·방송사·팬클립 등<br>영입 제외 대상을 구분합니다.",
    },
    {
        "num": "05",
        "icon": "check",
        "title": "액션버킷",
        "desc": "점수와 리스크를 함께 보고<br>검토 우선순위를 나눕니다.",
    },
]



def clean_html(markup: str) -> str:
    return "\n".join(line.strip() for line in textwrap.dedent(markup).strip().splitlines())


def html(markup: str) -> None:
    st.markdown(clean_html(markup), unsafe_allow_html=True)


# =========================================================
# 1. CSS
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #070b16 0%, #0d1324 45%, #070b16 100%);
        color: #f5f7fb;
    }

    section[data-testid="stSidebar"] {
        background: #0b1020;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .main-title {
        font-size: 34px;
        font-weight: 850;
        color: #ffffff;
        margin-bottom: 0px;
    }

    .sub-title {
        font-size: 14px;
        color: #a9b1c7;
        margin-top: 0px;
        margin-bottom: 20px;
    }

    .kpi-card {
        background: linear-gradient(145deg, rgba(30, 38, 62, 0.95), rgba(12, 18, 34, 0.95));
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 18px;
        padding: 20px 22px;
        min-height: 128px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.28);
    }

    .kpi-label {
        font-size: 14px;
        color: #aeb7cc;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 34px;
        font-weight: 850;
        color: #ffffff;
        margin-bottom: 4px;
    }

    .kpi-sub {
        font-size: 12px;
        color: #8c96ad;
    }


    .kpi-delta {
        font-size: 14px;
        font-weight: 800;
        margin-top: 8px;
        display: inline-block;
    }

    .kpi-up {
        color: #ff5b5b;
    }

    .kpi-down {
        color: #4da3ff;
    }

    .kpi-flat {
        color: #aeb7cc;
    }

    .candidate-card {
        background: linear-gradient(145deg, rgba(30, 38, 62, 0.95), rgba(12, 18, 34, 0.95));
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 18px;
        padding: 18px 18px;
        min-height: 250px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.24);
        position: relative;
    }

    .rank-badge {
        position: absolute;
        top: 14px;
        left: 14px;
        background: linear-gradient(135deg, #ffd85a, #ff9f43);
        color: #121212;
        font-weight: 850;
        border-radius: 8px;
        padding: 4px 9px;
        font-size: 14px;
    }

    .candidate-avatar {
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c4dff, #00d4ff);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        font-weight: 850;
        margin: 16px auto 12px auto;
        color: white;
        border: 2px solid rgba(255,255,255,0.35);
    }

    .candidate-name {
        text-align: center;
        color: white;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 8px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    .segment-pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(124,77,255,0.24);
        border: 1px solid rgba(124,77,255,0.35);
        color: #d7c7ff;
        font-size: 12px;
        font-weight: 700;
        margin: 2px;
    }

    .score-text {
        text-align: center;
        color: #b66cff;
        font-size: 30px;
        font-weight: 900;
        margin-top: 8px;
    }

    .small-muted {
        color: #9aa4bb;
        font-size: 12px;
    }

    .section-card {
        background: rgba(15, 22, 40, 0.92);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.20);
    }

    .detail-title {
        color: #ffffff;
        font-size: 22px;
        font-weight: 850;
        margin-bottom: 6px;
    }

    .reason-box {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 12px;
        color: #d8deed;
        font-size: 13px;
        margin-top: 10px;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 12px;
    }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }


    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(124,77,255,0.0), rgba(124,77,255,0.55), rgba(0,212,255,0.35), rgba(124,77,255,0.0));
        margin: 22px 0 18px 0;
    }

    .explain-box {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 16px;
        color: #d8deed;
        font-size: 14px;
        line-height: 1.65;
    }

    .guide-box {
        background: rgba(124,77,255,0.10);
        border: 1px solid rgba(124,77,255,0.24);
        border-radius: 14px;
        padding: 13px 15px;
        color: #d8deed;
        font-size: 13px;
        line-height: 1.6;
        margin-bottom: 12px;
    }

    .chart-caption {
        color: #aeb7cc;
        font-size: 12px;
        line-height: 1.55;
        margin-top: -4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 1-1. Cosmic Mission Control 스타일 오버라이드
# - 하단 디버그 expander 제거 버전
# - 전체 화면을 우주 관제실 느낌으로 통일
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800&display=swap');

    .stApp {
        background:
            radial-gradient(circle at 70% 8%, rgba(52, 255, 224, 0.20) 0, transparent 23%),
            radial-gradient(circle at 18% 18%, rgba(94, 112, 255, 0.18) 0, transparent 26%),
            radial-gradient(circle at 92% 72%, rgba(255, 63, 190, 0.12) 0, transparent 22%),
            linear-gradient(145deg, #020612 0%, #07111f 42%, #02040b 100%);
        color: #efffff;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image:
            radial-gradient(circle, rgba(255,255,255,0.78) 0.7px, transparent 1.2px),
            radial-gradient(circle, rgba(80,255,230,0.42) 0.6px, transparent 1.3px);
        background-size: 46px 46px, 91px 91px;
        background-position: 0 0, 18px 24px;
        opacity: 0.20;
    }

    .block-container {
        position: relative;
        z-index: 1;
        padding-top: 2.2rem;
        max-width: 1500px;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(4,12,25,0.98), rgba(2,7,15,0.98)),
            radial-gradient(circle at 50% 0%, rgba(39, 255, 218, 0.18), transparent 40%);
        border-right: 1px solid rgba(71,255,226,0.24);
        box-shadow: 12px 0 30px rgba(0, 255, 224, 0.05);
    }

    section[data-testid="stSidebar"] * {
        color: #dffdf8;
    }

    .mission-sidebar-title {
        padding: 10px 6px 18px 6px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(61,255,220,0.18);
    }

    .mission-sidebar-logo {
        font-family: 'Orbitron', sans-serif;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 1.6px;
        color: #63ffea;
        text-shadow: 0 0 18px rgba(99,255,234,0.75);
        line-height: 1.0;
    }

    .mission-sidebar-sub {
        font-size: 10px;
        letter-spacing: 2px;
        color: #8fb8c6;
        margin-top: 4px;
    }

    .mission-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(70,255,226,0.28);
        border-radius: 26px;
        padding: 30px 34px;
        margin-bottom: 24px;
        background:
            radial-gradient(circle at 70% 45%, rgba(65,255,226,0.28), transparent 18%),
            radial-gradient(circle at 86% 30%, rgba(255,76,216,0.14), transparent 16%),
            linear-gradient(135deg, rgba(7,20,38,0.96), rgba(3,8,20,0.94));
        box-shadow:
            0 0 0 1px rgba(255,255,255,0.035) inset,
            0 24px 60px rgba(0,0,0,0.36),
            0 0 40px rgba(48,255,225,0.08);
    }

    .mission-hero::after {
        content: "";
        position: absolute;
        right: 60px;
        top: 26px;
        width: 260px;
        height: 260px;
        border-radius: 50%;
        background:
            radial-gradient(circle at 36% 34%, rgba(255,255,255,0.92), rgba(89,255,232,0.72) 10%, rgba(31,172,162,0.20) 34%, transparent 62%);
        box-shadow: 0 0 38px rgba(77,255,232,0.42), inset 0 0 28px rgba(255,255,255,0.24);
        opacity: 0.55;
        filter: blur(0.2px);
    }

    .mission-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 1.4px;
        color: #f7ffff;
        text-shadow: 0 0 22px rgba(77,255,232,0.36);
        margin: 0;
        position: relative;
        z-index: 1;
    }

    .mission-highlight {
        color: #5fffe8;
        text-shadow: 0 0 18px rgba(95,255,232,0.80);
    }

    .mission-subtitle {
        color: #8efbea;
        font-size: 16px;
        font-weight: 700;
        margin-top: 12px;
        position: relative;
        z-index: 1;
    }

    .mission-desc {
        color: #b7c6d6;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 14px;
        max-width: 720px;
        position: relative;
        z-index: 1;
    }

    .mission-time-pill {
        display: inline-block;
        padding: 8px 12px;
        border: 1px solid rgba(92,255,232,0.28);
        border-radius: 999px;
        background: rgba(7,18,31,0.72);
        color: #bafdf3;
        box-shadow: 0 0 22px rgba(69,255,222,0.08) inset;
    }

    .kpi-card,
    .candidate-card,
    .section-card,
    div[data-testid="stMetric"] {
        background:
            linear-gradient(145deg, rgba(11, 29, 52, 0.88), rgba(5, 12, 26, 0.92));
        border: 1px solid rgba(83,255,226,0.18);
        box-shadow:
            0 18px 38px rgba(0,0,0,0.38),
            0 0 24px rgba(59,255,226,0.06),
            inset 0 1px 0 rgba(255,255,255,0.05);
        backdrop-filter: blur(6px);
    }

    .kpi-card:hover,
    .candidate-card:hover,
    .section-card:hover {
        border-color: rgba(97,255,232,0.34);
        box-shadow:
            0 22px 48px rgba(0,0,0,0.46),
            0 0 34px rgba(73,255,226,0.11),
            inset 0 1px 0 rgba(255,255,255,0.08);
    }

    .kpi-label,
    .small-muted,
    .chart-caption,
    .kpi-sub,
    .sub-title {
        color: #98adbf;
    }

    .kpi-value,
    .detail-title,
    h1, h2, h3 {
        color: #f4ffff !important;
        text-shadow: 0 0 14px rgba(90,255,232,0.18);
    }

    .score-text {
        color: #78ffee;
        text-shadow: 0 0 16px rgba(120,255,238,0.65);
    }

    .segment-pill {
        background: rgba(36,255,218,0.10);
        border: 1px solid rgba(75,255,230,0.28);
        color: #bffdf5;
        box-shadow: inset 0 0 18px rgba(30,255,218,0.04);
    }

    .rank-badge {
        background: linear-gradient(135deg, #fcf3a4, #ffe35a, #ffb347);
        color: #10131a;
        box-shadow: 0 0 18px rgba(255,218,90,0.35);
    }

    .candidate-avatar {
        background: radial-gradient(circle at 32% 28%, #ffffff, #69ffee 17%, #1f9df5 52%, #6b4dff 100%);
        box-shadow: 0 0 28px rgba(89,255,232,0.35);
        border: 1px solid rgba(255,255,255,0.52);
    }

    .reason-box,
    .explain-box,
    .guide-box {
        background: rgba(7, 20, 37, 0.74);
        border: 1px solid rgba(86,255,226,0.16);
        color: #d8f7f3;
    }

    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(59,255,226,0), rgba(59,255,226,0.68), rgba(255,82,211,0.38), rgba(59,255,226,0));
        margin: 26px 0 20px 0;
    }

    div[data-testid="stExpander"] {
        border: 1px solid rgba(86,255,226,0.15) !important;
        border-radius: 14px !important;
        background: rgba(5, 13, 27, 0.60) !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(86,255,226,0.14);
        border-radius: 14px;
        overflow: hidden;
    }

    button,
    .stButton > button,
    .stDownloadButton > button {
        border: 1px solid rgba(83,255,226,0.32) !important;
        background: linear-gradient(135deg, rgba(20,56,83,0.95), rgba(7,20,39,0.95)) !important;
        color: #dffff9 !important;
        border-radius: 12px !important;
        box-shadow: 0 0 18px rgba(69,255,225,0.10) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 1-2. Clean Cosmic 정돈형 스타일 오버라이드
# - 기존 코스믹 분위기는 유지하되, 캡처 참고처럼 카드/표/설명 영역을 정돈된 레이아웃으로 통일
# - 과한 글로우와 배경 노이즈를 줄이고, 섹션 간 경계/여백/카드 높이를 안정화
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --cime-bg-0: #050917;
        --cime-bg-1: #081426;
        --cime-card: rgba(10, 22, 40, 0.88);
        --cime-card-strong: rgba(13, 30, 54, 0.94);
        --cime-line: rgba(118, 242, 226, 0.18);
        --cime-line-strong: rgba(118, 242, 226, 0.34);
        --cime-text: #efffff;
        --cime-muted: #a9b9c9;
        --cime-accent: #5fffe8;
        --cime-blue: #7fb7ff;
        --cime-pink: #ff6edb;
        --cime-gold: #ffd76a;
    }

    .stApp {
        background:
            radial-gradient(circle at 78% 6%, rgba(95, 255, 232, 0.13) 0, transparent 22%),
            radial-gradient(circle at 8% 16%, rgba(95, 135, 255, 0.10) 0, transparent 24%),
            linear-gradient(145deg, var(--cime-bg-0) 0%, var(--cime-bg-1) 46%, #040712 100%);
        color: var(--cime-text);
    }

    .stApp::before {
        opacity: 0.09;
        background-size: 72px 72px, 128px 128px;
    }

    .block-container {
        max-width: 1480px;
        padding-top: 1.6rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.035em;
        line-height: 1.18;
        text-shadow: none !important;
    }

    h3 {
        margin-top: 0.2rem !important;
        margin-bottom: 0.85rem !important;
        font-size: 1.38rem !important;
    }

    .mission-hero {
        border-radius: 24px;
        padding: 28px 34px;
        margin-bottom: 22px;
        background:
            radial-gradient(circle at 72% 42%, rgba(95,255,232,0.20), transparent 18%),
            radial-gradient(circle at 87% 27%, rgba(255,110,219,0.11), transparent 14%),
            linear-gradient(135deg, rgba(10,26,48,0.94), rgba(5,12,26,0.96));
        border: 1px solid var(--cime-line-strong);
        box-shadow: 0 18px 46px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.06);
    }

    .mission-hero::after {
        width: 210px;
        height: 210px;
        right: 70px;
        top: 34px;
        opacity: 0.35;
        filter: blur(0.4px);
    }

    .mission-title {
        font-size: 38px;
        letter-spacing: 0.8px;
    }

    .mission-subtitle {
        color: var(--cime-accent);
        font-size: 15px;
        margin-top: 10px;
    }

    .mission-desc {
        color: var(--cime-muted);
        max-width: 760px;
        font-size: 13.5px;
        margin-top: 12px;
    }

    .mission-time-pill {
        background: rgba(6, 17, 33, 0.82);
        border: 1px solid var(--cime-line);
        color: #d8fff8;
        box-shadow: none;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(5, 13, 28, 0.98), rgba(3, 8, 18, 0.98));
        border-right: 1px solid rgba(118,242,226,0.20);
        box-shadow: 8px 0 26px rgba(0,0,0,0.22);
    }

    .mission-sidebar-title {
        border-bottom: 1px solid rgba(118,242,226,0.16);
        padding-bottom: 14px;
    }

    .mission-sidebar-logo {
        font-size: 25px;
        color: var(--cime-accent);
        text-shadow: 0 0 12px rgba(95,255,232,0.35);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {
        font-size: 0.9rem;
    }

    .kpi-card,
    .candidate-card,
    .section-card,
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(11,25,45,0.94), rgba(7,16,31,0.96));
        border: 1px solid var(--cime-line);
        border-radius: 20px;
        box-shadow: 0 14px 34px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.055);
        backdrop-filter: blur(4px);
    }

    .kpi-card:hover,
    .candidate-card:hover,
    .section-card:hover {
        border-color: var(--cime-line-strong);
        box-shadow: 0 16px 38px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.075);
        transform: translateY(-1px);
        transition: 0.16s ease;
    }

    .kpi-card {
        min-height: 142px;
        padding: 20px 22px 18px 22px;
    }

    .kpi-label {
        color: #bfd0dc;
        font-size: 13px;
        font-weight: 760;
        letter-spacing: -0.01em;
    }

    .kpi-value {
        font-size: 34px;
        font-weight: 900;
        color: #f7ffff;
        margin: 9px 0 2px 0;
    }

    .kpi-sub {
        color: #8ea0b2;
        font-size: 11.8px;
        line-height: 1.45;
        margin-top: 7px;
    }

    .kpi-delta {
        padding: 4px 8px;
        border-radius: 999px;
        background: rgba(255,255,255,0.045);
        font-size: 12px;
        margin-top: 8px;
    }

    .kpi-up { color: #ff7a7a; }
    .kpi-down { color: #69b4ff; }
    .kpi-flat { color: #b5c3ce; }

    .candidate-card {
        min-height: 245px;
        padding: 18px;
    }

    .candidate-avatar {
        width: 66px;
        height: 66px;
        font-size: 27px;
        margin: 14px auto 12px auto;
        box-shadow: 0 0 18px rgba(95,255,232,0.20);
    }

    .candidate-name {
        font-size: 16px;
        letter-spacing: -0.02em;
    }

    .score-text {
        color: var(--cime-accent);
        font-size: 28px;
        text-shadow: 0 0 10px rgba(95,255,232,0.34);
    }

    .section-card {
        padding: 20px 22px;
        margin-bottom: 0.35rem;
    }

    .section-card > div:first-child,
    .section-card h3:first-child {
        margin-top: 0 !important;
    }

    .section-divider {
        height: 1px;
        margin: 30px 0 22px 0;
        background: linear-gradient(90deg, transparent, rgba(95,255,232,0.30), rgba(255,110,219,0.18), transparent);
    }

    .segment-pill {
        background: rgba(95, 255, 232, 0.08);
        border: 1px solid rgba(95, 255, 232, 0.22);
        color: #d7fffa;
        box-shadow: none;
        padding: 5px 10px;
    }

    .rank-badge {
        background: linear-gradient(135deg, #fff0a6, #ffd76a);
        color: #111624;
        box-shadow: none;
    }

    .reason-box,
    .explain-box,
    .guide-box {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.085);
        border-radius: 14px;
        color: #dceaf1;
        line-height: 1.65;
    }

    .guide-box {
        background: rgba(95,255,232,0.065);
        border-left: 3px solid rgba(95,255,232,0.55);
    }

    .chart-caption {
        color: #9eb0bf;
        font-size: 12.5px;
        line-height: 1.58;
        margin-top: 4px;
    }

    div[data-testid="stExpander"] {
        background: rgba(8,18,34,0.78) !important;
        border: 1px solid rgba(118,242,226,0.16) !important;
        border-radius: 15px !important;
        box-shadow: none !important;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 750;
        color: #e9fffb !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(118,242,226,0.14);
        border-radius: 14px;
        overflow: hidden;
    }

    .stDataFrame div[role="grid"] {
        background: rgba(5, 12, 24, 0.72) !important;
    }

    button,
    .stButton > button,
    .stDownloadButton > button {
        border: 1px solid rgba(118,242,226,0.25) !important;
        background: linear-gradient(135deg, rgba(16,42,65,0.96), rgba(7,18,36,0.96)) !important;
        color: #eafffb !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        font-weight: 700 !important;
    }

    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background: rgba(7,18,34,0.85) !important;
        border-color: rgba(118,242,226,0.18) !important;
        border-radius: 12px !important;
    }

    .js-plotly-plot .plotly .modebar {
        opacity: 0.35;
    }

    hr {
        border-color: rgba(118,242,226,0.16) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# 1-3. CIME STREAM PLANET 홈 화면 스타일 - 첫 번째 파일 기준 적용
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        .stApp {
            background:
                radial-gradient(circle at 56% 31%, rgba(127, 47, 255, 0.42), transparent 28%),
                radial-gradient(circle at 60% 79%, rgba(121, 51, 255, 0.16), transparent 32%),
                linear-gradient(180deg, #050411 0%, #09051C 52%, #050411 100%);
            color: #F8F2FF;
        }

        [data-testid="stHeader"] {
            background: rgba(8, 12, 22, 0.96);
        }

        .block-container {
            max-width: 1540px;
            padding-top: 2.2rem;
            padding-left: 4.7rem;
            padding-right: 4.7rem;
            padding-bottom: 5rem;
        }

        h1, h2, h3, p {
            color: inherit;
        }

        .star-layer {
            position: fixed;
            left: 300px;
            top: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .twinkle-star {
            position: absolute;
            border-radius: 50%;
            background: white;
            pointer-events: none;
            z-index: 0;
            box-shadow:
                0 0 10px rgba(255,255,255,0.95),
                0 0 20px rgba(198,168,255,0.60);
            animation-name: twinkle;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
        }

        .twinkle-star:nth-child(3n) {
            background: #C8A8FF;
            box-shadow:
                0 0 12px rgba(200,168,255,0.95),
                0 0 25px rgba(139,92,255,0.58);
        }

        .twinkle-star:nth-child(5n) {
            background: #FF9DF5;
            box-shadow:
                0 0 12px rgba(255,157,245,0.95),
                0 0 25px rgba(255,120,230,0.50);
        }

        @keyframes twinkle {
            0%, 100% {
                opacity: 0.16;
                transform: scale(0.65);
                filter: brightness(0.75);
            }
            45% {
                opacity: var(--max-opacity);
                transform: scale(1.50);
                filter: brightness(1.7);
            }
            65% {
                opacity: 0.45;
                transform: scale(0.95);
                filter: brightness(1.05);
            }
        }

        .orbit-bg {
            position: fixed;
            left: 300px;
            top: 0;
            right: 0;
            bottom: 0;
            z-index: 0;
            pointer-events: none;
            opacity: 0.42;
            background:
                linear-gradient(150deg, transparent 15%, rgba(157, 88, 255, 0.13) 15.4%, transparent 16.5%),
                linear-gradient(150deg, transparent 34%, rgba(157, 88, 255, 0.09) 34.4%, transparent 35.5%),
                linear-gradient(150deg, transparent 54%, rgba(238, 142, 255, 0.08) 54.4%, transparent 55.5%);
            animation: drift 9s ease-in-out infinite alternate;
        }

        @keyframes drift {
            from { transform: translateY(0px); opacity: 0.28; }
            to { transform: translateY(-18px); opacity: 0.48; }
        }

        [data-testid="stSidebar"] {
            background: #0A061E;
            border-right: 1px solid rgba(154, 98, 255, 0.45);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 4.4rem;
        }

        .sidebar-title {
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 1px;
            color: #FFF9FF;
            margin-bottom: 18px;
        }

        .sidebar-subtitle {
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.2px;
            color: #D9C8FF;
            margin-bottom: 64px;
        }

        .sidebar-line {
            height: 1px;
            background: rgba(185, 147, 255, 0.28);
            margin: 0 0 24px 0;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            height: 43px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 850;
            letter-spacing: -0.3px;
            margin-bottom: 8px;
            transition: all 0.18s ease;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: #7D42FF !important;
            color: white !important;
            border: 1px solid rgba(229,155,255,0.65) !important;
            box-shadow: 0 0 18px rgba(125,66,255,0.25);
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: rgba(255,255,255,0.93) !important;
            color: #251A42 !important;
            border: 1px solid rgba(184,165,217,0.42) !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 18px rgba(125,66,255,0.32);
        }

        .main-wrap {
            position: relative;
            z-index: 2;
            text-align: center;
        }

        .hero-title {
            font-size: 58px;
            font-weight: 950;
            letter-spacing: 9px;
            line-height: 1;
            color: #FFF8FF;
            text-shadow: 0 0 22px rgba(230, 195, 255, 0.35);
            margin-top: 4px;
            margin-bottom: 14px;
        }

        .hero-subtitle {
            font-size: 19px;
            font-weight: 750;
            color: #C6BBD9;
            margin-bottom: 10px;
        }

        .planet-area {
            position: relative;
            height: 360px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: -10px;
            margin-bottom: 12px;
        }

        .planet-glow {
            position: absolute;
            width: 470px;
            height: 470px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(139,53,255,0.45) 0%, rgba(139,53,255,0.18) 34%, transparent 68%);
            filter: blur(14px);
            animation: planetPulse 4s ease-in-out infinite alternate;
        }

        @keyframes planetPulse {
            from { opacity: 0.78; transform: scale(0.98); }
            to { opacity: 1; transform: scale(1.03); }
        }

        .planet-orbit {
            position: absolute;
            width: 840px;
            height: 235px;
            border: 2px solid rgba(179,93,255,0.46);
            border-radius: 50%;
            transform: rotate(-2deg);
            box-shadow: 0 0 26px rgba(179,93,255,0.16);
        }

        .planet-orbit.orbit-2 {
            width: 660px;
            height: 185px;
            border-color: rgba(239,156,255,0.42);
            transform: rotate(1deg);
        }

        .planet-orbit.orbit-3 {
            width: 980px;
            height: 310px;
            border-color: rgba(125,66,255,0.20);
            transform: rotate(-4deg);
        }

        .planet {
            position: relative;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background:
                radial-gradient(circle at 72% 28%, rgba(246,166,255,0.55), transparent 20%),
                radial-gradient(circle at 58% 44%, rgba(147,55,255,0.95), transparent 38%),
                radial-gradient(circle at 42% 58%, rgba(42,8,110,0.95), transparent 48%),
                radial-gradient(circle at 50% 50%, #4812A7 0%, #270066 48%, #08011B 100%);
            box-shadow:
                0 0 34px rgba(246,166,255,0.62),
                0 0 100px rgba(139,53,255,0.55),
                inset 22px 18px 48px rgba(255,170,255,0.20),
                inset -48px -44px 78px rgba(0,0,0,0.55);
            overflow: hidden;
            animation: floatPlanet 5.4s ease-in-out infinite alternate;
        }

        @keyframes floatPlanet {
            from { transform: translateY(0px); }
            to { transform: translateY(-10px); }
        }

        .planet::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background:
                radial-gradient(ellipse at 32% 25%, rgba(20,0,70,0.70) 0 7%, transparent 14%),
                radial-gradient(ellipse at 62% 20%, rgba(25,0,72,0.68) 0 8%, transparent 15%),
                radial-gradient(ellipse at 45% 45%, rgba(105,32,205,0.35) 0 8%, transparent 18%),
                radial-gradient(ellipse at 70% 58%, rgba(12,0,38,0.54) 0 10%, transparent 19%),
                radial-gradient(ellipse at 31% 70%, rgba(96,24,190,0.32) 0 9%, transparent 18%),
                linear-gradient(178deg, transparent 0%, rgba(255,132,255,0.12) 45%, transparent 49%, rgba(0,0,0,0.22) 80%);
            filter: blur(0.4px);
            opacity: 0.9;
        }

        .planet::after {
            content: "";
            position: absolute;
            inset: 6px;
            border-radius: 50%;
            border-top: 5px solid rgba(246,166,255,0.72);
            border-right: 4px solid rgba(246,166,255,0.35);
            box-shadow: inset -48px -44px 70px rgba(0,0,0,0.35);
        }

        .planet-logo {
            position: absolute;
            inset: 0;
            z-index: 2;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            font-weight: 950;
            letter-spacing: 5px;
            color: #FFF8FF;
            text-shadow:
                0 0 10px rgba(255,255,255,0.85),
                0 0 22px rgba(234,203,255,0.9),
                0 0 40px rgba(179,93,255,0.8);
        }

        .satellite {
            position: absolute;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            box-shadow: 0 0 18px currentColor;
        }

        .sat-1 { color: #FF6BF1; background: #FF6BF1; transform: translate(365px, 8px); }
        .sat-2 { color: #FFD45D; background: #FFD45D; transform: translate(-350px, 62px); }
        .sat-3 { color: #95AFFF; background: #95AFFF; transform: translate(-240px, -66px); }
        .sat-4 { color: #C681FF; background: #C681FF; transform: translate(240px, -62px); }
        .sat-5 { color: #7DFF8A; background: #7DFF8A; transform: translate(470px, -72px); }

        div[data-testid="column"] {
            position: relative;
            z-index: 4;
        }

        .mission-card {
            min-height: 255px;
            border-radius: 26px;
            background: rgba(21, 16, 47, 0.90);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow:
                0 0 28px rgba(112, 53, 255, 0.18),
                inset 0 0 28px rgba(255,255,255,0.025);
            padding: 28px 38px 76px;
            text-align: left;
            position: relative;
            overflow: hidden;
        }

        .mission-card::before {
            content: "";
            position: absolute;
            left: 28px;
            right: 28px;
            top: 22px;
            height: 3px;
            border-radius: 3px;
        }

        .trail-card { border-color: rgba(255,212,93,0.42); }
        .seed-card { border-color: rgba(152,255,171,0.38); }

        .trail-card::before {
            background: #FFD45D;
            box-shadow: 0 0 16px rgba(255,212,93,0.55);
        }

        .seed-card::before {
            background: #98FFAB;
            box-shadow: 0 0 16px rgba(152,255,171,0.45);
        }

        .card-head {
            display: flex;
            align-items: center;
            gap: 24px;
            margin-top: 20px;
            margin-bottom: 26px;
        }

        .icon-box {
            width: 66px;
            height: 66px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .trail-spark-icon {
            position: relative;
            width: 56px;
            height: 56px;
            color: #FFD45D;
        }

        .trail-line {
            position: absolute;
            left: 5px;
            height: 3px;
            border-radius: 999px;
            background: currentColor;
            box-shadow: 0 0 8px rgba(255,212,93,0.28);
        }

        .trail-line-1 { top: 22px; width: 23px; opacity: 0.95; }
        .trail-line-2 { top: 31px; width: 16px; opacity: 0.72; }
        .trail-line-3 { top: 27px; left: 13px; width: 18px; opacity: 0.48; }

        .trail-star {
            position: absolute;
            color: currentColor;
            line-height: 1;
            text-shadow: 0 0 10px rgba(255,212,93,0.40);
        }

        .trail-star-main { left: 30px; top: 15px; font-size: 30px; }
        .trail-star-small { left: 23px; top: 6px; font-size: 14px; opacity: 0.95; }
        .trail-star-tiny { left: 17px; top: 38px; font-size: 10px; opacity: 0.85; }

        .trail-dot {
            position: absolute;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 6px rgba(255,212,93,0.35);
        }

        .trail-dot-1 { left: 44px; top: 11px; }
        .trail-dot-2 { left: 8px; top: 40px; opacity: 0.75; }

        .seed-search-icon {
            position: relative;
            width: 56px;
            height: 56px;
            color: #98FFAB;
        }

        .seed-lens {
            position: absolute;
            left: 7px;
            top: 7px;
            width: 30px;
            height: 30px;
            border: 4px solid currentColor;
            border-radius: 50%;
            box-sizing: border-box;
            box-shadow: 0 0 10px rgba(152,255,171,0.20);
        }

        .seed-handle {
            position: absolute;
            left: 33px;
            top: 35px;
            width: 18px;
            height: 4px;
            background: currentColor;
            border-radius: 999px;
            transform: rotate(45deg);
            transform-origin: left center;
            box-shadow: 0 0 8px rgba(152,255,171,0.20);
        }

        .seed-star-core {
            position: absolute;
            left: 15px;
            top: 12px;
            font-size: 18px;
            line-height: 1;
            font-weight: 900;
            text-shadow: 0 0 10px rgba(152,255,171,0.48);
        }

        .seed-sparkle-1 {
            position: absolute;
            left: 37px;
            top: 7px;
            font-size: 12px;
            line-height: 1;
            opacity: 0.95;
        }

        .seed-sparkle-2 {
            position: absolute;
            left: 4px;
            top: 35px;
            font-size: 9px;
            line-height: 1;
            opacity: 0.78;
        }

        .seed-dot-1,
        .seed-dot-2 {
            position: absolute;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 6px rgba(152,255,171,0.35);
        }

        .seed-dot-1 { left: 44px; top: 18px; }
        .seed-dot-2 { left: 11px; top: 43px; opacity: 0.8; }

        .trail-icon-box {
            background: rgba(255,212,93,0.12);
            border: 1px solid rgba(255,212,93,0.34);
        }

        .seed-icon-box {
            background: rgba(152,255,171,0.10);
            border: 1px solid rgba(152,255,171,0.30);
        }

        .css-star {
            width: 0;
            height: 0;
            color: #FFD45D;
            position: relative;
            display: block;
            border-right: 16px solid transparent;
            border-bottom: 11px solid #FFD45D;
            border-left: 16px solid transparent;
            transform: rotate(35deg);
            filter: drop-shadow(0 0 8px rgba(255,212,93,0.7));
        }

        .css-star::before {
            border-bottom: 13px solid #FFD45D;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            position: absolute;
            height: 0;
            width: 0;
            top: -9px;
            left: -10px;
            display: block;
            content: "";
            transform: rotate(-35deg);
        }

        .css-star::after {
            position: absolute;
            display: block;
            color: #FFD45D;
            top: 1px;
            left: -17px;
            width: 0;
            height: 0;
            border-right: 16px solid transparent;
            border-bottom: 11px solid #FFD45D;
            border-left: 16px solid transparent;
            transform: rotate(-70deg);
            content: "";
        }

        .css-seed {
            position: relative;
            width: 42px;
            height: 50px;
        }

        .css-seed::before {
            content: "";
            position: absolute;
            left: 19px;
            top: 18px;
            width: 4px;
            height: 28px;
            background: #98FFAB;
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(152,255,171,0.6);
        }

        .leaf-left, .leaf-right {
            position: absolute;
            background: #98FFAB;
            box-shadow: 0 0 10px rgba(152,255,171,0.55);
        }

        .leaf-left {
            width: 28px;
            height: 18px;
            left: 1px;
            top: 7px;
            border-radius: 28px 4px 28px 4px;
            transform: rotate(20deg);
        }

        .leaf-right {
            width: 30px;
            height: 19px;
            right: 0;
            top: 4px;
            border-radius: 4px 28px 4px 28px;
            transform: rotate(-20deg);
        }

        .seed-pot {
            position: absolute;
            left: 13px;
            top: 37px;
            width: 18px;
            height: 12px;
            background: #A97767;
            border-radius: 0 0 12px 12px;
        }

        .card-title {
            font-size: 40px;
            font-weight: 950;
            color: #FFF9FF;
            line-height: 1.05;
        }

        .card-en {
            font-size: 27px;
            font-weight: 900;
            margin-top: 6px;
        }

        .trail-en { color: #FFD45D; }
        .seed-en { color: #98FFAB; }

        .card-desc {
            font-size: 19px;
            line-height: 1.7;
            color: #D9CFE8;
            font-weight: 560;
        }

        .trail-point {
            color: #FFD45D;
            font-weight: 850;
        }

        .trail-soft-point {
            color: #F6D365;
            font-weight: 700;
        }

        .seed-point {
            color: #98FFAB;
            font-weight: 700;
        }

        .seed-soft-point {
            color: #98FFAB;
            font-weight: 750;
        }

        section.main .stButton > button {
            width: 100%;
            height: 44px;
            border-radius: 15px;
            background: rgba(255,255,255,0.035) !important;
            color: #FFF9FF !important;
            border: 1px solid rgba(255,255,255,0.13) !important;
            font-size: 16px;
            font-weight: 850;
            transition: all 0.18s ease;
            margin-top: -60px;
            position: relative;
            z-index: 20;
        }

        section.main .stButton > button:hover {
            transform: translateY(-2px);
            border-color: rgba(240,140,255,0.75) !important;
            background: rgba(125, 66, 255, 0.20) !important;
            box-shadow: 0 0 20px rgba(125, 66, 255, 0.25);
            color: white !important;
        }

        .detail-box {
            position: relative;
            z-index: 3;
            max-width: 1380px;
            margin: 42px auto 0 auto;
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(21,16,47,0.94), rgba(16,12,34,0.94));
            border: 1px solid rgba(196, 143, 255, 0.34);
            box-shadow:
                0 0 36px rgba(125, 66, 255, 0.20),
                inset 0 0 30px rgba(255,255,255,0.025);
            padding: 42px 48px 48px;
            text-align: left;
            animation: detailOpen 0.32s ease-out;
        }

        @keyframes detailOpen {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }


        .detail-phase-head {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 24px;
        }

        .detail-phase-icon {
            width: 54px;
            height: 54px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
            overflow: visible;
        }

        .detail-phase-icon .trail-spark-icon,
        .detail-phase-icon .seed-search-icon {
            transform: scale(0.92);
            transform-origin: center center;
        }

        .detail-phase-title-row {
            display: flex;
            align-items: baseline;
            gap: 12px;
            line-height: 1.05;
        }

        .detail-phase-ko {
            font-size: 34px;
            font-weight: 950;
            letter-spacing: -1.1px;
        }

        .detail-phase-en {
            font-size: 22px;
            font-weight: 850;
            color: rgba(255,255,255,0.90);
            letter-spacing: -0.2px;
        }

        .detail-phase-trail .detail-phase-ko {
            color: #FFD45D;
            text-shadow: 0 0 14px rgba(255,212,93,0.22);
        }

        .detail-phase-seed .detail-phase-ko {
            color: #98FFAB;
            text-shadow: 0 0 14px rgba(152,255,171,0.20);
        }
        .detail-kicker {
            font-size: 14px;
            font-weight: 950;
            letter-spacing: 2px;
            color: #DDBBFF;
            margin-bottom: 18px;
        }

        .detail-title {
            font-size: 34px;
            line-height: 1.35;
            font-weight: 950;
            color: #FFF9FF;
            margin-bottom: 24px;
        }

        .detail-text {
            font-size: 19px;
            line-height: 1.9;
            color: #D9CFE8;
            font-weight: 520;
            margin-bottom: 34px;
            word-break: keep-all;
            overflow-wrap: normal;
            letter-spacing: -0.02em;
        }

        .segment-grid,
        .seed-grid {
            display: grid;
            gap: 18px;
            align-items: stretch;
        }

        .segment-grid {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .seed-grid {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .segment-card {
            border-radius: 17px;
            padding: 24px 20px;
            background: rgba(255,255,255,0.038);
            border: 1px solid rgba(255,255,255,0.12);
            min-height: 250px;
        }

        .seed-step-card {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            padding: 28px 20px 26px;
            background:
                radial-gradient(circle at 50% 0%, rgba(152,255,171,0.085), transparent 42%),
                rgba(255,255,255,0.038);
            border: 1px solid rgba(152,255,171,0.18);
            min-height: 258px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow:
                inset 0 0 24px rgba(152,255,171,0.035),
                0 14px 36px rgba(0,0,0,0.18);
            transition: all 0.22s ease;
        }

        .seed-step-card:hover {
            transform: translateY(-4px);
            border-color: rgba(152,255,171,0.42);
            box-shadow:
                inset 0 0 28px rgba(152,255,171,0.06),
                0 18px 46px rgba(0,0,0,0.30),
                0 0 22px rgba(152,255,171,0.08);
        }

        .seed-step-card::before {
            content: "";
            position: absolute;
            left: 24px;
            right: 24px;
            top: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(152,255,171,0.55), transparent);
        }

        .segment-card {
            position: relative;
            overflow: hidden;
            padding: 30px 20px 26px;
            display: flex;
            flex-direction: column;
        }

        .segment-head {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            text-align: center;
            min-height: 132px;
            margin-bottom: 8px;
        }

        .segment-icon-badge {
            width: 58px;
            height: 58px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px auto;
            font-size: 27px;
            line-height: 1;
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 0 18px rgba(240, 140, 255, 0.12);
            background: rgba(255,255,255,0.05);
        }

        .icon-cluster {
            color: #FFD45D;
            background: rgba(255, 212, 93, 0.10);
            border-color: rgba(255, 212, 93, 0.25);
        }

        .icon-protostar {
            color: #98FFAB;
            background: rgba(152, 255, 171, 0.10);
            border-color: rgba(152, 255, 171, 0.25);
        }

        .icon-satellite {
            color: #8FB8FF;
            background: rgba(143, 184, 255, 0.10);
            border-color: rgba(143, 184, 255, 0.25);
        }

        .icon-supernova {
            color: #FF7AC8;
            background: rgba(255, 122, 200, 0.10);
            border-color: rgba(255, 122, 200, 0.25);
        }

        .icon-comet {
            color: #FF9E5E;
            background: rgba(255, 158, 94, 0.10);
            border-color: rgba(255, 158, 94, 0.25);
        }

        .segment-card:hover .segment-icon-badge {
            transform: translateY(-2px) scale(1.04);
            box-shadow: 0 0 24px rgba(240, 140, 255, 0.24);
        }

        .segment-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 34px;
            height: 26px;
            padding: 0 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 950;
            margin-bottom: 14px;
            color: #F7C2FF;
            background: rgba(240, 140, 255, 0.18);
            border: 1px solid rgba(240, 140, 255, 0.30);
        }

        .seed-icon-orbit {
            width: 82px;
            height: 82px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16px;
            background:
                radial-gradient(circle, rgba(152,255,171,0.18) 0%, rgba(152,255,171,0.06) 58%, transparent 72%);
            border: 1px solid rgba(152,255,171,0.28);
            box-shadow:
                0 0 24px rgba(152,255,171,0.08),
                inset 0 0 18px rgba(152,255,171,0.04);
        }

        .seed-icon-badge {
            width: 56px;
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            background: transparent;
            border: none;
            box-shadow: none;
            transform: scale(1.08);
            transform-origin: center center;
        }

        .seed-icon-badge::before,
        .seed-icon-badge::after {
            content: "";
            position: absolute;
            box-sizing: border-box;
            filter: drop-shadow(0 0 6px rgba(152,255,171,0.18));
        }

        /* 01 검색 */
        .seed-icon-search::before {
            width: 28px;
            height: 28px;
            border: 3.4px solid #98FFAB;
            border-radius: 50%;
            left: 10px;
            top: 9px;
        }

        .seed-icon-search::after {
            width: 20px;
            height: 3.4px;
            background: #98FFAB;
            border-radius: 999px;
            left: 33px;
            top: 35px;
            transform: rotate(45deg);
        }


/* 02 팬 반응 밀도 */
        .seed-icon-chat::before {
            width: 58px;
            height: 58px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%222.9%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%2012.5h24a3%203%200%200%201%203%203v12a3%203%200%200%201-3%203H22l-7%205v-5h-3a3%203%200%200%201-3-3v-12a3%203%200%200%201%203-3Z%22%2F%3E%3Cpath%20d%3D%22M24%2025.8s-4.8-2.7-4.8-5.9c0-1.6%201.3-2.9%202.9-2.9%201.2%200%202%20.7%202.6%201.6.6-.9%201.4-1.6%202.6-1.6%201.6%200%202.9%201.3%202.9%202.9%200%203.2-4.8%205.9-4.8%205.9Z%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;
            border: none;
        }

        .seed-icon-chat::after {
            display: none;
        }

        /* 03 라이브 전환성 */
        .seed-icon-live::before {
            width: 56px;
            height: 56px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%2214%22%20y%3D%2216%22%20width%3D%2216%22%20height%3D%2212%22%20rx%3D%222.5%22%2F%3E%3Cpath%20d%3D%22M30%2019l5-3v12l-5-3%22%2F%3E%3Cpath%20d%3D%22M10%2018c2-4.5%206.4-7.5%2011.4-7.8%22%2F%3E%3Cpath%20d%3D%22M18.2%207.6l3.9%202.2-3.7%202.4%22%2F%3E%3Cpath%20d%3D%22M38%2030c-2%204.5-6.4%207.5-11.4%207.8%22%2F%3E%3Cpath%20d%3D%22M29.8%2040.4l-3.9-2.2%203.7-2.4%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;
            border: none;
        }

        .seed-icon-live::after {
            display: none;
        }

        /* 04 실전 리스크 */
        .seed-icon-filter::before {
            width: 44px;
            height: 44px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223.4%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2224%22%20cy%3D%2224%22%20r%3D%2211.5%22%2F%3E%3Cpath%20d%3D%22M17.5%2024h13%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;
            border: none;
        }

        .seed-icon-filter::after {
            display: none;
        }

        /* 05 체크 */
        .seed-icon-check::before {
            width: 36px;
            height: 36px;
            border: 3.4px solid #98FFAB;
            border-radius: 10px;
            left: 10px;
            top: 10px;
        }

        .seed-icon-check::after {
            width: 21px;
            height: 12px;
            border-left: 4.5px solid #98FFAB;
            border-bottom: 4.5px solid #98FFAB;
            left: 18px;
            top: 21px;
            transform: rotate(-45deg);
        }

        .seed-mini-line {
            width: 28px;
            height: 2px;
            border-radius: 999px;
            background: rgba(152,255,171,0.92);
            margin: 0 auto 14px;
        }

        .segment-ko,
        .seed-title {
            color: #FFF9FF;
            font-size: 20px;
            line-height: 1.35;
            font-weight: 950;
            margin-bottom: 8px;
        }

        .segment-ko {
            text-align: center;
        }

        .segment-en {
            color: #F08CFF;
            font-size: 13px;
            font-weight: 950;
            margin-bottom: 0;
            text-align: center;
        }

        .segment-purpose {
            color: rgba(255,255,255,0.82);
            font-size: 14px;
            line-height: 1.55;
            font-weight: 760;
            padding: 12px 13px;
            margin-bottom: 20px;
            border-radius: 12px;
            background: rgba(240, 140, 255, 0.10);
            border: 1px solid rgba(240, 140, 255, 0.22);
            min-height: 74px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            word-break: keep-all;
        }

        .purpose-key {
            display: inline-block;
            margin-top: 2px;
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 950;
            letter-spacing: -0.2px;
            text-shadow: 0 0 10px rgba(240, 140, 255, 0.22);
        }

        .field-label {
            color: #F0B5FF;
            font-size: 12px;
            font-weight: 950;
            letter-spacing: 0.2px;
            margin-top: 12px;
            margin-bottom: 6px;
        }

        .field-value {
            color: rgba(255,255,255,0.76);
            font-size: 14px;
            line-height: 1.7;
            font-weight: 500;
            letter-spacing: -0.02em;
            word-break: keep-all;
            overflow-wrap: normal;
        }

        .seed-desc {
            color: rgba(255,255,255,0.76);
            font-size: 15px;
            line-height: 1.65;
            font-weight: 560;
            letter-spacing: -0.02em;
            word-break: keep-all;
            overflow-wrap: normal;
            min-height: 50px;
        }

        .seed-title {
            font-size: 21px;
            margin-bottom: 12px;
            margin-top: 2px;
            word-break: keep-all;
        }

        .empty-guide {
            position: relative;
            z-index: 3;
            margin-top: 34px;
            font-size: 15px;
            color: rgba(191,181,213,0.72);
            text-align: center;
        }

        .page-panel {
            position: relative;
            z-index: 3;
            border-radius: 22px;
            background: rgba(21, 16, 47, 0.86);
            border: 1px solid rgba(196, 143, 255, 0.26);
            padding: 36px 40px;
            margin-top: 30px;
            color: rgba(255,255,255,0.78);
            line-height: 1.8;
        }

        @media (max-width: 1200px) {
            .segment-grid,
            .seed-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .hero-title {
                font-size: 44px;
                letter-spacing: 5px;
            }

            .planet {
                width: 280px;
                height: 280px;
            }

            .planet-area {
                height: 330px;
            }
        }

        @media (max-width: 780px) {
            .segment-grid,
            .seed-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="star-layer">{st.session_state.bg_html}</div><div class="orbit-bg"></div>',
    unsafe_allow_html=True,
)

# =========================================================
# 1-4. Sidebar navigation / dropdown visibility patch
# - 비활성 네비게이션 버튼이 흰 배경+밝은 글씨로 보이는 문제 보정
# - 스타시드 필터 expander의 가독성 강화
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: rgba(24, 17, 54, 0.90) !important;
            color: #EEE7FF !important;
            border: 1px solid rgba(199, 168, 255, 0.42) !important;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.025) !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] p,
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] span {
            color: #EEE7FF !important;
            font-weight: 850 !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background: rgba(42, 27, 88, 0.96) !important;
            border-color: rgba(228, 205, 255, 0.72) !important;
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {
            color: #FFFFFF !important;
            font-weight: 900 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            background: rgba(18, 13, 44, 0.78) !important;
            border: 1px solid rgba(199, 168, 255, 0.28) !important;
            border-radius: 14px !important;
            margin-top: 10px !important;
            margin-bottom: 10px !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
            color: #F8F2FF !important;
            font-weight: 900 !important;
            letter-spacing: -0.2px;
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaptionContainer,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #DED5F8 !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] [data-baseweb="textarea"] > div {
            background: rgba(255,255,255,0.06) !important;
            border-color: rgba(199, 168, 255, 0.22) !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =========================================================
# 1-5. 선택형 그래프 / 압축 후보 상세 스타일
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        .compact-detail-card {
            min-height: 0px;
        }

        .compact-detail-card div[data-testid="stMetric"] {
            padding: 10px 12px !important;
            min-height: 86px;
        }

        .compact-detail-card div[data-testid="stMetric"] label,
        .compact-detail-card div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            color: #a9b9c9 !important;
        }

        .compact-detail-card div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
        }

        .compact-channel-id {
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-bottom: 10px;
        }

        .compact-reason-box {
            margin-top: 12px;
            max-height: 112px;
            overflow: hidden;
        }

        .compact-detail-card div[data-testid="stExpander"] {
            margin-top: 10px !important;
        }


        /* Graph selector section: dropdown 대신 가로 선택지로 정리 */
        div[role="radiogroup"] {
            gap: 10px;
            margin: 4px 0 14px 0;
        }

        div[role="radiogroup"] label {
            background: rgba(24, 17, 54, 0.72);
            border: 1px solid rgba(199, 168, 255, 0.25);
            border-radius: 999px;
            padding: 8px 12px;
        }

        .compact-detail-card {
            margin-top: 0 !important;
        }

        .cluster-summary-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(152,255,171,0.42), rgba(199,168,255,0.24), transparent);
            margin: 24px 0 18px 0;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(118,242,226,0.20) !important;
            background: rgba(7,18,34,0.46) !important;
            border-radius: 18px !important;
        }

        .selected-profile-area {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 16px 0 8px 0;
        }

        .selected-profile-img-wrap {
            width: 104px;
            height: 104px;
            border-radius: 50%;
            overflow: hidden;
            border: 1px solid rgba(95,255,232,0.50);
            box-shadow: 0 0 28px rgba(95,255,232,0.22), inset 0 1px 0 rgba(255,255,255,0.20);
            background: radial-gradient(circle at 35% 30%, rgba(95,255,232,0.28), rgba(72,18,167,0.38));
        }

        .selected-profile-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .selected-profile-fallback {
            width: 104px;
            height: 104px;
            transform: scale(1.18);
            margin: 0 auto;
        }

        .detail-title-centered {
            text-align: center;
            font-size: 28px !important;
            margin: 10px 0 16px 0 !important;
        }

        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =========================================================
# 1-6. TOP 후보 카드: 세부 콘텐츠 유형별 아이콘 아바타
# - 채널명 첫 글자 대신 콘텐츠 성격을 직관적으로 보여주는 아이콘형 이미지로 표시
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        .content-avatar {
            width: 76px;
            height: 76px;
            border-radius: 26px;
            margin: 16px auto 12px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.35);
            box-shadow: 0 0 24px rgba(95,255,232,0.18), inset 0 1px 0 rgba(255,255,255,0.18);
        }

        .content-avatar::before {
            content: "";
            position: absolute;
            inset: -35%;
            background:
                radial-gradient(circle at 30% 25%, rgba(255,255,255,0.74), transparent 15%),
                radial-gradient(circle at 70% 72%, rgba(255,255,255,0.22), transparent 18%),
                linear-gradient(135deg, rgba(255,255,255,0.24), transparent 42%);
            transform: rotate(-18deg);
            opacity: 0.82;
        }

        .content-avatar::after {
            content: "";
            position: absolute;
            inset: 8px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.12);
        }

        .content-avatar-icon {
            position: relative;
            z-index: 2;
            font-size: 36px;
            line-height: 1;
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.35));
        }

        .content-avatar-img {
            position: relative;
            z-index: 2;
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .content-avatar.has-profile-img {
            border-radius: 50%;
            background: radial-gradient(circle at 35% 30%, rgba(95,255,232,0.20), rgba(72,18,167,0.30));
            border: 1px solid rgba(95,255,232,0.46);
            box-shadow: 0 0 24px rgba(95,255,232,0.22), inset 0 1px 0 rgba(255,255,255,0.18);
        }

        .content-avatar.has-profile-img::before,
        .content-avatar.has-profile-img::after {
            display: none;
        }

        .candidate-name a,
        .detail-title a {
            color: inherit;
            text-decoration: none;
        }

        .candidate-name a:hover,
        .detail-title a:hover {
            color: #78ffee;
            text-decoration: underline;
            text-underline-offset: 3px;
        }

        .avatar-voice { background: linear-gradient(135deg, #5fffe8 0%, #3b82f6 55%, #6d5dfc 100%); }
        .avatar-cover { background: linear-gradient(135deg, #9dffb0 0%, #21d4a7 50%, #1b7ef3 100%); }
        .avatar-vtuber { background: linear-gradient(135deg, #c084fc 0%, #7c3aed 50%, #f472b6 100%); }
        .avatar-cosplay { background: linear-gradient(135deg, #ff8bd1 0%, #fb7185 45%, #facc15 100%); }
        .avatar-game { background: linear-gradient(135deg, #7dd3fc 0%, #2563eb 50%, #0f172a 100%); }
        .avatar-asmr { background: linear-gradient(135deg, #a7f3d0 0%, #14b8a6 50%, #0e7490 100%); }
        .avatar-music { background: linear-gradient(135deg, #fde68a 0%, #f59e0b 45%, #ef4444 100%); }
        .avatar-talk { background: linear-gradient(135deg, #f0abfc 0%, #a855f7 48%, #22d3ee 100%); }
        .avatar-default { background: linear-gradient(135deg, #94a3b8 0%, #475569 50%, #111827 100%); }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# =========================================================
# 1-6.5. Sidebar active color preload
# - 스타시드 페이지에서 사이드바 active 버튼이 먼저 보라색으로 칠해진 뒤
#   하단 CSS가 적용되며 초록색으로 바뀌는 플래시를 방지
# - 사이드바 버튼을 그리기 전에 현재 페이지 기준 active 색상을 먼저 주입
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            :root {
                --seed-green: #7CFF9E;
                --seed-green-soft: #98FFAB;
                --seed-green-bright: #37F58E;
                --seed-mint: #63FFD8;
                --seed-panel: rgba(6, 18, 26, 0.88);
                --seed-panel-strong: rgba(7, 24, 31, 0.96);
                --seed-line: rgba(124, 255, 158, 0.30);
                --seed-line-strong: rgba(124, 255, 158, 0.58);
                --seed-purple-base: #09051C;
                --seed-text: #FFF8FF;
                --seed-muted: #CFC4E4;
            }

            .stApp {
                background:
                    radial-gradient(circle at 72% 6%, rgba(50, 255, 130, 0.16) 0, transparent 22%),
                    radial-gradient(circle at 51% 22%, rgba(127, 47, 255, 0.34), transparent 30%),
                    radial-gradient(circle at 76% 76%, rgba(29, 255, 129, 0.09), transparent 31%),
                    linear-gradient(180deg, #050411 0%, #09051C 52%, #050411 100%) !important;
            }

            [data-testid="stHeader"] {
                background: rgba(8, 12, 22, 0.96) !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(7, 8, 24, 0.99), rgba(4, 6, 18, 0.99)) !important;
                border-right: 1px solid rgba(154, 98, 255, 0.42) !important;
                box-shadow: 10px 0 32px rgba(0, 0, 0, 0.28) !important;
            }

            .sidebar-subtitle,
            .mission-sidebar-sub {
                color: var(--seed-green-soft) !important;
                text-shadow: 0 0 12px rgba(124, 255, 158, 0.28) !important;
            }

            section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, rgba(30, 213, 102, 0.98), rgba(18, 146, 86, 0.96)) !important;
                color: #F5FFF7 !important;
                border: 1px solid rgba(152, 255, 171, 0.70) !important;
                box-shadow:
                    0 0 12px rgba(60, 255, 132, 0.14),
                    inset 0 1px 0 rgba(255,255,255,0.10) !important;
            }

            section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
            section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {
                color: #F5FFF7 !important;
                font-weight: 900 !important;
            }

            section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
                background: rgba(20, 16, 48, 0.78) !important;
                color: #EDE5FF !important;
                border: 1px solid rgba(196, 143, 255, 0.26) !important;
                box-shadow: none !important;
            }

            section[data-testid="stSidebar"] .stButton > button:hover {
                border-color: rgba(152, 255, 171, 0.58) !important;
                box-shadow: 0 0 20px rgba(124, 255, 158, 0.18) !important;
            }

            .starseed-board {
                margin-top: -30px !important;
            }

            .board-title {
                color: #FFF8FF !important;
                letter-spacing: 9px !important;
                text-shadow:
                    0 0 12px rgba(255,255,255,0.52),
                    0 0 24px rgba(152,255,171,0.32),
                    0 0 44px rgba(52,255,130,0.22) !important;
            }

            .board-title::after {
                content: "";
                display: block;
                width: 220px;
                height: 2px;
                margin-top: 14px;
                border-radius: 999px;
                background: linear-gradient(90deg, rgba(152,255,171,0.0), rgba(152,255,171,0.85), rgba(99,255,216,0.42), rgba(152,255,171,0.0));
                box-shadow: 0 0 18px rgba(124,255,158,0.34);
            }

            .board-info-card {
                border: 1px solid var(--seed-line-strong) !important;
                background:
                    radial-gradient(circle at 8% 45%, rgba(124,255,158,0.22), transparent 28%),
                    linear-gradient(135deg, rgba(10, 38, 30, 0.82), rgba(18, 16, 52, 0.88)) !important;
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,.08),
                    0 0 28px rgba(124,255,158,0.15) !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# SIDEBAR WIDTH / NATIVE TOGGLE SAFE MODE
# - 사이드바가 펼쳐졌을 때 폭만 고정
# - 접힘/펼침 동작은 Streamlit 기본 로직에 맡김
# - 기본 << / >> 토글은 반드시 보이게 유지
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --cime-sidebar-width: 300px;
    }

    @media (min-width: 900px) {
        section[data-testid="stSidebar"][aria-expanded="true"] {
            flex: 0 0 var(--cime-sidebar-width) !important;
            width: var(--cime-sidebar-width) !important;
            min-width: var(--cime-sidebar-width) !important;
            max-width: var(--cime-sidebar-width) !important;
            overflow: hidden auto !important;
            z-index: 999996 !important;
        }
    }

    /* 접힌 상태는 강제로 width 0 처리하지 않음. Streamlit 기본 토글 재오픈 기능 보존 */
    section[data-testid="stSidebar"][aria-expanded="false"] {
        pointer-events: auto !important;
    }

    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] *,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] *,
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="사이드바 열기"],
    button[aria-label="사이드바 닫기"],
    button[title="Open sidebar"],
    button[title="Close sidebar"],
    button[title="사이드바 열기"],
    button[title="사이드바 닫기"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        overflow: visible !important;
        z-index: 1000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    html(
        """
        <div class="sidebar-title">CIME</div>
        <div class="sidebar-subtitle">MISSION CONTROL</div>
        <div class="sidebar-line"></div>
        """
    )

    NAV_ITEMS = {
        "대시보드 홈": {
            "label": "대시보드 홈",
            "icon": ":material/dashboard:",
        },
        "스타트레일": {
            "label": "스타트레일",
            "icon": ":material/auto_awesome:",
        },
        "스타시드": {
            "label": "스타시드",
            "icon": ":material/search:",
        },
    }

    for page, item in NAV_ITEMS.items():
        is_active = st.session_state.page == page

        if st.button(
            item["label"],
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            icon=item["icon"],
        ):
            st.session_state.page = page
            st.session_state.card = None
            st.rerun()

def render_planet_home():
    html(
        """
        <div class="main-wrap planet-home-wrap">
        <div class="hero-title">CIME STREAM PLANET</div>
        <div class="hero-subtitle">데이터 우주에서 다음 플랫폼의 중심 별을 찾다</div>
        <div class="planet-area">
        <div class="planet-glow"></div>
        <div class="planet-orbit orbit-3"></div>
        <div class="planet-orbit"></div>
        <div class="planet-orbit orbit-2"></div>
        <div class="satellite sat-1"></div>
        <div class="satellite sat-2"></div>
        <div class="satellite sat-3"></div>
        <div class="satellite sat-4"></div>
        <div class="satellite sat-5"></div>
        <div class="planet">
        <div class="planet-logo">CIME</div>
        </div>
        </div>
        </div>
        """
    )


def render_mission_cards():
    col1, col2 = st.columns(2, gap="large")

    with col1:
        html(
            f"""
            <div class="mission-card trail-card">
                <div class="card-head">
                    <div class="icon-box trail-icon-box">
                        {TRAIL_ICON_HTML}
                    </div>
                    <div>
                        <div class="card-title">스타트레일</div>
                        <div class="card-en trail-en">Star Trail</div>
                    </div>
                </div>

                <div class="card-desc">
                    기존 플랫폼에서 검증된 
                    <span class="trail-point">성과와 팬덤</span>을 기반으로,<br>
                    <span class="trail-point">CIME 영입 우선 후보군</span>을 탐색합니다.
                </div>
            </div>
            """
        )
        if st.button("스타트레일 자세히 보기", key="btn_startrail", use_container_width=True):
            st.session_state.card = None if st.session_state.card == "trail" else "trail"

    with col2:
        html(
            f"""
            <div class="mission-card seed-card">
                <div class="card-head">
                    <div class="icon-box seed-icon-box">
                        {SEED_ICON_HTML}
                    </div>
                    <div>
                        <div class="card-title">스타시드</div>
                        <div class="card-en seed-en">Star Seed</div>
                    </div>
                </div>

                <div class="card-desc">
                    유튜브 기반 
                    <span class="seed-point">성장 잠재력</span>과 
                    <span class="seed-point">라이브 전환 가능성</span>을 분석해,<br>
                    <span class="seed-point">차세대 후보군</span>을 발굴합니다.
                </div>
            </div>
            """
        )
        if st.button("스타시드 자세히 보기", key="btn_starseed", use_container_width=True):
            st.session_state.card = None if st.session_state.card == "seed" else "seed"


def render_startrail_detail():
    cards = "".join(
        [
            f'<div class="segment-card">'
            f'<div class="segment-head">'
            f'<div class="segment-icon-badge {seg["icon_class"]}">{seg["icon"]}</div>'
            f'<div class="segment-ko">{seg["ko"]}</div>'
            f'<div class="segment-en">{seg["en"]}</div>'
            f'</div>'
            f'<div class="segment-purpose">{seg["purpose"]}</div>'
            f'<div class="field-label">주요 판단 기준</div>'
            f'<div class="field-value">{seg["criteria"]}</div>'
            f'<div class="field-label">CIME 활용 포인트</div>'
            f'<div class="field-value">{seg["point"]}</div>'
            f'</div>'
            for seg in STARTRAIL_SEGMENTS
        ]
    )

    st.markdown(
        (
            '<div class="detail-box">'
            f'<div class="detail-phase-head detail-phase-trail"><div class="detail-phase-icon">{TRAIL_ICON_HTML}</div><div class="detail-phase-title-row"><span class="detail-phase-ko">스타트레일</span><span class="detail-phase-en">Star Trail</span></div></div>'
            '<div class="detail-title">기존 플랫폼 성과를 기준으로 CIME 영입 후보군을 선별하는 단계</div>'
            '<div class="detail-text">'
            '스타트레일은 <span class="trail-soft-point">기존 플랫폼에서 이미 활동 성과가 확인된 스트리머</span>를 분석합니다.<br>'
            '대중성, 방송화력, 팬덤결집력, 수익성, 외부유입가능성을 함께 비교해<br>'
            '<span class="trail-soft-point">CIME 영입 우선순위가 높은 후보군</span>을 찾습니다.'
            '</div>'
            f'<div class="segment-grid">{cards}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_starseed_detail():
    cards = "".join(
        [
            f'<div class="seed-step-card">'
            f'<div class="seed-icon-orbit"><div class="seed-icon-badge seed-icon-{step["icon"]}"></div></div>'
                        f'<div class="seed-title">{step["title"]}</div>'
            f'<div class="seed-mini-line"></div>'
            f'<div class="seed-desc">{step["desc"]}</div>'
            f'</div>'
            for step in STAR_SEED_CARDS
        ]
    )

    st.markdown(
        (
            '<div class="detail-box">'
            f'<div class="detail-phase-head detail-phase-seed"><div class="detail-phase-icon">{SEED_ICON_HTML}</div><div class="detail-phase-title-row"><span class="detail-phase-ko">스타시드</span><span class="detail-phase-en">Star Seed</span></div></div>'
            '<div class="detail-title">유튜브에서 CIME가 실제로 검토할 후보를 찾는 단계</div>'
            '<div class="detail-text">'
            '스타시드는 <span class="seed-soft-point">유튜브에서 활동 중인 크리에이터</span> 중 단순 인기 채널이 아니라 실제 영입 검토가 가능한 후보를 분석합니다.<br>'
            '팬 반응 밀도, 라이브 전환성, 실전 리스크, 액션버킷을 함께 확인해<br>'
            '<span class="seed-soft-point">CIME가 우선 검토할 예비 스트리머 후보군</span>을 정리합니다.'
            '</div>'
            f'<div class="seed-grid">{cards}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

if st.session_state.page == "대시보드 홈":
    render_planet_home()
    render_mission_cards()

    if st.session_state.card == "trail":
        render_startrail_detail()
    elif st.session_state.card == "seed":
        render_starseed_detail()
    else:
        html(
            """
            <div class="empty-guide">
            스타트레일 또는 스타시드 카드를 선택하면 아래에 단계 설명이 표시됩니다.
            </div>
            """
        )
    st.stop()

elif st.session_state.page == "스타트레일":
    html(
        """
        <div class="main-wrap">
        <div class="hero-title">STAR TRAIL</div>
        <div class="hero-subtitle">기존 플랫폼 기반 영입 후보군 대시보드 영역</div>
        </div>
        <div class="page-panel">
        이 영역에는 추후 스타트레일 분석 대시보드가 들어갈 예정입니다.
        홈 화면의 스타트레일 카드 설명과는 별도로 운영되는 페이지입니다.
        </div>
        """
    )
    st.stop()

# 스타시드 선택 시 아래의 기존 유튜브 API 기반 영입후보 대시보드가 이어서 실행됩니다.

# =========================================================
# 2. 경로 및 데이터 로드
# =========================================================

def find_project_root() -> Path:
    """
    streamlit_app.py가 project_root/07_code 안에 있다고 가정.
    그래도 실행 위치가 달라도 최대한 project_root를 찾도록 처리.
    """
    here = Path(__file__).resolve().parent

    candidates = [
        here.parent,              # 07_code의 부모 = project_root
        here,
        Path.cwd(),
        Path.cwd().parent,
    ]

    for p in candidates:
        if (p / "10_dashboard").exists() or (p / "11_final").exists():
            return p.resolve()

    return here.parent.resolve()


PROJECT_ROOT = find_project_root()


def resolve_existing_path(relative_path: str) -> Path:
    """
    Streamlit Cloud / 로컬 환경 모두에서 CSV 경로를 안정적으로 찾기 위한 함수.
    1순위: PROJECT_ROOT / relative_path
    2순위: 현재 작업 폴더 / relative_path
    3순위: streamlit_app.py 위치 / relative_path
    4순위: 파일명 기준 재귀 탐색
    """
    rel = Path(relative_path)

    candidates = [
        PROJECT_ROOT / rel,
        Path.cwd() / rel,
        Path(__file__).resolve().parent / rel,
        Path(__file__).resolve().parent.parent / rel,
    ]

    for p in candidates:
        if p.exists():
            return p.resolve()

    # 마지막 fallback: 파일명으로 전체 repo 안에서 검색
    search_roots = [
        PROJECT_ROOT,
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    for root in search_roots:
        try:
            matches = list(root.rglob(rel.name))
            for m in matches:
                # 경로 끝부분이 최대한 일치하는 파일 우선
                if str(m).replace("\\", "/").endswith(str(rel).replace("\\", "/")):
                    return m.resolve()
            if matches:
                return matches[0].resolve()
        except Exception:
            pass

    return PROJECT_ROOT / rel


def resolve_first_existing(relative_paths):
    """여러 후보 경로 중 실제 존재하는 파일을 우선순위대로 반환한다."""
    for relative_path in relative_paths:
        path = resolve_existing_path(relative_path)
        if path.exists():
            return path
    return resolve_existing_path(relative_paths[0])


# thumbnail 보강본이 따로 올라간 경우도 자동 인식한다.
# 기존 파일명으로 덮어쓴 경우에도 그대로 동작한다.
CANDIDATE_DASHBOARD_PATH = resolve_first_existing([
    "10_dashboard/data/dashboard_candidate_table_with_thumbnail.csv",
    "10_dashboard/data/dashboard_candidate_table.csv",
])
SEGMENT_DASHBOARD_PATH = resolve_existing_path("10_dashboard/data/dashboard_segment_table.csv")
SUMMARY_DASHBOARD_PATH = resolve_existing_path("10_dashboard/data/dashboard_summary.csv")
REFERENCE_DASHBOARD_PATH = resolve_existing_path("10_dashboard/data/dashboard_reference_table.csv")

CANDIDATE_SCORED_FINAL_PATH = resolve_existing_path("11_final/core_output/candidate_scored_final.csv")
SHORTLIST_TRACKING_PATH = resolve_existing_path("11_final/core_output/candidate_shortlist_tracking.csv")

CANDIDATE_SCORED_SNAPSHOT_PATH = resolve_existing_path("09_intermediate/snapshots/candidate_scored_snapshot.csv")


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    for enc in ["utf-8-sig", "cp949", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue

    return pd.read_csv(path, low_memory=False)


def file_mtime_token(path: Path):
    """Streamlit cache가 오래된 CSV를 계속 잡고 있는 문제를 막기 위한 mtime token."""
    try:
        return path.stat().st_mtime_ns if path.exists() else 0
    except Exception:
        return 0


@st.cache_data(show_spinner=False)
def load_data(candidate_mtime, segment_mtime, summary_mtime, tracking_mtime, reference_mtime, snapshot_mtime):
    # mtime 인자는 cache key 용도다. 함수 내부에서는 직접 사용하지 않아도 된다.
    candidate = read_csv_safe(CANDIDATE_DASHBOARD_PATH)

    if candidate.empty:
        candidate = read_csv_safe(CANDIDATE_SCORED_FINAL_PATH)

    segment = read_csv_safe(SEGMENT_DASHBOARD_PATH)
    summary = read_csv_safe(SUMMARY_DASHBOARD_PATH)
    tracking = read_csv_safe(SHORTLIST_TRACKING_PATH)
    reference = read_csv_safe(REFERENCE_DASHBOARD_PATH)
    snapshot = read_csv_safe(CANDIDATE_SCORED_SNAPSHOT_PATH)

    return candidate, segment, summary, tracking, reference, snapshot


candidate_df, segment_df, summary_df, tracking_df, reference_df, snapshot_df = load_data(
    file_mtime_token(CANDIDATE_DASHBOARD_PATH),
    file_mtime_token(SEGMENT_DASHBOARD_PATH),
    file_mtime_token(SUMMARY_DASHBOARD_PATH),
    file_mtime_token(SHORTLIST_TRACKING_PATH),
    file_mtime_token(REFERENCE_DASHBOARD_PATH),
    file_mtime_token(CANDIDATE_SCORED_SNAPSHOT_PATH),
)


# =========================================================
# 3. 유틸 함수
# =========================================================

def first_existing(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def to_numeric_if_exists(df: pd.DataFrame, cols):
    for c in cols:
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def fmt_int(x):
    try:
        if pd.isna(x):
            return "-"
        return f"{int(round(float(x))):,}"
    except Exception:
        return "-"


def fmt_float(x, ndigits=3):
    try:
        if pd.isna(x):
            return "-"
        return f"{float(x):,.{ndigits}f}"
    except Exception:
        return "-"


def get_first_value_from_row(row, candidates):
    """행에서 후보 컬럼명을 순서대로 탐색해 첫 번째 유효값을 반환한다."""
    for c in candidates:
        if c and c in row.index:
            val = row.get(c)
            if pd.notna(val) and str(val).strip() not in ["", "nan", "None", "NaN", "-"]:
                return val
    return np.nan


def normalize_score_to_100(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.dropna().empty:
        return s

    max_v = s.max()
    if max_v <= 1.5:
        return s * 100
    return s


def fmt_delta(value, ndigits=0, suffix=""):
    try:
        if pd.isna(value):
            return "-"
        value = float(value)
        # KPI 변화량 표기에서는 + 부호를 제거한다.
        if ndigits == 0:
            return f"{int(round(value)):,}{suffix}"
        return f"{value:,.{ndigits}f}{suffix}"
    except Exception:
        return "-"


def make_kpi_delta_html(delta, ndigits=0, suffix=""):
    """
    KPI 변화량 HTML 생성
    - 상승: 빨간 ▲
    - 하락: 파란 ▼
    - 변화 없음: 회색 —
    """
    try:
        if pd.isna(delta):
            return '<div class="kpi-delta kpi-flat">비교 기준 없음</div>'

        delta = float(delta)

        if delta > 0:
            return f'<div class="kpi-delta kpi-up">▲ {fmt_delta(delta, ndigits, suffix)}</div>'
        elif delta < 0:
            return f'<div class="kpi-delta kpi-down">▼ {fmt_delta(abs(delta), ndigits, suffix)}</div>'
        else:
            return '<div class="kpi-delta kpi-flat">— 변화 없음</div>'

    except Exception:
        return '<div class="kpi-delta kpi-flat">비교 불가</div>'


def add_score_display_column(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    현재 데이터와 snapshot 데이터를 모두 100점 기준 최종점수 컬럼으로 정렬한다.
    """
    out = input_df.copy()
    local_score_col = first_existing(out, ["최종점수", "위성점수_log_minmax", "final_score", "score"])

    if local_score_col is not None:
        out["_score_raw"] = pd.to_numeric(out[local_score_col], errors="coerce")
        out["최종점수_100점"] = normalize_score_to_100(out[local_score_col])
        out["_score_display"] = out["최종점수_100점"]
    else:
        out["_score_raw"] = np.nan
        out["최종점수_100점"] = np.nan
        out["_score_display"] = np.nan

    return out


def apply_snapshot_filters_for_kpi(base_df: pd.DataFrame) -> pd.DataFrame:
    """
    기준 시점 snapshot에도 현재 화면의 주요 필터를 최대한 동일하게 적용한다.
    컬럼이 없는 필터는 건너뛴다.
    """
    out = base_df.copy()

    local_segment_col = first_existing(out, ["대표상위세그먼트", "대표세그먼트", "segment", "대표상위세그먼트명"])
    local_lower_segment_col = first_existing(out, ["대표하위세그먼트", "sub_segment", "대표하위세그먼트명"])
    local_action_col = first_existing(out, ["액션버킷", "action_bucket"])
    local_shortlist_col = first_existing(out, ["shortlist_선정여부", "shortlist", "shortlisted"])
    local_channel_name_col = first_existing(out, ["채널명", "channel_title", "채널명_clean"])
    local_subs_col = first_existing(out, ["채널구독자수", "채널 구독자 수", "구독자수", "구독자 수", "subscriber_count", "subscribers", "channel_subscriber_count"])
    local_view_col = first_existing(out, ["최근영상조회수평균", "avg_recent_views", "최근조회수평균"])
    local_score_display_col = "최종점수_100점" if "최종점수_100점" in out.columns else None

    if local_segment_col and "selected_segments" in globals() and selected_segments:
        out = out[out[local_segment_col].astype(str).isin(selected_segments)]

    if local_lower_segment_col and "selected_lower" in globals() and selected_lower:
        out = out[out[local_lower_segment_col].astype(str).isin(selected_lower)]

    if local_action_col and "selected_actions" in globals() and selected_actions:
        out = out[out[local_action_col].astype(str).isin(selected_actions)]

    if local_shortlist_col and "only_shortlist" in globals() and only_shortlist:
        shortlist_bool = out[local_shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])
        out = out[shortlist_bool]

    if local_action_col and "hide_hold" in globals() and hide_hold:
        out = out[~out[local_action_col].astype(str).str.contains("보류|제외", na=False)]

    if local_score_display_col and "score_filter_100" in globals() and score_filter_100 is not None:
        out = out[pd.to_numeric(out[local_score_display_col], errors="coerce") >= score_filter_100]

    if local_subs_col and "min_subs" in globals() and min_subs > 0:
        out = out[pd.to_numeric(out[local_subs_col], errors="coerce").fillna(0) >= min_subs]

    if local_view_col and "min_views" in globals() and min_views > 0:
        out = out[pd.to_numeric(out[local_view_col], errors="coerce").fillna(0) >= min_views]

    if local_channel_name_col and "search_text" in globals() and search_text:
        out = out[out[local_channel_name_col].astype(str).str.contains(search_text, case=False, na=False)]

    return out


def calc_kpi_values(kpi_df: pd.DataFrame) -> dict:
    """
    KPI 카드용 수치 계산
    """
    if kpi_df is None or kpi_df.empty:
        return {
            "total": np.nan,
            "shortlist": np.nan,
            "avg_score": np.nan,
            "high_priority": np.nan,
        }

    local_action_col = first_existing(kpi_df, ["액션버킷", "action_bucket"])
    local_shortlist_col = first_existing(kpi_df, ["shortlist_선정여부", "shortlist", "shortlisted"])
    local_score_display_col = "최종점수_100점" if "최종점수_100점" in kpi_df.columns else None

    total = len(kpi_df)

    if local_shortlist_col:
        shortlist = int(
            kpi_df[local_shortlist_col]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes", "y"])
            .sum()
        )
    elif local_action_col:
        shortlist = int(
            kpi_df[local_action_col]
            .astype(str)
            .str.contains("즉시검토|성장관찰|검증", na=False)
            .sum()
        )
    else:
        shortlist = 0

    if local_score_display_col:
        avg_score = pd.to_numeric(kpi_df[local_score_display_col], errors="coerce").mean()
    else:
        avg_score = np.nan

    if local_action_col:
        high_priority = int(
            kpi_df[local_action_col]
            .astype(str)
            .str.contains("즉시검토|영입제한|위성|Satellite", na=False)
            .sum()
        )
    else:
        high_priority = 0

    return {
        "total": total,
        "shortlist": shortlist,
        "avg_score": avg_score,
        "high_priority": high_priority,
    }


def render_kpi_card(label, value, sub, delta=None, value_suffix="", value_ndigits=0, delta_ndigits=0, delta_suffix=""):
    """
    KPI 카드 렌더링
    """
    if value_ndigits == 0:
        value_text = f"{fmt_int(value)}{value_suffix}"
    else:
        value_text = f"{fmt_float(value, value_ndigits)}{value_suffix}"

    delta_html = make_kpi_delta_html(delta, ndigits=delta_ndigits, suffix=delta_suffix)

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value_text}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_short_reason(row, reason_cols):
    texts = []
    for c in reason_cols:
        if c in row.index:
            val = row.get(c)
            if pd.notna(val) and str(val).strip():
                texts.append(str(val).strip())
    return " / ".join(texts[:2]) if texts else "-"


def get_initial(name):
    if pd.isna(name) or not str(name).strip():
        return "?"
    return str(name).strip()[0]





def get_content_avatar_spec(segment, lower_segment):
    """
    TOP 후보 카드에서 채널명 첫 글자 대신 세부 콘텐츠 유형에 맞는 아이콘을 보여준다.
    외부 이미지 파일 없이 emoji + CSS 카드로 구성해 Streamlit Cloud에서도 별도 asset 없이 동작한다.
    """
    raw = f"{segment} {lower_segment}".lower()

    rules = [
        (("성우", "더빙", "voice", "보이스"), ("🎙️", "avatar-voice", "성우/더빙")),
        (("커버", "노래", "보컬", "j-pop", "jpop", "애니송", "음악"), ("🎧", "avatar-cover", "음악/커버")),
        (("버튜버", "vtuber", "버츄얼", "virtual"), ("🪐", "avatar-vtuber", "버튜버")),
        (("코스프레", "cosplay"), ("🎭", "avatar-cosplay", "코스프레")),
        (("게임", "롤", "로블록스", "발로란트", "valorant", "roblox", "원신", "마인크래프트"), ("🎮", "avatar-game", "게임")),
        (("asmr", "에이에스엠알"), ("🎧", "avatar-asmr", "ASMR")),
        (("댄스", "퍼포먼스", "아이돌", "무대"), ("✨", "avatar-music", "퍼포먼스")),
        (("토크", "팬덤", "라디오", "소통"), ("💬", "avatar-talk", "토크/팬덤")),
    ]

    for keywords, spec in rules:
        if any(k in raw for k in keywords):
            return spec
    return ("🌱", "avatar-default", "기타 콘텐츠")


def get_content_avatar_html(segment, lower_segment):
    icon, css_class, label = get_content_avatar_spec(segment, lower_segment)
    safe_label = html_lib.escape(label)
    return f'<div class="content-avatar {css_class}" title="{safe_label}"><span class="content-avatar-icon">{icon}</span></div>'


def is_valid_url(value) -> bool:
    if pd.isna(value):
        return False
    text_value = str(value).strip()
    if not text_value or text_value.lower() in ["nan", "none", "null", "-"]:
        return False
    return text_value.startswith("http://") or text_value.startswith("https://")


def get_candidate_avatar_html(row, segment_col=None, lower_segment_col=None, thumbnail_col=None):
    """
    후보 카드 이미지 HTML 생성.
    1순위: YouTube 채널 프로필 이미지 URL(channel_thumbnail_url)
    2순위: 세부 콘텐츠 유형 기반 fallback 아이콘
    """
    thumbnail_url = row.get(thumbnail_col, "") if thumbnail_col else ""

    if is_valid_url(thumbnail_url):
        safe_url = html_lib.escape(str(thumbnail_url).strip(), quote=True)
        return f'<div class="content-avatar has-profile-img" title="YouTube 채널 프로필 이미지"><img src="{safe_url}" class="content-avatar-img" loading="lazy" referrerpolicy="no-referrer"></div>'

    segment = row.get(segment_col, "-") if segment_col else "-"
    lower_segment = row.get(lower_segment_col, "") if lower_segment_col else ""
    return get_content_avatar_html(segment, lower_segment)


def get_selected_profile_html(row, segment_col=None, lower_segment_col=None, thumbnail_col=None):
    """
    선택 후보 상세용 프로필 이미지 HTML.
    1순위는 YouTube 채널 프로필 이미지, 없으면 콘텐츠 유형 fallback 아이콘을 가운데 표시한다.
    """
    thumbnail_url = row.get(thumbnail_col, "") if thumbnail_col else ""
    if is_valid_url(thumbnail_url):
        safe_url = html_lib.escape(str(thumbnail_url).strip(), quote=True)
        return (
            '<div class="selected-profile-img-wrap" title="YouTube 채널 프로필 이미지">'
            f'<img src="{safe_url}" class="selected-profile-img" loading="lazy" referrerpolicy="no-referrer">'
            '</div>'
        )

    fallback_html = get_candidate_avatar_html(row, segment_col, lower_segment_col, thumbnail_col=None)
    return f'<div class="selected-profile-fallback">{fallback_html}</div>'


def make_channel_name_html(name, url=""):
    safe_name = html_lib.escape(str(name) if str(name).strip() else "-", quote=False)

    if is_valid_url(url):
        safe_url = html_lib.escape(str(url).strip(), quote=True)
        return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" title="YouTube 채널 열기">{safe_name}</a>'

    return safe_name


def color_by_segment(seg):
    s = str(seg)
    if "영입제한" in s:
        return "#b66cff"
    if "위성" in s or "Satellite" in s:
        return "#33d6c5"
    if "즉시검토" in s:
        return "#ff6fae"
    if "성장" in s:
        return "#37c7ff"
    if "검증" in s:
        return "#ffae42"
    return "#6b7280"


def add_section_divider():
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def clean_display_text(series: pd.Series) -> pd.Series:
    return series.replace(["None", "nan", "NaN", "", None], pd.NA).fillna("미분류")


def is_unclassified_value(series: pd.Series) -> pd.Series:
    """상위 콘텐츠군 미확인 값을 판정한다."""
    return (
        series.astype(str)
        .str.strip()
        .isin(["", "미분류", "None", "none", "nan", "NaN", "NULL", "null", "<NA>"])
    )


def apply_unclassified_hold_rule(data: pd.DataFrame, seg_col: str | None, action_col_name: str | None, output_col: str = "검토단계_표시") -> pd.DataFrame:
    """
    상위 콘텐츠군이 미분류인 후보는 점수와 관계없이 화면/변화추적 기준 검토 단계를 보류로 보정한다.
    - 원본 액션버킷은 보존하고, output_col에 표시/운영용 검토 단계를 만든다.
    - 이유: 미분류는 콘텐츠군이 확인되지 않은 데이터 품질 이슈이므로 즉시검토로 보이면 해석 모순이 발생한다.
    """
    out = data.copy()

    if action_col_name and action_col_name in out.columns:
        out[output_col] = out[action_col_name]
    else:
        out[output_col] = pd.NA

    out[output_col] = out[output_col].replace(["None", "nan", "NaN", "", None], pd.NA).fillna("미분류")

    if seg_col and seg_col in out.columns:
        unclassified_mask = is_unclassified_value(out[seg_col])
        out.loc[unclassified_mask, output_col] = "보류"

    return out


# =========================================================
# 3-1. Snapshot 기반 변화 추적 유틸
# =========================================================

def _snapshot_date_col(snap: pd.DataFrame):
    return first_existing(
        snap,
        [
            "snapshot_ts_kst",
            "snapshot_datetime",
            "snapshot_date",
            "스냅샷시각",
            "기준시각",
            "created_at",
        ],
    )


def prepare_snapshot_df(snap: pd.DataFrame) -> pd.DataFrame:
    if snap is None or snap.empty:
        return pd.DataFrame()

    out = snap.copy()
    date_col = _snapshot_date_col(out)

    if date_col is None:
        return pd.DataFrame()

    # -----------------------------------------------------
    # 날짜 파싱 보정
    # - Streamlit Cloud / pandas 버전에 따라 timezone이 섞인 timestamp가
    #   하루 밀려 보이는 경우를 방지하기 위해, 원본 문자열에
    #   YYYY-MM-DD 패턴이 있으면 그 날짜를 우선 사용한다.
    # - 예: 2026-05-01T23:xx:xx+09:00 같은 값이 UTC 변환 과정에서
    #   2026-05-02로 보이는 문제를 방지한다.
    # -----------------------------------------------------
    raw_date_text = out[date_col].astype(str).str.strip()
    extracted_date = raw_date_text.str.extract(r"(20\d{2}-\d{2}-\d{2})", expand=False)

    out["__snapshot_dt__"] = pd.to_datetime(out[date_col], errors="coerce")
    out["__snapshot_date__"] = extracted_date

    # 원본 문자열에서 날짜를 못 뽑은 행만 datetime 파싱값으로 보완
    missing_date_mask = out["__snapshot_date__"].isna() | (out["__snapshot_date__"].astype(str).str.strip() == "")
    out.loc[missing_date_mask, "__snapshot_date__"] = (
        out.loc[missing_date_mask, "__snapshot_dt__"].dt.strftime("%Y-%m-%d")
    )

    out["__snapshot_date_dt__"] = pd.to_datetime(out["__snapshot_date__"], errors="coerce")
    out = out.dropna(subset=["__snapshot_date_dt__"]).copy()

    if out.empty:
        return pd.DataFrame()

    # 같은 날짜 내부에서 최신 실행분을 고르기 위해 dt가 없으면 날짜 기준으로 보완
    out["__snapshot_dt__"] = out["__snapshot_dt__"].fillna(out["__snapshot_date_dt__"])
    out["__snapshot_date__"] = out["__snapshot_date_dt__"].dt.strftime("%Y-%m-%d")

    return out


def get_snapshot_by_date(snap: pd.DataFrame, date_label: str) -> pd.DataFrame:
    if snap is None or snap.empty or "__snapshot_date__" not in snap.columns:
        return pd.DataFrame()

    target = snap[snap["__snapshot_date__"] == date_label].copy()
    if target.empty:
        return pd.DataFrame()

    # 같은 날짜에 여러 번 snapshot이 append되어 있으면 해당 날짜의 가장 마지막 실행분만 사용
    latest_dt = target["__snapshot_dt__"].max()
    target = target[target["__snapshot_dt__"] == latest_dt].copy()

    # 혹시 같은 채널이 중복되면 최신 행/상위 행 우선으로 1개만 유지
    id_col = first_existing(target, ["채널ID", "channel_id"])
    rank_col_local = first_existing(target, ["운영우선순위", "최종순위", "rank", "순위"])
    score_col_local = first_existing(target, ["최종점수", "위성점수_log_minmax", "final_score", "score"])

    if rank_col_local:
        target[rank_col_local] = pd.to_numeric(target[rank_col_local], errors="coerce")
        target = target.sort_values(rank_col_local, ascending=True, na_position="last")
    elif score_col_local:
        target[score_col_local] = pd.to_numeric(target[score_col_local], errors="coerce")
        target = target.sort_values(score_col_local, ascending=False, na_position="last")

    if id_col:
        target[id_col] = target[id_col].astype(str).str.strip()
        target = target.drop_duplicates(subset=[id_col], keep="first")

    return target.reset_index(drop=True)


def standardize_for_tracking(source: pd.DataFrame, prefix: str) -> pd.DataFrame:
    if source is None or source.empty:
        return pd.DataFrame()

    src = source.copy()

    id_col = first_existing(src, ["채널ID", "channel_id"])
    name_col = first_existing(src, ["채널명", "channel_title", "채널명_clean"])
    rank_col_local = first_existing(src, ["운영우선순위", "최종순위", "rank", "순위"])
    score_col_local = first_existing(src, ["최종점수", "위성점수_log_minmax", "final_score", "score"])
    action_col_local = first_existing(src, ["액션버킷", "action_bucket"])
    upper_col = first_existing(src, ["대표상위세그먼트", "대표세그먼트", "segment", "대표상위세그먼트명"])
    lower_col = first_existing(src, ["대표하위세그먼트", "sub_segment", "대표하위세그먼트명"])

    if id_col is None:
        return pd.DataFrame()

    src[id_col] = src[id_col].astype(str).str.strip()

    # 운영우선순위가 없으면 점수 기준으로 순위를 임시 생성
    if rank_col_local is None:
        if score_col_local:
            src[score_col_local] = pd.to_numeric(src[score_col_local], errors="coerce")
            src = src.sort_values(score_col_local, ascending=False, na_position="last").copy()
        src[f"{prefix}_운영우선순위"] = np.arange(1, len(src) + 1)
        rank_col_local = f"{prefix}_운영우선순위"

    keep = pd.DataFrame()
    keep["채널ID"] = src[id_col]
    keep[f"{prefix}_채널명"] = src[name_col] if name_col else pd.NA
    keep[f"{prefix}_운영우선순위"] = pd.to_numeric(src[rank_col_local], errors="coerce")
    if score_col_local:
        keep[f"{prefix}_최종점수"] = normalize_score_to_100(src[score_col_local])
    else:
        keep[f"{prefix}_최종점수"] = np.nan
    keep[f"{prefix}_액션버킷"] = src[action_col_local] if action_col_local else pd.NA
    keep[f"{prefix}_대표상위세그먼트"] = src[upper_col] if upper_col else pd.NA
    keep[f"{prefix}_대표하위세그먼트"] = src[lower_col] if lower_col else pd.NA

    # 상위 콘텐츠군 미분류 후보는 변화 추적에서도 즉시검토/성장관찰로 보이지 않도록 보류 처리
    # 원본 snapshot이 과거 로직으로 즉시검토를 갖고 있어도 표시 기준은 보류가 맞다.
    if f"{prefix}_대표상위세그먼트" in keep.columns:
        unclassified_mask = is_unclassified_value(keep[f"{prefix}_대표상위세그먼트"])
        keep.loc[unclassified_mask, f"{prefix}_액션버킷"] = "보류"

    return keep.drop_duplicates(subset=["채널ID"], keep="first")


def build_tracking_between(base_df: pd.DataFrame, target_df: pd.DataFrame, base_label: str, target_label: str) -> pd.DataFrame:
    base = standardize_for_tracking(base_df, "기준")
    target = standardize_for_tracking(target_df, "비교")

    if target.empty:
        return pd.DataFrame()

    merged = target.merge(base, on="채널ID", how="left")

    merged["채널명"] = merged["비교_채널명"].combine_first(merged.get("기준_채널명"))
    merged["기준시점"] = base_label
    merged["비교시점"] = target_label
    # -----------------------------------------------------
    # 대표상위/하위세그먼트 누락 보완
    # - 비교 시점 snapshot에 세그먼트가 비어 있으면
    #   기준 시점 세그먼트 → 현재 최신 df 매핑 순서로 보완
    # -----------------------------------------------------

    if "비교_대표상위세그먼트" in merged.columns:
        merged["비교_대표상위세그먼트"] = (
            merged["비교_대표상위세그먼트"]
            .replace(["None", "nan", "NaN", ""], pd.NA)
        )

        if "기준_대표상위세그먼트" in merged.columns:
            merged["기준_대표상위세그먼트"] = (
                merged["기준_대표상위세그먼트"]
                .replace(["None", "nan", "NaN", ""], pd.NA)
            )
            merged["비교_대표상위세그먼트"] = (
                merged["비교_대표상위세그먼트"]
                .combine_first(merged["기준_대표상위세그먼트"])
            )

        # 현재 최신 df에서 채널ID 기준으로 대표상위세그먼트 보완
        try:
            if "df" in globals() and channel_id_col and segment_col:
                latest_segment_map = (
                    df[[channel_id_col, segment_col]]
                    .dropna(subset=[channel_id_col])
                    .copy()
                )
                latest_segment_map[channel_id_col] = latest_segment_map[channel_id_col].astype(str).str.strip()
                latest_segment_map[segment_col] = latest_segment_map[segment_col].replace(
                    ["None", "nan", "NaN", ""], pd.NA
                )
                latest_segment_map = latest_segment_map.dropna(subset=[segment_col])
                latest_segment_map = latest_segment_map.drop_duplicates(subset=[channel_id_col], keep="first")

                seg_map = latest_segment_map.set_index(channel_id_col)[segment_col].to_dict()

                merged["비교_대표상위세그먼트"] = (
                    merged["비교_대표상위세그먼트"]
                    .combine_first(merged["채널ID"].astype(str).str.strip().map(seg_map))
                )
        except Exception:
            pass

        merged["비교_대표상위세그먼트"] = merged["비교_대표상위세그먼트"].fillna("미분류")

    if "비교_대표하위세그먼트" in merged.columns:
        merged["비교_대표하위세그먼트"] = (
            merged["비교_대표하위세그먼트"]
            .replace(["None", "nan", "NaN", ""], pd.NA)
        )

        if "기준_대표하위세그먼트" in merged.columns:
            merged["기준_대표하위세그먼트"] = (
                merged["기준_대표하위세그먼트"]
                .replace(["None", "nan", "NaN", ""], pd.NA)
            )
            merged["비교_대표하위세그먼트"] = (
                merged["비교_대표하위세그먼트"]
                .combine_first(merged["기준_대표하위세그먼트"])
            )

        try:
            if "df" in globals() and channel_id_col and lower_segment_col:
                latest_lower_map = (
                    df[[channel_id_col, lower_segment_col]]
                    .dropna(subset=[channel_id_col])
                    .copy()
                )
                latest_lower_map[channel_id_col] = latest_lower_map[channel_id_col].astype(str).str.strip()
                latest_lower_map[lower_segment_col] = latest_lower_map[lower_segment_col].replace(
                    ["None", "nan", "NaN", ""], pd.NA
                )
                latest_lower_map = latest_lower_map.dropna(subset=[lower_segment_col])
                latest_lower_map = latest_lower_map.drop_duplicates(subset=[channel_id_col], keep="first")

                lower_map = latest_lower_map.set_index(channel_id_col)[lower_segment_col].to_dict()

                merged["비교_대표하위세그먼트"] = (
                    merged["비교_대표하위세그먼트"]
                    .combine_first(merged["채널ID"].astype(str).str.strip().map(lower_map))
                )
        except Exception:
            pass

        merged["비교_대표하위세그먼트"] = merged["비교_대표하위세그먼트"].fillna("미분류")

    # -----------------------------------------------------
    # 변화 추적 검토 단계 보정
    # - 상위 콘텐츠군이 미분류이면 점수 상승 여부와 관계없이 현재/이전 검토 단계를 보류로 표시
    # - 즉시검토 후보로 보이면 TOP 후보 표와 변화 추적 표의 해석이 충돌하기 때문
    # -----------------------------------------------------
    for prefix in ["기준", "비교"]:
        seg_c = f"{prefix}_대표상위세그먼트"
        action_c = f"{prefix}_액션버킷"
        if seg_c in merged.columns and action_c in merged.columns:
            unclassified_mask = is_unclassified_value(merged[seg_c])
            merged.loc[unclassified_mask, action_c] = "보류"

    merged["운영우선순위변동"] = merged["기준_운영우선순위"] - merged["비교_운영우선순위"]
    merged["최종점수변동"] = merged["비교_최종점수"] - merged["기준_최종점수"]
    merged["신규진입여부"] = merged["기준_운영우선순위"].isna()
    merged["버킷변경여부"] = (
        merged["기준_액션버킷"].fillna("신규")
        != merged["비교_액션버킷"].fillna("미분류")
    )

    def make_change_summary(row):
        if bool(row.get("신규진입여부", False)):
            return "신규진입"

        parts = []
        rank_delta = row.get("운영우선순위변동")
        score_delta = row.get("최종점수변동")

        if pd.notna(rank_delta):
            if rank_delta > 0:
                parts.append(f"순위 {int(rank_delta)}단계 상승")
            elif rank_delta < 0:
                parts.append(f"순위 {abs(int(rank_delta))}단계 하락")
            else:
                parts.append("순위 유지")

        if pd.notna(score_delta):
            if score_delta > 0:
                parts.append(f"점수 +{score_delta:.1f}")
            elif score_delta < 0:
                parts.append(f"점수 {score_delta:.1f}")
            else:
                parts.append("점수 유지")

        if row.get("버킷변경여부", False):
            parts.append(f"버킷 {row.get('기준_액션버킷')} → {row.get('비교_액션버킷')}")

        return " / ".join(parts) if parts else "변화 없음"

    merged["변화요약"] = merged.apply(make_change_summary, axis=1)

    out_cols = [
        "기준시점",
        "비교시점",
        "채널명",
        "채널ID",
        "기준_운영우선순위",
        "비교_운영우선순위",
        "운영우선순위변동",
        "기준_최종점수",
        "비교_최종점수",
        "최종점수변동",
        "기준_액션버킷",
        "비교_액션버킷",
        "버킷변경여부",
        "신규진입여부",
        "비교_대표상위세그먼트",
        "비교_대표하위세그먼트",
        "변화요약",
    ]

    out = merged[[c for c in out_cols if c in merged.columns]].copy()
    out = out.sort_values(
        ["비교_운영우선순위", "비교_최종점수"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)

    return out


# =========================================================
# 4. 데이터 없을 때
# =========================================================

if candidate_df.empty:
    st.error(
        "후보 데이터 CSV를 찾지 못했습니다. 먼저 파이프라인을 실행해서 "
        "`10_dashboard/data/dashboard_candidate_table.csv` 또는 "
        "`11_final/core_output/candidate_scored_final.csv`를 생성해주세요."
    )
    st.stop()


# =========================================================
# 5. 컬럼 매핑
# =========================================================

df = candidate_df.copy()

channel_id_col = first_existing(df, ["채널ID", "channel_id"])
channel_name_col = first_existing(df, ["채널명", "channel_title", "채널명_clean"])
channel_thumbnail_col = first_existing(df, ["channel_thumbnail_url", "채널썸네일URL", "채널프로필이미지URL", "thumbnail_url"])
channel_url_col = first_existing(df, ["channel_url", "채널URL", "youtube_channel_url", "유튜브채널URL"])

# ---------------------------------------------------------
# 주요 화면/필터용 컬럼 매핑
# - 사이드바 일부 블록 제거 과정에서 누락되면 NameError가 나므로
#   스타시드 본문에서 쓰는 컬럼을 여기서 먼저 안정적으로 정의한다.
# ---------------------------------------------------------
score_col = first_existing(df, [
    "최종점수", "최종점수_100점", "영입적합도점수", "영입 적합도 점수",
    "영입종합점수", "영입 종합 점수", "위성점수_log_minmax", "final_score", "score"
])
rank_col = first_existing(df, [
    "운영우선순위", "최종순위", "현재 필터 기준 순위", "순위", "rank", "final_rank"
])
segment_col = first_existing(df, [
    "대표상위세그먼트", "주요 콘텐츠군", "상위 콘텐츠군", "대표세그먼트",
    "segment", "segment_unified", "대표상위세그먼트명"
])
lower_segment_col = first_existing(df, [
    "대표하위세그먼트", "세부 콘텐츠 유형", "하위 콘텐츠군", "sub_segment",
    "대표하위세그먼트명", "segment_seed", "segment_seed_raw"
])
action_col = first_existing(df, [
    "액션버킷", "검토 단계", "현재 검토 단계", "현재검토단계", "action_bucket"
])
shortlist_col = first_existing(df, [
    "shortlist_선정여부", "shortlist 선정 여부", "shortlist", "is_shortlist", "shortlist_selected"
])
shortlist_type_col = first_existing(df, [
    "shortlist_유형", "shortlist 유형", "shortlist_type"
])
subs_col = first_existing(df, [
    "채널구독자수", "채널 구독자 수", "구독자수", "구독자 수",
    "subscriber_count", "subscribers", "channel_subscriber_count"
])
view_col = first_existing(df, [
    "최근영상조회수평균", "최근 영상 평균 조회수", "최근 조회수 평균", "recent_view_avg",
    "avg_recent_view_count", "view_count_mean", "평균조회수"
])
eng_col = first_existing(df, [
    "평균참여율", "평균 참여율", "참여율", "engagement_rate", "avg_engagement_rate"
])
growth_col = first_existing(df, [
    "성장성점수", "성장성", "growth_score", "growth_proxy", "성장성_score"
])
fan_col = first_existing(df, [
    "팬밀도점수", "팬밀도", "fan_density_score", "fan_density", "팬밀도_score"
])
live_col = first_existing(df, [
    "라이브친화점수", "라이브친화", "live_friendly_score", "live_affinity", "라이브친화_score"
])
recommend_col = first_existing(df, [
    "추천사유", "추천 사유", "recommend_reason", "추천근거"
])
caution_col = first_existing(df, [
    "주의사유", "주의 사유", "caution_reason", "리스크사유"
])
change_col = first_existing(df, [
    "변화요약", "변화 요약", "change_summary"
])

# =========================================================
# 최종점수 100점 기준 표시 컬럼 생성
# - 원본 최종점수가 0~1이면 100점 환산
# - 이미 0~100이면 그대로 사용
# - Streamlit 화면/필터/표/그래프에서는 이 컬럼을 기준으로 사용
# =========================================================

if score_col is not None:
    df["_score_raw"] = pd.to_numeric(df[score_col], errors="coerce")
    df["최종점수_100점"] = normalize_score_to_100(df[score_col])
    df["_score_display"] = df["최종점수_100점"]
else:
    df["_score_raw"] = np.nan
    df["최종점수_100점"] = np.nan
    df["_score_display"] = np.nan

score_display_col = "최종점수_100점"

# =========================================================
# 표시/운영용 검토 단계 보정
# - 상위 콘텐츠군이 미분류인 후보는 점수가 높아도 즉시검토로 해석하지 않고 보류 처리
# - 원본 액션버킷은 보존하고, 화면 필터/표/그래프에서는 검토단계_표시를 사용
# =========================================================
original_action_col = action_col
df = apply_unclassified_hold_rule(df, segment_col, original_action_col, output_col="검토단계_표시")
action_col = "검토단계_표시"

if rank_col is not None:
    df = df.sort_values(rank_col, ascending=True, na_position="last")
elif score_col is not None:
    df = df.sort_values(score_col, ascending=False, na_position="last")

df = df.reset_index(drop=True)

# Snapshot 테이블 준비
snapshot_prepared_df = prepare_snapshot_df(snapshot_df)


# =========================================================
# 6. 사이드바 필터
# - 스타시드 필터는 드롭다운(expander) 안에 배치
# - 기본은 접힘 상태로 두어 홈/네비게이션 가시성을 확보
# =========================================================

st.sidebar.markdown("---")

filtered = df.copy()

# apply_snapshot_filters_for_kpi()에서 참조할 수 있도록 기본값 선할당
selected_segments = []
selected_lower = []
selected_actions = []
only_shortlist = False
hide_hold = True
score_filter_100 = None
min_subs = 0
min_views = 0
search_text = ""

def _filter_widget_container():
    """스타시드 필터용 드롭다운 컨테이너."""
    return st.sidebar.expander("스타시드 필터", expanded=False)

with _filter_widget_container() as filter_panel:
    filter_panel.caption("상위 콘텐츠군, 검토 단계, 점수·규모 조건으로 후보군을 좁혀봅니다.")

    if segment_col:
        seg_values = sorted([x for x in filtered[segment_col].dropna().astype(str).unique()])
        selected_segments = filter_panel.multiselect(
            "상위 콘텐츠군",
            options=seg_values,
            default=seg_values,
            help="후보 채널의 대표 상위 콘텐츠군입니다. 예: 게임 실황형, 음악·보이스형 등",
        )
        if selected_segments:
            filtered = filtered[filtered[segment_col].astype(str).isin(selected_segments)]

    if lower_segment_col:
        lower_values = sorted([x for x in filtered[lower_segment_col].dropna().astype(str).unique()])
        selected_lower = filter_panel.multiselect(
            "세부 콘텐츠 유형",
            options=lower_values,
            default=[],
            help="상위 콘텐츠군보다 더 세분화된 콘텐츠 유형입니다.",
        )
        if selected_lower:
            filtered = filtered[filtered[lower_segment_col].astype(str).isin(selected_lower)]

    if action_col:
        action_values = sorted([x for x in filtered[action_col].dropna().astype(str).unique()])
        selected_actions = filter_panel.multiselect(
            "검토 단계",
            options=action_values,
            default=action_values,
            help="즉시검토, 성장관찰, 검증필요, 보류, 제외 등 운영용 후보 분류입니다.",
        )
        if selected_actions:
            filtered = filtered[filtered[action_col].astype(str).isin(selected_actions)]

    if shortlist_col:
        only_shortlist = filter_panel.checkbox("shortlist 선정 후보만 보기", value=False)
        if only_shortlist:
            shortlist_bool = filtered[shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])
            filtered = filtered[shortlist_bool]

    hide_hold = filter_panel.checkbox("보류/제외 숨기기", value=True)

    if hide_hold and action_col:
        filtered = filtered[
            ~filtered[action_col].astype(str).str.contains("보류|제외", na=False)
        ]

    # =========================================================
    # 점수 필터: 100점 기준
    # - 원본 최종점수가 0~1이어도 화면에서는 0~100점으로 필터링
    # =========================================================

    if score_col:
        score_series_100 = pd.to_numeric(df[score_display_col], errors="coerce")

        if score_series_100.dropna().empty:
            score_filter_100 = 0.0
        else:
            min_score_100 = float(score_series_100.min(skipna=True))
            max_score_100 = float(score_series_100.max(skipna=True))

            score_filter_100 = filter_panel.slider(
                "최소 영입 적합도 점수(100점 기준)",
                min_value=float(np.floor(min_score_100)),
                max_value=float(np.ceil(max_score_100)),
                value=float(np.floor(min_score_100)),
                step=1.0,
            )

            filtered = filtered[
                pd.to_numeric(filtered[score_display_col], errors="coerce") >= score_filter_100
            ]

    if subs_col:
        min_subs = int(filter_panel.number_input("최소 구독자 수", min_value=0, value=0, step=1000))
        if min_subs > 0:
            filtered = filtered[pd.to_numeric(filtered[subs_col], errors="coerce").fillna(0) >= min_subs]

    if view_col:
        min_views = int(filter_panel.number_input("최소 최근영상조회수평균", min_value=0, value=0, step=1000))
        if min_views > 0:
            filtered = filtered[pd.to_numeric(filtered[view_col], errors="coerce").fillna(0) >= min_views]

    search_text = filter_panel.text_input("채널명 검색", placeholder="채널명을 입력하세요")

    if search_text and channel_name_col:
        filtered = filtered[
            filtered[channel_name_col].astype(str).str.contains(search_text, case=False, na=False)
        ]

    top_n = filter_panel.slider("TOP N", min_value=5, max_value=50, value=10, step=5)

# =========================================================
# 필터 적용 후 화면 표시용 순위 재부여
# =========================================================

filtered = filtered.copy()
filtered["표시순위"] = np.arange(1, len(filtered) + 1)

# =========================================================
# 변화 추적 기준 시점 필터
# - 2026-05-01 이전 snapshot은 선택 불가
# - 비교 대상 시점/기준 시점 모두 최소 날짜를 2026-05-01로 제한
# =========================================================

st.sidebar.markdown("---")
change_panel = st.sidebar.expander("변화 추적 기준", expanded=False)
change_panel.caption("snapshot 기준 시점과 현재/비교 시점을 선택해 후보 변화량을 계산합니다.")

tracking_base_df = pd.DataFrame()
tracking_target_df = pd.DataFrame()
tracking_base_label = "-"
tracking_target_label = "현재"

if not snapshot_prepared_df.empty:
    snapshot_dates_all = (
        snapshot_prepared_df[["__snapshot_date__", "__snapshot_date_dt__"]]
        .dropna(subset=["__snapshot_date__", "__snapshot_date_dt__"])
        .drop_duplicates(subset=["__snapshot_date__"])
        .sort_values("__snapshot_date_dt__")
        ["__snapshot_date__"]
        .tolist()
    )

    # 핵심 수정: 2026-05-01 이전 날짜 제거
    # - 날짜 문자열 비교가 아니라 datetime 기준으로 비교
    # - 2026-05-01은 포함되어야 하므로 >= 조건 유지
    snapshot_dates = [
        d for d in snapshot_dates_all
        if pd.to_datetime(d, errors="coerce") >= MIN_TRACKING_DATE
    ]

    if not snapshot_dates:
        change_panel.warning(
            f"{MIN_TRACKING_DATE_LABEL} 이후 snapshot 날짜가 없습니다. "
            "STEP11 snapshot append를 다시 누적하세요."
        )
        tracking_target_df = df.copy()
        tracking_target_label = "현재"
    else:
        target_options = snapshot_dates + ["현재"]

        default_target_idx = len(target_options) - 1

        tracking_target_label = change_panel.selectbox(
            "비교 대상 시점",
            options=target_options,
            index=default_target_idx,
            help=f"{MIN_TRACKING_DATE_LABEL} 이후 snapshot 또는 현재 데이터를 비교 대상 시점으로 선택합니다.",
        )

        if tracking_target_label == "현재":
            tracking_target_df = df.copy()
            available_base_dates = snapshot_dates
        else:
            tracking_target_df = get_snapshot_by_date(snapshot_prepared_df, tracking_target_label)

            # 기준 시점도 2026-05-01 이상 + 비교 대상 시점 이하만 허용
            available_base_dates = [
                d for d in snapshot_dates
                if d <= tracking_target_label
            ]

        if available_base_dates:
            # 기본값:
            # - 현재 비교: 가장 최근 snapshot
            # - 과거 snapshot 비교: 같은 날짜가 있으면 같은 날짜를 기본값으로 둠
            #   동일 날짜 비교 시 증감이 0으로 나와야 정상
            if tracking_target_label == "현재":
                # 기본 기준 시점은 2026-05-01이 있으면 2026-05-01로 둔다.
                # 없으면 사용 가능한 가장 이른 날짜를 기본값으로 사용한다.
                if MIN_TRACKING_DATE_LABEL in available_base_dates:
                    default_base_label = MIN_TRACKING_DATE_LABEL
                else:
                    default_base_label = available_base_dates[0]
            else:
                default_base_label = tracking_target_label

            if default_base_label not in available_base_dates:
                default_base_label = available_base_dates[-1]

            default_base_idx = available_base_dates.index(default_base_label)

            tracking_base_label = change_panel.selectbox(
                "기준 시점",
                options=available_base_dates,
                index=default_base_idx,
                help=f"{MIN_TRACKING_DATE_LABEL} 이후 날짜만 기준 시점으로 선택할 수 있습니다.",
            )

            tracking_base_df = get_snapshot_by_date(snapshot_prepared_df, tracking_base_label)
        else:
            change_panel.warning("비교 가능한 기준 snapshot 날짜가 없습니다.")
else:
    change_panel.warning("snapshot 파일이 없거나 날짜 컬럼을 찾지 못했습니다.")




# =========================================================
# 6-9. 최종 디자인 피드백 반영
# - STAR SEED 상단 폰트/정렬을 메인 프론트와 맞춤
# - KPI/후보/표/그래프 카드 배경을 더 불투명하게 조정
# - Plotly 그래프 배경과 카드 배경을 분리해 별빛/반짝임과 헷갈리지 않게 함
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        /* 전체 컨테이너 폭/상단 간격: 메인 대시보드와 유사한 밀도 */
        .block-container {
            max-width: 1520px !important;
            padding-top: 0rem !important;
            padding-left: 2.0rem !important;
            padding-right: 2.0rem !important;
            padding-bottom: 2.5rem !important;
        }

        .starseed-board {
            width: 100%;
            padding: 0 0 18px 0;
            margin-top: -30px;
            position: relative;
            z-index: 2;
        }

        .starseed-title {
            font-family: 'Orbitron', sans-serif !important;
            font-size: clamp(78px, 7.9vw, 108px) !important;
            font-weight: 950 !important;
            letter-spacing: 17px !important;
            line-height: 0.96 !important;
            color: #fff8ff !important;
            text-align: center !important;
            text-shadow:
                0 0 10px rgba(255,255,255,0.28),
                0 0 24px rgba(214,182,255,0.34),
                0 0 46px rgba(125,66,255,0.18) !important;
            margin: 0 !important;
        }

        .starseed-subtitle {
            font-size: clamp(20px, 1.65vw, 27px) !important;
            font-weight: 850 !important;
            letter-spacing: -0.035em !important;
            color: #d7cded !important;
            text-align: center !important;
            margin-top: 24px !important;
            margin-bottom: 0 !important;
            line-height: 1.25 !important;
            text-shadow: 0 0 16px rgba(198,168,255,0.16) !important;
        }

        /* 카드 배경: 기존보다 불투명하게 하여 별빛과 내부 콘텐츠 분리 */
        .kpi-card,
        .candidate-card,
        .section-card,
        .priority-board-wrap,
        .tracking-board-wrap,
        .detail-box,
        .reason-box,
        .explain-box,
        .guide-box,
        div[data-testid="stExpander"] {
            background:
                linear-gradient(180deg, rgba(9, 22, 42, 0.98), rgba(5, 13, 28, 0.985)) !important;
            border: 1px solid rgba(118, 242, 226, 0.22) !important;
            box-shadow:
                0 16px 36px rgba(0,0,0,0.38),
                inset 0 1px 0 rgba(255,255,255,0.055) !important;
            backdrop-filter: blur(2px) !important;
        }

        /* KPI 카드는 메인 대시보드 카드 톤으로 통일 */
        .kpi-card {
            background:
                linear-gradient(180deg, rgba(8, 24, 45, 0.985), rgba(5, 13, 28, 0.995)) !important;
            border-color: rgba(89, 219, 210, 0.26) !important;
        }



        /* KPI 카드와 첫 번째 드롭다운 사이 여백 보정 */
        .kpi-expander-spacer {
            height: 22px;
        }

        /* TOP 후보 카드도 투명감을 줄이고 내부 정보 가독성 강화 */
        .candidate-card {
            background:
                linear-gradient(180deg, rgba(8, 24, 45, 0.985), rgba(5, 13, 28, 0.995)) !important;
            border-color: rgba(89, 219, 210, 0.24) !important;
        }

        /* HTML 랭킹/변화 테이블: 배경을 완전히 분리 */
        .priority-board-wrap,
        .tracking-board-wrap {
            background:
                linear-gradient(180deg, rgba(9, 19, 35, 0.995), rgba(4, 10, 22, 0.998)) !important;
            border-color: rgba(118, 242, 226, 0.20) !important;
        }

        .priority-board,
        .tracking-board {
            background: rgba(4, 10, 22, 0.99) !important;
        }

        .priority-board thead th,
        .tracking-board thead th {
            background: rgba(22, 35, 54, 0.98) !important;
        }

        .priority-board tbody td,
        .tracking-board tbody td {
            background: rgba(5, 13, 27, 0.92) !important;
        }

        .priority-board tbody tr:hover td,
        .tracking-board tbody tr:hover td {
            background: rgba(22, 47, 70, 0.95) !important;
        }

        /* Plotly 그래프 외곽 영역: 투명 배경 대신 어두운 패널감을 부여 */
        .js-plotly-plot,
        .stPlotlyChart {
            background: rgba(7, 16, 32, 0.94) !important;
            border-radius: 16px !important;
        }

        .js-plotly-plot .plotly,
        .js-plotly-plot .main-svg {
            border-radius: 16px !important;
        }


        /* 후보 운영 그래프: 테이블/드롭다운과 동일한 패널 테두리 적용 */
        .stPlotlyChart {
            background: linear-gradient(180deg, rgba(8, 18, 34, 0.985), rgba(5, 12, 24, 0.995)) !important;
            border: 1px solid rgba(118, 242, 226, 0.20) !important;
            border-radius: 18px !important;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255,255,255,0.045) !important;
            padding: 10px 12px 8px 12px !important;
            overflow: hidden !important;
        }

        .stPlotlyChart:hover {
            border-color: rgba(118, 242, 226, 0.34) !important;
            box-shadow: 0 16px 38px rgba(0, 0, 0, 0.40), inset 0 1px 0 rgba(255,255,255,0.065) !important;
        }

        .stPlotlyChart .js-plotly-plot,
        .stPlotlyChart .plotly,
        .stPlotlyChart .main-svg {
            background: transparent !important;
            border-radius: 16px !important;
        }

        /* Streamlit dataframe도 별빛 배경과 분리 */
        div[data-testid="stDataFrame"] {
            background: rgba(5, 12, 24, 0.98) !important;
            border-color: rgba(118, 242, 226, 0.20) !important;
            box-shadow: 0 14px 32px rgba(0,0,0,0.34) !important;
        }

        /* 그래프/설명 사이 경계가 더 선명하게 보이도록 조정 */
        .section-divider {
            margin: 24px 0 18px 0 !important;
            background: linear-gradient(90deg, transparent, rgba(95,255,232,0.42), rgba(170,112,255,0.30), transparent) !important;
        }

        @media (max-width: 900px) {
            .starseed-title {
                font-size: 52px !important;
                letter-spacing: 9px !important;
            }
            .starseed-subtitle {
                font-size: 18px !important;
                margin-top: 16px !important;
            }
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)



# =========================================================
# 6-9. STAR SEED Mission Board 레이아웃 보정
# - 첨부 레퍼런스처럼 STAR SEED 페이지를 관제보드형으로 재배치
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1520px !important;
        padding-top: 1.0rem !important;
    }

    .starseed-dashboard-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
        gap: 22px;
        align-items: stretch;
        margin: 8px 0 18px 0;
    }

    .starseed-head-left {
        min-height: 132px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding-left: 10px;
    }

    .starseed-title-mini {
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(54px, 5.5vw, 76px);
        font-weight: 950;
        letter-spacing: 8px;
        line-height: 0.95;
        color: #FFF8FF;
        text-shadow: 0 0 22px rgba(180, 108, 255, 0.56), 0 0 8px rgba(255,255,255,0.24);
        margin: 0 0 14px 0;
    }

    .starseed-subtitle-mini {
        font-size: 20px;
        font-weight: 850;
        letter-spacing: -0.035em;
        color: #D8CDEF;
        margin: 0;
    }

    .starseed-info-card {
        border: 1px solid rgba(165, 103, 255, 0.40);
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(39, 20, 83, 0.86), rgba(12, 18, 42, 0.94));
        box-shadow: 0 16px 38px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.06);
        padding: 22px 26px;
        display: grid;
        grid-template-columns: 72px 1fr;
        gap: 18px;
        align-items: center;
    }

    .starseed-info-icon {
        width: 62px;
        height: 62px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-size: 30px;
        background: radial-gradient(circle at 35% 28%, rgba(255,255,255,0.28), rgba(136,73,255,0.90));
        border: 1px solid rgba(230, 210, 255, 0.34);
        box-shadow: 0 0 26px rgba(142, 78, 255, 0.45);
    }

    .starseed-info-title {
        color: #F8F2FF;
        font-size: 18px;
        font-weight: 900;
        margin-bottom: 7px;
    }

    .starseed-info-text {
        color: #C9BEDC;
        font-size: 13.5px;
        line-height: 1.55;
        word-break: keep-all;
    }

    .kpi-card {
        min-height: 112px !important;
        padding: 18px 24px !important;
        border-radius: 16px !important;
        background: linear-gradient(180deg, rgba(13,24,49,.95), rgba(8,14,31,.97)) !important;
        border-color: rgba(139, 92, 246, 0.42) !important;
    }
    .kpi-card::before { display:none !important; }
    .kpi-label { font-size: 13.5px !important; color:#d4cbec !important; }
    .kpi-value { font-size: 30px !important; margin-top: 6px !important; }
    .kpi-delta { margin-top: 6px !important; }

    .top-cards-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 19px;
        font-weight: 900;
        color: #F8F2FF;
        margin: 8px 0 12px 0;
    }

    .candidate-card {
        min-height: 172px !important;
        padding: 16px 14px 14px !important;
        border-radius: 15px !important;
        background: linear-gradient(180deg, rgba(18,21,52,.88), rgba(9,14,31,.95)) !important;
        border-color: rgba(139,92,246,.34) !important;
    }
    .candidate-avatar, .content-avatar {
        width: 58px !important;
        height: 58px !important;
        margin: 8px auto 8px auto !important;
    }
    .content-avatar-img { width: 58px !important; height: 58px !important; }
    .rank-badge {
        top: 10px !important;
        left: 10px !important;
        min-width: 21px;
        height: 21px;
        padding: 0 6px !important;
        display:flex; align-items:center; justify-content:center;
        border-radius: 6px !important;
        font-size: 12px !important;
        background: rgba(255, 214, 95, .16) !important;
        border: 1px solid rgba(255, 214, 95, .85) !important;
        color: #FFD76A !important;
    }
    .candidate-name { font-size: 15px !important; margin-bottom: 5px !important; }
    .score-text { font-size: 22px !important; margin-top: 5px !important; color:#F0E9FF !important; }
    .candidate-card .small-muted { display:none; }
    .candidate-card .segment-pill { font-size: 11px !important; padding: 3px 8px !important; }

    .priority-board-wrap {
        background: rgba(9, 14, 31, 0.72);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        overflow: hidden;
    }
    .priority-board th {
        background: rgba(255,255,255,0.055) !important;
        color: #EDE8FF !important;
        font-size: 12.5px !important;
    }
    .priority-board td {
        font-size: 12.5px !important;
        padding-top: 7px !important;
        padding-bottom: 7px !important;
    }
    .priority-tag, .priority-action {
        font-size: 11px !important;
        padding: 3px 8px !important;
        min-height: 21px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(139, 92, 246, 0.28) !important;
        background: rgba(8, 14, 31, 0.50) !important;
        border-radius: 16px !important;
    }

    .selected-profile-img-wrap, .selected-profile-fallback .content-avatar {
        width: 106px !important;
        height: 106px !important;
        margin: 2px auto 12px auto !important;
    }
    .selected-profile-img {
        width: 106px !important;
        height: 106px !important;
        border-radius: 999px !important;
        object-fit: cover;
        border: 2px solid rgba(230, 210, 255, 0.50);
        box-shadow: 0 0 22px rgba(139,92,246,.32);
    }
    .detail-title-centered { text-align:center !important; font-size: 24px !important; }
    div[data-testid="stMetric"] { padding: 9px 10px !important; }
    div[data-testid="stMetric"] label { font-size: 12px !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 20px !important; }

    .stPlotlyChart {
        background: linear-gradient(180deg, rgba(8, 13, 29, 0.96), rgba(4, 10, 22, 0.98)) !important;
        border: 1px solid rgba(139, 92, 246, 0.28) !important;
        border-radius: 16px !important;
    }

    .mock-chart-tabs [data-testid="stRadio"] label {
        border-radius: 999px !important;
    }

    @media (max-width: 1100px) {
        .starseed-dashboard-hero { grid-template-columns: 1fr; }
        .starseed-title-mini { font-size: 48px; letter-spacing: 6px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 7. STAR SEED 관제보드형 대시보드 본문
# - 레퍼런스 이미지 기반으로 STAR SEED 페이지 전체 배치 재구성
# - 상단 헤더 / KPI 4카드 / 추천 후보 TOP5 / 우선순위 표+상세 / 하단 그래프 탭
# =========================================================

# ---------------------------------------------------------
# 7-0. 레퍼런스형 STAR SEED CSS
# ---------------------------------------------------------
st.markdown(
    clean_html(
        """
        <style>
        .block-container {
            max-width: 1380px !important;
            padding-top: 0rem !important;
            padding-left: 2.0rem !important;
            padding-right: 2.0rem !important;
            padding-bottom: 2.5rem !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(4, 8, 20, .98), rgba(7, 8, 26, .98)) !important;
            border-right: 1px solid rgba(132, 93, 255, .34) !important;
        }

        .starseed-board {
            width: 100%;
            padding: 0 0 18px 0;
            margin-top: -34px;
            position: relative;
            z-index: 2;
        }

        .board-hero {
            display: grid;
            grid-template-columns: 1.05fr .95fr;
            gap: 20px;
            align-items: center;
            margin-bottom: 12px;
        }

        .board-title {
            font-family: Arial, Helvetica, sans-serif !important;
            font-size: 58px;
            font-weight: 950;
            line-height: 1;
            letter-spacing: 9px;
            color: #FFF8FF;
            text-shadow:
                0 0 10px rgba(255,255,255,0.65),
                0 0 22px rgba(230,195,255,0.45),
                0 0 38px rgba(179,93,255,0.55);
            margin: 0 0 12px 0;
        }

        .board-subtitle {
            color: #D9CFE8;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.02em;
            text-shadow: 0 0 12px rgba(230,195,255,0.18);
        }

        .board-info-card {
            display: grid;
            grid-template-columns: 58px 1fr;
            gap: 16px;
            align-items: center;
            min-height: 82px;
            border-radius: 18px;
            border: 1px solid rgba(164, 111, 255, .36);
            background: linear-gradient(135deg, rgba(55, 22, 102, .72), rgba(22, 17, 55, .86));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.07), 0 0 26px rgba(143, 84, 255, .14);
            padding: 15px 20px;
        }

        .board-info-icon {
            width: 52px;
            height: 52px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 25px;
            background: radial-gradient(circle at 32% 28%, #cfa9ff, #7037d7 55%, #27164e 100%);
            box-shadow: 0 0 18px rgba(178, 118, 255, .38);
        }

        .board-info-title {
            color: #f7efff;
            font-size: 14px;
            font-weight: 900;
            margin-bottom: 5px;
        }

        .board-info-text {
            color: #bdb2d6;
            font-size: 12px;
            line-height: 1.55;
            word-break: keep-all;
        }

        .board-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 8px 0 8px 0;
        }

        .board-kpi-card {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: 52px 1fr;
            gap: 13px;
            align-items: center;
            min-height: 82px;
            border-radius: 14px;
            padding: 13px 16px;
            border: 1px solid rgba(122, 100, 220, .36);
            background: linear-gradient(180deg, rgba(20, 25, 50, .90), rgba(12, 15, 34, .96));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 10px 24px rgba(0,0,0,.20);
        }

        .board-kpi-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 8% 18%, rgba(155, 98, 255, .18), transparent 30%);
            pointer-events: none;
        }

        .board-kpi-icon {
            position: relative;
            width: 48px;
            height: 48px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
            background: radial-gradient(circle at 34% 24%, rgba(255,255,255,.36), rgba(124, 83, 236, .82) 48%, rgba(48, 25, 112, .92) 100%);
            box-shadow: 0 0 18px rgba(144, 94, 255, .35);
        }

        .board-kpi-content { position: relative; min-width: 0; }
        .board-kpi-label { color: #c9c1dd; font-size: 12px; font-weight: 850; margin-bottom: 3px; }
        .board-kpi-value { color: #fff; font-size: 25px; font-weight: 950; line-height: 1.1; letter-spacing: -.03em; }
        .board-kpi-delta { display:inline-flex; align-items:center; gap:2px; margin-top: 3px; font-size: 10px; font-weight: 900; border-radius:999px; padding: 2px 7px; background: rgba(255,255,255,.05); }
        .board-kpi-delta.up { color:#ff7b86; background: rgba(255, 91, 108, .12); }
        .board-kpi-delta.down { color:#72b8ff; background: rgba(79, 150, 255, .12); }
        .board-kpi-delta.flat { color:#c4bad8; background: rgba(185,170,230,.10); }
        .board-kpi-note { display:inline-block; margin-left: 6px; color:#8d849f; font-size: 10px; font-weight: 700; }

        .board-panel {
            border-radius: 16px;
            border: 1px solid rgba(127, 98, 221, .35);
            background: linear-gradient(180deg, rgba(22, 18, 48, .86), rgba(11, 14, 33, .93));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 16px 32px rgba(0,0,0,.20);
            padding: 12px 14px;
        }

        .board-panel-title {
            display:flex;
            align-items:center;
            gap: 8px;
            color:#f5efff;
            font-size: 15px;
            font-weight: 950;
            margin: 0 0 10px 0;
        }

        .top5-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 10px;
        }

        .top5-grid .mini-candidate-card a {
            color: inherit;
            text-decoration: none;
        }
        .top5-grid .mini-candidate-card a:hover {
            color: #ffffff;
            text-decoration: none;
        }

        .mini-candidate-card {
            position: relative;
            min-height: 92px;
            border-radius: 12px;
            border: 1px solid rgba(135, 105, 232, .30);
            background: linear-gradient(180deg, rgba(22, 24, 52, .84), rgba(13, 15, 36, .96));
            padding: 13px 12px 11px 104px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-sizing: border-box;
        }

        .mini-rank {
            position:absolute;
            top: 9px;
            left: 9px;
            width: 20px;
            height: 20px;
            border-radius: 5px;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#ffd86b;
            border:1px solid rgba(255,216,107,.75);
            background: rgba(42, 29, 72, .78);
            font-size: 11px;
            font-weight: 950;
        }

        .mini-avatar-wrap {
            position: absolute;
            left: 38px;
            top: 50%;
            transform: translateY(-50%);
            width: 54px;
            height: 54px;
            border-radius: 999px;
            overflow: hidden;
            background: radial-gradient(circle at 32% 28%, #fff, #8b5cf6 42%, #25154d 100%);
            border: 2px solid rgba(255,255,255,.42);
            box-shadow: 0 0 14px rgba(155, 109, 255, .38);
        }

        .mini-avatar-wrap img { width: 100%; height: 100%; object-fit: cover; display:block; }
        .mini-avatar-fallback { width:100%; height:100%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:950; font-size:20px; }
        .mini-name {
            color:#fff;
            font-size: 13.5px;
            font-weight: 950;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
            margin-top: 0;
            line-height: 1.15;
            max-width: 100%;
        }
        .mini-score {
            color:#fff;
            font-size: 17px;
            font-weight: 950;
            margin-top: 3px;
            line-height: 1.1;
            white-space: nowrap;
            letter-spacing: -0.02em;
        }
        .mini-stage {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width: fit-content;
            max-width: 94px;
            color:#b9ffe8;
            background: rgba(20, 152, 123, .28);
            border:1px solid rgba(64,226,190,.35);
            border-radius:999px;
            padding: 3px 9px;
            font-size: 10px;
            font-weight: 900;
            margin-top:5px;
            white-space: nowrap;
        }
        .mini-reason { display: none !important; }

        .mid-grid {
            display: grid;
            grid-template-columns: 1.05fr .95fr;
            gap: 12px;
            margin-top: 10px;
        }

        .priority-table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border-radius: 11px;
            table-layout: fixed;
            font-size: 11px;
        }
        .priority-table th {
            background: rgba(255,255,255,.08);
            color:#ddd5ef;
            font-weight:900;
            padding: 7px 8px;
            border-bottom: 1px solid rgba(255,255,255,.09);
            text-align:center;
        }
        .priority-table td {
            color:#f7f4ff;
            padding: 4px 8px;
            border-bottom: 1px solid rgba(255,255,255,.055);
            text-align:center;
            font-weight: 740;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .priority-table td.name { text-align:left; font-weight:900; }
        .priority-score { color:#fff !important; font-weight:950 !important; }

        .tag-pill {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            border-radius: 999px;
            min-width: 54px;
            max-width: 118px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 950;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color:#fff;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
        }
        .seg-music { background: linear-gradient(135deg, #7b5cff, #5840c6); }
        .seg-visual { background: linear-gradient(135deg, #d64b92, #963069); }
        .seg-virtual { background: linear-gradient(135deg, #d69428, #9d5f12); }
        .seg-game { background: linear-gradient(135deg, #2a9dd6, #1768a5); }
        .seg-subculture { background: linear-gradient(135deg, #ff9c55, #c96a28); }
        .seg-etc { background: linear-gradient(135deg, #7d8798, #4c5568); }
        .sub-music { background: linear-gradient(135deg, #5d3acc, #352079); }
        .sub-visual { background: linear-gradient(135deg, #a82c6d, #681a48); }
        .sub-virtual { background: linear-gradient(135deg, #9e5a16, #65350c); }
        .sub-game { background: linear-gradient(135deg, #1b73b7, #113d70); }
        .sub-subculture { background: linear-gradient(135deg, #ca6930, #7c3918); }
        .sub-etc { background: linear-gradient(135deg, #5c6576, #343b48); }
        .action-immediate { background: linear-gradient(135deg, #1aa98c, #0e6b62); color:#dffff8; }
        .action-watch { background: linear-gradient(135deg, #6f83ee, #4350a5); }
        .action-verify { background: linear-gradient(135deg, #d75d86, #8e2d56); }
        .action-hold { background: linear-gradient(135deg, #7b8798, #4b5363); }

        .view-more-bar {
            margin-top: 6px;
            height: 23px;
            border-radius: 7px;
            color:#d9d2ef;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size: 10px;
            font-weight: 850;
            background: linear-gradient(90deg, rgba(68, 76, 142, .55), rgba(25, 33, 73, .70));
            border:1px solid rgba(145, 116, 233, .22);
        }

        .detail-card-inner {
            display: grid;
            grid-template-columns: 125px 1fr 210px;
            gap: 16px;
            align-items: center;
        }
        .detail-avatar-big {
            width: 108px;
            height: 108px;
            border-radius: 999px;
            overflow:hidden;
            border: 3px solid rgba(255,255,255,.55);
            box-shadow: 0 0 20px rgba(160, 102, 255, .35);
            margin: 0 auto;
            background: radial-gradient(circle at 32% 28%, #fff, #9c6aff 43%, #25154d 100%);
        }
        .detail-avatar-big img { width:100%; height:100%; object-fit:cover; display:block; }
        .detail-avatar-big .mini-avatar-fallback { font-size: 42px; }
        .detail-name-row { display:flex; gap: 8px; align-items:center; margin-bottom: 10px; }
        .detail-name-main { color:#fff; font-size: 20px; font-weight: 950; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .detail-metric-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
        .detail-metric-box { border: 1px solid rgba(139,110,230,.26); background:rgba(255,255,255,.045); border-radius:8px; padding:7px 9px; min-height:48px; }
        .detail-metric-label { color:#bfb4d3; font-size:10px; font-weight:850; }
        .detail-metric-value { color:#fff; font-size:18px; font-weight:950; line-height:1.2; margin-top:2px; }
        .reason-panel { border:1px solid rgba(157,103,255,.32); background:rgba(49,28,91,.36); border-radius:12px; padding:12px 14px; min-height:106px; }
        .reason-title { color:#e4d6ff; font-size:12px; font-weight:950; margin-bottom:8px; }
        .reason-bullet { color:#cfc4e4; font-size:11px; line-height:1.55; margin:5px 0; }
        .reason-bullet::before { content:'●'; color:#8f5bff; margin-right:7px; }

        .bottom-panel { margin-top: 10px; }
        .mock-tabs { display:flex; gap:8px; align-items:center; justify-content:center; margin: -2px 0 10px 0; }
        .mock-tab { min-width: 160px; text-align:center; border-radius:999px; padding:7px 16px; color:#c9c0dc; background:rgba(255,255,255,.055); border:1px solid rgba(145,116,233,.24); font-size:11px; font-weight:900; }
        .mock-tab.active { color:#fff; background: linear-gradient(135deg, rgba(143,84,255,.90), rgba(207,71,178,.72)); border-color: rgba(221,160,255,.48); box-shadow: 0 0 16px rgba(145, 93, 255, .25); }
        .graph-grid { display:grid; grid-template-columns: 250px 1fr; gap: 14px; align-items:stretch; }
        .graph-explain { padding: 18px 8px 12px 8px; }
        .graph-explain-title { color:#fff; font-size:17px; font-weight:950; margin-bottom: 8px; }
        .graph-explain-text { color:#bcb3d2; font-size:12px; line-height:1.65; word-break: keep-all; }
        .plot-shell { border-radius:13px; border:1px solid rgba(133, 103, 229, .22); background: rgba(7, 10, 24, .62); padding: 4px 8px 0 8px; min-height: 230px; }

        .recent-mini-table { width:100%; border-collapse: collapse; table-layout:fixed; font-size:11px; }
        .recent-mini-table th { color:#ddd5ef; background:rgba(255,255,255,.07); padding:7px; font-weight:950; }
        .recent-mini-table td { color:#f7f4ff; padding:7px; border-bottom:1px solid rgba(255,255,255,.06); font-weight:750; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .recent-up { color:#ff838d !important; font-weight:950 !important; }

        .stPlotlyChart {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
        }

        @media (max-width: 1200px) {
            .board-hero, .mid-grid, .detail-card-inner, .graph-grid { grid-template-columns: 1fr; }
            .board-kpi-grid, .top5-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .board-title { font-size: 44px; }
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 7-1. 보조 함수
# ---------------------------------------------------------

def _safe_html(value):
    return html_lib.escape(str(value if pd.notna(value) else "-"), quote=True)


def _short_text(value, limit=42):
    text = str(value if pd.notna(value) else "-").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _fmt_num(value, ndigits=0, suffix=""):
    if pd.isna(value):
        return "-"
    try:
        f = float(value)
        if ndigits == 0:
            return f"{int(round(f)):,}{suffix}"
        return f"{f:,.{ndigits}f}{suffix}"
    except Exception:
        return f"{value}{suffix}"


def _delta_badge(delta, ndigits=0, suffix=""):
    if pd.isna(delta):
        return '<span class="board-kpi-delta flat">— 변화 없음</span>'
    try:
        d = float(delta)
    except Exception:
        return '<span class="board-kpi-delta flat">— 변화 없음</span>'
    arrow = "▲" if d > 0 else "▼" if d < 0 else "—"
    cls = "up" if d > 0 else "down" if d < 0 else "flat"
    mag = abs(d)
    val = f"{mag:,.{ndigits}f}" if ndigits else f"{int(round(mag)):,}"
    return f'<span class="board-kpi-delta {cls}">{arrow} {val}{suffix}</span>'


def _seg_key(text):
    t = str(text or "")
    if "음악" in t or "보이스" in t or "커버" in t or "성우" in t:
        return "music"
    if "창작" in t or "비주얼" in t or "코스프레" in t or "일러" in t:
        return "visual"
    if "버츄얼" in t or "버튜" in t or "VTuber" in t:
        return "virtual"
    if "게임" in t or "롤" in t or "실황" in t:
        return "game"
    if "서브컬처" in t or "토크" in t or "팬덤" in t:
        return "subculture"
    return "etc"


def _tag(value, level="main"):
    text = str(value if pd.notna(value) and str(value).strip() else "미분류")
    key = _seg_key(text)
    cls = f"seg-{key}" if level == "main" else f"sub-{key}"
    return f'<span class="tag-pill {cls}" title="{_safe_html(text)}">{_safe_html(text)}</span>'


def _action_tag(value):
    text = str(value if pd.notna(value) and str(value).strip() else "미분류")
    if "즉시" in text:
        cls = "action-immediate"
    elif "성장" in text:
        cls = "action-watch"
    elif "검증" in text:
        cls = "action-verify"
    else:
        cls = "action-hold"
    return f'<span class="tag-pill {cls}" title="{_safe_html(text)}">{_safe_html(text)}</span>'


def _thumb_url(row):
    if channel_thumbnail_col and channel_thumbnail_col in row.index:
        url = str(row.get(channel_thumbnail_col, "") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            return url
    return ""


def _avatar_small(row):
    url = _thumb_url(row)
    name = str(row.get(channel_name_col, "?") if channel_name_col else "?")
    initial = _safe_html(name[:1] if name else "?")
    if url:
        return f'<div class="mini-avatar-wrap"><img src="{_safe_html(url)}" loading="lazy" referrerpolicy="no-referrer"></div>'
    return f'<div class="mini-avatar-wrap"><div class="mini-avatar-fallback">{initial}</div></div>'


def _avatar_big(row):
    url = _thumb_url(row)
    name = str(row.get(channel_name_col, "?") if channel_name_col else "?")
    initial = _safe_html(name[:1] if name else "?")
    if url:
        return f'<div class="detail-avatar-big"><img src="{_safe_html(url)}" loading="lazy" referrerpolicy="no-referrer"></div>'
    return f'<div class="detail-avatar-big"><div class="mini-avatar-fallback">{initial}</div></div>'


def _channel_link(name, row):
    safe_name = _safe_html(name)
    if channel_url_col and channel_url_col in row.index:
        url = str(row.get(channel_url_col, "") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            return f'<a href="{_safe_html(url)}" target="_blank" style="color:inherit;text-decoration:none;">{safe_name}</a>'
    return safe_name


def _reason_short(row):
    for c in ["추천사유", "자동판정근거", "주의사유", "변화요약"]:
        if c in row.index and pd.notna(row.get(c)) and str(row.get(c)).strip():
            return str(row.get(c))
    seg = row.get(segment_col, "") if segment_col else ""
    return f"{seg} 콘텐츠 적합도 우수"

# ---------------------------------------------------------
# 8. KPI 계산
# ---------------------------------------------------------

if tracking_target_df is not None and not tracking_target_df.empty:
    target_all_kpi_df = add_score_display_column(tracking_target_df)
else:
    target_all_kpi_df = add_score_display_column(df)

if tracking_base_df is not None and not tracking_base_df.empty:
    base_all_kpi_df = add_score_display_column(tracking_base_df)
else:
    base_all_kpi_df = pd.DataFrame()

target_filtered_kpi_df = apply_snapshot_filters_for_kpi(target_all_kpi_df)
base_filtered_kpi_df = apply_snapshot_filters_for_kpi(base_all_kpi_df) if not base_all_kpi_df.empty else pd.DataFrame()

target_all_kpi = calc_kpi_values(target_all_kpi_df)
target_filtered_kpi = calc_kpi_values(target_filtered_kpi_df)
base_all_kpi = calc_kpi_values(base_all_kpi_df) if not base_all_kpi_df.empty else {"total": np.nan, "shortlist": np.nan, "avg_score": np.nan, "high_priority": np.nan}
base_filtered_kpi = calc_kpi_values(base_filtered_kpi_df) if not base_filtered_kpi_df.empty else {"total": np.nan, "shortlist": np.nan, "avg_score": np.nan, "high_priority": np.nan}

is_same_snapshot_compare = tracking_base_label != "-" and tracking_target_label != "현재" and tracking_base_label == tracking_target_label
if is_same_snapshot_compare:
    delta_total = delta_shortlist = delta_avg_score = delta_high_priority = 0
else:
    delta_total = target_all_kpi["total"] - base_all_kpi["total"] if pd.notna(base_all_kpi["total"]) else np.nan
    delta_shortlist = target_all_kpi["shortlist"] - base_all_kpi["shortlist"] if pd.notna(base_all_kpi["shortlist"]) else np.nan
    delta_avg_score = target_filtered_kpi["avg_score"] - base_filtered_kpi["avg_score"] if pd.notna(base_filtered_kpi["avg_score"]) else np.nan
    delta_high_priority = target_filtered_kpi["high_priority"] - base_filtered_kpi["high_priority"] if pd.notna(base_filtered_kpi["high_priority"]) else np.nan

# ---------------------------------------------------------
# 9. 변화 추적 mini 데이터 생성
# ---------------------------------------------------------

mini_tracking_df = pd.DataFrame()
if tracking_base_df is not None and tracking_target_df is not None and not tracking_base_df.empty and not tracking_target_df.empty:
    try:
        mini_tracking_df = build_tracking_between(
            base_df=tracking_base_df,
            target_df=tracking_target_df,
            base_label=tracking_base_label,
            target_label=tracking_target_label,
        )
    except Exception:
        mini_tracking_df = pd.DataFrame()

if not mini_tracking_df.empty:
    rename_tracking_cols = {
        "기준_운영우선순위": "이전순위",
        "비교_운영우선순위": "현재순위",
        "운영우선순위변동": "순위변동",
        "기준_최종점수": "이전점수",
        "비교_최종점수": "현재점수",
        "최종점수변동": "점수변동",
        "기준_액션버킷": "이전단계",
        "비교_액션버킷": "현재단계",
    }
    mini_tracking_df = mini_tracking_df.rename(columns=rename_tracking_cols)
    if "순위변동" in mini_tracking_df.columns:
        mini_tracking_df["순위변동"] = pd.to_numeric(mini_tracking_df["순위변동"], errors="coerce")
        mini_tracking_df = mini_tracking_df.sort_values("순위변동", ascending=False)


# ---------------------------------------------------------
# 9-9. STAR SEED 최종 문구/폰트 보정
# - 홈 화면의 메인 타이틀과 톤을 맞추기 위한 최종 override
# ---------------------------------------------------------
st.markdown(
    clean_html(
        """
        <style>
        .starseed-board {
            margin-top: -34px !important;
        }

        /* 대시보드 홈(.hero-title)과 동일한 타이틀 톤으로 맞춤 */
        .board-title {
            font-family: inherit !important;
            font-size: 58px !important;
            font-weight: 950 !important;
            letter-spacing: 9px !important;
            line-height: 1 !important;
            color: #FFF8FF !important;
            text-shadow: 0 0 22px rgba(230, 195, 255, 0.35) !important;
            margin: 4px 0 14px 0 !important;
        }

        .board-subtitle {
            color: #C6BBD9 !important;
            font-size: 19px !important;
            font-weight: 750 !important;
            letter-spacing: -0.02em !important;
            text-shadow: none !important;
        }

        .board-info-title {
            color: #FFF8FF !important;
            font-size: 14.5px !important;
            font-weight: 950 !important;
        }

        .board-info-text {
            color: #CFC4E4 !important;
            font-size: 12px !important;
            line-height: 1.58 !important;
            word-break: keep-all !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 10. 상단 헤더 + KPI
# ---------------------------------------------------------

html(
    f"""
    <div class="starseed-board">
        <div class="board-hero board-hero-compact">
            <div class="board-head-left">
                <div class="board-title-icon">
                    {SEED_ICON_HTML}
                </div>
                <div>
                    <div class="board-title board-title-ko">스타시드 <span>Star Seed</span></div>
                    <div class="board-title-accent-line"></div>
                    <div class="board-subtitle">유튜브 기반 성장 잠재력과 라이브 전환 가능성을 분석해, 차세대 후보군을 발굴합니다</div>
                </div>
            </div>
            <div class="board-info-card">
                <div class="board-info-icon">✦</div>
                <div>
                    <div class="board-info-title">후보를 선별하는 기준</div>
                    <div class="board-info-text">팬 반응 밀도, 라이브 전환성, 실전 리스크, 액션버킷을 함께 확인해<br>CIME가 우선 검토할 예비 스트리머 후보군을 정리합니다.</div>
                </div>
            </div>
        </div>
        <div class="board-kpi-grid">
            <div class="board-kpi-card"><div class="board-kpi-icon">👥</div><div class="board-kpi-content"><div class="board-kpi-label">전체 분석 후보</div><div class="board-kpi-value">{_fmt_num(target_all_kpi['total'], 0, '명')}</div>{_delta_badge(delta_total, 0, '명')}<span class="board-kpi-note">지난 분석 대비</span></div></div>
            <div class="board-kpi-card"><div class="board-kpi-icon">▾</div><div class="board-kpi-content"><div class="board-kpi-label">1차 선별 후보</div><div class="board-kpi-value">{_fmt_num(target_all_kpi['shortlist'], 0, '명')}</div>{_delta_badge(delta_shortlist, 0, '명')}<span class="board-kpi-note">지난 분석 대비</span></div></div>
            <div class="board-kpi-card"><div class="board-kpi-icon">★</div><div class="board-kpi-content"><div class="board-kpi-label">평균 추천 점수</div><div class="board-kpi-value">{_fmt_num(target_filtered_kpi['avg_score'], 1, '점')}</div>{_delta_badge(delta_avg_score, 1, '점')}<span class="board-kpi-note">지난 분석 대비</span></div></div>
            <div class="board-kpi-card"><div class="board-kpi-icon">◎</div><div class="board-kpi-content"><div class="board-kpi-label">즉시 검토 후보</div><div class="board-kpi-value">{_fmt_num(target_filtered_kpi['high_priority'], 0, '명')}</div>{_delta_badge(delta_high_priority, 0, '명')}<span class="board-kpi-note">지난 분석 대비</span></div></div>
        </div>
    </div>
    """
)

# ---------------------------------------------------------
# 11. 우선 검토 추천 후보 TOP 5
# ---------------------------------------------------------

top_candidates = filtered.head(5).copy()
mini_cards = []
for i, (_, row) in enumerate(top_candidates.iterrows()):
    name = row.get(channel_name_col, "-") if channel_name_col else "-"
    score = row.get("_score_display", np.nan)
    action = row.get(action_col, "") if action_col else ""
    mini_cards.append(
        f"""
        <div class="mini-candidate-card">
            <div class="mini-rank">{i + 1}</div>
            {_avatar_small(row)}
            <div class="mini-name">{_channel_link(name, row)}</div>
            <div class="mini-score">{_fmt_num(score, 1, '점')}</div>
            <span class="mini-stage">{_safe_html(action or '검토')}</span>
        </div>
        """
    )

html(
    f"""
    <div class="board-panel">
        <div class="board-panel-title">✩ 우선 검토 추천 후보 TOP 5</div>
        <div class="top5-grid">{''.join(mini_cards)}</div>
    </div>
    """
)

# ---------------------------------------------------------
# 12. 후보별 검토 우선순위 + 선택 후보 상세
# ---------------------------------------------------------

priority_df = filtered.head(8).copy()
priority_rows = []
for i, (_, row) in enumerate(priority_df.iterrows()):
    name = row.get(channel_name_col, "-") if channel_name_col else "-"
    segment = row.get(segment_col, "-") if segment_col else "-"
    action = row.get(action_col, "-") if action_col else "-"
    score = row.get("_score_display", np.nan)
    priority_rows.append(
        f"""
        <tr>
            <td style="width:9%;">{i + 1}</td>
            <td class="name" style="width:30%;">{_channel_link(_short_text(name, 18), row)}</td>
            <td style="width:24%;">{_tag(segment, 'main')}</td>
            <td style="width:17%;">{_action_tag(action)}</td>
            <td class="priority-score" style="width:12%;">{_fmt_num(score, 1, '')}</td>
        </tr>
        """
    )

recent_priority_rows = []
if not mini_tracking_df.empty:
    recent_priority_df = mini_tracking_df.head(8).copy()
    for _, r in recent_priority_df.iterrows():
        recent_priority_rows.append(
            f"""
            <tr>
                <td class="name" style="width:28%;">{_safe_html(_short_text(r.get('채널명', '-'), 18))}</td>
                <td style="width:13%;">{_fmt_num(r.get('이전순위', np.nan), 0, '')}</td>
                <td style="width:13%;">{_fmt_num(r.get('현재순위', np.nan), 0, '')}</td>
                <td class="recent-up" style="width:17%;">▲ {_fmt_num(abs(float(r.get('순위변동', 0) or 0)), 0, '')}</td>
                <td class="priority-score" style="width:13%;">{_fmt_num(r.get('현재점수', np.nan), 1, '')}</td>
                <td style="width:16%;">{_action_tag(r.get('현재단계', '-'))}</td>
            </tr>
            """
        )

# 선택 후보 드롭다운은 현재 사이드바/화면 필터가 적용된 전체 1차 선별 후보 풀을 사용합니다.
# 단, 상단 우선순위 표는 기존처럼 TOP 8만 보여줍니다.
candidate_select_df = filtered.copy()
if channel_name_col and not candidate_select_df.empty:
    candidate_select_df = candidate_select_df[candidate_select_df[channel_name_col].notna()].copy()
    candidate_select_df[channel_name_col] = candidate_select_df[channel_name_col].astype(str)
    candidate_select_df = candidate_select_df.drop_duplicates(subset=[channel_name_col], keep="first")
    selected_options = candidate_select_df[channel_name_col].tolist()
else:
    selected_options = []
selected_name = selected_options[0] if selected_options else None

left_col, right_col = st.columns([0.58, 0.42], gap="small")

with left_col:
    # 표 제목과 전환 필터를 같은 행에 고정 배치합니다.
    # 버튼 클릭 직후 title/table이 한 번에 바뀌도록 on_click 콜백으로 session_state를 먼저 갱신합니다.
    def _set_priority_mode(mode: str) -> None:
        st.session_state["priority_table_view_mode"] = mode

    current_priority_mode = st.session_state.get("priority_table_view_mode", "영입 우선순위 TOP")
    if current_priority_mode not in ["추천 점수 높은 순", "최근 상승한 후보"]:
        current_priority_mode = "영입 우선순위 TOP"
        st.session_state["priority_table_view_mode"] = current_priority_mode

    st.markdown('<div class="priority-tight-anchor"></div>', unsafe_allow_html=True)
    try:
        title_col, mode_col_1, mode_col_2 = st.columns([0.42, 0.29, 0.29], gap="small", vertical_alignment="center")
    except TypeError:
        title_col, mode_col_1, mode_col_2 = st.columns([0.42, 0.29, 0.29], gap="small")

    with mode_col_1:
        st.button(
            "영입 우선순위 TOP",
            key="priority_mode_top_button",
            use_container_width=True,
            type="primary" if current_priority_mode == "영입 우선순위 TOP" else "secondary",
            on_click=_set_priority_mode,
            args=("영입 우선순위 TOP",),
        )

    with mode_col_2:
        st.button(
            "최근 순위 상승 후보",
            key="priority_mode_recent_button",
            use_container_width=True,
            type="primary" if current_priority_mode == "최근 순위 상승 후보" else "secondary",
            on_click=_set_priority_mode,
            args=("최근 순위 상승 후보",),
        )

    priority_view_mode = st.session_state.get("priority_table_view_mode", "영입 우선순위 TOP")
    if priority_view_mode not in ["영입 우선순위 TOP", "최근 순위 상승 후보"]:
        priority_view_mode = "영입 우선순위 TOP"
        st.session_state["priority_table_view_mode"] = priority_view_mode
    priority_title_label = "🏆 영입 우선순위 TOP" if priority_view_mode == "영입 우선순위 TOP" else "📈 최근 순위 상승 후보"

    with title_col:
        st.markdown(
            f'<div class="priority-header-title">{priority_title_label}</div>',
            unsafe_allow_html=True,
        )

    if priority_view_mode == "영입 우선순위 TOP":
        html(
            f"""
            <div class="board-panel priority-table-panel" style="min-height:228px;">
                <table class="priority-table">
                    <thead>
                        <tr><th>순위</th><th>스트리머명</th><th>주요 콘텐츠군</th><th>검토단계</th><th>점수</th></tr>
                    </thead>
                    <tbody>{''.join(priority_rows)}</tbody>
                </table>
            </div>
            """
        )
    else:
        if recent_priority_rows:
            html(
                f"""
                <div class="board-panel priority-table-panel" style="min-height:228px;">
                    <table class="priority-table recent-priority-table">
                        <thead>
                            <tr><th>후보</th><th>이전</th><th>현재</th><th>상승</th><th>점수</th><th>단계</th></tr>
                        </thead>
                        <tbody>{''.join(recent_priority_rows)}</tbody>
                    </table>
                </div>
                """
            )
        else:
            html(
                """
                <div class="board-panel priority-table-panel" style="min-height:228px;">
                    <div class="board-info-text">비교 가능한 최근 순위 상승 후보 데이터가 없습니다.</div>
                </div>
                """
            )


    with st.expander("표 보는 방법", expanded=False):
        if priority_view_mode == "영입 우선순위 TOP":
            st.markdown(
                """
                <div class="explain-box">
                <b>읽는 법</b>: 현재 필터 조건에서 영입 우선순위가 높은 후보를 순위대로 보여줍니다. 점수뿐 아니라 주요 콘텐츠군과 검토단계를 함께 확인해야 합니다.<br><br>
                <b>도출 가능한 인사이트</b>: 상위권에 반복적으로 등장하는 콘텐츠군은 우선 탐색 풀이 두꺼운 영역입니다. 점수가 높고 검토단계가 즉시검토인 후보는 우선 컨택 또는 수기 검증 대상으로 볼 수 있습니다.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="explain-box">
                <b>읽는 법</b>: 이전 시점 대비 현재 순위가 크게 상승한 후보를 보여줍니다. 상승 폭, 현재 점수, 현재 검토단계를 함께 확인합니다.<br><br>
                <b>도출 가능한 인사이트</b>: 순위가 크게 오른 후보는 최근 데이터 반영 이후 주목도가 상승한 후보입니다. 다만 현재 단계가 보류라면 수치 상승 원인과 리스크 플래그를 먼저 검토하는 것이 좋습니다.
                </div>
                """,
                unsafe_allow_html=True,
            )

with right_col:
    if selected_options:
        # 좌측의 우선순위 제목/필터 행과 시각적 기준선을 맞추기 위해
        # 선택 후보 드롭다운 위에 소폭 여백을 둡니다.
        st.markdown('<div class="candidate-select-top-spacer"></div>', unsafe_allow_html=True)
        previous_selected = st.session_state.get("mock_selected_candidate")
        selected_index = selected_options.index(previous_selected) if previous_selected in selected_options else 0
        selected_name = st.selectbox(
            "선택 후보",
            options=selected_options,
            index=selected_index,
            key="mock_selected_candidate",
            label_visibility="collapsed",
        )
        selected_match = candidate_select_df[candidate_select_df[channel_name_col].astype(str) == str(selected_name)]
        selected_row = selected_match.iloc[0] if not selected_match.empty else candidate_select_df.iloc[0]
        sel_name = selected_row.get(channel_name_col, "-") if channel_name_col else "-"
        sel_action = selected_row.get(action_col, "-") if action_col else "-"
        sel_segment = selected_row.get(segment_col, "-") if segment_col else "-"
        sel_lower = selected_row.get(lower_segment_col, "-") if lower_segment_col else "-"
        sel_score = selected_row.get("_score_display", np.nan)
        sel_growth = selected_row.get("성장성점수", selected_row.get("성장성", np.nan))
        sel_subs = selected_row.get(subs_col, np.nan) if "subs_col" in globals() and subs_col else np.nan
        sel_fan = selected_row.get("팬밀도점수", selected_row.get("팬밀도", np.nan))
        sel_reason = _reason_short(selected_row)
        bullets = [x.strip() for x in str(sel_reason).replace("/", "|").split("|") if x.strip()][:4]
        if not bullets:
            bullets = ["최종점수 상위권", "콘텐츠 적합도 양호", "실전성 리스크 낮음"]
        reason_html = "".join([f'<div class="reason-bullet">{_safe_html(_short_text(b, 22))}</div>' for b in bullets])
        html(
            f"""
            <div class="board-panel detail-panel-v2" style="min-height:286px;">
                <div class="board-panel-title">👥 선택한 후보 상세 보기</div>
                <div class="detail-card-inner detail-card-inner-v2">
                    <div class="detail-avatar-area">{_avatar_big(selected_row)}</div>
                    <div class="detail-content-area">
                        <div class="detail-name-row"><div class="detail-name-main">{_channel_link(sel_name, selected_row)}</div>{_action_tag(sel_action)}</div>
                        <div class="detail-metric-grid">
                            <div class="detail-metric-box"><div class="detail-metric-label">추천 점수</div><div class="detail-metric-value">{_fmt_num(sel_score, 1, '점')}</div></div>
                            <div class="detail-metric-box"><div class="detail-metric-label">성장성</div><div class="detail-metric-value">{_fmt_num(sel_growth, 3, '')}</div></div>
                            <div class="detail-metric-box"><div class="detail-metric-label">구독자수</div><div class="detail-metric-value">{_fmt_num(sel_subs, 0, '')}</div></div>
                            <div class="detail-metric-box"><div class="detail-metric-label">팬밀도</div><div class="detail-metric-value">{_fmt_num(sel_fan, 3, '')}</div></div>
                        </div>
                    </div>
                    <div class="reason-panel detail-reason-bottom">
                        <div class="reason-title">왜 추천되었나요?</div>
                        {reason_html}
                    </div>
                </div>
            </div>
            """
        )
    else:
        html('<div class="board-panel"><div class="board-panel-title">👥 선택 후보 상세</div><div class="board-info-text">표시할 후보가 없습니다.</div></div>')


# 선택 후보 드롭다운/우선순위 토글 동기화 보정
st.markdown(
    clean_html(
        """
        <style>
        .priority-header-title {
            white-space: nowrap !important;
        }
        div[data-testid="column"] .stButton > button {
            white-space: nowrap !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)



# =========================================================
# 12-1. 요청 반영: 상단 여백 최소 조정 + 그래프 영역 정렬 보정
# - TOP5 카드 내부 간격은 건드리지 않고, 전체 STAR SEED 본문만 위로 당김
# - 그래프/테이블 출력 위치가 동일한 우측 출력 영역에 고정되도록 보정
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        /* 상단 여백만 조정: 카드 내부 높이/프로필 이미지 위치는 유지 */
        .block-container {
            padding-top: 0rem !important;
        }

        .starseed-dashboard-hero {
            margin-top: -24px !important;
            margin-bottom: 12px !important;
        }

        .starseed-board {
            padding-top: 0 !important;
            margin-top: -24px !important;
        }

        /* 하단 그래프 영역: 타이틀 → 선택 필터 → 설명/출력 순서로 고정 */
        .bottom-panel {
            margin-top: 14px !important;
            padding: 18px 20px 20px 20px !important;
        }

        .graph-radio-wrap {
            margin: 8px 0 14px 0;
        }

        .graph-radio-wrap div[role="radiogroup"] {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }

        .graph-radio-wrap label {
            min-width: 168px;
            justify-content: center;
            padding: 8px 14px !important;
            border-radius: 999px !important;
            background: rgba(255,255,255,0.055) !important;
            border: 1px solid rgba(145,116,233,0.26) !important;
            color: #d9d2ef !important;
            font-weight: 900 !important;
        }

        .graph-radio-wrap label:has(input:checked) {
            background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
            border-color: rgba(221,160,255,0.52) !important;
            box-shadow: 0 0 16px rgba(145, 93, 255, 0.24) !important;
        }

        .graph-radio-wrap label p {
            font-size: 12px !important;
            font-weight: 900 !important;
        }

        .priority-inline-title {
            min-height: 42px;
            display: flex;
            align-items: center;
            color: #fff7ff;
            font-size: 18px;
            font-weight: 950;
            padding: 0 0 4px 2px;
            letter-spacing: -0.02em;
        }

        .priority-view-switch {
            margin: 0 0 6px 0;
            display: flex;
            justify-content: flex-end;
        }

        .priority-view-switch div[role="radiogroup"] {
            display: flex;
            justify-content: flex-end;
            gap: 6px;
        }

        .priority-view-switch label {
            min-width: 128px;
            justify-content: center;
            padding: 7px 11px !important;
            border-radius: 999px !important;
            background: rgba(255,255,255,0.055) !important;
            border: 1px solid rgba(145,116,233,0.28) !important;
            color: #d9d2ef !important;
            font-weight: 900 !important;
        }

        .priority-view-switch label:has(input:checked) {
            background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
            border-color: rgba(221,160,255,0.52) !important;
            box-shadow: 0 0 16px rgba(145, 93, 255, 0.24) !important;
        }

        .priority-view-switch label p {
            font-size: 11px !important;
            font-weight: 900 !important;
        }

        .priority-table-panel {
            padding-top: 16px !important;
        }

        .recent-priority-table th,
        .recent-priority-table td {
            white-space: nowrap;
        }

        .graph-output-card {
            min-height: 282px;
            border-radius: 13px;
            border: 1px solid rgba(133, 103, 229, 0.22);
            background: rgba(7, 10, 24, 0.62);
            padding: 8px 10px;
            display: flex;
            align-items: stretch;
        }

        .graph-output-card .stPlotlyChart {
            width: 100%;
            min-height: 250px;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        .graph-table-card {
            min-height: 282px;
            border-radius: 13px;
            border: 1px solid rgba(133, 103, 229, 0.22);
            background: rgba(7, 10, 24, 0.62);
            padding: 10px;
        }

        /* 영입 우선순위 표 선택 필터: 같은 줄에 가로 배치 */
        .priority-view-switch div[role="radiogroup"],
        .priority-view-switch .stRadio > div {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 8px !important;
        }
        .priority-view-switch label {
            min-width: 118px !important;
            max-width: 168px !important;
            margin-bottom: 0 !important;
            white-space: nowrap !important;
        }
        .priority-view-switch label p {
            white-space: nowrap !important;
        }

        /* 선택 후보 상세: 이름 줄바꿈 방지 + 추천 사유 하단 배치 */
        .detail-panel-v2 {
            min-height: 286px !important;
        }
        .detail-card-inner-v2 {
            display: grid !important;
            grid-template-columns: 124px minmax(0, 1fr) !important;
            grid-template-areas:
                "avatar content"
                "reason reason" !important;
            gap: 14px 16px !important;
            align-items: center !important;
        }
        .detail-avatar-area { grid-area: avatar; }
        .detail-content-area { grid-area: content; min-width: 0; }
        .detail-reason-bottom {
            grid-area: reason;
            min-height: auto !important;
            padding: 10px 13px !important;
        }
        .detail-name-row {
            flex-wrap: nowrap !important;
            min-width: 0 !important;
        }
        .detail-name-main {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            max-width: 100% !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .detail-name-main a {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            display: block !important;
        }
        .detail-reason-bottom .reason-bullet {
            display: inline-block;
            margin-right: 14px;
            white-space: nowrap;
        }

        /* Plotly 위에 생기는 빈 wrapper 방지: 실제 차트 자체만 패널처럼 정리 */
        .stPlotlyChart {
            border-radius: 13px !important;
            border: 1px solid rgba(133, 103, 229, 0.22) !important;
            background: rgba(7, 10, 24, 0.62) !important;
            padding: 8px 10px !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------


st.markdown(
    """
    <style>
    /* 후보군 비교 그래프: 영입 우선순위 TOP과 동일한 제목+버튼 한 줄 레이아웃 */
    .graph-header-title {
        font-size: 25px;
        font-weight: 950;
        color: #fff8ff;
        letter-spacing: -0.04em;
        line-height: 46px;
        white-space: nowrap;
        margin: 0 !important;
        padding: 0 !important;
        text-shadow: 0 0 14px rgba(180, 120, 255, 0.30);
    }

    /* graph buttons가 radio처럼 보이도록 높이/간격 통일 */
    div[data-testid="column"] .stButton > button[kind="primary"],
    div[data-testid="column"] .stButton > button[kind="secondary"] {
        min-height: 46px !important;
        height: 46px !important;
        padding: 0 16px !important;
        border-radius: 16px !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        white-space: nowrap !important;
    }

    /* 활성 버튼은 기존 후보군 버튼과 동일하게 보라/코스믹 톤 */
    div[data-testid="column"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
        border-color: rgba(221,160,255,0.52) !important;
        color: #fffaff !important;
        box-shadow: 0 0 16px rgba(145, 93, 255, 0.24) !important;
    }

    div[data-testid="column"] .stButton > button[kind="secondary"] {
        background: rgba(7,18,34,0.84) !important;
        border-color: rgba(118,242,226,0.22) !important;
        color: #e9f7ff !important;
        box-shadow: none !important;
    }

    /* 그래프 헤더 행과 실제 그래프 사이 간격을 영입 우선순위 표와 유사하게 정리 */
    .graph-header-title + div {
        margin: 0 !important;
    }

    /* 후보군 비교 그래프: 상단 여백 축소 + 설명 텍스트 가독성 보강 */
    div[data-testid="stHorizontalBlock"]:has(.graph-header-title) {
        margin-top: -18px !important;
        margin-bottom: 4px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.graph-header-title) + div {
        margin-top: 0 !important;
    }

    .graph-explain {
        padding: 16px 8px 4px 8px !important;
        min-height: 258px !important;
        box-sizing: border-box !important;
    }

    .graph-explain-title {
        color: #fff8ff !important;
        font-size: 22px !important;
        font-weight: 950 !important;
        line-height: 1.25 !important;
        margin: 0 0 18px 0 !important;
        letter-spacing: -0.04em !important;
        text-shadow: 0 0 12px rgba(180, 120, 255, 0.28) !important;
    }

    .graph-explain-text {
        color: #c9c0dc !important;
        font-size: 13.5px !important;
        line-height: 1.9 !important;
        font-weight: 650 !important;
        word-break: keep-all !important;
        max-width: 245px !important;
    }

    /* Plotly 차트 카드와 설명 영역의 높이감을 맞추고 하단 공백을 줄임 */
    .stPlotlyChart {
        min-height: 282px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# 13. 하단 후보군 비교 그래프
# ---------------------------------------------------------

classified_filtered = filtered.copy()
unclassified_filtered_count = 0
if segment_col and segment_col in classified_filtered.columns:
    unclassified_mask = (
        classified_filtered[segment_col]
        .fillna("미분류")
        .astype(str)
        .str.contains("미분류|None|nan", case=False, na=False)
    )
    unclassified_filtered_count = int(unclassified_mask.sum())
    classified_filtered = classified_filtered[~unclassified_mask].copy()

GRAPH_OPTIONS = [
    "콘텐츠 유형별 추천 점수",
    "검토 단계별 후보 분포",
    "후보군 콘텐츠 비율",
]

# 후보군 비교 그래프도 영입 우선순위 TOP 영역과 동일하게
# 제목과 버튼형 필터를 같은 라인에 배치한다.
def _set_graph_view(mode: str) -> None:
    st.session_state["mock_graph_view"] = mode

current_graph_view = st.session_state.get("mock_graph_view", GRAPH_OPTIONS[0])
if current_graph_view not in GRAPH_OPTIONS:
    current_graph_view = GRAPH_OPTIONS[0]
    st.session_state["mock_graph_view"] = current_graph_view

try:
    graph_title_col, graph_btn_col_1, graph_btn_col_2, graph_btn_col_3 = st.columns(
        [0.34, 0.22, 0.22, 0.22], gap="small", vertical_alignment="center"
    )
except TypeError:
    graph_title_col, graph_btn_col_1, graph_btn_col_2, graph_btn_col_3 = st.columns(
        [0.34, 0.22, 0.22, 0.22], gap="small"
    )

with graph_title_col:
    st.markdown(
        '<div class="graph-header-title">📊 후보군 비교 그래프</div>',
        unsafe_allow_html=True,
    )

with graph_btn_col_1:
    st.button(
        "콘텐츠 유형별 추천 점수",
        key="graph_view_score_button",
        use_container_width=True,
        type="primary" if current_graph_view == "콘텐츠 유형별 추천 점수" else "secondary",
        on_click=_set_graph_view,
        args=("콘텐츠 유형별 추천 점수",),
    )

with graph_btn_col_2:
    st.button(
        "검토 단계별 후보 분포",
        key="graph_view_bucket_button",
        use_container_width=True,
        type="primary" if current_graph_view == "검토 단계별 후보 분포" else "secondary",
        on_click=_set_graph_view,
        args=("검토 단계별 후보 분포",),
    )

with graph_btn_col_3:
    st.button(
        "후보군 콘텐츠 비율",
        key="graph_view_ratio_button",
        use_container_width=True,
        type="primary" if current_graph_view == "후보군 콘텐츠 비율" else "secondary",
        on_click=_set_graph_view,
        args=("후보군 콘텐츠 비율",),
    )

graph_view = st.session_state.get("mock_graph_view", GRAPH_OPTIONS[0])
if graph_view not in GRAPH_OPTIONS:
    graph_view = GRAPH_OPTIONS[0]
    st.session_state["mock_graph_view"] = graph_view

# 모든 그래프/테이블은 같은 2열 구조의 우측 출력 박스에 표시한다.
graph_left, graph_right = st.columns([0.23, 0.77], gap="small")

COSMIC_COLORS = ["#8b5cf6", "#5b7cfa", "#c94ea2", "#33c7b1", "#f09a4a", "#8fb4ff", "#b48cff"]

with graph_left:
    if graph_view == "콘텐츠 유형별 추천 점수":
        html('<div class="graph-explain"><div class="graph-explain-title">콘텐츠 유형별 추천 점수</div><div class="graph-explain-text">어떤 콘텐츠군의 후보가 평균적으로 높은 추천 점수를 받는지 비교합니다. 점수가 높은 콘텐츠군은 우선 탐색 영역으로 볼 수 있습니다.</div></div>')
    elif graph_view == "검토 단계별 후보 분포":
        html('<div class="graph-explain"><div class="graph-explain-title">검토 단계별 후보 분포</div><div class="graph-explain-text">즉시검토, 성장관찰, 검증필요 등 운영 단계별 후보 수를 비교합니다. 검증필요가 많으면 리스크 검토 공수가 큽니다.</div></div>')
    else:
        html('<div class="graph-explain"><div class="graph-explain-title">후보군 콘텐츠 비율</div><div class="graph-explain-text">현재 후보 풀이 특정 콘텐츠군에 쏠려 있는지 확인합니다. 쏠림이 크면 수집 키워드와 필터 편향을 점검합니다.</div></div>')

with graph_right:
    if graph_view == "콘텐츠 유형별 추천 점수":
        if segment_col and score_display_col and not classified_filtered.empty:
            seg_score = classified_filtered.copy()
            seg_score["__score__"] = pd.to_numeric(seg_score[score_display_col], errors="coerce")
            seg_score["__segment__"] = seg_score[segment_col].fillna("미분류").astype(str)
            seg_summary = (
                seg_score.groupby("__segment__", dropna=False)
                .agg(추천점수=("__score__", "mean"), 후보수=("__score__", "size"))
                .reset_index()
                .sort_values("추천점수", ascending=False)
                .head(8)
            )
            fig = px.bar(
                seg_summary,
                x="__segment__",
                y="추천점수",
                text="추천점수",
                custom_data=["후보수"],
                color="__segment__",
                color_discrete_sequence=COSMIC_COLORS,
                template="plotly_dark",
                height=282,
            )
            fig.update_traces(
                texttemplate="%{y:.1f}",
                textposition="outside",
                cliponaxis=False,
                hovertemplate="콘텐츠군=%{x}<br>추천점수=%{y:.1f}<br>후보수=%{customdata[0]}명<extra></extra>",
            )
            fig.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=12, r=12, t=16, b=54),
                xaxis_title="",
                yaxis_title="추천 점수",
                xaxis=dict(tickangle=0, tickfont=dict(size=10, color="#d7cdeb")),
                yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")),
                font=dict(color="#eee8ff"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("콘텐츠군별 점수를 만들 수 있는 컬럼이 부족합니다.")

    elif graph_view == "검토 단계별 후보 분포":
        if action_col and action_col in filtered.columns:
            bucket_order = ["즉시검토", "성장관찰", "검증필요", "보류", "제외", "미분류"]
            bucket_df = filtered[action_col].fillna("미분류").astype(str).value_counts().rename_axis("검토단계").reset_index(name="후보수")
            bucket_df["정렬"] = bucket_df["검토단계"].apply(lambda x: bucket_order.index(x) if x in bucket_order else 999)
            bucket_df = bucket_df.sort_values(["정렬", "후보수"], ascending=[True, False])
            fig = px.bar(
                bucket_df,
                x="후보수",
                y="검토단계",
                orientation="h",
                text="후보수",
                color="검토단계",
                color_discrete_sequence=COSMIC_COLORS,
                template="plotly_dark",
                height=282,
            )
            fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="검토단계=%{y}<br>후보수=%{x}명<extra></extra>")
            fig.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=8, r=32, t=12, b=30),
                xaxis_title="",
                yaxis_title="",
                xaxis=dict(gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")),
                yaxis=dict(tickfont=dict(color="#d7cdeb")),
                font=dict(color="#eee8ff"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("검토 단계 컬럼이 없어 그래프를 만들 수 없습니다.")

    else:
        if segment_col and segment_col in classified_filtered.columns and not classified_filtered.empty:
            pie_df = classified_filtered[segment_col].fillna("미분류").astype(str).value_counts().reset_index()
            pie_df.columns = ["구분", "후보수"]
            fig = px.pie(
                pie_df,
                names="구분",
                values="후보수",
                hole=.58,
                color_discrete_sequence=COSMIC_COLORS,
                template="plotly_dark",
                height=282,
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                marker=dict(line=dict(color="rgba(7,10,24,.85)", width=2)),
                hovertemplate="콘텐츠군=%{label}<br>후보수=%{value}명<br>비중=%{percent}<extra></extra>",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=6, r=6, t=6, b=6),
                legend=dict(font=dict(size=12, color="#eee8ff"), title_font=dict(size=12, color="#eee8ff"), x=1.02, y=.5, yanchor="middle"),
                font=dict(color="#eee8ff"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("콘텐츠군 구성 비율을 만들 수 없습니다.")

# ---------------------------------------------------------
# 14. 상세 설명 드롭다운
# ---------------------------------------------------------

with st.expander("KPI 해석 방법", expanded=False):
    st.markdown(
        """
        <div class="explain-box">
        <b>분석한 전체 채널</b>: 수집/전처리 후 대시보드에 올라온 전체 후보 수입니다.<br><br>
        <b>1차 조건 통과 후보</b>: shortlist 또는 주요 액션버킷 기준으로 사람이 실제 검토할 수 있는 후보군입니다.<br><br>
        <b>추천 점수 평균</b>: 현재 필터 조건에 남은 후보들의 평균 영입 점수입니다.<br><br>
        <b>바로 검토할 후보</b>: 우선 컨택 또는 수기 검증을 빠르게 진행할 만한 후보 수입니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("영입 점수 설명", expanded=False):
    st.markdown(
        """
        <div class="explain-box">
        <b>기본 산식</b><br>
        <code>영입점수 = 0.22×채널력 + 0.28×성장성 + 0.22×팬밀도 + 0.15×라이브친화 + 0.13×실전성 - 리스크 감점</code><br><br>
        성장성에 가장 높은 가중치를 둔 이유는 신생 플랫폼 입장에서 이미 너무 큰 채널보다, 최근 반응과 성장 흐름이 확인되는 후보가 영입 현실성이 높다고 보았기 때문입니다.
        채널력과 팬밀도는 최소 체급과 팬덤 결집력을 균형 있게 반영하고, 라이브친화와 실전성은 실제 방송 전환 가능성과 운영 리스크를 보정합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
# =========================================================
# 추가 수정: 영입 우선순위/최근 상승 후보 전환 타이틀 동기화 + 같은 행 정렬 보정
# =========================================================
st.markdown(
    """
    <style>
    .priority-inline-title {
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 0 0 6px 2px !important;
        margin: 0 !important;
        color: #fff7ff !important;
        font-size: 20px !important;
        font-weight: 950 !important;
        letter-spacing: -0.03em !important;
        white-space: nowrap !important;
    }

    .priority-view-switch-inline,
    .priority-view-switch {
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        margin: 0 0 6px 0 !important;
    }

    .priority-view-switch-inline div[role="radiogroup"],
    .priority-view-switch div[role="radiogroup"],
    .priority-view-switch-inline .stRadio > div,
    .priority-view-switch .stRadio > div {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 10px !important;
        width: 100% !important;
    }

    .priority-view-switch-inline label,
    .priority-view-switch label {
        min-width: 150px !important;
        max-width: 210px !important;
        height: 38px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 7px 14px !important;
        border-radius: 999px !important;
        background: rgba(255,255,255,0.055) !important;
        border: 1px solid rgba(145,116,233,0.30) !important;
        color: #ded7f5 !important;
        font-weight: 900 !important;
        white-space: nowrap !important;
    }

    .priority-view-switch-inline label:has(input:checked),
    .priority-view-switch label:has(input:checked) {
        background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
        border-color: rgba(221,160,255,0.56) !important;
        box-shadow: 0 0 16px rgba(145, 93, 255, 0.24) !important;
    }

    .priority-view-switch-inline label p,
    .priority-view-switch label p {
        font-size: 12px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 추가 수정: 영입 우선순위 TOP 제목-필터 같은 행 고정 보정
# - 제목 왼쪽, 표 전환 필터 오른쪽을 같은 기준선에 맞춤
# - st.radio 기본 상단 여백을 제거해 필터가 아래로 떨어지지 않게 함
# =========================================================
st.markdown(
    """
    <style>
    .priority-inline-title {
        height: 52px !important;
        min-height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 0 0 0 2px !important;
        margin: 0 !important;
        color: #fff7ff !important;
        font-size: 22px !important;
        font-weight: 950 !important;
        letter-spacing: -0.035em !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    .priority-view-switch-inline,
    .priority-view-switch {
        height: 52px !important;
        min-height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .priority-view-switch-inline [data-testid="stRadio"],
    .priority-view-switch [data-testid="stRadio"] {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .priority-view-switch-inline [data-testid="stRadio"] > div,
    .priority-view-switch [data-testid="stRadio"] > div,
    .priority-view-switch-inline div[role="radiogroup"],
    .priority-view-switch div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 14px !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .priority-view-switch-inline label,
    .priority-view-switch label {
        min-width: 170px !important;
        max-width: 230px !important;
        height: 42px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 8px 16px !important;
        border-radius: 999px !important;
        background: rgba(255,255,255,0.055) !important;
        border: 1px solid rgba(145,116,233,0.32) !important;
        color: #ded7f5 !important;
        font-weight: 900 !important;
        white-space: nowrap !important;
    }

    .priority-view-switch-inline label:has(input:checked),
    .priority-view-switch label:has(input:checked) {
        background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
        border-color: rgba(221,160,255,0.58) !important;
        box-shadow: 0 0 16px rgba(145, 93, 255, 0.26) !important;
    }

    .priority-view-switch-inline label p,
    .priority-view-switch label p {
        font-size: 13px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    /* 제목/필터 행과 표 사이 간격을 안정화 */
    .priority-table-panel {
        margin-top: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 최종 보정: 영입 우선순위 TOP 제목-필터 동일 선상 강제 정렬
# =========================================================
st.markdown(
    """
    <style>
    .priority-header-title {
        height: 48px !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        margin: 0 !important;
        padding: 0 0 0 2px !important;
        color: #fff7ff !important;
        font-size: 24px !important;
        font-weight: 950 !important;
        letter-spacing: -0.04em !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    .priority-header-switch {
        height: 48px !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .priority-header-switch [data-testid="stRadio"] {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .priority-header-switch [data-testid="stRadio"] > div,
    .priority-header-switch div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 18px !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .priority-header-switch label {
        height: 44px !important;
        min-width: 180px !important;
        max-width: 240px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 8px 18px !important;
        border-radius: 999px !important;
        background: rgba(255,255,255,0.055) !important;
        border: 1px solid rgba(145,116,233,0.34) !important;
        color: #ded7f5 !important;
        font-weight: 900 !important;
        white-space: nowrap !important;
    }

    .priority-header-switch label:has(input:checked) {
        background: linear-gradient(135deg, rgba(143,84,255,0.92), rgba(207,71,178,0.70)) !important;
        border-color: rgba(221,160,255,0.58) !important;
        box-shadow: 0 0 16px rgba(145, 93, 255, 0.26) !important;
    }

    .priority-header-switch label p {
        font-size: 14px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }

    /* 기존 priority-view-switch 보정 CSS가 남아 있더라도 새 header 클래스에는 영향을 주지 않도록 분리 */
    .priority-table-panel {
        margin-top: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 추가 보정: 영입 우선순위 헤더-테이블 세로 여백 최소화
# - TOP5 카드 하단과 우선순위 헤더 사이의 공백 축소
# - 헤더/필터 행과 테이블 사이의 공백 축소
# =========================================================
st.markdown(
    """
    <style>
    div.element-container:has(.top5-grid) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    div.element-container:has(.priority-tight-anchor) {
        height: 0 !important;
        min-height: 0 !important;
        margin: -8px 0 0 0 !important;
        padding: 0 !important;
    }

    div.element-container:has(.priority-header-title) {
        margin-top: -10px !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .priority-header-title {
        height: 38px !important;
        min-height: 38px !important;
        padding: 0 !important;
        margin: 0 !important;
        align-items: center !important;
    }

    div[data-testid="column"]:has(button[kind="primary"]),
    div[data-testid="column"]:has(button[kind="secondary"]) {
        padding-top: 0 !important;
    }

    button[kind="primary"][data-testid="baseButton-primary"],
    button[kind="secondary"][data-testid="baseButton-secondary"] {
        min-height: 38px !important;
        height: 38px !important;
        padding-top: 6px !important;
        padding-bottom: 6px !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        border-radius: 999px !important;
    }

    div.element-container:has(.priority-table-panel) {
        margin-top: -8px !important;
        padding-top: 0 !important;
    }

    .priority-table-panel {
        margin-top: 0 !important;
        padding-top: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 추가 보정: 우측 선택 후보 드롭다운 상단 여백
# - TOP5 카드 바로 아래에 붙어 보이지 않도록 좌측 제목 영역과 비슷한 여백 확보
# =========================================================
st.markdown(
    """
    <style>
    .candidate-select-top-spacer {
        height: 1px !important;
        min-height: 1px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div.element-container:has(.candidate-select-top-spacer) {
        height: 1px !important;
        min-height: 1px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 선택 후보 selectbox 자체의 위/아래 기본 여백을 안정화 */
    div.element-container:has(.candidate-select-top-spacer) + div.element-container {
        margin-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# STAR SEED 최종 디자인 오버라이드
# - 문구는 그대로 두고, 메인 홈의 스타시드 카드와 연결되는 민트/그린 포인트 강화
# - 기존 보라 우주톤은 유지하면서 STAR SEED 페이지의 액티브/카드/표/상세 영역을 통일
# =========================================================
st.markdown(
    clean_html(
        """
        <style>
        :root {
            --seed-green: #7CFF9E;
            --seed-green-soft: #98FFAB;
            --seed-green-bright: #37F58E;
            --seed-mint: #63FFD8;
            --seed-panel: rgba(6, 18, 26, 0.88);
            --seed-panel-strong: rgba(7, 24, 31, 0.96);
            --seed-line: rgba(124, 255, 158, 0.30);
            --seed-line-strong: rgba(124, 255, 158, 0.58);
            --seed-purple-base: #09051C;
            --seed-text: #FFF8FF;
            --seed-muted: #CFC4E4;
        }

        /* STAR SEED 본문 배경: 메인 홈의 보라 우주톤 위에 은은한 초록 광원만 추가 */
        .stApp {
            background:
                radial-gradient(circle at 72% 6%, rgba(50, 255, 130, 0.16) 0, transparent 22%),
                radial-gradient(circle at 51% 22%, rgba(127, 47, 255, 0.34), transparent 30%),
                radial-gradient(circle at 76% 76%, rgba(29, 255, 129, 0.09), transparent 31%),
                linear-gradient(180deg, #050411 0%, #09051C 52%, #050411 100%) !important;
        }

        [data-testid="stHeader"] {
            background: rgba(8, 12, 22, 0.96) !important;
        }

        /* 사이드바는 홈과 같은 어두운 미션 컨트롤 톤 유지 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(7, 8, 24, 0.99), rgba(4, 6, 18, 0.99)) !important;
            border-right: 1px solid rgba(154, 98, 255, 0.42) !important;
            box-shadow: 10px 0 32px rgba(0, 0, 0, 0.28) !important;
        }

        .sidebar-subtitle,
        .mission-sidebar-sub {
            color: var(--seed-green-soft) !important;
            text-shadow: 0 0 12px rgba(124, 255, 158, 0.28) !important;
        }

        /* STAR SEED 선택 상태: 홈의 스타시드 카드와 연결되는 그린 액티브 */
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, rgba(30, 213, 102, 0.98), rgba(18, 146, 86, 0.96)) !important;
            color: #F5FFF7 !important;
            border: 1px solid rgba(152, 255, 171, 0.70) !important;
            box-shadow:
                0 0 22px rgba(60, 255, 132, 0.30),
                inset 0 1px 0 rgba(255,255,255,0.16) !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: rgba(20, 16, 48, 0.78) !important;
            color: #EDE5FF !important;
            border: 1px solid rgba(196, 143, 255, 0.26) !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: rgba(152, 255, 171, 0.58) !important;
            box-shadow: 0 0 20px rgba(124, 255, 158, 0.18) !important;
        }

        .starseed-board {
            margin-top: -30px !important;
        }

        /* 제목: 텍스트는 그대로, STAR SEED에 초록 림라이트만 추가 */
        .board-title {
            color: #FFF8FF !important;
            letter-spacing: 9px !important;
            text-shadow:
                0 0 12px rgba(255,255,255,0.52),
                0 0 24px rgba(152,255,171,0.32),
                0 0 44px rgba(52,255,130,0.22) !important;
        }

        .board-title::after {
            content: "";
            display: block;
            width: 220px;
            height: 2px;
            margin-top: 14px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(152,255,171,0.0), rgba(152,255,171,0.85), rgba(99,255,216,0.42), rgba(152,255,171,0.0));
            box-shadow: 0 0 18px rgba(124,255,158,0.34);
        }

        .board-subtitle {
            color: #D9CFE8 !important;
            text-shadow: 0 0 12px rgba(124,255,158,0.08) !important;
        }

        .board-subtitle .seed-point,
        .seed-point,
        .seed-soft-point {
            color: var(--seed-green-soft) !important;
            text-shadow: 0 0 12px rgba(124,255,158,0.34) !important;
        }

        /* 안내 카드 */
        .board-info-card {
            border: 1px solid var(--seed-line-strong) !important;
            background:
                radial-gradient(circle at 8% 45%, rgba(124,255,158,0.22), transparent 28%),
                linear-gradient(135deg, rgba(10, 38, 30, 0.82), rgba(18, 16, 52, 0.88)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.08),
                0 0 28px rgba(124,255,158,0.15) !important;
        }

        .board-info-icon {
            background: radial-gradient(circle at 34% 26%, #EFFFF4, #47F587 44%, #0B7A4E 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 0 22px rgba(71,245,135,0.42) !important;
        }

        .board-info-title {
            color: #F7FFF8 !important;
        }

        .board-info-text {
            color: #D7E7DA !important;
        }

        /* KPI 카드 */
        .board-kpi-card {
            border: 1px solid rgba(124,255,158,0.30) !important;
            background:
                radial-gradient(circle at 10% 18%, rgba(124,255,158,0.14), transparent 30%),
                linear-gradient(180deg, rgba(9, 24, 38, .92), rgba(8, 12, 31, .96)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.06),
                0 10px 26px rgba(0,0,0,.24),
                0 0 18px rgba(124,255,158,.055) !important;
        }

        .board-kpi-card:hover {
            border-color: rgba(152,255,171,0.55) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.08),
                0 14px 30px rgba(0,0,0,.28),
                0 0 24px rgba(124,255,158,.12) !important;
        }

        .board-kpi-card::before {
            background: radial-gradient(circle at 8% 18%, rgba(124,255,158,.18), transparent 30%) !important;
        }

        .board-kpi-icon {
            background: radial-gradient(circle at 34% 24%, rgba(255,255,255,.40), rgba(57, 230, 125, .86) 48%, rgba(12, 93, 64, .95) 100%) !important;
            box-shadow: 0 0 20px rgba(80,255,146,.33) !important;
        }

        .board-kpi-label { color: #D5E6DD !important; }
        .board-kpi-value { color: #FFFFFF !important; }
        .board-kpi-note { color: #92A995 !important; }

        /* 공통 패널 */
        .board-panel {
            border: 1px solid rgba(124,255,158,0.26) !important;
            background:
                linear-gradient(180deg, rgba(14, 18, 43, .86), rgba(6, 11, 27, .94)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.06),
                0 16px 32px rgba(0,0,0,.22),
                0 0 24px rgba(124,255,158,.055) !important;
        }

        .board-panel-title {
            color: #FFF8FF !important;
        }

        /* TOP5 카드 */
        .mini-candidate-card {
            border: 1px solid rgba(124,255,158,0.28) !important;
            background:
                radial-gradient(circle at 22% 48%, rgba(124,255,158,0.08), transparent 42%),
                linear-gradient(180deg, rgba(14, 20, 45, .86), rgba(8, 12, 31, .97)) !important;
        }

        .mini-candidate-card:hover {
            border-color: rgba(152,255,171,0.50) !important;
            box-shadow: 0 0 20px rgba(124,255,158,0.11) !important;
        }

        .mini-avatar-wrap,
        .detail-avatar-big {
            border-color: rgba(152,255,171,0.66) !important;
            box-shadow:
                0 0 22px rgba(124,255,158,0.28),
                0 0 42px rgba(124,255,158,0.08) !important;
        }

        .mini-stage,
        .action-immediate {
            color: #DFFFF0 !important;
            background: linear-gradient(135deg, rgba(35, 194, 112, .92), rgba(10, 111, 76, .92)) !important;
            border: 1px solid rgba(124,255,158,.42) !important;
        }

        /* 우선순위 버튼 / 그래프 버튼: 보라에서 그린으로 연결 */
        div[data-testid="column"] .stButton > button[kind="primary"],
        button[kind="primary"][data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, rgba(36, 193, 104, 0.96), rgba(17, 113, 80, 0.96)) !important;
            border-color: rgba(152,255,171,0.56) !important;
            color: #F7FFF8 !important;
            box-shadow: 0 0 18px rgba(124,255,158,0.20) !important;
        }

        div[data-testid="column"] .stButton > button[kind="secondary"],
        button[kind="secondary"][data-testid="baseButton-secondary"] {
            background: rgba(7,18,34,0.84) !important;
            border-color: rgba(124,255,158,0.24) !important;
            color: #EAF7EF !important;
            box-shadow: none !important;
        }

        div[data-testid="column"] .stButton > button:hover {
            border-color: rgba(152,255,171,0.60) !important;
            box-shadow: 0 0 18px rgba(124,255,158,0.15) !important;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background: rgba(6, 18, 26, 0.92) !important;
            border: 1px solid rgba(124,255,158,0.30) !important;
            border-radius: 13px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04) !important;
        }

        /* 테이블 */
        .priority-table th {
            background: rgba(255,255,255,.075) !important;
            color: #E4E9E2 !important;
            border-bottom: 1px solid rgba(124,255,158,0.16) !important;
        }

        .priority-table td {
            border-bottom: 1px solid rgba(124,255,158,0.075) !important;
        }

        .priority-table tr:hover td {
            background: rgba(124,255,158,0.045) !important;
        }

        .priority-score,
        .mini-score,
        .detail-metric-value {
            color: #FFFFFF !important;
        }

        .view-more-bar {
            background: linear-gradient(90deg, rgba(12, 80, 58, .65), rgba(8, 32, 38, .78)) !important;
            border: 1px solid rgba(124,255,158,.30) !important;
            color: #EFFFF4 !important;
        }

        /* 선택 후보 상세 패널: 가장 강한 그린 포인트 */
        .detail-panel-v2 {
            border: 1px solid rgba(124,255,158,0.50) !important;
            background:
                radial-gradient(circle at 9% 45%, rgba(124,255,158,0.13), transparent 30%),
                linear-gradient(180deg, rgba(8, 32, 27, .88), rgba(8, 13, 31, .96)) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.07),
                0 0 26px rgba(124,255,158,0.16),
                0 18px 34px rgba(0,0,0,.26) !important;
        }

        .detail-metric-box {
            border: 1px solid rgba(124,255,158,.28) !important;
            background: rgba(124,255,158,.045) !important;
        }

        .detail-metric-label {
            color: #C5DCCB !important;
        }

        .reason-panel {
            border: 1px solid rgba(124,255,158,.38) !important;
            background: rgba(11, 55, 34, .28) !important;
        }

        .reason-title {
            color: #F3FFF5 !important;
        }

        .reason-bullet {
            color: #DDEBDD !important;
        }

        .reason-bullet::before {
            color: var(--seed-green-bright) !important;
            text-shadow: 0 0 8px rgba(124,255,158,0.45) !important;
        }

        /* 그래프 영역 */
        .graph-header-title {
            color: #FFF8FF !important;
            text-shadow: 0 0 14px rgba(124,255,158,0.22) !important;
        }

        .graph-explain-title {
            color: #FFF8FF !important;
            text-shadow: 0 0 12px rgba(124,255,158,0.20) !important;
        }

        .graph-explain-text {
            color: #CFC4E4 !important;
        }

        .stPlotlyChart,
        .plot-shell,
        .graph-output-card,
        .graph-table-card {
            border-color: rgba(124,255,158,0.24) !important;
            background: rgba(6, 12, 25, 0.66) !important;
        }

        /* expander / 설명 박스 */
        div[data-testid="stExpander"] {
            border-color: rgba(124,255,158,0.20) !important;
            background: rgba(8,18,34,0.78) !important;
        }

        .explain-box,
        .guide-box,
        .reason-box {
            border-color: rgba(124,255,158,0.18) !important;
            background: rgba(7, 20, 28, 0.70) !important;
        }

        /* 이미지 시안처럼 전체적으로 조금 더 촘촘한 관제보드 느낌 */
        .board-kpi-grid {
            gap: 12px !important;
            margin: 12px 0 12px 0 !important;
        }

        .top5-grid {
            gap: 10px !important;
        }

        .mid-grid {
            gap: 14px !important;
            margin-top: 12px !important;
        }

        @media (max-width: 1200px) {
            .board-title::after { width: 180px; }
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =========================================================
# 1-8. STAR SEED 눈부심 완화 오버라이드
# - 문구/레이아웃은 유지하고, 초록 포인트의 발광감만 낮춤
# - 보라 우주톤은 유지하되 카드/아이콘/상세패널 글로우를 부드럽게 조정
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            :root {
                --seed-green-bright: #83F6A0;
                --seed-green-soft: #6FDE90;
                --seed-green-line: rgba(131, 246, 160, 0.24);
                --seed-green-line-soft: rgba(131, 246, 160, 0.16);
                --seed-green-bg: rgba(78, 191, 118, 0.055);
            }

            /* 배경의 초록 안개를 한 단계 낮춰 눈부심 완화 */
            .stApp {
                background:
                    radial-gradient(circle at 56% 31%, rgba(127, 47, 255, 0.34), transparent 30%),
                    radial-gradient(circle at 78% 7%, rgba(93, 224, 131, 0.075), transparent 24%),
                    radial-gradient(circle at 60% 79%, rgba(121, 51, 255, 0.13), transparent 33%),
                    linear-gradient(180deg, #050411 0%, #09051C 52%, #050411 100%) !important;
            }

            /* STAR SEED 타이틀/강조 텍스트: 빛 번짐 축소 */
            .board-title,
            .graph-header-title,
            .graph-explain-title {
                text-shadow: 0 0 8px rgba(131,246,160,0.12) !important;
            }

            .board-title::after {
                opacity: 0.72 !important;
                box-shadow: 0 0 10px rgba(131,246,160,0.10) !important;
            }

            .seed-page-highlight,
            .seed-point,
            .seed-soft-point,
            .reason-bullet::before {
                color: var(--seed-green-bright) !important;
                text-shadow: none !important;
            }

            /* 사이드바 active 버튼: 색은 유지, 네온만 낮춤 */
            section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, rgba(28, 174, 88, 0.95), rgba(15, 105, 70, 0.96)) !important;
                border-color: rgba(131,246,160,0.42) !important;
                box-shadow:
                    0 0 10px rgba(80, 220, 120, 0.12),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
            }

            /* KPI / 패널 공통: 테두리는 보이되 광량은 낮춤 */
            .board-kpi-card,
            .board-panel,
            .mini-candidate-card,
            .detail-panel-v2,
            .stPlotlyChart,
            .plot-shell,
            .graph-output-card,
            .graph-table-card {
                border-color: var(--seed-green-line-soft) !important;
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,.045),
                    0 12px 26px rgba(0,0,0,.24) !important;
            }

            .board-kpi-card:hover,
            .board-panel:hover,
            .mini-candidate-card:hover,
            .detail-panel-v2:hover {
                border-color: rgba(131,246,160,0.30) !important;
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,.055),
                    0 14px 28px rgba(0,0,0,.28),
                    0 0 10px rgba(131,246,160,.055) !important;
            }

            .board-kpi-card::before,
            .mini-candidate-card,
            .detail-panel-v2 {
                background:
                    radial-gradient(circle at 10% 28%, rgba(131,246,160,0.055), transparent 32%),
                    linear-gradient(180deg, rgba(14, 18, 43, .86), rgba(6, 11, 27, .94)) !important;
            }

            /* 원형 아이콘/아바타 빛 완화 */
            .board-kpi-icon {
                background: radial-gradient(circle at 34% 24%, rgba(255,255,255,.28), rgba(48, 190, 102, .78) 50%, rgba(12, 78, 56, .92) 100%) !important;
                box-shadow: 0 0 10px rgba(80,255,146,.16) !important;
            }

            .mini-avatar-wrap,
            .detail-avatar-big {
                border-color: rgba(131,246,160,0.38) !important;
                box-shadow: 0 0 12px rgba(131,246,160,0.12) !important;
            }

            /* 상세 패널은 포인트만 남기고 녹색 면광 제거 */
            .detail-panel-v2 {
                border-color: rgba(131,246,160,0.28) !important;
                background:
                    radial-gradient(circle at 9% 45%, rgba(131,246,160,0.060), transparent 30%),
                    linear-gradient(180deg, rgba(8, 25, 27, .82), rgba(8, 13, 31, .96)) !important;
            }

            .detail-metric-box,
            .reason-panel {
                border-color: rgba(131,246,160,.20) !important;
                background: rgba(131,246,160,.030) !important;
            }

            /* 태그/버튼도 덜 쨍하게 */
            .mini-stage,
            .action-immediate {
                background: linear-gradient(135deg, rgba(26, 158, 91, .86), rgba(9, 88, 62, .88)) !important;
                border-color: rgba(131,246,160,.28) !important;
                box-shadow: none !important;
            }

            div[data-testid="column"] .stButton > button[kind="primary"],
            button[kind="primary"][data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, rgba(26, 158, 91, 0.92), rgba(12, 92, 65, 0.94)) !important;
                border-color: rgba(131,246,160,0.32) !important;
                box-shadow: none !important;
            }

            div[data-testid="column"] .stButton > button:hover {
                border-color: rgba(131,246,160,0.38) !important;
                box-shadow: 0 0 8px rgba(131,246,160,0.08) !important;
            }

            .view-more-bar,
            .stSelectbox > div > div {
                border-color: rgba(131,246,160,.20) !important;
                box-shadow: none !important;
            }

            /* 별 배경이 너무 튀지 않게 */
            .star-layer { opacity: 0.78 !important; }
            .twinkle-star { box-shadow: 0 0 6px rgba(255,255,255,0.55), 0 0 12px rgba(198,168,255,0.28) !important; }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 1-9. STAR SEED 제목 포인트 복구 오버라이드
# - 전체 눈부심은 낮춘 상태로 유지
# - STAR SEED 제목만 선명도/존재감 강화
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            /* 제목은 다시 힘 있게, 대신 화면 전체로 번지는 네온은 제한 */
            .board-title {
                color: #F7FFF9 !important;
                letter-spacing: 10px !important;
                text-shadow:
                    0 0 5px rgba(255,255,255,0.30),
                    0 0 14px rgba(131,246,160,0.26),
                    0 0 26px rgba(131,246,160,0.16) !important;
                position: relative;
            }

            /* 글자 아래 그린 라인을 조금 더 또렷하게 */
            .board-title::after {
                width: 250px !important;
                height: 3px !important;
                margin-top: 15px !important;
                opacity: 0.92 !important;
                background: linear-gradient(
                    90deg,
                    rgba(131,246,160,0),
                    rgba(131,246,160,0.92),
                    rgba(99,255,216,0.48),
                    rgba(131,246,160,0)
                ) !important;
                box-shadow: 0 0 12px rgba(131,246,160,0.18) !important;
            }

            /* 제목 주변에 아주 얇은 녹색 분위기만 추가 */
            .starseed-head-left {
                position: relative;
            }

            .starseed-head-left::before {
                content: "";
                position: absolute;
                left: -28px;
                top: -20px;
                width: 420px;
                height: 150px;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(131,246,160,0.075), transparent 66%);
                pointer-events: none;
                z-index: -1;
            }

            /* 부제목 강조 단어는 살짝만 더 밝게 */
            .board-subtitle .seed-point,
            .board-subtitle .seed-soft-point {
                color: #8EF3A5 !important;
                text-shadow: 0 0 8px rgba(131,246,160,0.14) !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 1-10. STAR SEED 상단 컴팩트 헤더 시안 오버라이드
# - 요청한 캡처처럼 제목을 한 줄 카드형 헤더로 변경
# - 하단 본문/문구는 유지하고 상단 톤만 정리
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            .starseed-board {
                margin-top: -18px !important;
                padding-top: 18px !important;
                position: relative !important;
            }

            .starseed-board::before {
                content: "";
                position: absolute;
                left: 0;
                right: 0;
                top: 0;
                height: 3px;
                border-radius: 999px;
                background: linear-gradient(
                    90deg,
                    rgba(131, 246, 160, 0.94) 0%,
                    rgba(131, 246, 160, 0.94) 50%,
                    rgba(128, 88, 255, 0.64) 50%,
                    rgba(131, 246, 160, 0.82) 100%
                );
                box-shadow: 0 0 10px rgba(131,246,160,0.14) !important;
            }

            .board-hero,
            .board-hero-compact {
                display: grid !important;
                grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.72fr) !important;
                gap: 26px !important;
                align-items: center !important;
                margin-bottom: 14px !important;
            }

            .board-head-left {
                display: grid !important;
                grid-template-columns: 72px minmax(0, 1fr) !important;
                gap: 18px !important;
                align-items: center !important;
                min-height: 96px !important;
                position: relative !important;
            }

            .board-head-left::before {
                content: "";
                position: absolute;
                left: -18px;
                top: -16px;
                width: 430px;
                height: 128px;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(131,246,160,0.06), transparent 68%);
                pointer-events: none;
                z-index: -1;
            }

            .board-title-icon {
                width: 60px !important;
                height: 60px !important;
                border-radius: 10px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background:
                    radial-gradient(circle at 45% 30%, rgba(131,246,160,0.14), transparent 56%),
                    rgba(12, 20, 38, 0.86) !important;
                border: 2px solid rgba(238, 235, 255, 0.82) !important;
                box-shadow:
                    0 0 10px rgba(131,246,160,0.10),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
                overflow: hidden !important;
            }

            .board-title-icon .seed-search-icon {
                transform: scale(0.78) !important;
                transform-origin: center center !important;
            }

            .board-title,
            .board-title-ko {
                font-family: inherit !important;
                font-size: 39px !important;
                font-weight: 950 !important;
                letter-spacing: -0.055em !important;
                line-height: 1.03 !important;
                color: #FFF8FF !important;
                margin: 0 0 8px 0 !important;
                text-shadow:
                    0 0 4px rgba(255,255,255,0.20),
                    0 0 12px rgba(131,246,160,0.16) !important;
                display: flex !important;
                align-items: baseline !important;
                gap: 10px !important;
                white-space: nowrap !important;
                position: relative !important;
            }

            .board-title span {
                color: #76F08D !important;
                font-size: 31px !important;
                font-weight: 950 !important;
                letter-spacing: -0.035em !important;
                text-shadow: 0 0 10px rgba(131,246,160,0.16) !important;
            }

            .board-title::after,
            .board-title-ko::after {
                display: none !important;
                content: none !important;
            }

            .board-subtitle {
                margin: 0 !important;
                font-size: 14.2px !important;
                font-weight: 720 !important;
                line-height: 1.45 !important;
                letter-spacing: -0.035em !important;
                color: #D8D0E7 !important;
                text-align: left !important;
                text-shadow: none !important;
                white-space: nowrap !important;
            }

            .board-subtitle .seed-point,
            .board-subtitle .seed-soft-point {
                color: #8EF3A5 !important;
                text-shadow: none !important;
            }

            .board-info-card {
                min-height: 76px !important;
                grid-template-columns: 52px 1fr !important;
                gap: 14px !important;
                padding: 14px 18px !important;
                border-radius: 12px !important;
                border: 1px solid rgba(131, 246, 160, 0.40) !important;
                background:
                    radial-gradient(circle at 9% 50%, rgba(131,246,160,0.14), transparent 28%),
                    linear-gradient(135deg, rgba(11, 35, 28, 0.78), rgba(18, 16, 45, 0.82)) !important;
                box-shadow:
                    0 10px 24px rgba(0,0,0,0.20),
                    inset 0 1px 0 rgba(255,255,255,0.06) !important;
            }

            .board-info-icon {
                width: 42px !important;
                height: 42px !important;
                font-size: 20px !important;
                background: radial-gradient(circle at 34% 26%, #F1FFF4, #58E984 48%, #11894D 100%) !important;
                box-shadow: 0 0 12px rgba(88,233,132,0.20) !important;
            }

            .board-info-title {
                font-size: 13.2px !important;
                margin-bottom: 4px !important;
                color: #F5FFF7 !important;
            }

            .board-info-text {
                font-size: 11.2px !important;
                line-height: 1.5 !important;
                color: #D6E5D8 !important;
            }

            @media (max-width: 1100px) {
                .board-hero,
                .board-hero-compact {
                    grid-template-columns: 1fr !important;
                }
                .board-subtitle {
                    white-space: normal !important;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

# =========================================================
# 1-11. STAR SEED 상단 선 제거 + 상단 여백 압축 최종 오버라이드
# - 문구/레이아웃은 유지
# - 초록 상단 장식선 제거
# - 화면 위쪽 여백만 줄여서 헤더가 더 위로 붙도록 조정
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            /* Streamlit 기본 본문 상단 여백 압축 */
            .block-container {
                padding-top: 0.55rem !important;
            }

            /* 스타시드 보드 자체 상단 여백 압축 */
            .starseed-board {
                margin-top: -30px !important;
                padding-top: 6px !important;
            }

            /* 위쪽 초록/보라 긴 선 제거 */
            .starseed-board::before,
            .board-hero::before,
            .board-hero-compact::before,
            .starseed-dashboard-hero::before {
                display: none !important;
                content: none !important;
                opacity: 0 !important;
                height: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            /* 헤더 블록 간격만 살짝 더 압축 */
            .board-hero,
            .board-hero-compact {
                margin-top: 0 !important;
                margin-bottom: 10px !important;
            }

            .board-head-left {
                min-height: 84px !important;
            }

            .board-title-icon {
                width: 56px !important;
                height: 56px !important;
            }

            .board-title,
            .board-title-ko {
                margin-bottom: 6px !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 1-12. STAR SEED 제목 위 빛 번짐 제거 최종 오버라이드
# - 제목 위쪽에 선처럼 보이는 text-shadow / 배경광 제거
# - 제목 자체는 너무 밋밋하지 않게 아주 약한 그림자만 유지
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            /* 제목 주변의 둥근 배경광이 선처럼 보이는 현상 제거 */
            .board-head-left::before,
            .starseed-head-left::before,
            .board-title::before,
            .board-title-ko::before,
            .board-title span::before,
            .board-title-ko span::before,
            .starseed-title::before,
            .starseed-compact-title::before,
            .starseed-head-title::before {
                display: none !important;
                content: none !important;
                opacity: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
                filter: none !important;
            }

            /* 제목 위로 번지는 강한 그림자 제거 */
            .board-title,
            .board-title-ko,
            .starseed-title,
            .starseed-compact-title,
            .starseed-head-title {
                text-shadow: 0 1px 0 rgba(255,255,255,0.10) !important;
                filter: none !important;
            }

            /* Star Seed 영문 초록 글자도 번짐 최소화 */
            .board-title span,
            .board-title-ko span,
            .starseed-title span,
            .starseed-compact-title span,
            .starseed-head-title span {
                text-shadow: 0 0 4px rgba(131,246,160,0.10) !important;
                filter: none !important;
            }

            /* 혹시 텍스트 뒤 블러/라인 역할을 하는 after 장식도 완전 제거 */
            .board-title::after,
            .board-title-ko::after,
            .starseed-title::after,
            .starseed-compact-title::after,
            .starseed-head-title::after {
                display: none !important;
                content: none !important;
                opacity: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            /* 제목 영역 위쪽 여백은 유지하되, 위로 삐져나오는 빛만 숨김 */
            .board-head-left,
            .starseed-head-left {
                overflow: visible !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# STAR SEED 상단 여백 최종 압축 오버라이드
# - Streamlit 기본 상단 헤더 높이를 줄여 위쪽 빈 공간 제거
# - 스타시드 헤더를 화면 상단에 더 가깝게 배치
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            /* Streamlit 기본 헤더는 사이드바 토글 때문에 보존 */
            [data-testid="stHeader"] {
                display: block !important;
                visibility: visible !important;
                height: 2.4rem !important;
                min-height: 2.4rem !important;
                max-height: 2.4rem !important;
                background: transparent !important;
                overflow: visible !important;
            }

            [data-testid="stDecoration"] {
                display: none !important;
                height: 0px !important;
            }

            /* 본문 컨테이너 상단 여백 제거 */
            .block-container {
                padding-top: 0rem !important;
                margin-top: -2.1rem !important;
            }

            /* 스타시드 상단 헤더를 더 위로 당김 */
            .starseed-board {
                margin-top: -42px !important;
                padding-top: 0 !important;
            }

            .board-hero,
            .board-hero-compact {
                margin-top: 0 !important;
                padding-top: 4px !important;
                padding-bottom: 8px !important;
                margin-bottom: 8px !important;
            }

            .board-head-left {
                min-height: 70px !important;
                align-items: center !important;
            }

            .board-title-icon {
                width: 52px !important;
                height: 52px !important;
            }

            .board-title,
            .board-title-ko {
                margin-top: 0 !important;
                margin-bottom: 4px !important;
                line-height: 1.05 !important;
            }

            .board-subtitle {
                margin-top: 0 !important;
                line-height: 1.35 !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 대시보드 홈 상단 배치 조정
# - Deploy/상단바 숨김 상태에서 홈 화면을 더 위로 당김
# - 문구/카드 내용은 수정하지 않음
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        /* 모든 페이지에서 Streamlit 상단 툴바/Deploy 숨김 */
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        [data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            height: 2.4rem !important;
            min-height: 2.4rem !important;
            max-height: 2.4rem !important;
            background: transparent !important;
            overflow: visible !important;
        }

        /* 홈 화면만 위로 당기는 전용 클래스 */
        .planet-home-wrap {
            margin-top: -56px !important;
        }

        .planet-home-wrap .hero-title {
            margin-top: 0 !important;
            margin-bottom: 10px !important;
        }

        .planet-home-wrap .hero-subtitle {
            margin-bottom: 2px !important;
        }

        .planet-home-wrap .planet-area {
            height: 315px !important;
            margin-top: -16px !important;
            margin-bottom: -24px !important;
        }

        /* 행성 크기는 유지하되 카드가 더 위로 붙게 카드 영역만 살짝 당김 */
        .mission-card {
            margin-top: -6px !important;
        }

        section.main .stButton > button {
            margin-top: -60px !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =========================================================
# Streamlit Deploy 버튼/상단바 완전 숨김 최종 오버라이드
# - 모든 페이지 공통 적용
# - Streamlit 버전별 data-testid/class 차이를 넓게 대응
# =========================================================
st.markdown(
    clean_html(
        """
        <style>
        /* Streamlit 헤더는 사이드바 토글 때문에 보존 */
        header,
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            height: 2.4rem !important;
            min-height: 2.4rem !important;
            max-height: 2.4rem !important;
            background: transparent !important;
            overflow: visible !important;
        }

        /* Deploy 버튼/툴바 숨김: Streamlit 버전별 선택자 대응 */
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        [data-testid="stAppDeployButton"],
        .stDeployButton,
        .stAppDeployButton,
        button[title="Deploy"],
        button[aria-label="Deploy"],
        a[title="Deploy"],
        a[aria-label="Deploy"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            min-height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            overflow: hidden !important;
        }

        /* 상단바가 사라진 뒤 남는 여백 제거 */
        .block-container {
            padding-top: 0rem !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =========================================================
# 홈 화면 레이아웃 복구/안전 조정
# - 행성이 카드 위로 겹치지 않게 원래 비율 복구
# - Deploy 숨김 유지
# - 홈 첫 진입 시 너무 아래로 처지지 않도록만 살짝 위로 조정
# =========================================================
st.markdown(
    clean_html(
        """
        <style>
        /* Deploy / Streamlit 툴바 숨김 유지: header/stHeader는 사이드바 토글 때문에 제외 */
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        [data-testid="stAppDeployButton"],
        .stDeployButton,
        button[title="Deploy"],
        button[aria-label="Deploy"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
        }

        /* 홈 화면: 압축은 풀고, 전체만 살짝 위로 */
        .block-container:has(.planet-home-wrap) {
            padding-top: 0 !important;
            margin-top: -3.2rem !important;
            padding-bottom: 2.5rem !important;
        }

        .planet-home-wrap {
            transform: translateY(-22px) !important;
            margin-bottom: -22px !important;
        }

        .planet-home-wrap .hero-title {
            font-size: 58px !important;
            margin-top: 8px !important;
            margin-bottom: 14px !important;
            letter-spacing: 9px !important;
        }

        .planet-home-wrap .hero-subtitle {
            font-size: 19px !important;
            margin-bottom: 8px !important;
        }

        /* 행성 영역은 너무 줄이면 카드와 겹치므로 340px 정도로 복구 */
        .planet-home-wrap .planet-area {
            height: 340px !important;
            margin-top: -8px !important;
            margin-bottom: -2px !important;
        }

        .planet-home-wrap .planet {
            width: 300px !important;
            height: 300px !important;
        }

        .planet-home-wrap .planet-logo {
            font-size: 45px !important;
        }

        .planet-home-wrap .planet-glow {
            width: 440px !important;
            height: 440px !important;
        }

        .planet-home-wrap .planet-orbit {
            width: 790px !important;
            height: 220px !important;
        }

        .planet-home-wrap .planet-orbit.orbit-2 {
            width: 625px !important;
            height: 176px !important;
        }

        .planet-home-wrap .planet-orbit.orbit-3 {
            width: 920px !important;
            height: 285px !important;
        }

        /* 카드 원래 높이 복구: 겹침 방지 */
        .planet-home-wrap .mission-card {
            min-height: 245px !important;
            padding: 26px 38px 74px !important;
        }

        .planet-home-wrap .card-head {
            margin-top: 20px !important;
            margin-bottom: 24px !important;
        }

        .planet-home-wrap .card-title {
            font-size: 40px !important;
        }

        .planet-home-wrap .card-desc {
            font-size: 19px !important;
            line-height: 1.68 !important;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# Streamlit이 이전 스크롤 위치를 기억할 때를 대비해, 홈에서는 첫 렌더 후 상단으로 복귀
if st.session_state.get("page") == "대시보드 홈":
    st.components.v1.html(
        """
        <script>
        const scrollHomeTop = () => {
            try {
                window.parent.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                const doc = window.parent.document;
                const main = doc.querySelector('section.main') || doc.querySelector('[data-testid="stAppViewContainer"]');
                if (main) main.scrollTo({ top: 0, left: 0, behavior: 'auto' });
            } catch(e) {}
        };
        scrollHomeTop();
        setTimeout(scrollHomeTop, 80);
        setTimeout(scrollHomeTop, 250);
        </script>
        """,
        height=0,
    )


# =========================================================
# STAR SEED 헤더 최종 미세 조정
# - 제목과 설명 사이 초록 라인 배치
# - 좌측 아이콘을 제목+설명 높이에 맞게 확대
# - 우측 기준 카드가 KPI 영역보다 튀어나오지 않도록 왼쪽 정렬
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            /* 상단 헤더 전체 폭/정렬 안정화 */
            .board-hero,
            .board-hero-compact {
                grid-template-columns: minmax(0, 1fr) 560px !important;
                column-gap: 22px !important;
                align-items: center !important;
                padding-right: 0 !important;
                box-sizing: border-box !important;
            }

            /* 좌측 아이콘이 제목~설명 높이와 맞도록 확대 */
            .board-head-left {
                grid-template-columns: 86px minmax(0, 1fr) !important;
                gap: 20px !important;
                min-height: 88px !important;
                align-items: center !important;
            }

            .board-title-icon {
                width: 72px !important;
                height: 72px !important;
                border-radius: 12px !important;
                align-self: center !important;
            }

            .board-title-icon .seed-search-icon {
                transform: scale(1.02) !important;
                transform-origin: center center !important;
            }

            .board-title-icon .seed-lens {
                border-width: 4px !important;
            }

            /* 제목 바로 아래, 설명 바로 위의 짧은 초록 라인 */
            .board-title,
            .board-title-ko {
                margin-bottom: 7px !important;
            }

            .board-title-accent-line {
                width: 235px !important;
                height: 2px !important;
                margin: 0 0 9px 2px !important;
                border-radius: 999px !important;
                background: linear-gradient(
                    90deg,
                    rgba(126, 255, 153, 0.92) 0%,
                    rgba(126, 255, 153, 0.58) 42%,
                    rgba(126, 255, 153, 0.18) 78%,
                    rgba(126, 255, 153, 0.00) 100%
                ) !important;
                box-shadow: 0 0 8px rgba(126, 255, 153, 0.16) !important;
            }

            .board-subtitle {
                margin-top: 0 !important;
                white-space: nowrap !important;
            }

            /* 우측 기준 카드: 아래 KPI 영역보다 오른쪽으로 튀어나오지 않게 왼쪽으로 당김 */
            .board-info-card {
                width: 100% !important;
                max-width: none !important;
                justify-self: stretch !important;
                transform: none !important;
                box-sizing: border-box !important;
                grid-template-columns: 54px minmax(0, 1fr) !important;
                padding-right: 22px !important;
            }

            .board-info-text {
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: unset !important;
                line-height: 1.5 !important;
                font-size: 12px !important;
                word-break: keep-all !important;
                overflow-wrap: break-word !important;
            }

            @media (max-width: 1200px) {
                .board-hero,
                .board-hero-compact {
                    grid-template-columns: 1fr !important;
                    padding-right: 0 !important;
                }

                .board-info-card {
                    transform: none !important;
                    max-width: none !important;
                }

                .board-subtitle,
                .board-info-text {
                    white-space: normal !important;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 1-13. STAR SEED 상단 기준 카드 텍스트 잘림 방지 + 경량 보정
# - 긴 문구가 한 줄 고정으로 잘리지 않도록 마지막에 한 번 더 보정
# - decorative star DOM 수는 위에서 180개로 낮춰 렌더링 부담을 줄임
# =========================================================
if st.session_state.page == "스타시드":
    st.markdown(
        clean_html(
            """
            <style>
            .board-info-card {
                align-self: center !important;
                min-width: 0 !important;
                overflow: visible !important;
            }

            .board-info-card > div:last-child {
                min-width: 0 !important;
            }

            .board-info-title,
            .board-info-text {
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: unset !important;
            }

            .board-info-text {
                line-height: 1.45 !important;
                word-break: keep-all !important;
                overflow-wrap: break-word !important;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )
