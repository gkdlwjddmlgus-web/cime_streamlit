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
# 0-1. CIME STREAM PLANET 네비게이션 상태
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "대시보드 홈"

if "card" not in st.session_state:
    st.session_state.card = None

if "bg_html" not in st.session_state:
    random.seed(42)
    stars = []
    for _ in range(230):
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
        <div class="main-wrap">
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
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue

    return pd.read_csv(path)


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
            max-width: 1540px !important;
            padding-top: 1.25rem !important;
        }

        /* STAR SEED 상단: 홈 화면의 큰 타이틀 톤과 정렬을 유지 */
        .starseed-hero {
            width: 100% !important;
            text-align: center !important;
            padding: 4px 0 26px 0 !important;
            margin: -10px auto 12px auto !important;
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
# 7. 헤더
# =========================================================

st.markdown(
    """
    <style>
    /* STAR SEED 페이지 상단 헤더 정렬/크기 조정 */
    .starseed-hero {
        width: 100%;
        text-align: center;
        padding: 10px 0 30px 0;
        margin: 0 auto 18px auto;
        position: relative;
        z-index: 2;
    }

    .starseed-title {
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(68px, 7.2vw, 96px);
        font-weight: 950;
        letter-spacing: 16px;
        line-height: 0.98;
        color: #FFF8FF;
        text-align: center;
        text-shadow:
            0 0 14px rgba(255,255,255,0.22),
            0 0 30px rgba(198,168,255,0.28);
        margin: 0;
    }

    .starseed-subtitle {
        font-size: clamp(20px, 1.7vw, 28px);
        font-weight: 850;
        letter-spacing: -0.035em;
        color: #D7CDED;
        text-align: center;
        margin-top: 24px;
        line-height: 1.25;
    }

    @media (max-width: 900px) {
        .starseed-hero {
            padding-top: 8px;
            padding-bottom: 22px;
        }
        .starseed-title {
            font-size: 48px;
            letter-spacing: 8px;
        }
        .starseed-subtitle {
            font-size: 18px;
            margin-top: 16px;
        }
    }
    </style>
    <div class="starseed-hero">
        <div class="starseed-title">STAR SEED</div>
        <div class="starseed-subtitle">유튜브 기반 잠재 후보군 영입 분석 대시보드</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 8. KPI 카드
# =========================================================

# ---------------------------------------------------------
# KPI 계산 기준
# - 기존 문제:
#   사이드바에서 "비교 대상 시점"을 바꿔도 KPI 빅넘버는 항상 현재 df 기준으로만 계산됨
#
# - 수정 방향:
#   빅넘버 = 사용자가 선택한 비교 대상 시점 기준
#   증감 = 기준 시점 대비 비교 대상 시점
#
# 예:
#   기준 시점: 2026-05-01
#   비교 대상 시점: 현재
#   → 현재 값과 2026-05-01 snapshot의 차이 표시
#
#   기준 시점: 2026-05-01
#   비교 대상 시점: 2026-05-01
#   → 같은 snapshot끼리 비교하므로 증감 0
# ---------------------------------------------------------

# 비교 대상 데이터가 비어 있으면 현재 df로 fallback
if tracking_target_df is not None and not tracking_target_df.empty:
    target_all_kpi_df = add_score_display_column(tracking_target_df)
else:
    target_all_kpi_df = add_score_display_column(df)

# 기준 시점 데이터
if tracking_base_df is not None and not tracking_base_df.empty:
    base_all_kpi_df = add_score_display_column(tracking_base_df)
else:
    base_all_kpi_df = pd.DataFrame()

# 현재 화면 필터 조건을 비교 대상/기준 snapshot에도 최대한 동일 적용
target_filtered_kpi_df = apply_snapshot_filters_for_kpi(target_all_kpi_df)

if not base_all_kpi_df.empty:
    base_filtered_kpi_df = apply_snapshot_filters_for_kpi(base_all_kpi_df)
else:
    base_filtered_kpi_df = pd.DataFrame()

# KPI 값 계산
target_all_kpi = calc_kpi_values(target_all_kpi_df)
target_filtered_kpi = calc_kpi_values(target_filtered_kpi_df)

base_all_kpi = calc_kpi_values(base_all_kpi_df) if not base_all_kpi_df.empty else {
    "total": np.nan,
    "shortlist": np.nan,
    "avg_score": np.nan,
    "high_priority": np.nan,
}

base_filtered_kpi = calc_kpi_values(base_filtered_kpi_df) if not base_filtered_kpi_df.empty else {
    "total": np.nan,
    "shortlist": np.nan,
    "avg_score": np.nan,
    "high_priority": np.nan,
}

# ---------------------------------------------------------
# 동일 날짜 비교 방어
# - 기준 시점과 비교 대상 시점이 같으면 증감은 강제로 0 처리
# - 동일 snapshot인데도 증감이 뜨는 문제 방지
# ---------------------------------------------------------

is_same_snapshot_compare = (
    tracking_base_label != "-"
    and tracking_target_label != "현재"
    and tracking_base_label == tracking_target_label
)

if is_same_snapshot_compare:
    delta_total = 0
    delta_shortlist = 0
    delta_avg_score = 0
    delta_high_priority = 0
else:
    delta_total = (
        target_all_kpi["total"] - base_all_kpi["total"]
        if pd.notna(base_all_kpi["total"])
        else np.nan
    )

    delta_shortlist = (
        target_all_kpi["shortlist"] - base_all_kpi["shortlist"]
        if pd.notna(base_all_kpi["shortlist"])
        else np.nan
    )

    delta_avg_score = (
        target_filtered_kpi["avg_score"] - base_filtered_kpi["avg_score"]
        if pd.notna(base_filtered_kpi["avg_score"])
        else np.nan
    )

    delta_high_priority = (
        target_filtered_kpi["high_priority"] - base_filtered_kpi["high_priority"]
        if pd.notna(base_filtered_kpi["high_priority"])
        else np.nan
    )

# 카드 하단 설명 문구
if tracking_base_label != "-":
    compare_label = f"기준: {tracking_base_label} → 비교: {tracking_target_label}"
else:
    compare_label = "비교 기준 없음"

target_label_for_sub = tracking_target_label if tracking_target_label else "현재"

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi_card(
        label="전체 후보군",
        value=target_all_kpi["total"],
        value_suffix="명",
        sub=f"{target_label_for_sub} 전체 후보 기준 · {compare_label}",
        delta=delta_total,
        value_ndigits=0,
        delta_ndigits=0,
        delta_suffix="명",
    )

with k2:
    render_kpi_card(
        label="핵심 검토 대상",
        value=target_all_kpi["shortlist"],
        value_suffix="명",
        sub=f"shortlist 또는 주요 액션버킷 기준 · {compare_label}",
        delta=delta_shortlist,
        value_ndigits=0,
        delta_ndigits=0,
        delta_suffix="명",
    )

with k3:
    render_kpi_card(
        label="평균 영입 점수(100점)",
        value=target_filtered_kpi["avg_score"],
        value_suffix="",
        sub=f"{target_label_for_sub} 필터 적용 기준 · {compare_label}",
        delta=delta_avg_score,
        value_ndigits=1,
        delta_ndigits=1,
        delta_suffix="점",
    )

with k4:
    render_kpi_card(
        label="고우선 후보 수",
        value=target_filtered_kpi["high_priority"],
        value_suffix="명",
        sub=f"즉시검토/영입제한/위성 등 · {compare_label}",
        delta=delta_high_priority,
        value_ndigits=0,
        delta_ndigits=0,
        delta_suffix="명",
    )


html('<div class="kpi-expander-spacer"></div>')

with st.expander("KPI 해석 방법", expanded=False):
    st.markdown(
        """
        <div class="explain-box">
        <b>전체 후보군</b>: 선택한 비교 대상 시점의 전체 후보 수입니다. 후보군 규모가 충분히 확보되었는지 확인합니다.<br><br>
        <b>핵심 검토 대상</b>: shortlist 또는 주요 액션버킷에 해당하는 후보 수입니다. 사람이 실제로 검토할 후보 pool의 크기를 의미합니다.<br><br>
        <b>평균 영입 점수</b>: 현재 필터 조건에 남은 후보들의 평균 영입 적합도 점수입니다. 특정 세그먼트나 검토 단계를 선택했을 때 후보군의 평균 품질을 비교할 수 있습니다.<br><br>
        <b>고우선 후보 수</b>: 즉시검토 또는 이에 준하는 우선순위 후보 수입니다. 우선 컨택/검증 대상의 규모를 빠르게 확인하는 지표입니다.<br><br>
        <b>증감 표시</b>: 기준 시점 대비 비교 대상 시점의 변화량입니다. ▲는 증가, ▼는 감소, —는 변화 없음을 의미합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("영입 점수 설명", expanded=False):
    st.markdown(
        """
        <div class="explain-box">
        <b>영입 점수</b>는 유튜브 후보 채널이 CIME에서 실제 영입 검토 대상이 될 수 있는지를 보기 위한 100점 기준의 운영 점수입니다.
        단순히 조회수나 구독자 수가 높은 채널을 찾는 것이 아니라, <b>채널 규모, 최근 성장성, 팬 반응 밀도, 라이브 전환 가능성, 영입 현실성</b>을 함께 봅니다.<br><br>

        <b>기본 산식</b><br>
        <code>기본 영입점수 = 0.22×채널력점수 + 0.28×성장성점수 + 0.22×팬밀도점수 + 0.15×라이브친화점수 + 0.13×실전성점수</code><br><br>

        <b>리스크 반영</b><br>
        <code>최종 영입점수 = 기본 영입점수 - 수기제외/운영제외/검증필요 리스크 감점</code><br>
        즉, 점수가 높더라도 방송사·기관·팬클립·아카이브·리믹스·외국채널·콘텐츠군 미분류 등 실제 영입 후보로 보기 어려운 신호가 있으면 검토 단계가 낮아질 수 있습니다.<br><br>

        <b>가중치 설정 이유</b><br>
        성장성점수에 가장 높은 가중치(<code>0.28</code>)를 둔 이유는 CIME가 신생 플랫폼이므로 이미 너무 큰 채널보다 <b>최근 성장 중인 잠재 후보</b>가 영입 현실성이 높다고 보았기 때문입니다.
        채널력점수와 팬밀도점수는 각각 <code>0.22</code>로 두어, 최소한의 채널 체급과 팬덤 반응을 균형 있게 반영했습니다.
        라이브친화점수(<code>0.15</code>)는 유튜브 채널이 스트리밍으로 전환될 가능성을 보기 위한 보조 축이며, 실전성점수(<code>0.13</code>)는 실제 영입 대상이 아닌 노이즈 채널을 낮추기 위한 보정 축입니다.<br><br>

        따라서 영입 점수는 최종 의사결정 점수가 아니라, <b>후보를 빠르게 좁히기 위한 우선순위 점수</b>입니다. 실제 검토에서는 검토 단계, 추천 사유, 콘텐츠군, 최근 변화 추적을 함께 확인해야 합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# 9. TOP 후보 카드
# =========================================================

add_section_divider()
st.markdown("### ⭐ TOP 영입 후보")

top_candidates = filtered.head(5).copy()

card_cols = st.columns(5)

for i, (_, row) in enumerate(top_candidates.iterrows()):
    with card_cols[i]:
        rank_value = row.get("표시순위", i + 1)
        name = row.get(channel_name_col, "-") if channel_name_col else "-"
        segment = row.get(segment_col, "-") if segment_col else "-"
        lower_segment = row.get(lower_segment_col, "") if lower_segment_col else ""
        action = row.get(action_col, "") if action_col else ""
        score = row.get("_score_display", np.nan)

        pill_text = action if str(action).strip() else segment
        sub_pill = lower_segment if str(lower_segment).strip() else segment
        avatar_html = get_candidate_avatar_html(row, segment_col, lower_segment_col, channel_thumbnail_col)
        channel_url = row.get(channel_url_col, "") if channel_url_col else ""
        candidate_name_html = make_channel_name_html(name, channel_url)

        st.markdown(
            f"""
            <div class="candidate-card">
                <div class="rank-badge">{fmt_int(rank_value)}</div>
                {avatar_html}
                <div class="candidate-name">{candidate_name_html}</div>
                <div style="text-align:center;">
                    <span class="segment-pill">{pill_text}</span>
                </div>
                <div class="score-text">{fmt_float(score, 1)}</div>
                <div style="text-align:center;" class="small-muted">영입 종합 점수(100점)</div>
                <div style="text-align:center; margin-top: 12px;">
                    <span class="segment-pill">{sub_pill}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown("<br>", unsafe_allow_html=True)


add_section_divider()
# =========================================================
# 10. 본문 레이아웃
# - 좌측에는 영입 우선순위 TOP 표
# - 우측에는 선택 후보 상세를 같은 높이 라인에 배치
# - 기존처럼 빈 section-card div가 먼저 렌더링되는 문제를 피하기 위해
#   우측 상세는 st.container(border=True)로 직접 감싼다.
# =========================================================

main_left, main_right = st.columns([0.68, 0.32], gap="large")


# =========================================================
# 10-1. 좌측: 영입 우선순위 TOP 표
# =========================================================

with main_left:
    with st.container(border=True):
        st.markdown("### 🛰️ 영입 우선순위 TOP")
        st.caption("현재 필터 조건에서 검토 우선순위가 높은 후보를 보여줍니다. 표의 순위는 전체 원본 순위가 아니라 현재 필터 결과 기준입니다.")

        # -------------------------------------------------
        # TOP 후보 표시 컬럼
        # - shortlist 유형, 변화 요약은 운영 상세 컬럼이므로 TOP 테이블에서는 제외
        # - '현재 필터 기준 순위'는 화면에서 '순위'로 축약 표시
        # -------------------------------------------------
        display_cols = [
            "표시순위",
            channel_name_col,
            segment_col,
            lower_segment_col,
            score_display_col,
            subs_col,
            view_col,
            eng_col,
            action_col,
            recommend_col,
            caution_col,
        ]

        display_cols = [c for c in display_cols if c and c in filtered.columns]
        table_df = filtered[display_cols].head(top_n).copy()

        display_rename_map = {
            "표시순위": "순위",
            score_display_col: "영입 적합도 점수",
            channel_name_col: "채널명",
            segment_col: "주요 콘텐츠군",
            lower_segment_col: "세부 콘텐츠 유형",
            subs_col: "구독자 수",
            view_col: "최근 영상 평균 조회수",
            eng_col: "평균 참여율",
            action_col: "검토 단계",
            recommend_col: "추천 사유",
            caution_col: "주의 사유",
        }
        display_rename_map = {k: v for k, v in display_rename_map.items() if k and k in table_df.columns}
        table_df = table_df.rename(columns=display_rename_map)

        if "영입 적합도 점수" in table_df.columns:
            table_df["영입 적합도 점수"] = pd.to_numeric(table_df["영입 적합도 점수"], errors="coerce").round(1)

        def _plain_cell(value, default="-"):
            if value is None:
                return default
            try:
                if pd.isna(value):
                    return default
            except Exception:
                pass
            text_value = str(value).strip()
            return text_value if text_value else default

        def _safe_cell(value, default="-"):
            return html_lib.escape(_plain_cell(value, default), quote=False)

        def _short_text(value, limit=62):
            text = _plain_cell(value, "")
            if len(text) > limit:
                return text[:limit].rstrip() + "…"
            return text

        def _score_class(value):
            # 점수 색상은 전체 순위에서 동일한 강조색으로 통일한다.
            return "priority-score-main"

        # 주요 콘텐츠군 색상: 세부 콘텐츠 유형은 같은 계열의 더 짙은 색상으로 표시
        def _segment_theme_class(text):
            label = _plain_cell(text, "")
            if any(k in label for k in ["버츄얼", "퍼포먼스", "버튜버", "VTuber"]):
                return "seg-virtual"
            if any(k in label for k in ["음악", "보이스", "커버", "성우", "더빙", "ASMR"]):
                return "seg-music"
            if any(k in label for k in ["창작", "비주얼", "코스프레", "일러스트"]):
                return "seg-visual"
            if any(k in label for k in ["게임", "실황", "롤", "로블록스", "발로란트"]):
                return "seg-game"
            if any(k in label for k in ["서브컬처", "토크", "팬덤"]):
                return "seg-fandom"
            return "seg-default"

        def _segment_pill(text, kind="main"):
            label = _safe_cell(text, "-")
            raw = _plain_cell(text, "-")
            base_cls = _segment_theme_class(raw)
            depth_cls = "main-tag" if kind == "main" else "sub-tag"
            return f'<span class="priority-tag {base_cls} {depth_cls}" title="{label}">{label}</span>'

        def _action_pill(text):
            label = _safe_cell(text, "-")
            raw = _plain_cell(text, "-")
            if "즉시" in raw:
                cls = "action-immediate"
            elif "성장" in raw:
                cls = "action-growth"
            elif "검증" in raw:
                cls = "action-verify"
            elif "제외" in raw:
                cls = "action-exclude"
            else:
                cls = "action-hold"
            return f'<span class="priority-action {cls}" title="{label}">{label}</span>'

        def _make_note(row):
            # 변화 요약/shortlist 유형은 TOP 테이블에서 제외. 비고는 추천/주의 사유 중심으로 축약.
            rec = _short_text(row.get("추천 사유", ""), 72)
            caution = _short_text(row.get("주의 사유", ""), 40)
            if rec and caution:
                return f"{rec} / 주의: {caution}"
            if rec:
                return rec
            if caution:
                return f"주의: {caution}"

            seg_text = _plain_cell(row.get("주요 콘텐츠군", ""), "")
            lower_text = _plain_cell(row.get("세부 콘텐츠 유형", ""), "")
            view_text = _plain_cell(row.get("최근 영상 평균 조회수", ""), "")
            eng_text = _plain_cell(row.get("평균 참여율", ""), "")
            parts = []
            if seg_text or lower_text:
                parts.append(" · ".join([x for x in [seg_text, lower_text] if x]))
            if view_text:
                parts.append(f"최근 평균 조회수 {view_text}")
            if eng_text:
                parts.append(f"참여율 {eng_text}")
            return " / ".join(parts) if parts else "필터 조건 기준 상위 후보"

        st.markdown(
            """
            <style>
            .priority-board-wrap {
                width: 100%;
                overflow: hidden;
                border-radius: 16px;
                border: 1px solid rgba(118, 242, 226, 0.18);
                background: linear-gradient(180deg, rgba(12, 22, 39, 0.94), rgba(7, 13, 26, 0.98));
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 14px 30px rgba(0,0,0,0.22);
                margin-top: 12px;
                margin-bottom: 12px;
            }
            .priority-board {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                color: #efffff;
                font-size: 13.2px;
            }
            .priority-board thead th {
                background: rgba(255,255,255,0.055);
                color: #d9e8f2;
                font-size: 12.5px;
                font-weight: 850;
                padding: 9px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.10);
                text-align: center;
                white-space: nowrap;
            }
            .priority-board tbody td {
                padding: 10px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.075);
                vertical-align: middle;
                text-align: center;
            }
            .priority-board tbody tr:last-child td { border-bottom: 0; }
            .priority-board tbody tr:hover { background: rgba(118, 242, 226, 0.055); }
            .priority-rank {
                color: #eafcff;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
            }
            .priority-name {
                text-align: left !important;
                font-weight: 900;
                color: #ffffff;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
            }
            .priority-name a { color: #ffffff; text-decoration: none; }
            .priority-name a:hover { color: #78ffee; text-decoration: underline; text-underline-offset: 3px; }
            .priority-score {
                font-size: 16px;
                font-weight: 950;
                font-variant-numeric: tabular-nums;
                color: #7cfff1;
                text-shadow: 0 0 10px rgba(95,255,232,0.32);
            }
            .priority-score-main,
            .priority-score-high,
            .priority-score-mid,
            .priority-score-low { color: #7cfff1; }
            .priority-note {
                text-align: left !important;
                color: #c4d1dc;
                font-size: 12px;
                line-height: 1.35;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            .priority-board-top-chip {
                display: inline-block;
                padding: 7px 18px;
                border-radius: 999px;
                background: rgba(255,255,255,0.95);
                color: #111827;
                font-size: 13px;
                font-weight: 850;
                box-shadow: 0 8px 20px rgba(0,0,0,0.22);
                margin: 2px 0 10px 0;
            }
            .priority-tag,
            .priority-action {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                max-width: 138px;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 11.5px;
                font-weight: 900;
                line-height: 1.05;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                border: 1px solid rgba(255,255,255,0.16);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 0 14px rgba(0,0,0,0.10);
            }
            .main-tag.seg-virtual { background: linear-gradient(135deg, rgba(245,158,11,.84), rgba(217,119,6,.58)); color:#fff4d8; }
            .sub-tag.seg-virtual  { background: linear-gradient(135deg, rgba(180,83,9,.92), rgba(124,45,18,.72)); color:#ffe7bf; }
            .main-tag.seg-music   { background: linear-gradient(135deg, rgba(99,102,241,.84), rgba(124,58,237,.58)); color:#eeeaff; }
            .sub-tag.seg-music    { background: linear-gradient(135deg, rgba(76,29,149,.94), rgba(49,46,129,.75)); color:#e4dcff; }
            .main-tag.seg-visual  { background: linear-gradient(135deg, rgba(236,72,153,.82), rgba(190,24,93,.58)); color:#ffe6f4; }
            .sub-tag.seg-visual   { background: linear-gradient(135deg, rgba(157,23,77,.94), rgba(112,26,117,.72)); color:#ffd7ef; }
            .main-tag.seg-game    { background: linear-gradient(135deg, rgba(14,165,233,.82), rgba(37,99,235,.58)); color:#e1f6ff; }
            .sub-tag.seg-game     { background: linear-gradient(135deg, rgba(30,64,175,.94), rgba(15,23,42,.74)); color:#dbeafe; }
            .main-tag.seg-fandom  { background: linear-gradient(135deg, rgba(20,184,166,.82), rgba(13,148,136,.58)); color:#dcfff8; }
            .sub-tag.seg-fandom   { background: linear-gradient(135deg, rgba(15,118,110,.94), rgba(19,78,74,.74)); color:#ccfbf1; }
            .main-tag.seg-default { background: linear-gradient(135deg, rgba(100,116,139,.78), rgba(51,65,85,.58)); color:#e9f0f8; }
            .sub-tag.seg-default  { background: linear-gradient(135deg, rgba(71,85,105,.90), rgba(30,41,59,.76)); color:#e2e8f0; }
            .priority-action { min-width: 64px; max-width: 95px; }
            .action-immediate { background: linear-gradient(135deg, rgba(20,184,166,.70), rgba(13,148,136,.48)); color:#dffff9; }
            .action-growth    { background: linear-gradient(135deg, rgba(124,58,237,.70), rgba(91,33,182,.48)); color:#efe7ff; }
            .action-verify    { background: linear-gradient(135deg, rgba(245,158,11,.70), rgba(180,83,9,.48)); color:#fff2d2; }
            .action-hold      { background: linear-gradient(135deg, rgba(100,116,139,.70), rgba(51,65,85,.48)); color:#e9f0f8; }
            .action-exclude   { background: linear-gradient(135deg, rgba(148,85,255,.58), rgba(76,29,149,.46)); color:#eee7ff; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        rows_html = []
        for _, r in table_df.head(top_n).iterrows():
            rank_text = _safe_cell(r.get("순위", "-"))
            name_raw = _plain_cell(r.get("채널명", "-"), "-")
            name_text = _safe_cell(name_raw)
            channel_match = filtered[filtered[channel_name_col].astype(str) == str(name_raw)] if channel_name_col else pd.DataFrame()
            channel_url = ""
            if channel_url_col and not channel_match.empty and channel_url_col in channel_match.columns:
                channel_url = str(channel_match.iloc[0].get(channel_url_col, "") or "").strip()
            if is_valid_url(channel_url):
                safe_url = html_lib.escape(channel_url, quote=True)
                name_html = f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{name_text}</a>'
            else:
                name_html = name_text

            segment_html = _segment_pill(r.get("주요 콘텐츠군", "-"), kind="main")
            lower_html = _segment_pill(r.get("세부 콘텐츠 유형", "-"), kind="sub")
            action_html = _action_pill(r.get("검토 단계", "-"))
            score_val = r.get("영입 적합도 점수", np.nan)
            score_text = fmt_float(score_val, 1)
            score_cls = _score_class(score_val)
            rows_html.append(
                f"""
                <tr>
                    <td class="priority-rank">{rank_text}</td>
                    <td class="priority-name">{name_html}</td>
                    <td>{segment_html}</td>
                    <td>{lower_html}</td>
                    <td>{action_html}</td>
                    <td class="priority-score {score_cls}">{score_text}</td>
                </tr>
                """
            )

        html(
            f"""
            <div class="priority-board-wrap">
                <table class="priority-board">
                    <colgroup>
                        <col style="width: 7%;">
                        <col style="width: 21%;">
                        <col style="width: 20%;">
                        <col style="width: 20%;">
                        <col style="width: 17%;">
                        <col style="width: 15%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th>순위</th>
                            <th>스트리머명</th>
                            <th>주요 콘텐츠군</th>
                            <th>세부 콘텐츠 유형</th>
                            <th>검토단계</th>
                            <th>점수</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
            """
        )

        with st.expander("📘 테이블 읽는 법과 도출 가능한 인사이트", expanded=False):
            st.markdown(
                """
                <div class="guide-box">
                    <b>테이블 읽는 법</b><br>
                    현재 필터 조건에서 <b>검토 우선순위가 높은 후보</b>를 위에서부터 보여줍니다.
                    순위는 전체 후보군 고정 순위가 아니라, 사이드바 필터가 적용된 뒤 다시 매긴 <b>현재 화면 기준 순위</b>입니다.
                    주요 콘텐츠군과 세부 콘텐츠 유형은 같은 계열 색상으로 묶어 표시하며, 세부 유형은 더 짙은 색으로 표시해 소속 관계를 빠르게 볼 수 있습니다.
                    <br><br>
                    <b>도출 가능한 인사이트</b><br>
                    상위권에 반복적으로 나타나는 콘텐츠군은 CIME가 우선 검토할 만한 후보 풀이 두꺼운 영역입니다.
                    점수는 높지만 참여율이나 조회수 규모가 낮은 후보는 수기 검증이 필요하고,
                    점수·참여율·라이브친화 신호가 함께 높은 후보는 우선 컨택 후보로 볼 수 있습니다.
                </div>
                """,
                unsafe_allow_html=True,
            )

        csv_download = table_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "현재 TOP 후보 CSV 다운로드",
            data=csv_download,
            file_name="cime_top_candidates.csv",
            mime="text/csv",
        )


# =========================================================
# 10-2. 우측: 선택 후보 상세
# - 빈 박스가 따로 생기지 않도록 section-card HTML wrapper 제거
# - 상세 판정 근거 expander 제거
# - TOP 표와 비슷한 높이에서 끝나도록 핵심 지표와 압축 사유만 표시
# =========================================================

with main_right:
    with st.container(border=True):
        st.markdown("### 🔭 선택 후보 상세")

        if channel_name_col:
            candidate_names = filtered[channel_name_col].dropna().astype(str).tolist()

            if candidate_names:
                selected_name = st.selectbox("후보 선택", candidate_names, index=0)
                selected_row = filtered[filtered[channel_name_col].astype(str) == selected_name].iloc[0]

                def _clip_detail(value, limit=80):
                    text_value = "-" if pd.isna(value) else str(value).strip()
                    if not text_value:
                        text_value = "-"
                    return text_value if len(text_value) <= limit else text_value[:limit].rstrip() + "..."

                selected_channel_url = selected_row.get(channel_url_col, "") if channel_url_col else ""
                selected_name_html = make_channel_name_html(selected_row.get(channel_name_col, "-"), selected_channel_url)
                selected_profile_html = get_selected_profile_html(selected_row, segment_col, lower_segment_col, channel_thumbnail_col)

                html(
                    f"""
                    <div class="selected-profile-area">
                        {selected_profile_html}
                    </div>
                    <div class="detail-title detail-title-centered">{selected_name_html}</div>
                    """
                )

                metric_cols = st.columns(2)
                with metric_cols[0]:
                    st.metric("점수(100점)", fmt_float(selected_row.get(score_display_col), 1) if score_col else "-")
                    st.metric(
                        "구독자 수",
                        fmt_int(
                            get_first_value_from_row(
                                selected_row,
                                [subs_col, "채널구독자수", "채널 구독자 수", "구독자수", "구독자 수", "subscriber_count", "subscribers", "channel_subscriber_count"]
                            )
                        ),
                    )
                    st.metric("최근 조회수 평균", fmt_int(selected_row.get(view_col)) if view_col else "-")
                with metric_cols[1]:
                    st.metric("성장성", fmt_float(selected_row.get(growth_col), 3) if growth_col else "-")
                    st.metric("팬밀도", fmt_float(selected_row.get(fan_col), 3) if fan_col else "-")
                    st.metric("라이브친화", fmt_float(selected_row.get(live_col), 3) if live_col else "-")

                st.markdown(
                    f"""
                    <div style="margin-top:8px;">
                        <span class="segment-pill">{selected_row.get(segment_col, '-') if segment_col else '-'}</span>
                        <span class="segment-pill">{selected_row.get(action_col, '-') if action_col else '-'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                reason_text = selected_row.get(recommend_col, "-") if recommend_col else "-"

                st.markdown(
                    f"""
                    <div class="reason-box compact-reason-box">
                        <b>핵심 추천 사유</b><br>{_clip_detail(reason_text, 92)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("현재 필터 조건에 해당하는 후보가 없습니다.")
        else:
            st.info("후보명을 표시할 수 있는 컬럼을 찾지 못했습니다.")


# =========================================================
# 10-3. 후보 운영 그래프 선택형 뷰
# - 우측 후보 상세와 겹치지 않도록 TOP 표/상세 아래의 전체 폭 영역으로 배치
# =========================================================

add_section_divider()
# =====================================================
# 후보 운영 그래프 선택형 뷰
# - 상위 콘텐츠별 점수 분포 / 검토 단계별 후보 수 /
#   콘텐츠군별 평균 점수 / 콘텐츠군 구성 비율 중 1개만 표시
# - 상위 콘텐츠군이 미분류인 후보는 콘텐츠 비교 그래프에서 제외
# =====================================================

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### 🌌 후보 운영 그래프")
st.caption("아래 선택지에서 그래프 유형을 고르면, 선택한 그래프 1개만 넓게 표시됩니다. 콘텐츠군 비교 그래프에서는 `미분류` 후보를 제외합니다.")

graph_view = st.radio(
    "그래프 유형 선택",
    [
        "상위 콘텐츠별 영입 후보 점수 분포",
        "검토 단계별 후보 수",
        "콘텐츠군별 평균 영입 점수",
        "콘텐츠군 구성 비율",
    ],
    index=0,
    horizontal=True,
    key="starseed_graph_view_selector",
    label_visibility="collapsed",
)

def _is_unclassified_segment(s: pd.Series) -> pd.Series:
    return (
        s.fillna("미분류")
        .astype(str)
        .str.strip()
        .isin(["", "미분류", "None", "none", "nan", "NaN", "NULL", "null"])
    )

classified_filtered = filtered.copy()
classified_all = df.copy()
unclassified_filtered_count = 0
unclassified_all_count = 0

if segment_col and segment_col in filtered.columns:
    unclassified_filtered_count = int(_is_unclassified_segment(filtered[segment_col]).sum())
    classified_filtered = filtered[~_is_unclassified_segment(filtered[segment_col])].copy()

if segment_col and segment_col in df.columns:
    unclassified_all_count = int(_is_unclassified_segment(df[segment_col]).sum())
    classified_all = df[~_is_unclassified_segment(df[segment_col])].copy()

if graph_view == "상위 콘텐츠별 영입 후보 점수 분포":
    st.markdown("#### 🌠 상위 콘텐츠별 영입 후보 점수 분포")
    st.caption("각 점은 후보 채널 1개를 의미합니다. x축은 상위 콘텐츠군, y축은 영입 적합도 점수입니다.")

    if segment_col and score_col and not classified_all.empty:
        plot_all = classified_all.copy()
        plot_all = plot_all.reset_index().rename(columns={"index": "__original_index__"})

        selected_index_set = set(classified_filtered.index.tolist())
        plot_all["__is_selected__"] = plot_all["__original_index__"].isin(selected_index_set)
        plot_all["__score_plot__"] = pd.to_numeric(plot_all[score_display_col], errors="coerce")
        y_axis_title = "최종점수(100점 기준)"
        plot_all["__segment__"] = plot_all[segment_col].fillna("미분류").astype(str)

        segment_order = (
            plot_all
            .groupby("__segment__")["__score_plot__"]
            .median()
            .sort_values(ascending=False)
            .index
            .tolist()
        )

        seg_to_x = {seg: i for i, seg in enumerate(segment_order)}
        plot_all["__x_base__"] = plot_all["__segment__"].map(seg_to_x)

        rng = np.random.default_rng(42)
        plot_all["__x_jitter__"] = plot_all["__x_base__"] + rng.normal(
            loc=0,
            scale=0.08,
            size=len(plot_all),
        )

        palette = px.colors.qualitative.Safe + px.colors.qualitative.Set3 + px.colors.qualitative.Pastel
        seg_color_map = {seg: palette[i % len(palette)] for i, seg in enumerate(segment_order)}

        selected_plot = plot_all[plot_all["__is_selected__"] == True].copy()
        unselected_plot = plot_all[plot_all["__is_selected__"] == False].copy()

        hover_cols = [
            c for c in [
                channel_name_col,
                segment_col,
                lower_segment_col,
                action_col,
                score_display_col,
                subs_col,
                view_col,
                eng_col,
            ]
            if c and c in plot_all.columns
        ]

        fig = go.Figure()

        if not unselected_plot.empty:
            fig.add_trace(
                go.Scatter(
                    x=unselected_plot["__x_jitter__"],
                    y=unselected_plot["__score_plot__"],
                    mode="markers",
                    name="필터 제외",
                    marker=dict(size=7, color="rgba(150,150,150,0.28)", line=dict(width=0)),
                    customdata=unselected_plot[hover_cols].astype(str).values if hover_cols else None,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        + "상위 콘텐츠군: %{customdata[1]}<br>" if len(hover_cols) >= 2 else ""
                    )
                    + "점수: %{y:.2f}<br>"
                    + "<extra>필터 제외</extra>",
                    showlegend=True,
                )
            )

        for seg in segment_order:
            seg_df = selected_plot[selected_plot["__segment__"] == seg].copy()
            if seg_df.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=seg_df["__x_jitter__"],
                    y=seg_df["__score_plot__"],
                    mode="markers",
                    name=seg,
                    marker=dict(
                        size=9,
                        color=seg_color_map.get(seg, "#888888"),
                        opacity=0.82,
                        line=dict(width=0.8, color="rgba(255,255,255,0.35)"),
                    ),
                    customdata=seg_df[hover_cols].astype(str).values if hover_cols else None,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        + "상위 콘텐츠군: %{customdata[1]}<br>" if len(hover_cols) >= 2 else ""
                    )
                    + ("세부 콘텐츠 유형: %{customdata[2]}<br>" if len(hover_cols) >= 3 else "")
                    + ("검토 단계: %{customdata[3]}<br>" if len(hover_cols) >= 4 else "")
                    + "점수: %{y:.2f}<br>"
                    + "<extra></extra>",
                )
            )

        fig.update_layout(
            template="plotly_dark",
            height=460,
            paper_bgcolor="rgba(7, 16, 32, 0.96)",
            plot_bgcolor="rgba(7, 16, 32, 0.96)",
            margin=dict(l=10, r=10, t=30, b=80),
            legend_title_text="상위 콘텐츠군",
            xaxis=dict(
                title="상위 콘텐츠군",
                tickmode="array",
                tickvals=list(range(len(segment_order))),
                ticktext=segment_order,
                tickangle=-35,
                showgrid=False,
            ),
            yaxis=dict(title=y_axis_title, gridcolor="rgba(255,255,255,0.12)", zeroline=False),
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"해석 포인트: 어느 상위 콘텐츠군에 고득점 후보가 많은지, 특정 상위 콘텐츠군이 낮은 점수대에 몰려 있는지 확인합니다. "
            f"색상 점은 현재 필터에 포함된 후보, 회색 점은 필터에서 제외된 후보입니다. "
            f"상위 콘텐츠군이 확인되지 않은 미분류 후보 {unclassified_all_count:,}명은 이 그래프에서 제외했습니다."
        )
    else:
        st.info("상위 콘텐츠별 점수 분포를 만들기 위해서는 대표상위세그먼트 컬럼과 최종점수 컬럼이 필요합니다.")

elif graph_view == "검토 단계별 후보 수":
    st.markdown("#### 🚦 검토 단계별 후보 수")
    if action_col and action_col in filtered.columns:
        bucket_order = ["즉시검토", "성장관찰", "검증필요", "보류", "제외", "미분류"]
        bucket_df = (
            filtered[action_col]
            .fillna("미분류")
            .astype(str)
            .value_counts()
            .rename_axis("액션버킷")
            .reset_index(name="후보수")
        )
        bucket_df["정렬순서"] = bucket_df["액션버킷"].apply(lambda x: bucket_order.index(x) if x in bucket_order else 999)
        bucket_df = bucket_df.sort_values(["정렬순서", "후보수"], ascending=[True, False])

        color_map_bucket = {
            "즉시검토": "#19d3a2",
            "성장관찰": "#636efa",
            "검증필요": "#ef553b",
            "보류": "#a0a7b8",
            "제외": "#5b657a",
            "미분류": "#8892a6",
        }

        fig_bucket = px.bar(
            bucket_df,
            x="후보수",
            y="액션버킷",
            orientation="h",
            text="후보수",
            template="plotly_dark",
            height=460,
            color="액션버킷",
            color_discrete_map=color_map_bucket,
        )
        fig_bucket.update_traces(textposition="outside", cliponaxis=False, hovertemplate="액션버킷=%{y}<br>후보수=%{x}명<extra></extra>")
        fig_bucket.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(7, 16, 32, 0.96)",
            plot_bgcolor="rgba(7, 16, 32, 0.96)",
            margin=dict(l=5, r=35, t=20, b=45),
            xaxis_title="후보 수",
            yaxis_title="",
            yaxis=dict(categoryorder="array", categoryarray=list(reversed(bucket_df["액션버킷"].tolist()))),
        )
        st.plotly_chart(fig_bucket, use_container_width=True)
        st.caption("해석 포인트: 즉시검토, 성장관찰, 검증필요, 보류, 제외 중 후보가 어디에 몰려 있는지 확인합니다. 검증필요가 과도하게 많으면 리스크 검토 대상이 많다는 뜻이고, 즉시검토가 적으면 바로 컨택 가능한 후보 풀이 제한적이라는 뜻입니다.")
    else:
        st.info("액션버킷 컬럼이 없어 시각화를 만들 수 없습니다.")

elif graph_view == "콘텐츠군별 평균 영입 점수":
    st.markdown("#### ✨ 콘텐츠군별 평균 영입 점수")
    if segment_col and score_display_col and segment_col in classified_filtered.columns and score_display_col in classified_filtered.columns and not classified_filtered.empty:
        seg_score_df = classified_filtered.copy()
        seg_score_df["__score__"] = pd.to_numeric(seg_score_df[score_display_col], errors="coerce")
        seg_score_df["__segment__"] = seg_score_df[segment_col].fillna("미분류").astype(str)

        seg_summary = (
            seg_score_df.groupby("__segment__", dropna=False)
            .agg(평균최종점수=("__score__", "mean"), 후보수=("__score__", "size"))
            .reset_index()
            .sort_values(["평균최종점수", "후보수"], ascending=[False, False])
        )

        fig_seg_score = px.bar(
            seg_summary,
            x="__segment__",
            y="평균최종점수",
            text="평균최종점수",
            custom_data=["후보수"],
            template="plotly_dark",
            height=460,
            color="__segment__",
        )
        fig_seg_score.update_traces(
            texttemplate="%{y:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="상위 콘텐츠군=%{x}<br>평균최종점수=%{y:.1f}<br>후보수=%{customdata[0]}명<extra></extra>",
        )
        fig_seg_score.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(7, 16, 32, 0.96)",
            plot_bgcolor="rgba(7, 16, 32, 0.96)",
            margin=dict(l=5, r=5, t=20, b=90),
            xaxis_title="상위 콘텐츠군",
            yaxis_title="평균 점수",
            xaxis=dict(tickangle=-35),
            yaxis=dict(range=[0, max(100, float(seg_summary["평균최종점수"].max(skipna=True) or 0) * 1.15)]),
        )
        st.plotly_chart(fig_seg_score, use_container_width=True)
        st.caption(f"해석 포인트: 어떤 상위 콘텐츠군이 평균적으로 높은 영입 적합도를 보이는지 비교합니다. 단, 후보 수가 적은 콘텐츠군은 평균이 쉽게 흔들릴 수 있습니다. 미분류 후보 {unclassified_filtered_count:,}명은 제외했습니다.")
    else:
        st.info("콘텐츠군별 평균 점수를 만들기 위해서는 대표상위세그먼트 컬럼과 최종점수 컬럼이 필요합니다.")

elif graph_view == "콘텐츠군 구성 비율":
    st.markdown("#### 🪐 콘텐츠군 구성 비율")
    if segment_col and segment_col in classified_filtered.columns and not classified_filtered.empty:
        pie_data = (
            classified_filtered[segment_col]
            .fillna("미분류")
            .astype(str)
            .value_counts()
            .reset_index()
        )
        pie_data.columns = ["구분", "후보수"]
        fig_pie = px.pie(pie_data, names="구분", values="후보수", hole=0.55, template="plotly_dark", height=460)
        fig_pie.update_traces(textposition="inside", textinfo="percent", hovertemplate="상위 콘텐츠군=%{label}<br>후보수=%{value}명<br>비중=%{percent}<extra></extra>")
        fig_pie.update_layout(
            paper_bgcolor="rgba(7, 16, 32, 0.96)",
            plot_bgcolor="rgba(7, 16, 32, 0.96)",
            margin=dict(l=5, r=5, t=20, b=20),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption(f"해석 포인트: 현재 후보군이 특정 상위 콘텐츠군에 과도하게 쏠려 있는지 확인합니다. 쏠림이 크면 수집 키워드나 필터가 특정 콘텐츠군에 편향됐을 가능성을 점검해야 합니다. 미분류 후보 {unclassified_filtered_count:,}명은 제외했습니다.")
    else:
        st.info("콘텐츠군 구성 비율을 만들기 위해서는 대표상위세그먼트 컬럼이 필요합니다.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 10-4. 후보 클러스터 포지셔닝 맵
# - 요청에 따라 대시보드 본문에서 제외함
# =========================================================

# =========================================================
# 11. 하단: Snapshot 기반 변화 추적
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)
add_section_divider()
st.markdown("### 📡 최근 주목 후보 변화")
with st.expander("📘 표 해석법", expanded=False):
    st.markdown(
        """
        <div class="guide-box">
        <b>변화 추적 표를 읽는 법</b><br>
        - <b>순위 변동</b>이 양수이면 이전 시점보다 현재 순위가 상승한 후보입니다.<br>
        - <b>점수 변동</b>이 양수이면 영입 적합도 점수가 상승한 후보입니다.<br>
        - <b>검토 단계</b>가 보류 → 성장관찰, 검증필요 → 즉시검토처럼 개선되면 우선 확인 대상입니다.<br>
        - <b>신규진입</b>은 기준 시점에는 없었지만 비교 시점에 새로 등장한 후보입니다.<br><br>
        <b>도출 가능한 인사이트</b><br>
        버킷이 개선된 후보는 단순 순위 상승보다 운영상 의미가 큽니다. 특히 순위와 점수가 함께 상승하고 현재 검토 단계가 즉시검토로 바뀐 후보는 후속 수기 검증 우선순위를 높게 볼 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

if not tracking_base_df.empty and not tracking_target_df.empty:
    dynamic_tracking_df = build_tracking_between(
        base_df=tracking_base_df,
        target_df=tracking_target_df,
        base_label=tracking_base_label,
        target_label=tracking_target_label,
    )

    st.caption(f"기준 시점: {tracking_base_label}  →  비교 대상 시점: {tracking_target_label}")

    if not dynamic_tracking_df.empty:
        tracking_filter_cols = st.columns([0.25, 0.25, 0.25, 0.25])

        with tracking_filter_cols[0]:
            only_bucket_changed = st.checkbox("버킷변경", value=True)
        with tracking_filter_cols[1]:
            only_new = st.checkbox("신규진입", value=False)
        with tracking_filter_cols[2]:
            only_rank_up = st.checkbox("순위상승", value=False)
        with tracking_filter_cols[3]:
            max_tracking_rows = st.number_input("표시 행 수", min_value=10, max_value=500, value=10, step=10)

        tracking_view = dynamic_tracking_df.copy()

        if only_new and "신규진입여부" in tracking_view.columns:
            tracking_view = tracking_view[tracking_view["신규진입여부"] == True]

        if only_bucket_changed and "버킷변경여부" in tracking_view.columns:
            tracking_view = tracking_view[tracking_view["버킷변경여부"] == True]

        if only_rank_up and "운영우선순위변동" in tracking_view.columns:
            tracking_view = tracking_view[pd.to_numeric(tracking_view["운영우선순위변동"], errors="coerce") > 0]

        # 표시 컬럼명 정리
        rename_tracking_cols = {
            "기준_운영우선순위": "기준순위",
            "비교_운영우선순위": "비교순위",
            "기준_최종점수": "기준점수",
            "비교_최종점수": "비교점수",
            "기준_액션버킷": "기준액션버킷",
            "비교_액션버킷": "비교액션버킷",
            "비교_대표상위세그먼트": "대표상위세그먼트",
            "비교_대표하위세그먼트": "대표하위세그먼트",
        }

        tracking_view = tracking_view.rename(columns=rename_tracking_cols)

        for c in ["대표상위세그먼트", "대표하위세그먼트"]:
            if c in tracking_view.columns:
                tracking_view[c] = (
                    tracking_view[c]
                    .replace(["None", "nan", "NaN", ""], pd.NA)
                    .fillna("미분류")
                )
        for c in ["기준점수", "비교점수", "최종점수변동"]:
            if c in tracking_view.columns:
                tracking_view[c] = pd.to_numeric(tracking_view[c], errors="coerce").round(1)

        # 기본 표는 제3자가 바로 해석할 수 있도록 핵심 컬럼만 간략 표시
        # 요청 반영: 주요 콘텐츠군 컬럼은 기본 변화 추적 표에서 제외
        display_cols_tracking = [
            "채널명",
            "기준순위",
            "비교순위",
            "운영우선순위변동",
            "기준점수",
            "비교점수",
            "최종점수변동",
            "기준액션버킷",
            "비교액션버킷",
            "변화요약",
        ]
        display_cols_tracking = [c for c in display_cols_tracking if c in tracking_view.columns]

        tracking_display = tracking_view[display_cols_tracking].head(int(max_tracking_rows)).copy()
        target_name_for_table = "현재" if tracking_target_label == "현재" else "비교 시점"
        tracking_display = tracking_display.rename(columns={
            "기준순위": "이전 순위",
            "비교순위": f"{target_name_for_table} 순위",
            "운영우선순위변동": "순위 변동",
            "기준점수": "이전 점수",
            "비교점수": f"{target_name_for_table} 점수",
            "최종점수변동": "점수 변동",
            "기준액션버킷": "이전 검토 단계",
            "비교액션버킷": f"{target_name_for_table} 검토 단계",
            "변화요약": "변화 요약",
        })

        # Streamlit 기본 dataframe 대신 TOP 테이블과 같은 랭킹 보드형 HTML 테이블로 표시
        st.markdown(
            """
            <style>
            .tracking-board-wrap {
                margin-top: 14px;
                margin-bottom: 16px;
            }
            .tracking-board {
                font-size: 13px;
            }
            .tracking-board thead th {
                padding: 10px 8px;
                font-size: 12.3px;
            }
            .tracking-board tbody td {
                padding: 10px 8px;
                height: 38px;
            }
            .tracking-name {
                text-align: left !important;
                font-weight: 900;
                color: #ffffff;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
            }
            .tracking-num {
                font-weight: 850;
                font-variant-numeric: tabular-nums;
                color: #eafcff;
            }
            .tracking-rank-up,
            .tracking-score-up {
                color: #ff7a7a;
                font-weight: 950;
            }
            .tracking-rank-down,
            .tracking-score-down {
                color: #69b4ff;
                font-weight: 950;
            }
            .tracking-rank-flat,
            .tracking-score-flat {
                color: #b8c7d5;
                font-weight: 850;
            }
            .tracking-summary {
                text-align: left !important;
                color: #c9d7e3;
                font-size: 12px;
                line-height: 1.35;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            .tracking-chip {
                display: inline-block;
                padding: 7px 18px;
                border-radius: 999px;
                background: rgba(255,255,255,0.95);
                color: #111827;
                font-size: 13px;
                font-weight: 850;
                box-shadow: 0 8px 20px rgba(0,0,0,0.22);
                margin: 4px 0 10px 0;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        def _tracking_num_cell(value, ndigits=0):
            if pd.isna(value):
                return "-"
            try:
                num = float(value)
                if ndigits == 0:
                    return f"{int(round(num)):,}"
                return f"{num:,.{ndigits}f}"
            except Exception:
                return _safe_cell(value, "-")

        def _tracking_delta_class(value, prefix):
            try:
                num = float(value)
            except Exception:
                return f"{prefix}-flat"
            if num > 0:
                return f"{prefix}-up"
            if num < 0:
                return f"{prefix}-down"
            return f"{prefix}-flat"

        def _tracking_delta_text(value, ndigits=0):
            if pd.isna(value):
                return "-"
            try:
                num = float(value)
                abs_num = abs(num)
                if ndigits == 0:
                    formatted = f"{int(round(abs_num)):,}"
                else:
                    formatted = f"{abs_num:,.{ndigits}f}"
                if num > 0:
                    return f"▲ {formatted}"
                if num < 0:
                    return f"▼ {formatted}"
                return "—"
            except Exception:
                return _safe_cell(value, "-")

        tracking_rows_html = []
        for _, row in tracking_display.iterrows():
            name_html = _safe_cell(row.get("채널명", "-"))
            prev_rank = _tracking_num_cell(row.get("이전 순위"), 0)
            cur_rank_col = f"{target_name_for_table} 순위"
            cur_score_col = f"{target_name_for_table} 점수"
            cur_action_col = f"{target_name_for_table} 검토 단계"
            cur_rank = _tracking_num_cell(row.get(cur_rank_col), 0)
            rank_delta_val = row.get("순위 변동", np.nan)
            rank_delta = _tracking_delta_text(rank_delta_val, 0)
            rank_delta_cls = _tracking_delta_class(rank_delta_val, "tracking-rank")
            prev_score = _tracking_num_cell(row.get("이전 점수"), 1)
            cur_score = _tracking_num_cell(row.get(cur_score_col), 1)
            score_delta_val = row.get("점수 변동", np.nan)
            score_delta = _tracking_delta_text(score_delta_val, 1)
            score_delta_cls = _tracking_delta_class(score_delta_val, "tracking-score")
            prev_action = _action_pill(row.get("이전 검토 단계", "-"))
            cur_action = _action_pill(row.get(cur_action_col, "-"))
            summary = _safe_cell(_short_text(row.get("변화 요약", "-"), 70))

            tracking_rows_html.append(
                f"""
                <tr>
                    <td class="tracking-name">{name_html}</td>
                    <td class="tracking-num">{prev_rank}</td>
                    <td class="tracking-num">{cur_rank}</td>
                    <td class="{rank_delta_cls}">{rank_delta}</td>
                    <td class="tracking-num">{prev_score}</td>
                    <td class="tracking-num">{cur_score}</td>
                    <td class="{score_delta_cls}">{score_delta}</td>
                    <td>{prev_action}</td>
                    <td>{cur_action}</td>
                    <td class="tracking-summary" title="{summary}">{summary}</td>
                </tr>
                """
            )

        html(
            f"""
            <div class="priority-board-wrap tracking-board-wrap">
                <table class="priority-board tracking-board">
                    <colgroup>
                        <col style="width: 16%;">
                        <col style="width: 8%;">
                        <col style="width: 8%;">
                        <col style="width: 8%;">
                        <col style="width: 8%;">
                        <col style="width: 8%;">
                        <col style="width: 8%;">
                        <col style="width: 10%;">
                        <col style="width: 10%;">
                        <col style="width: 16%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th>채널명</th>
                            <th>이전 순위</th>
                            <th>{target_name_for_table} 순위</th>
                            <th>순위 변동</th>
                            <th>이전 점수</th>
                            <th>{target_name_for_table} 점수</th>
                            <th>점수 변동</th>
                            <th>이전 단계</th>
                            <th>{target_name_for_table} 단계</th>
                            <th>변화 요약</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(tracking_rows_html)}
                    </tbody>
                </table>
            </div>
            """
        )

        with st.expander("변화 추적 상세 컬럼 보기", expanded=False):
            detail_cols_tracking = [
                "기준시점",
                "비교시점",
                "채널명",
                "채널ID",
                "기준순위",
                "비교순위",
                "운영우선순위변동",
                "기준점수",
                "비교점수",
                "최종점수변동",
                "기준액션버킷",
                "비교액션버킷",
                "버킷변경여부",
                "신규진입여부",
                "대표상위세그먼트",
                "대표하위세그먼트",
                "변화요약",
            ]
            detail_cols_tracking = [c for c in detail_cols_tracking if c in tracking_view.columns]
            st.dataframe(
                tracking_view[detail_cols_tracking].head(int(max_tracking_rows)),
                use_container_width=True,
                hide_index=True,
            )

        tracking_csv = tracking_view.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "현재 변화 추적 CSV 다운로드",
            data=tracking_csv,
            file_name=f"cime_tracking_{tracking_base_label}_to_{tracking_target_label}.csv".replace(":", "-"),
            mime="text/csv",
        )
    else:
        st.info("선택한 두 시점으로 계산된 변화 추적 결과가 없습니다.")
else:
    st.info(
        "과거 시점 비교를 하려면 `09_intermediate/snapshots/candidate_scored_snapshot.csv`에 "
        "날짜가 다른 snapshot이 1개 이상 있어야 합니다. 현재 snapshot이 부족하면 STEP11 snapshot append를 먼저 누적하세요."
    )
