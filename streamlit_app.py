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

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
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
        primary_bg = "linear-gradient(135deg, rgba(125, 66, 255, 0.98), rgba(75, 42, 168, 0.98) 58%, rgba(184, 138, 46, 0.94))"
        primary_bg_hover = "linear-gradient(135deg, rgba(145, 86, 255, 1), rgba(95, 55, 190, 1) 58%, rgba(210, 160, 60, 0.98))"
        primary_border = "rgba(255, 212, 93, 0.58)"
        primary_border_hover = "rgba(255, 226, 135, 0.76)"
        primary_shadow = "0 0 16px rgba(255, 212, 93, 0.16), inset 0 1px 0 rgba(255,255,255,0.12)"
        secondary_border = "rgba(196, 143, 255, 0.28)"
        secondary_hover_border = "rgba(228, 205, 255, 0.58)"

    else:
        primary_bg = "linear-gradient(135deg, #8B4DFF 0%, #6D38E8 52%, #7D42FF 100%)"
        primary_bg_hover = "linear-gradient(135deg, #9B65FF 0%, #7D42FF 56%, #8B4DFF 100%)"
        primary_border = "rgba(229, 155, 255, 0.68)"
        primary_border_hover = "rgba(240, 190, 255, 0.82)"
        primary_shadow = "0 0 20px rgba(125, 66, 255, 0.34), inset 0 1px 0 rgba(255,255,255,0.13)"
        secondary_border = "rgba(196, 143, 255, 0.28)"
        secondary_hover_border = "rgba(228, 205, 255, 0.58)"

    st.markdown(
        f"""
        <style>
        /* 모든 primary 버튼: 현재 페이지 기준 active 색상 */
        html body .stApp button[data-testid="stBaseButton-primary"],
        html body .stApp button[data-testid="baseButton-primary"],
        html body .stApp button[kind="primary"] {{
            background: {primary_bg} !important;
            background-color: transparent !important;
            color: #F8FFF9 !important;
            border: 1px solid {primary_border} !important;
            box-shadow: {primary_shadow} !important;
        }}

        html body .stApp button[data-testid="stBaseButton-primary"] *,
        html body .stApp button[data-testid="baseButton-primary"] *,
        html body .stApp button[kind="primary"] * {{
            color: #F8FFF9 !important;
            font-weight: 900 !important;
        }}

        html body .stApp button[data-testid="stBaseButton-primary"]:hover,
        html body .stApp button[data-testid="baseButton-primary"]:hover,
        html body .stApp button[kind="primary"]:hover {{
            background: {primary_bg_hover} !important;
            border-color: {primary_border_hover} !important;
        }}

        /* 모든 secondary 버튼 */
        html body .stApp button[data-testid="stBaseButton-secondary"],
        html body .stApp button[data-testid="baseButton-secondary"],
        html body .stApp button[kind="secondary"] {{
            background: rgba(7, 18, 34, 0.86) !important;
            background-color: rgba(7, 18, 34, 0.86) !important;
            color: #EDE5FF !important;
            border: 1px solid {secondary_border} !important;
            box-shadow: none !important;
        }}

        html body .stApp button[data-testid="stBaseButton-secondary"] *,
        html body .stApp button[data-testid="baseButton-secondary"] *,
        html body .stApp button[kind="secondary"] * {{
            color: #EDE5FF !important;
            font-weight: 850 !important;
        }}

        html body .stApp button[data-testid="stBaseButton-secondary"]:hover,
        html body .stApp button[data-testid="baseButton-secondary"]:hover,
        html body .stApp button[kind="secondary"]:hover {{
            background: rgba(13, 34, 42, 0.92) !important;
            border-color: {secondary_hover_border} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_button_theme_by_page()

# =========================================================
# 접힌 사이드바 열기 토글 가시성 개선
# - sidebar가 접힌 상태의 open 토글만 ☰ 형태로 변경
# - sidebar가 열린 상태의 close 토글은 기존 모양 유지
# =========================================================
st.markdown(
    """
    <style>
    /* 접힌 상태에서 보이는 사이드바 열기 토글 컨테이너 */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        position: fixed !important;
        top: 22px !important;
        left: 18px !important;
        width: 42px !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 1000000 !important;
    }

    /* 접힌 상태 열기 버튼 자체 */
    [data-testid="collapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] button {
        width: 42px !important;
        height: 42px !important;
        min-width: 42px !important;
        min-height: 42px !important;
        border-radius: 999px !important;
        border: 1px solid rgba(152, 255, 171, 0.48) !important;
        background:
            radial-gradient(circle at 35% 25%, rgba(152,255,171,0.18), transparent 42%),
            rgba(7, 18, 34, 0.92) !important;
        box-shadow:
            0 0 16px rgba(95, 255, 160, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.10) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        color: transparent !important;
    }

    /* 기존 >> / svg 아이콘은 접힌 상태에서만 숨김 */
    [data-testid="collapsedControl"] button svg,
    [data-testid="collapsedControl"] button img,
    [data-testid="collapsedControl"] button span,
    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="stSidebarCollapsedControl"] button img,
    [data-testid="stSidebarCollapsedControl"] button span {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    /* 접힌 상태 열기 토글을 ☰ 모양으로 표시 */
    [data-testid="collapsedControl"] button::before,
    [data-testid="stSidebarCollapsedControl"] button::before {
        content: "☰";
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 100% !important;
        color: #DFFFF0 !important;
        font-size: 23px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        text-shadow: 0 0 10px rgba(152,255,171,0.32) !important;
        transform: translateY(-1px);
    }

    [data-testid="collapsedControl"] button:hover,
    [data-testid="stSidebarCollapsedControl"] button:hover {
        border-color: rgba(152, 255, 171, 0.72) !important;
        background:
            radial-gradient(circle at 35% 25%, rgba(152,255,171,0.25), transparent 42%),
            rgba(9, 32, 42, 0.96) !important;
        box-shadow:
            0 0 20px rgba(95, 255, 160, 0.26),
            inset 0 1px 0 rgba(255,255,255,0.14) !important;
    }

    /* 열린 상태의 닫기 토글은 건드리지 않음 */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
    section[data-testid="stSidebar"] button[title="Close sidebar"],
    section[data-testid="stSidebar"] button[aria-label="사이드바 닫기"],
    section[data-testid="stSidebar"] button[title="사이드바 닫기"] {
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Streamlit 우측 액션 버튼 최소 숨김
# - toolbar 컨테이너는 숨기지 않음
# - sidebar toggle 안정성 우선
# =========================================================
st.markdown(
    """
    <style>
    /* header 자체와 toolbar 컨테이너는 유지 */
    header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stHeaderActionElements"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background: transparent !important;
        overflow: visible !important;
    }

    /* 명확하게 식별 가능한 우측 액션 버튼만 숨김 */
    header button[title="Share"],
    header button[aria-label="Share"],
    header button[title*="Share"],
    header button[aria-label*="Share"],
    header a[title*="Share"],
    header a[aria-label*="Share"],

    header button[title*="GitHub"],
    header button[aria-label*="GitHub"],
    header a[title*="GitHub"],
    header a[aria-label*="GitHub"],

    header button[title*="Fork"],
    header button[aria-label*="Fork"],
    header a[title*="Fork"],
    header a[aria-label*="Fork"],

    header button[title*="Star"],
    header button[aria-label*="Star"],
    header a[title*="Star"],
    header a[aria-label*="Star"],

    header button[title*="Edit"],
    header button[aria-label*="Edit"],
    header a[title*="Edit"],
    header a[aria-label*="Edit"],

    header button[title*="Deploy"],
    header button[aria-label*="Deploy"],
    header a[title*="Deploy"],
    header a[aria-label*="Deploy"],

    [data-testid="stDeployButton"],
    [data-testid="stAppDeployButton"],
    [data-testid="stStatusWidget"],
    [data-testid="stDecoration"],
    .stDeployButton,
    .stAppDeployButton {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* sidebar open/close 토글은 반드시 유지 */
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


if "bg_html" not in st.session_state:
    random.seed(42)
    stars = []
    for _ in range(90):
        size = random.uniform(1.2, 3.6)
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        delay = random.uniform(0, 7)
        duration = random.uniform(2.2, 6.4)
        opacity = random.uniform(0.55, 0.9)
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
        "ko": "성단",
        "en": "Star Cluster",
        "icon": "⭐",
        "icon_class": "icon-cluster",
        "purpose": '팬덤이 함께 이동할 가능성이 높은<br><span class="purpose-key">그룹형 후보군</span>',
        "criteria": "그룹/소속성, 팬덤 결집, 멤버 단위 이동 가능성",
        "point": "여러 스트리머와 팬덤을 함께 유입시켜 초기 트래픽을 빠르게 확보합니다.",
    },
    {
        "ko": "프로토스타",
        "en": "Protostar",
        "icon": "🌱",
        "icon_class": "icon-protostar",
        "purpose": '현재 규모는 작지만 방송 반응이 좋은<br><span class="purpose-key">성장형 후보군</span>',
        "criteria": "시청자 반응, 채팅, 뷰어십, 팔로워 대비 성과",
        "point": "성장 가능성이 높은 후보를 조기에 발굴해 CIME의 육성 타깃으로 활용합니다.",
    },
    {
        "ko": "위성",
        "en": "Satellite",
        "icon": "🛰️",
        "icon_class": "icon-satellite",
        "purpose": '소속 없이도 방송 성과가 검증된<br><span class="purpose-key">개인형 후보군</span>',
        "criteria": "도네이션, 채팅화력, 평균 시청자, 개인 활동 여부",
        "point": "검증된 개인 방송 화력을 바탕으로 안정적인 콘텐츠와 수익성을 확보합니다.",
    },
    {
        "ko": "슈퍼노바",
        "en": "Supernova",
        "icon": "💥",
        "icon_class": "icon-supernova",
        "purpose": '대중성과 팬덤 규모가 큰<br><span class="purpose-key">간판형 후보군</span>',
        "criteria": "팔로워, 최고 시청자, 유튜브 구독자, 팬덤지수, 방송화력",
        "point": "인지도 높은 스트리머를 통해 플랫폼 주목도와 외부 유입을 높입니다.",
    },
    {
        "ko": "코멧",
        "en": "Comet",
        "icon": "☄️",
        "icon_class": "icon-comet",
        "purpose": '방송 외 다른곳에서 인지도가 높은<br><span class="purpose-key">발견형 후보군</span>',
        "criteria": "유튜브 구독자, X 팔로워, 유튜브/X 유입지수, 플랫폼 대비 외부 체급",
        "point": "외부 팬덤을 CIME으로 연결해 새로운 이용자 유입을 만듭니다.",
    },
]

STAR_SEED_CARDS = [
    {"icon": "search", "title": "후보 수집 기준", "desc": "유튜브 활동 채널 중<br>영입 검토 가능한 후보를 모읍니다."},
    {"icon": "chat", "title": "팬 반응 밀도", "desc": "조회수 대비 좋아요·댓글로<br>팬덤 반응 강도를 봅니다."},
    {"icon": "live", "title": "라이브 전환성", "desc": "콘텐츠 유형과 라이브 신호로<br>방송 전환 가능성을 봅니다."},
    {"icon": "filter", "title": "실전 리스크", "desc": "기관·방송사·팬클립 등<br>영입 제외 대상을 구분합니다."},
    {"icon": "check", "title": "액션버킷", "desc": "점수와 리스크를 함께 보고<br>검토 우선순위를 나눕니다."},
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


def clean_html(markup: str) -> str:
    return "\n".join(line.strip() for line in textwrap.dedent(markup).strip().splitlines())


def html(markup: str) -> None:
    st.markdown(clean_html(markup), unsafe_allow_html=True)

# =========================================================
# 2. 통합 경량 CSS
# =========================================================

st.markdown(
    clean_html(
        """
        <style>
        #MainMenu, footer,
        [data-testid="stDecoration"], [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"], [data-testid="stAppDeployButton"],
        .stDeployButton, .stAppDeployButton,
        button[title="Deploy"], button[aria-label="Deploy"],
        a[title="Deploy"], a[aria-label="Deploy"] {
            display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important;
        }
        :root {
            --cime-sidebar-width: 300px; --cime-sidebar-toggle-top: 22px; --cime-sidebar-toggle-size: 34px; --cime-sidebar-toggle-left: 16px;
            --seed-green: #83F6A0; --seed-purple-line: rgba(154, 98, 255, 0.36);
        }
        header, header[data-testid="stHeader"], [data-testid="stHeader"], header [data-testid="stToolbar"], [data-testid="stToolbar"] {
            display: block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;
            height: 2.4rem !important; min-height: 2.4rem !important; max-height: 2.4rem !important;
            overflow: visible !important; background: transparent !important; z-index: 999990 !important;
        }
        .stApp {
            background:
                radial-gradient(circle at 56% 31%, rgba(127, 47, 255, 0.34), transparent 30%),
                radial-gradient(circle at 78% 7%, rgba(93, 224, 131, 0.075), transparent 24%),
                radial-gradient(circle at 60% 79%, rgba(121, 51, 255, 0.13), transparent 33%),
                linear-gradient(180deg, #050411 0%, #09051C 52%, #050411 100%) !important;
            color: #F8F2FF;
        }
        .stApp::before {
            content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
            background-image:
                radial-gradient(circle, rgba(255,255,255,0.60) 0.7px, transparent 1.2px),
                radial-gradient(circle, rgba(200,168,255,0.32) 0.6px, transparent 1.3px);
            background-size: 72px 72px, 128px 128px; background-position: 0 0, 18px 24px; opacity: 0.08;
        }
        .block-container { position: relative; z-index: 1; max-width: 1380px !important; padding-top: 0 !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-bottom: 2.5rem !important; }
        section[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(7,8,24,.99), rgba(4,6,18,.99)) !important; border-right: 1px solid var(--seed-purple-line) !important; box-shadow: 10px 0 32px rgba(0,0,0,.28) !important; z-index: 999996 !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 4.1rem !important; }
        @media (min-width: 900px) { section[data-testid="stSidebar"][aria-expanded="true"] { flex: 0 0 var(--cime-sidebar-width) !important; width: var(--cime-sidebar-width) !important; min-width: var(--cime-sidebar-width) !important; max-width: var(--cime-sidebar-width) !important; overflow: hidden auto !important; } }
        [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { position: fixed !important; top: var(--cime-sidebar-toggle-top) !important; left: var(--cime-sidebar-toggle-left) !important; width: var(--cime-sidebar-toggle-size) !important; height: var(--cime-sidebar-toggle-size) !important; display: flex !important; align-items: center !important; justify-content: center !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; overflow: visible !important; z-index: 1000000 !important; }
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"], section[data-testid="stSidebar"] button[aria-label="Close sidebar"], section[data-testid="stSidebar"] button[title="Close sidebar"], section[data-testid="stSidebar"] button[aria-label="사이드바 닫기"], section[data-testid="stSidebar"] button[title="사이드바 닫기"] { position: fixed !important; top: var(--cime-sidebar-toggle-top) !important; left: calc(var(--cime-sidebar-width) - var(--cime-sidebar-toggle-size) - 12px) !important; width: var(--cime-sidebar-toggle-size) !important; height: var(--cime-sidebar-toggle-size) !important; min-width: var(--cime-sidebar-toggle-size) !important; min-height: var(--cime-sidebar-toggle-size) !important; display: flex !important; align-items: center !important; justify-content: center !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; z-index: 1000001 !important; margin: 0 !important; }
        [data-testid="collapsedControl"] button, [data-testid="stSidebarCollapsedControl"] button, section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button, section[data-testid="stSidebar"] button[aria-label="Close sidebar"], section[data-testid="stSidebar"] button[title="Close sidebar"], section[data-testid="stSidebar"] button[aria-label="사이드바 닫기"], section[data-testid="stSidebar"] button[title="사이드바 닫기"] { width: var(--cime-sidebar-toggle-size) !important; height: var(--cime-sidebar-toggle-size) !important; border-radius: 999px !important; border: 1px solid rgba(118,242,226,.42) !important; background: rgba(7,22,38,.86) !important; box-shadow: 0 0 14px rgba(95,255,232,.16) !important; }
        .star-layer { position: fixed; left: 300px; top: 0; right: 0; bottom: 0; pointer-events: none; z-index: 0; overflow: hidden; opacity: .72; }
        .twinkle-star { position: absolute; border-radius: 50%; background: white; pointer-events: none; z-index: 0; box-shadow: 0 0 6px rgba(255,255,255,.55), 0 0 12px rgba(198,168,255,.28); animation-name: twinkle; animation-timing-function: ease-in-out; animation-iteration-count: infinite; }
        .twinkle-star:nth-child(3n) { background: #C8A8FF; } .twinkle-star:nth-child(5n) { background: #FF9DF5; }
        @keyframes twinkle { 0%,100% { opacity:.12; transform:scale(.65); } 45% { opacity:var(--max-opacity); transform:scale(1.35); } 65% { opacity:.38; transform:scale(.95); } }
        .orbit-bg { position: fixed; left: 300px; top: 0; right: 0; bottom: 0; z-index: 0; pointer-events: none; opacity: .28; background: linear-gradient(150deg, transparent 15%, rgba(157,88,255,.10) 15.4%, transparent 16.5%), linear-gradient(150deg, transparent 34%, rgba(157,88,255,.07) 34.4%, transparent 35.5%); }
        .sidebar-title { font-size: 22px; font-weight: 900; letter-spacing: 1px; color: #FFF9FF; margin-bottom: 18px; }
        .sidebar-subtitle { font-size: 10px; font-weight: 800; letter-spacing: 1.2px; color: var(--seed-green) !important; margin-bottom: 64px; }
        .sidebar-line { height: 1px; background: rgba(185,147,255,.28); margin: 0 0 24px 0; }
        section[data-testid="stSidebar"] .stButton > button { width: 100%; height: 43px; border-radius: 8px; font-size: 16px; font-weight: 850; letter-spacing: -.3px; margin-bottom: 8px; transition: all .18s ease; }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] { background: linear-gradient(135deg, rgba(28,174,88,.95), rgba(15,105,70,.96)) !important; color: #F5FFF7 !important; border: 1px solid rgba(131,246,160,.42) !important; box-shadow: 0 0 10px rgba(80,220,120,.12), inset 0 1px 0 rgba(255,255,255,.08) !important; }
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] { background: rgba(20,16,48,.78) !important; color: #EDE5FF !important; border: 1px solid rgba(196,143,255,.26) !important; box-shadow: none !important; }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] { background: rgba(18,13,44,.78) !important; border: 1px solid rgba(199,168,255,.28) !important; border-radius: 14px !important; margin: 10px 0 !important; }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary { color: #F8F2FF !important; font-weight: 900 !important; }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stCaptionContainer, section[data-testid="stSidebar"] .stMarkdown p { color: #DED5F8 !important; }
        .main-wrap { position: relative; z-index: 2; text-align: center; }
        .hero-title { font-size: 58px; font-weight: 950; letter-spacing: 9px; line-height: 1; color: #FFF8FF; text-shadow: 0 0 22px rgba(230,195,255,.35); margin: 4px 0 14px; }
        .hero-subtitle { font-size: 19px; font-weight: 750; color: #C6BBD9; margin-bottom: 10px; }
        .block-container:has(.planet-home-wrap) { padding-top: 0 !important; margin-top: 0rem !important; padding-bottom: 2.2rem !important; }
        .planet-home-wrap { transform: translateY(0px) !important; margin-bottom: 0px !important; }
        .planet-area { position: relative; height: 326px; display: flex; align-items: center; justify-content: center; margin-top: -12px; margin-bottom: -6px; }
        .planet-glow { position: absolute; width: 440px; height: 440px; border-radius: 50%; background: radial-gradient(circle, rgba(139,53,255,.45) 0%, rgba(139,53,255,.18) 34%, transparent 68%); filter: blur(14px); }
        .planet-orbit { position: absolute; width: 790px; height: 220px; border: 2px solid rgba(179,93,255,.46); border-radius: 50%; transform: rotate(-2deg); box-shadow: 0 0 26px rgba(179,93,255,.16); }
        .planet-orbit.orbit-2 { width: 625px; height: 176px; border-color: rgba(239,156,255,.42); transform: rotate(1deg); }
        .planet-orbit.orbit-3 { width: 920px; height: 285px; border-color: rgba(125,66,255,.20); transform: rotate(-4deg); }
        .planet { position: relative; width: 300px; height: 300px; border-radius: 50%; background: radial-gradient(circle at 72% 28%, rgba(246,166,255,.55), transparent 20%), radial-gradient(circle at 58% 44%, rgba(147,55,255,.95), transparent 38%), radial-gradient(circle at 42% 58%, rgba(42,8,110,.95), transparent 48%), radial-gradient(circle at 50% 50%, #4812A7 0%, #270066 48%, #08011B 100%); box-shadow: 0 0 34px rgba(246,166,255,.62), 0 0 100px rgba(139,53,255,.55), inset 22px 18px 48px rgba(255,170,255,.20), inset -48px -44px 78px rgba(0,0,0,.55); overflow: hidden; }
        .planet-logo { position: absolute; inset: 0; z-index: 2; display: flex; align-items: center; justify-content: center; font-size: 45px; font-weight: 950; letter-spacing: 5px; color: #FFF8FF; text-shadow: 0 0 10px rgba(255,255,255,.85), 0 0 22px rgba(234,203,255,.9); }
        .satellite { position: absolute; width: 16px; height: 16px; border-radius: 50%; box-shadow: 0 0 18px currentColor; }
        .sat-1 { color:#FF6BF1; background:#FF6BF1; transform:translate(365px,8px); } .sat-2 { color:#FFD45D; background:#FFD45D; transform:translate(-350px,62px); } .sat-3 { color:#95AFFF; background:#95AFFF; transform:translate(-240px,-66px); } .sat-4 { color:#C681FF; background:#C681FF; transform:translate(240px,-62px); } .sat-5 { color:#7DFF8A; background:#7DFF8A; transform:translate(470px,-72px); }
        .mission-card { min-height: 255px; border-radius: 26px; background: rgba(21,16,47,.90); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 0 28px rgba(112,53,255,.18), inset 0 0 28px rgba(255,255,255,.025); padding: 28px 38px 76px; text-align: left; position: relative; overflow: hidden; }
        .mission-card::before { content:""; position:absolute; left:28px; right:28px; top:22px; height:3px; border-radius:3px; }
        .trail-card { border-color: rgba(255,212,93,.42); } .seed-card { border-color: rgba(152,255,171,.38); }
        .trail-card::before { background:#FFD45D; box-shadow: 0 0 16px rgba(255,212,93,.55); } .seed-card::before { background:#98FFAB; box-shadow: 0 0 16px rgba(152,255,171,.45); }
        .card-head { display:flex; align-items:center; gap:24px; margin-top:20px; margin-bottom:26px; } .icon-box { width:66px; height:66px; border-radius:18px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
        .trail-icon-box { background: rgba(255,212,93,.12); border: 1px solid rgba(255,212,93,.34); } .seed-icon-box { background: rgba(152,255,171,.10); border: 1px solid rgba(152,255,171,.30); }
        .card-title { font-size: 40px; font-weight: 950; color:#FFF9FF; line-height:1.05; } .card-en { font-size:27px; font-weight:900; margin-top:6px; } .trail-en { color:#FFD45D; } .seed-en { color:#98FFAB; }
        .card-desc { font-size:19px; line-height:1.7; color:#D9CFE8; font-weight:560; } .trail-point,.trail-soft-point { color:#FFD45D; font-weight:850; } .seed-point,.seed-soft-point { color:#98FFAB; font-weight:750; }
        section.main .stButton > button { width:100%; height:44px; border-radius:15px; background:rgba(255,255,255,.035) !important; color:#FFF9FF !important; border:1px solid rgba(255,255,255,.13) !important; font-size:16px; font-weight:850; margin-top:-60px; position:relative; z-index:20; }
        .detail-box { position:relative; z-index:3; max-width:1380px; margin:42px auto 0; border-radius:26px; background:linear-gradient(135deg, rgba(21,16,47,.94), rgba(16,12,34,.94)); border:1px solid rgba(196,143,255,.34); box-shadow:0 0 36px rgba(125,66,255,.20), inset 0 0 30px rgba(255,255,255,.025); padding:42px 48px 48px; text-align:left; }
        .detail-phase-head { display:flex; align-items:center; gap:18px; margin-bottom:24px; } .detail-phase-icon { width:54px; height:54px; display:flex; align-items:center; justify-content:center; flex:0 0 auto; } .detail-phase-title-row { display:flex; align-items:baseline; gap:12px; line-height:1.05; } .detail-phase-ko { font-size:34px; font-weight:950; letter-spacing:-1.1px; } .detail-phase-en { font-size:22px; font-weight:850; color:rgba(255,255,255,.90); } .detail-phase-trail .detail-phase-ko { color:#FFD45D; } .detail-phase-seed .detail-phase-ko { color:#98FFAB; }
        .detail-title { font-size:34px; line-height:1.35; font-weight:950; color:#FFF9FF; margin-bottom:24px; } .detail-text { font-size:19px; line-height:1.9; color:#D9CFE8; font-weight:520; margin-bottom:34px; word-break:keep-all; }
        .segment-grid,.seed-grid { display:grid; gap:18px; align-items:stretch; grid-template-columns:repeat(5,minmax(0,1fr)); }
        .segment-card,.seed-step-card { position:relative; overflow:hidden; border-radius:18px; padding:28px 20px 26px; background:rgba(255,255,255,.038); border:1px solid rgba(255,255,255,.12); min-height:250px; display:flex; flex-direction:column; align-items:center; text-align:center; }
        .seed-step-card { border-color:rgba(152,255,171,.18); background:radial-gradient(circle at 50% 0%, rgba(152,255,171,.085), transparent 42%), rgba(255,255,255,.038); }
        .segment-head { display:flex; flex-direction:column; align-items:center; justify-content:flex-start; min-height:132px; margin-bottom:8px; } .segment-icon-badge { width:58px; height:58px; border-radius:18px; display:flex; align-items:center; justify-content:center; margin:0 auto 15px; font-size:27px; border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.05); }
        .icon-cluster { color:#FFD45D; background:rgba(255,212,93,.10); border-color:rgba(255,212,93,.25); } .icon-protostar { color:#98FFAB; background:rgba(152,255,171,.10); border-color:rgba(152,255,171,.25); } .icon-satellite { color:#8FB8FF; background:rgba(143,184,255,.10); border-color:rgba(143,184,255,.25); } .icon-supernova { color:#FF7AC8; background:rgba(255,122,200,.10); border-color:rgba(255,122,200,.25); } .icon-comet { color:#FF9E5E; background:rgba(255,158,94,.10); border-color:rgba(255,158,94,.25); }
        .segment-ko,.seed-title { color:#FFF9FF; font-size:20px; line-height:1.35; font-weight:950; margin-bottom:8px; } .segment-en { color:#F08CFF; font-size:13px; font-weight:950; text-align:center; }
        .segment-purpose { color:rgba(255,255,255,.82); font-size:14px; line-height:1.55; font-weight:760; padding:12px 13px; margin-bottom:20px; border-radius:12px; background:rgba(240,140,255,.10); border:1px solid rgba(240,140,255,.22); min-height:74px; display:flex; align-items:center; justify-content:center; text-align:center; word-break:keep-all; }
        .purpose-key { display:inline-block; margin-top:2px; color:#fff; font-size:16px; font-weight:950; } .field-label { color:#F0B5FF; font-size:12px; font-weight:950; margin-top:12px; margin-bottom:6px; } .field-value { color:rgba(255,255,255,.76); font-size:14px; line-height:1.7; word-break:keep-all; }
        .seed-desc { color:rgba(255,255,255,.76); font-size:15px; line-height:1.65; font-weight:560; word-break:keep-all; min-height:50px; }
        .seed-icon-orbit { width:82px; height:82px; border-radius:999px; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; background:radial-gradient(circle, rgba(152,255,171,.18) 0%, rgba(152,255,171,.06) 58%, transparent 72%); border:1px solid rgba(152,255,171,.28); }
        .seed-icon-badge { width:56px; height:56px; display:flex; align-items:center; justify-content:center; position:relative; background:transparent; } .seed-icon-badge::before,.seed-icon-badge::after { content:""; position:absolute; box-sizing:border-box; }
        .seed-icon-search::before { width:28px; height:28px; border:3.4px solid #98FFAB; border-radius:50%; left:10px; top:9px; } .seed-icon-search::after { width:20px; height:3.4px; background:#98FFAB; border-radius:999px; left:33px; top:35px; transform:rotate(45deg); }
        .seed-icon-chat::before { width:34px; height:24px; border:3px solid #98FFAB; border-radius:9px; left:10px; top:14px; } .seed-icon-chat::after { width:10px; height:10px; border-right:3px solid #98FFAB; border-bottom:3px solid #98FFAB; left:20px; top:34px; transform:rotate(45deg); }
        .seed-icon-live::before { width:30px; height:22px; border:3px solid #98FFAB; border-radius:7px; left:8px; top:17px; } .seed-icon-live::after { width:15px; height:15px; border-top:3px solid #98FFAB; border-right:3px solid #98FFAB; left:34px; top:20px; transform:rotate(45deg); }
        .seed-icon-filter::before { width:38px; height:30px; border-top:4px solid #98FFAB; border-left:4px solid transparent; border-right:4px solid transparent; left:9px; top:13px; } .seed-icon-filter::after { width:8px; height:20px; background:#98FFAB; border-radius:999px; left:24px; top:28px; }
        .seed-icon-check::before { width:36px; height:36px; border:3.4px solid #98FFAB; border-radius:10px; left:10px; top:10px; } .seed-icon-check::after { width:21px; height:12px; border-left:4.5px solid #98FFAB; border-bottom:4.5px solid #98FFAB; left:18px; top:21px; transform:rotate(-45deg); }
        .seed-mini-line { width:28px; height:2px; border-radius:999px; background:rgba(152,255,171,.92); margin:0 auto 14px; }
        .empty-guide { position:relative; z-index:3; margin-top:34px; font-size:15px; color:rgba(191,181,213,.72); text-align:center; } .page-panel { position:relative; z-index:3; border-radius:22px; background:rgba(21,16,47,.86); border:1px solid rgba(196,143,255,.26); padding:36px 40px; margin-top:30px; color:rgba(255,255,255,.78); line-height:1.8; }
        .trail-spark-icon,.seed-search-icon { position:relative; width:56px; height:56px; } .trail-spark-icon { color:#FFD45D; } .seed-search-icon { color:#98FFAB; } .trail-line { position:absolute; left:5px; height:3px; border-radius:999px; background:currentColor; } .trail-line-1 { top:22px; width:23px; } .trail-line-2 { top:31px; width:16px; opacity:.72; } .trail-line-3 { top:27px; left:13px; width:18px; opacity:.48; } .trail-star { position:absolute; color:currentColor; line-height:1; } .trail-star-main { left:30px; top:15px; font-size:30px; } .trail-star-small { left:23px; top:6px; font-size:14px; } .trail-star-tiny { left:17px; top:38px; font-size:10px; } .trail-dot { position:absolute; width:3px; height:3px; border-radius:50%; background:currentColor; } .trail-dot-1 { left:44px; top:11px; } .trail-dot-2 { left:8px; top:40px; opacity:.75; }
        .seed-lens { position:absolute; left:7px; top:7px; width:30px; height:30px; border:4px solid currentColor; border-radius:50%; box-sizing:border-box; } .seed-handle { position:absolute; left:33px; top:35px; width:18px; height:4px; background:currentColor; border-radius:999px; transform:rotate(45deg); transform-origin:left center; } .seed-star-core { position:absolute; left:15px; top:12px; font-size:18px; line-height:1; font-weight:900; } .seed-sparkle-1 { position:absolute; left:37px; top:7px; font-size:12px; line-height:1; } .seed-sparkle-2 { position:absolute; left:4px; top:35px; font-size:9px; line-height:1; opacity:.78; } .seed-dot-1,.seed-dot-2 { position:absolute; width:3px; height:3px; border-radius:50%; background:currentColor; } .seed-dot-1 { left:44px; top:18px; } .seed-dot-2 { left:11px; top:43px; opacity:.8; }
        .starseed-loading-wrap { width:min(980px,92vw); margin:22vh auto 0; padding:34px 38px; border-radius:26px; border:1px solid rgba(118,242,226,.28); background:radial-gradient(circle at 16% 36%, rgba(95,255,232,.16), transparent 28%), radial-gradient(circle at 86% 20%, rgba(144,94,255,.24), transparent 30%), linear-gradient(145deg, rgba(9,22,42,.92), rgba(12,8,35,.92)); box-shadow:0 24px 72px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.08); text-align:center; position:relative; overflow:hidden; } .starseed-loading-orb { width:74px; height:74px; margin:0 auto 18px; border-radius:50%; background:radial-gradient(circle at 36% 30%, #fff 0 7%, #8cffb3 13%, #29d976 38%, #6b42ff 100%); box-shadow:0 0 18px rgba(140,255,179,.28), 0 0 42px rgba(107,66,255,.20); position:relative; z-index:1; } .starseed-loading-orb::after { content:"✦"; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:white; font-size:30px; } .starseed-loading-title { position:relative; z-index:1; font-size:32px; font-weight:950; color:#f6fffb; margin-bottom:10px; } .starseed-loading-sub { position:relative; z-index:1; font-size:15px; line-height:1.65; color:#b8c9d8; } .starseed-loading-steps { position:relative; z-index:1; display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-top:22px; } .starseed-loading-chip { padding:7px 12px; border-radius:999px; background:rgba(95,255,232,.075); border:1px solid rgba(95,255,232,.18); color:#d9fff8; font-size:12px; font-weight:800; }
        .block-container:has(.starseed-board) { padding-top:0 !important; margin-top:-.6rem !important; padding-bottom:2.5rem !important; } .starseed-board { width:100%; padding:0 0 18px; margin-top:10px !important; position:relative; z-index:2; } .board-hero,.board-hero-compact { display:grid !important; grid-template-columns:minmax(0,1fr) 560px !important; column-gap:22px !important; align-items:center !important; margin:0 0 10px !important; padding:0 !important; } .board-head-left { display:grid !important; grid-template-columns:86px minmax(0,1fr) !important; gap:20px !important; min-height:88px !important; align-items:center !important; } .board-title-icon { width:72px !important; height:72px !important; border-radius:12px !important; display:flex !important; align-items:center !important; justify-content:center !important; background:radial-gradient(circle at 45% 30%, rgba(131,246,160,.14), transparent 56%), rgba(12,20,38,.86) !important; border:2px solid rgba(238,235,255,.82) !important; box-shadow:0 0 10px rgba(131,246,160,.10), inset 0 1px 0 rgba(255,255,255,.08) !important; overflow:hidden !important; } .board-title-icon .seed-search-icon { transform:scale(1.02) !important; transform-origin:center center !important; } .board-title,.board-title-ko { font-size:39px !important; font-weight:950 !important; letter-spacing:-.055em !important; line-height:1.03 !important; color:#FFF8FF !important; margin:0 0 7px !important; text-shadow:0 1px 0 rgba(255,255,255,.10) !important; display:flex !important; align-items:baseline !important; gap:10px !important; white-space:nowrap !important; } .board-title span { color:var(--seed-green) !important; font-size:31px !important; font-weight:950 !important; letter-spacing:-.035em !important; text-shadow:0 0 4px rgba(131,246,160,.10) !important; } .board-title-accent-line { width:235px !important; height:2px !important; margin:0 0 9px 2px !important; border-radius:999px !important; background:linear-gradient(90deg, rgba(126,255,153,.84) 0%, rgba(126,255,153,.48) 42%, rgba(126,255,153,.14) 78%, rgba(126,255,153,0) 100%) !important; } .board-subtitle { margin:0 !important; font-size:14.2px !important; font-weight:720 !important; line-height:1.45 !important; letter-spacing:-.035em !important; color:#D8D0E7 !important; text-align:left !important; white-space:nowrap !important; }
        .board-info-card { display:grid; grid-template-columns:54px minmax(0,1fr) !important; gap:14px !important; align-items:center; min-height:76px !important; width:100% !important; border-radius:12px !important; border:1px solid rgba(131,246,160,.30) !important; background:radial-gradient(circle at 9% 50%, rgba(131,246,160,.10), transparent 28%), linear-gradient(135deg, rgba(11,35,28,.74), rgba(18,16,45,.82)) !important; box-shadow:0 10px 24px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.06) !important; padding:14px 22px 14px 18px !important; box-sizing:border-box !important; overflow:visible !important; } .board-info-icon { width:42px !important; height:42px !important; border-radius:999px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:20px !important; background:radial-gradient(circle at 34% 26%, #F1FFF4, #58E984 48%, #11894D 100%) !important; box-shadow:0 0 12px rgba(88,233,132,.16) !important; } .board-info-title { color:#F5FFF7 !important; font-size:13.2px !important; font-weight:950 !important; margin-bottom:4px !important; white-space:normal !important; } .board-info-text { color:#D6E5D8 !important; font-size:12px !important; line-height:1.45 !important; word-break:keep-all !important; overflow-wrap:break-word !important; white-space:normal !important; overflow:visible !important; text-overflow:unset !important; }
        .board-kpi-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px !important; margin:12px 0 !important; } .board-kpi-card { position:relative; overflow:hidden; display:grid; grid-template-columns:52px 1fr; gap:13px; align-items:center; min-height:82px; border-radius:14px; padding:13px 16px; border:1px solid rgba(131,246,160,.16) !important; background:radial-gradient(circle at 10% 28%, rgba(131,246,160,.055), transparent 32%), linear-gradient(180deg, rgba(14,18,43,.86), rgba(6,11,27,.94)) !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.045), 0 12px 26px rgba(0,0,0,.24) !important; } .board-kpi-icon { width:48px; height:48px; border-radius:999px; display:flex; align-items:center; justify-content:center; font-size:23px; background:radial-gradient(circle at 34% 24%, rgba(255,255,255,.28), rgba(48,190,102,.78) 50%, rgba(12,78,56,.92) 100%) !important; box-shadow:0 0 10px rgba(80,255,146,.16) !important; } .board-kpi-label { color:#D5E6DD !important; font-size:12px; font-weight:850; margin-bottom:3px; } .board-kpi-value { color:#fff !important; font-size:25px; font-weight:950; line-height:1.1; letter-spacing:-.03em; } .board-kpi-delta { display:inline-flex; align-items:center; gap:2px; margin-top:3px; font-size:10px; font-weight:900; border-radius:999px; padding:2px 7px; background:rgba(255,255,255,.05); } .board-kpi-delta.up { color:#ff7b86; background:rgba(255,91,108,.12); } .board-kpi-delta.down { color:#72b8ff; background:rgba(79,150,255,.12); } .board-kpi-delta.flat { color:#c4bad8; background:rgba(185,170,230,.10); } .board-kpi-note { display:inline-block; margin-left:6px; color:#92A995 !important; font-size:10px; font-weight:700; }
        .board-panel { border-radius:16px; border:1px solid rgba(131,246,160,.16) !important; background:linear-gradient(180deg, rgba(14,18,43,.86), rgba(6,11,27,.94)) !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.045), 0 12px 26px rgba(0,0,0,.24) !important; padding:12px 14px; } .board-panel-title { display:flex; align-items:center; gap:8px; color:#f5efff; font-size:15px; font-weight:950; margin:0 0 10px; } .top5-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px !important; } .mini-candidate-card { position:relative; min-height:92px; border-radius:12px; border:1px solid rgba(131,246,160,.16) !important; background:radial-gradient(circle at 22% 48%, rgba(131,246,160,.055), transparent 42%), linear-gradient(180deg, rgba(14,20,45,.86), rgba(8,12,31,.97)) !important; padding:13px 12px 11px 104px; overflow:hidden; display:flex; flex-direction:column; justify-content:center; box-sizing:border-box; } .mini-rank { position:absolute; top:9px; left:9px; width:20px; height:20px; border-radius:5px; display:flex; align-items:center; justify-content:center; color:#ffd86b; border:1px solid rgba(255,216,107,.75); background:rgba(42,29,72,.78); font-size:11px; font-weight:950; } .mini-avatar-wrap { position:absolute; left:38px; top:50%; transform:translateY(-50%); width:54px; height:54px; border-radius:999px; overflow:hidden; background:radial-gradient(circle at 32% 28%, #fff, #8b5cf6 42%, #25154d 100%); border:2px solid rgba(131,246,160,.38) !important; box-shadow:0 0 12px rgba(131,246,160,.12) !important; } .mini-avatar-wrap img { width:100%; height:100%; object-fit:cover; display:block; } .mini-avatar-fallback { width:100%; height:100%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:950; font-size:20px; } .mini-name { color:#fff; font-size:13.5px; font-weight:950; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:1.15; max-width:100%; } .mini-name a { color:inherit; text-decoration:none; } .mini-score { color:#fff; font-size:17px; font-weight:950; margin-top:3px; line-height:1.1; white-space:nowrap; letter-spacing:-.02em; } .mini-stage { display:inline-flex; align-items:center; justify-content:center; width:fit-content; max-width:94px; color:#DFFFF0 !important; background:linear-gradient(135deg, rgba(26,158,91,.86), rgba(9,88,62,.88)) !important; border:1px solid rgba(131,246,160,.28) !important; border-radius:999px; padding:3px 9px; font-size:10px; font-weight:900; margin-top:5px; white-space:nowrap; }
        .priority-header-title,.graph-header-title { color:#fff7ff !important; font-size:24px !important; font-weight:950 !important; letter-spacing:-.04em !important; line-height:38px !important; white-space:nowrap !important; margin:0 !important; padding:0 !important; text-shadow:0 0 8px rgba(131,246,160,.12) !important; } div[data-testid="column"] .stButton > button[kind="primary"], button[kind="primary"][data-testid="baseButton-primary"] { min-height:38px !important; height:38px !important; padding:6px 16px !important; border-radius:999px !important; font-size:13px !important; font-weight:900 !important; white-space:nowrap !important; background:linear-gradient(135deg, rgba(26,158,91,.92), rgba(12,92,65,.94)) !important; border-color:rgba(131,246,160,.32) !important; color:#F7FFF8 !important; box-shadow:none !important; } div[data-testid="column"] .stButton > button[kind="secondary"], button[kind="secondary"][data-testid="baseButton-secondary"] { min-height:38px !important; height:38px !important; padding:6px 16px !important; border-radius:999px !important; font-size:13px !important; font-weight:900 !important; white-space:nowrap !important; background:rgba(7,18,34,.84) !important; border-color:rgba(131,246,160,.20) !important; color:#EAF7EF !important; box-shadow:none !important; }
        .priority-table-panel { margin-top:0 !important; padding-top:10px !important; min-height:228px; } .priority-table { width:100%; border-collapse:collapse; overflow:hidden; border-radius:11px; table-layout:fixed; font-size:11px; } .priority-table th { background:rgba(255,255,255,.075) !important; color:#E4E9E2 !important; font-weight:900; padding:7px 8px; border-bottom:1px solid rgba(131,246,160,.16) !important; text-align:center; } .priority-table td { color:#f7f4ff; padding:4px 8px; border-bottom:1px solid rgba(131,246,160,.075) !important; text-align:center; font-weight:740; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; } .priority-table td.name { text-align:left; font-weight:900; } .priority-score { color:#fff !important; font-weight:950 !important; }
        .tag-pill { display:inline-flex; align-items:center; justify-content:center; border-radius:999px; min-width:54px; max-width:118px; padding:3px 8px; font-size:10px; font-weight:950; line-height:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:#fff; box-shadow:inset 0 1px 0 rgba(255,255,255,.18); } .seg-music { background:linear-gradient(135deg,#7b5cff,#5840c6); } .seg-visual { background:linear-gradient(135deg,#d64b92,#963069); } .seg-virtual { background:linear-gradient(135deg,#d69428,#9d5f12); } .seg-game { background:linear-gradient(135deg,#2a9dd6,#1768a5); } .seg-subculture { background:linear-gradient(135deg,#ff9c55,#c96a28); } .seg-etc { background:linear-gradient(135deg,#7d8798,#4c5568); } .action-immediate { background:linear-gradient(135deg, rgba(26,158,91,.86), rgba(9,88,62,.88)) !important; color:#dffff8; border:1px solid rgba(131,246,160,.28) !important; } .action-watch { background:linear-gradient(135deg,#6f83ee,#4350a5); } .action-verify { background:linear-gradient(135deg,#d75d86,#8e2d56); } .action-hold { background:linear-gradient(135deg,#7b8798,#4b5363); }
        .stSelectbox > div > div { background:rgba(6,18,26,.92) !important; border:1px solid rgba(131,246,160,.20) !important; border-radius:13px !important; box-shadow:none !important; } .candidate-select-top-spacer { height:1px !important; min-height:1px !important; margin:0 !important; padding:0 !important; }
        .detail-panel-v2 { min-height:286px !important; border:1px solid rgba(131,246,160,.22) !important; background:radial-gradient(circle at 9% 45%, rgba(131,246,160,.055), transparent 30%), linear-gradient(180deg, rgba(8,25,27,.82), rgba(8,13,31,.96)) !important; } .detail-card-inner-v2 { display:grid !important; grid-template-columns:124px minmax(0,1fr) !important; grid-template-areas:"avatar content" "reason reason" !important; gap:14px 16px !important; align-items:center !important; } .detail-avatar-area { grid-area:avatar; } .detail-content-area { grid-area:content; min-width:0; } .detail-reason-bottom { grid-area:reason; } .detail-avatar-big { width:108px; height:108px; border-radius:999px; overflow:hidden; border:3px solid rgba(131,246,160,.38) !important; box-shadow:0 0 12px rgba(131,246,160,.12) !important; margin:0 auto; background:radial-gradient(circle at 32% 28%, #fff, #9c6aff 43%, #25154d 100%); } .detail-avatar-big img { width:100%; height:100%; object-fit:cover; display:block; } .detail-name-row { display:flex; gap:8px; align-items:center; margin-bottom:10px; flex-wrap:nowrap !important; min-width:0 !important; } .detail-name-main { flex:1 1 auto !important; min-width:0 !important; max-width:100% !important; color:#fff; font-size:20px; font-weight:950; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; } .detail-name-main a { color:inherit; text-decoration:none; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; } .detail-metric-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; } .detail-metric-box { border:1px solid rgba(131,246,160,.18) !important; background:rgba(131,246,160,.025) !important; border-radius:8px; padding:7px 9px; min-height:48px; } .detail-metric-label { color:#C5DCCB !important; font-size:10px; font-weight:850; } .detail-metric-value { color:#fff; font-size:18px; font-weight:950; line-height:1.2; margin-top:2px; } .reason-panel { border:1px solid rgba(131,246,160,.18) !important; background:rgba(131,246,160,.025) !important; border-radius:12px; padding:10px 13px !important; min-height:auto !important; } .reason-title { color:#F3FFF5 !important; font-size:12px; font-weight:950; margin-bottom:8px; } .reason-bullet { display:inline-block; margin-right:14px; white-space:nowrap; color:#DDEBDD !important; font-size:11px; line-height:1.55; } .reason-bullet::before { content:'●'; color:var(--seed-green) !important; margin-right:7px; }
        .graph-explain { padding:16px 8px 4px !important; min-height:258px !important; box-sizing:border-box !important; } .graph-explain-title { color:#fff8ff !important; font-size:22px !important; font-weight:950 !important; line-height:1.25 !important; margin:0 0 18px !important; letter-spacing:-.04em !important; text-shadow:0 0 8px rgba(131,246,160,.12) !important; } .graph-explain-text { color:#c9c0dc !important; font-size:13.5px !important; line-height:1.9 !important; font-weight:650 !important; word-break:keep-all !important; max-width:245px !important; } .stPlotlyChart { min-height:282px !important; border-radius:13px !important; border:1px solid rgba(131,246,160,.16) !important; background:rgba(6,12,25,.66) !important; padding:8px 10px !important; box-shadow:none !important; } div[data-testid="stExpander"] { border-color:rgba(131,246,160,.16) !important; background:rgba(8,18,34,.78) !important; border-radius:14px !important; } .explain-box,.guide-box,.reason-box { border:1px solid rgba(131,246,160,.16) !important; background:rgba(7,20,28,.70) !important; border-radius:14px; padding:14px 16px; color:#d8deed; font-size:14px; line-height:1.65; }
        @media (max-width:1200px) { .board-hero,.board-hero-compact,.mid-grid,.graph-grid { grid-template-columns:1fr !important; } .board-kpi-grid,.top5-grid,.segment-grid,.seed-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .board-subtitle,.board-info-text { white-space:normal !important; } }
        @media (max-width:780px) { .board-kpi-grid,.top5-grid,.segment-grid,.seed-grid { grid-template-columns:1fr; } .board-title,.board-title-ko { font-size:30px !important; } .board-title span { font-size:24px !important; } .hero-title { font-size:42px; letter-spacing:5px; } }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

st.markdown(f'<div class="star-layer">{st.session_state.bg_html}</div><div class="orbit-bg"></div>', unsafe_allow_html=True)


# =========================================================
# 사이드바 페이지별 active 색상 분리
# - 홈: 보라색
# - 스타시드: 초록색
# - 스타트레일: 보라/골드 계열
# =========================================================
current_page_for_sidebar = st.session_state.get("page", "대시보드 홈")

if current_page_for_sidebar == "스타시드":
    sidebar_primary_css = """
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #22C55E 0%, #168557 100%) !important;
        color: #F5FFF7 !important;
        border: 1px solid rgba(152, 255, 171, 0.62) !important;
        box-shadow:
            0 0 18px rgba(72, 255, 135, 0.22),
            inset 0 1px 0 rgba(255,255,255,0.14) !important;
    }
    """
elif current_page_for_sidebar == "스타트레일":
    sidebar_primary_css = """
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #7D42FF 0%, #4B2AA8 58%, #B88A2E 100%) !important;
        color: #FFF9FF !important;
        border: 1px solid rgba(255, 212, 93, 0.58) !important;
        box-shadow:
            0 0 18px rgba(255, 212, 93, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.12) !important;
    }
    """
else:
    sidebar_primary_css = """
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #8B4DFF 0%, #6D38E8 52%, #7D42FF 100%) !important;
        color: #FFF9FF !important;
        border: 1px solid rgba(229, 155, 255, 0.68) !important;
        box-shadow:
            0 0 20px rgba(125, 66, 255, 0.34),
            inset 0 1px 0 rgba(255,255,255,0.13) !important;
    }
    """

st.markdown(
    f"""
    <style>
    /* 사이드바 공통 비활성 버튼 */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {{
        background: rgba(24, 17, 54, 0.88) !important;
        color: #EDE5FF !important;
        border: 1px solid rgba(196, 143, 255, 0.28) !important;
        box-shadow: none !important;
    }}

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {{
        background: rgba(42, 27, 88, 0.96) !important;
        color: #FFFFFF !important;
        border-color: rgba(228, 205, 255, 0.58) !important;
        box-shadow: 0 0 14px rgba(125, 66, 255, 0.16) !important;
    }}

    /* 현재 페이지 active 버튼 */
    {sidebar_primary_css}

    /* 버튼 안쪽 텍스트/아이콘 색상 강제 */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] * {{
        color: inherit !important;
        font-weight: 900 !important;
    }}

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] *,
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] * {{
        color: inherit !important;
        font-weight: 850 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
# =========================================================
# 3. 사이드바 네비게이션
# =========================================================

with st.sidebar:
    html("""
    <div class="sidebar-title">CIME</div>
    <div class="sidebar-subtitle">MISSION CONTROL</div>
    <div class="sidebar-line"></div>
    """)

    NAV_ITEMS = {
        "대시보드 홈": {"label": "대시보드 홈", "icon": ":material/dashboard:"},
        "스타트레일": {"label": "스타트레일", "icon": ":material/auto_awesome:"},
        "스타시드": {"label": "스타시드", "icon": ":material/search:"},
    }

    def _go_page(page_name: str) -> None:
        if st.session_state.get("page") != page_name:
            st.session_state.page = page_name
            st.session_state.card = None
        else:
            st.session_state.card = None

    for page, item in NAV_ITEMS.items():
        st.button(
            item["label"],
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if st.session_state.page == page else "secondary",
            icon=item["icon"],
            on_click=_go_page,
            args=(page,),
        )

# =========================================================
# 4. 홈 / 스타트레일 렌더링
# =========================================================

def render_planet_home():
    html("""
    <div class="main-wrap planet-home-wrap">
        <div class="hero-title">CIME STREAM PLANET</div>
        <div class="hero-subtitle">데이터 우주에서 다음 플랫폼의 중심 별을 찾다</div>
        <div class="planet-area">
            <div class="planet-glow"></div>
            <div class="planet-orbit orbit-3"></div>
            <div class="planet-orbit"></div>
            <div class="planet-orbit orbit-2"></div>
            <div class="satellite sat-1"></div><div class="satellite sat-2"></div><div class="satellite sat-3"></div><div class="satellite sat-4"></div><div class="satellite sat-5"></div>
            <div class="planet"><div class="planet-logo">CIME</div></div>
        </div>
    </div>
    """)


def render_mission_cards():
    col1, col2 = st.columns(2, gap="large")
    with col1:
        html(f"""
        <div class="mission-card trail-card">
            <div class="card-head"><div class="icon-box trail-icon-box">{TRAIL_ICON_HTML}</div><div><div class="card-title">스타트레일</div><div class="card-en trail-en">Star Trail</div></div></div>
            <div class="card-desc">기존 플랫폼에서 검증된 <span class="trail-point">성과와 팬덤</span>을 기반으로,<br><span class="trail-point">CIME 영입 우선 후보군</span>을 탐색합니다.</div>
        </div>
        """)
        if st.button("스타트레일 자세히 보기", key="btn_startrail", use_container_width=True):
            st.session_state.card = None if st.session_state.card == "trail" else "trail"
    with col2:
        html(f"""
        <div class="mission-card seed-card">
            <div class="card-head"><div class="icon-box seed-icon-box">{SEED_ICON_HTML}</div><div><div class="card-title">스타시드</div><div class="card-en seed-en">Star Seed</div></div></div>
            <div class="card-desc">유튜브 기반 <span class="seed-point">성장 잠재력</span>과 <span class="seed-point">라이브 전환 가능성</span>을 분석해,<br><span class="seed-point">차세대 후보군</span>을 발굴합니다.</div>
        </div>
        """)
        if st.button("스타시드 자세히 보기", key="btn_starseed", use_container_width=True):
            st.session_state.card = None if st.session_state.card == "seed" else "seed"


def render_startrail_detail():
    cards = "".join([
        f'<div class="segment-card"><div class="segment-head"><div class="segment-icon-badge {seg["icon_class"]}">{seg["icon"]}</div><div class="segment-ko">{seg["ko"]}</div><div class="segment-en">{seg["en"]}</div></div><div class="segment-purpose">{seg["purpose"]}</div><div class="field-label">주요 판단 기준</div><div class="field-value">{seg["criteria"]}</div><div class="field-label">CIME 활용 포인트</div><div class="field-value">{seg["point"]}</div></div>'
        for seg in STARTRAIL_SEGMENTS
    ])
    st.markdown(
        '<div class="detail-box">'
        f'<div class="detail-phase-head detail-phase-trail"><div class="detail-phase-icon">{TRAIL_ICON_HTML}</div><div class="detail-phase-title-row"><span class="detail-phase-ko">스타트레일</span><span class="detail-phase-en">Star Trail</span></div></div>'
        '<div class="detail-title">기존 플랫폼 성과를 기준으로 CIME 영입 후보군을 선별하는 단계</div>'
        '<div class="detail-text">스타트레일은 <span class="trail-soft-point">기존 플랫폼에서 이미 활동 성과가 확인된 스트리머</span>를 분석합니다.<br>대중성, 방송화력, 팬덤결집력, 수익성, 외부유입가능성을 함께 비교해<br><span class="trail-soft-point">CIME 영입 우선순위가 높은 후보군</span>을 찾습니다.</div>'
        f'<div class="segment-grid">{cards}</div></div>',
        unsafe_allow_html=True,
    )


def render_starseed_detail():
    cards = "".join([
        f'<div class="seed-step-card"><div class="seed-icon-orbit"><div class="seed-icon-badge seed-icon-{step["icon"]}"></div></div><div class="seed-title">{step["title"]}</div><div class="seed-mini-line"></div><div class="seed-desc">{step["desc"]}</div></div>'
        for step in STAR_SEED_CARDS
    ])
    st.markdown(
        '<div class="detail-box">'
        f'<div class="detail-phase-head detail-phase-seed"><div class="detail-phase-icon">{SEED_ICON_HTML}</div><div class="detail-phase-title-row"><span class="detail-phase-ko">스타시드</span><span class="detail-phase-en">Star Seed</span></div></div>'
        '<div class="detail-title">유튜브에서 CIME가 실제로 검토할 후보를 찾는 단계</div>'
        '<div class="detail-text">스타시드는 <span class="seed-soft-point">유튜브에서 활동 중인 크리에이터</span> 중 단순 인기 채널이 아니라 실제 영입 검토가 가능한 후보를 분석합니다.<br>팬 반응 밀도, 라이브 전환성, 실전 리스크, 액션버킷을 함께 확인해<br><span class="seed-soft-point">CIME가 우선 검토할 예비 스트리머 후보군</span>을 정리합니다.</div>'
        f'<div class="seed-grid">{cards}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    clean_html(
        """
        <style>
        /* =====================================================
           STAR SEED 5단계 카드 아이콘 교체
           - 스타일/카드 구조는 유지
           - 아이콘만 두 번째 캡처 기준으로 변경
        ===================================================== */

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
            filter: drop-shadow(0 0 6px rgba(152,255,171,0.22));
        }

        /* 01 후보 수집 기준: 돋보기 */
        .seed-icon-search::before {
            width: 29px;
            height: 29px;
            border: 3.6px solid #98FFAB;
            border-radius: 50%;
            left: 9px;
            top: 9px;
        }

        .seed-icon-search::after {
            width: 21px;
            height: 3.6px;
            background: #98FFAB;
            border-radius: 999px;
            left: 32px;
            top: 35px;
            transform: rotate(45deg);
            transform-origin: left center;
        }

        /* 02 팬 반응 밀도: 말풍선 + 하트 */
        .seed-icon-chat::before {
            width: 58px;
            height: 58px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223.1%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%2013h24a3.2%203.2%200%200%201%203.2%203.2v12.2a3.2%203.2%200%200%201-3.2%203.2H22.3l-7.4%205.2v-5.2H12a3.2%203.2%200%200%201-3.2-3.2V16.2A3.2%203.2%200%200%201%2012%2013Z%22%2F%3E%3Cpath%20d%3D%22M24%2026.6s-5-2.9-5-6.1c0-1.7%201.35-3%203-3%201.25%200%202.05.72%202.65%201.65.62-.93%201.43-1.65%202.65-1.65%201.65%200%203%201.3%203%203%200%203.25-5%206.1-5%206.1Z%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;
            border: none;
        }

        .seed-icon-chat::after {
            display: none;
        }

        /* 03 라이브 전환성: 카메라 + 순환 화살표 */
        .seed-icon-live::before {
            width: 58px;
            height: 58px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223.1%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%2214%22%20y%3D%2217%22%20width%3D%2216%22%20height%3D%2212%22%20rx%3D%222.8%22%2F%3E%3Cpath%20d%3D%22M30%2020l5.5-3.2v12.4L30%2026%22%2F%3E%3Cpath%20d%3D%22M11%2018.6c2.1-4.7%206.6-7.7%2011.7-7.9%22%2F%3E%3Cpath%20d%3D%22M19.4%208l4%202.4-3.9%202.5%22%2F%3E%3Cpath%20d%3D%22M37%2029.4c-2.1%204.7-6.6%207.7-11.7%207.9%22%2F%3E%3Cpath%20d%3D%22M28.6%2040l-4-2.4%203.9-2.5%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;
            border: none;
        }

        .seed-icon-live::after {
            display: none;
        }

        /* 04 실전 리스크: 원형 마이너스 */
        .seed-icon-filter::before {
            width: 42px;
            height: 42px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            border: 3.3px solid #98FFAB;
            border-radius: 50%;
        }

        .seed-icon-filter::after {
            width: 17px;
            height: 3.6px;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: #98FFAB;
            border-radius: 999px;
        }

        /* 05 액션버킷: 체크박스 */
        .seed-icon-check::before {
            width: 38px;
            height: 38px;
            border: 3.5px solid #98FFAB;
            border-radius: 10px;
            left: 9px;
            top: 9px;
        }

        .seed-icon-check::after {
            width: 22px;
            height: 13px;
            border-left: 4.5px solid #98FFAB;
            border-bottom: 4.5px solid #98FFAB;
            left: 18px;
            top: 21px;
            transform: rotate(-45deg);
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


def render_home():
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
# =========================================================
# STAR TRAIL 대시보드 통합 코드
# =========================================================

STARTRAIL_DATA_FILES = {
    "summary": "10_dashboard/data/startrail_대시보드요약.csv",
    "kpi": "10_dashboard/data/startrail_핵심KPI.csv",
    "candidate": "10_dashboard/data/startrail_개인후보통합테이블.csv",
    "constellation": "10_dashboard/data/startrail_성단그룹후보테이블.csv",
}

STARTRAIL_ASSET_FILES = {
    "calendar": "assets/달력.png",
    "soop": "assets/숲3.png",
    "chzzk": "assets/치지직3.png",
}

STARTRAIL_GRAPH_BG = "#15102F"
STARTRAIL_TRANSPARENT = "rgba(0,0,0,0)"


def startrail_resolve_path(relative_path: str) -> Path:
    rel = Path(relative_path)
    here = Path(__file__).resolve().parent

    candidates = [
        here / rel,
        here.parent / rel,
        Path.cwd() / rel,
        Path.cwd().parent / rel,
    ]

    for p in candidates:
        if p.exists():
            return p.resolve()

    for root in [here, here.parent, Path.cwd(), Path.cwd().parent]:
        try:
            matches = list(root.rglob(rel.name))
            for m in matches:
                if str(m).replace("\\", "/").endswith(str(rel).replace("\\", "/")):
                    return m.resolve()
            if matches:
                return matches[0].resolve()
        except Exception:
            pass

    return here.parent / rel


def startrail_img_to_base64(relative_path: str) -> str:
    path = startrail_resolve_path(relative_path)
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


def startrail_read_csv(relative_path: str) -> pd.DataFrame:
    path = startrail_resolve_path(relative_path)
    if not path.exists():
        return pd.DataFrame()

    for enc in ["utf-8-sig", "cp949", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def load_startrail_summary_data():
    summary_df = startrail_read_csv(STARTRAIL_DATA_FILES["summary"])
    if summary_df.empty or "지표" not in summary_df.columns or "값" not in summary_df.columns:
        return {}
    return dict(zip(summary_df["지표"], summary_df["값"]))


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def load_startrail_kpi_data():
    kpi_df = startrail_read_csv(STARTRAIL_DATA_FILES["kpi"])
    if kpi_df.empty or "지표" not in kpi_df.columns or "값" not in kpi_df.columns:
        return {}
    return dict(zip(kpi_df["지표"], kpi_df["값"]))


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def load_startrail_raw_candidate_data():
    return startrail_read_csv(STARTRAIL_DATA_FILES["candidate"])


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
def load_startrail_constellation_data():
    const = startrail_read_csv(STARTRAIL_DATA_FILES["constellation"])

    if const.empty:
        return pd.DataFrame()

    required = ["소속", "영입우선_점수", "멤버수", "합계_뷰어십", "합계_도네이션"]
    for col in required:
        if col not in const.columns:
            const[col] = 0 if col != "소속" else "미확인"

    const["소속"] = const["소속"].astype(str).str.strip()
    const["스코어"] = pd.to_numeric(const["영입우선_점수"], errors="coerce").fillna(0).round(0)
    const["멤버수"] = pd.to_numeric(const["멤버수"], errors="coerce").fillna(0)
    const["합계_뷰어십"] = pd.to_numeric(const["합계_뷰어십"], errors="coerce").fillna(0)
    const["합계_도네이션"] = pd.to_numeric(const["합계_도네이션"], errors="coerce").fillna(0)

    const = const.sort_values("스코어", ascending=False).reset_index(drop=True)
    const["순위"] = const.index + 1
    const["상위퍼센트"] = (const["순위"] / len(const) * 100).round(2) if len(const) else 0

    return const


def build_startrail_candidate_data(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()

    raw = raw.copy()
    data_list = []

    segment_rules = {
        "프로토스타": {"filter_col": "프로토스타_구분", "filter_value": "S급 후보군", "score_col": "프로토스타_score"},
        "위성": {"filter_col": "세그먼트_위성", "filter_value": "위성(Satellite)", "score_col": "위성점수"},
        "슈퍼노바": {"filter_col": "슈퍼노바_구분", "filter_value": "슈퍼노바 핵심 후보군", "score_col": "슈퍼노바_score"},
        "코멧": {"filter_col": "코멧여부", "filter_value": 1, "score_col": "코멧score"},
    }

    for seg, rule in segment_rules.items():
        filter_col = rule["filter_col"]
        filter_value = rule["filter_value"]
        score_col = rule["score_col"]

        if filter_col not in raw.columns or score_col not in raw.columns:
            continue

        if seg == "코멧":
            temp = raw[pd.to_numeric(raw[filter_col], errors="coerce").fillna(0) == 1].copy()
        else:
            temp = raw[raw[filter_col] == filter_value].copy()

        if temp.empty:
            continue

        temp["세그먼트"] = seg
        temp["스코어"] = pd.to_numeric(temp[score_col], errors="coerce").fillna(0).round(2)

        if seg == "코멧" and "코멧유입경로" in temp.columns:
            temp["세그먼트필터"] = temp["코멧유입경로"].fillna("해당 없음")
        elif seg == "슈퍼노바" and "슈퍼노바_구분" in temp.columns:
            temp["세그먼트필터"] = temp["슈퍼노바_구분"].fillna("해당 없음")
        else:
            temp["세그먼트필터"] = "해당 없음"

        data_list.append(temp)

    if not data_list:
        return pd.DataFrame()

    df = pd.concat(data_list, ignore_index=True)

    df["스트리머"] = df["스트리머명"] if "스트리머명" in df.columns else "미확인"
    df["이미지URL"] = df["이미지URL"].fillna("").astype(str).str.strip() if "이미지URL" in df.columns else ""
    df["평균시청자"] = pd.to_numeric(df.get("평균_시청자_최댓값", 0), errors="coerce").fillna(0)
    df["최고시청자"] = pd.to_numeric(df.get("최고_시청자", 0), errors="coerce").fillna(0)
    df["팔로워수"] = pd.to_numeric(df.get("최고_팔로워", 0), errors="coerce").fillna(0)
    df["뷰어십"] = pd.to_numeric(df.get("뷰어십", 0), errors="coerce").fillna(0)
    df["도네이션"] = pd.to_numeric(df.get("도네이션", 0), errors="coerce").fillna(0)
    df["평균도네이션"] = df["도네이션"]
    df["상위퍼센트"] = 0

    return df


def inject_startrail_css():
    st.html(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

        <style>
        .startrail-page {
            position: relative;
            z-index: 2;
            color: #F8F2FF;
        }

        /* ============================================================
           STARTRAIL 상단 헤더
           - 스타시드 대시보드와 유사한 좌측 타이틀 + 우측 설명 카드 구조
           - 색감은 보라/골드 기반
        ============================================================ */

        .startrail-page .dashboard-hero {
            position: relative;
            z-index: 3;
            margin-top: 2px;
            margin-bottom: 30px;
        }

        .startrail-page .hero-top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 34px;
        }

        .startrail-page .trail-title-wrap {
            display: flex;
            align-items: center;
            gap: 24px;
            min-width: 0;
        }

        .startrail-page .trail-logo-box {
            width: 82px;
            height: 82px;
            min-width: 82px;
            border-radius: 18px;
            border: 2px solid rgba(255, 212, 93, 0.72);
            background:
                radial-gradient(circle at 35% 28%, rgba(255,255,255,0.24), transparent 20%),
                linear-gradient(145deg, rgba(43, 34, 18, 0.96), rgba(18, 13, 35, 0.98));
            box-shadow:
                0 0 22px rgba(255, 212, 93, 0.20),
                0 0 28px rgba(125, 66, 255, 0.18),
                inset 0 0 20px rgba(255,255,255,0.035);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #FFD45D;
            font-size: 36px;
        }

        .startrail-page .hero-main-title {
            display: flex;
            align-items: baseline;
            gap: 14px;
            margin: 0 0 8px 0;
            line-height: 1.02;
            word-break: keep-all;
        }

        .startrail-page .hero-main-title-ko {
            font-size: 52px;
            font-weight: 950;
            letter-spacing: -2.6px;
            color: #FFF8FF;
            text-shadow:
                0 0 7px rgba(255,255,255,0.36),
                0 0 18px rgba(198,168,255,0.32),
                0 0 30px rgba(125,66,255,0.30);
        }

        .startrail-page .hero-main-title-en {
            font-size: 27px;
            font-weight: 950;
            letter-spacing: -1.3px;
            color: #FFD45D;
            text-shadow:
                0 0 10px rgba(255, 212, 93, 0.42),
                0 0 18px rgba(125, 66, 255, 0.18);
        }

        .startrail-page .hero-title-underbar {
            width: 330px;
            height: 3px;
            border-radius: 999px;
            margin: 2px 0 12px 0;
            background: linear-gradient(90deg, #FFD45D, rgba(155, 107, 255, 0.85), transparent);
            box-shadow:
                0 0 14px rgba(255, 212, 93, 0.35),
                0 0 18px rgba(155, 107, 255, 0.28);
        }

        .startrail-page .hero-main-subtitle {
            font-size: 17px;
            font-weight: 780;
            color: #E8DFFF;
            margin-top: 7px;
            word-break: keep-all;
        }

        .startrail-page .hero-date-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding: 8px 15px;
            border-radius: 999px;
            background: rgba(8, 18, 35, 0.78) !important;
            border: 1px solid rgba(255, 212, 93, 0.32);
            color: #F8E7A0;
            font-size: 13px;
            font-weight: 850;
            box-shadow:
                0 0 14px rgba(255, 212, 93, 0.14),
                inset 0 0 12px rgba(255,255,255,0.02);
        }

        .startrail-page .hero-right-area {
            width: 560px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .startrail-page .hero-info-card {
            width: 100%;
            min-height: 104px;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(42, 31, 16, 0.86), rgba(18, 16, 47, 0.92)) !important;
            border: 1px solid rgba(255, 212, 93, 0.30);
            box-shadow:
                0 0 24px rgba(255, 212, 93, 0.12),
                0 0 26px rgba(125, 66, 255, 0.14),
                inset 0 0 22px rgba(255,255,255,0.024);
            padding: 20px 24px;
            display: flex;
            align-items: center;
            gap: 18px;
        }

        .startrail-page .hero-info-icon {
            min-width: 58px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background:
                radial-gradient(circle at 35% 28%, rgba(255,255,255,0.95), transparent 16%),
                linear-gradient(135deg, #FFE278, #C99700 48%, #7B42FF);
            box-shadow:
                0 0 18px rgba(255, 212, 93, 0.42),
                0 0 26px rgba(125, 66, 255, 0.24),
                inset 0 0 13px rgba(255,255,255,0.18);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
            color: #160F2D;
            font-weight: 950;
        }

        .startrail-page .hero-info-title {
            font-size: 17px;
            font-weight: 950;
            color: #FFF9FF;
            margin-bottom: 6px;
        }

        .startrail-page .hero-info-desc {
            font-size: 13px;
            line-height: 1.62;
            color: rgba(255,255,255,0.72);
            font-weight: 650;
            word-break: keep-all;
        }

        .startrail-page .hero-info-desc .trail-point {
            color: #FFD45D;
            font-weight: 900;
        }

        /* ============================================================
           세그먼트 카드
        ============================================================ */

        .startrail-page .segment-card {
            background: #15102F !important;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 22px;
            padding: 22px 16px;
            transition: 0.25s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            min-height: 205px;
            box-shadow: 0 0 24px rgba(112, 53, 255, 0.14);
            overflow: hidden;
            position: relative;
        }

        .startrail-page .segment-card::before {
            content: "";
            position: absolute;
            left: 22px;
            right: 22px;
            top: 16px;
            height: 3px;
            border-radius: 3px;
            background: rgba(240, 140, 255, 0.36);
        }

        .startrail-page .segment-card i {
            margin-top: 16px;
            margin-bottom: 13px;
            color: #DDBBFF;
            text-shadow: 0 0 14px rgba(221,187,255,0.30);
        }

        .startrail-page .seg-name {
            font-size: 19px;
            font-weight: 950;
            margin-bottom: 7px;
            color: #FFF9FF;
        }

        .startrail-page .seg-count {
            font-size: 25px;
            font-weight: 950;
            color: #F08CFF;
            margin-bottom: 9px;
        }

        .startrail-page .seg-desc {
            font-size: 12px;
            color: rgba(255,255,255,0.70);
            line-height: 1.55;
            white-space: pre-wrap;
            word-break: keep-all;
        }

        .startrail-page .segment-card.active-성단,
        .startrail-page .segment-card.active-성단 i,
        .startrail-page .segment-card.active-성단 .seg-name,
        .startrail-page .segment-card.active-성단 .seg-count {
            color: #FF6B8A !important;
            border-color: #FF6B8A !important;
        }

        .startrail-page .segment-card.active-프로토스타,
        .startrail-page .segment-card.active-프로토스타 i,
        .startrail-page .segment-card.active-프로토스타 .seg-name,
        .startrail-page .segment-card.active-프로토스타 .seg-count {
            color: #FFD45D !important;
            border-color: #FFD45D !important;
        }

        .startrail-page .segment-card.active-위성,
        .startrail-page .segment-card.active-위성 i,
        .startrail-page .segment-card.active-위성 .seg-name,
        .startrail-page .segment-card.active-위성 .seg-count {
            color: #75CCFF !important;
            border-color: #75CCFF !important;
        }

        .startrail-page .segment-card.active-슈퍼노바,
        .startrail-page .segment-card.active-슈퍼노바 i,
        .startrail-page .segment-card.active-슈퍼노바 .seg-name,
        .startrail-page .segment-card.active-슈퍼노바 .seg-count {
            color: #98FFAB !important;
            border-color: #98FFAB !important;
        }

        .startrail-page .segment-card.active-코멧,
        .startrail-page .segment-card.active-코멧 i,
        .startrail-page .segment-card.active-코멧 .seg-name,
        .startrail-page .segment-card.active-코멧 .seg-count {
            color: #FF9DF5 !important;
            border-color: #FF9DF5 !important;
        }

        /* ============================================================
           TOP 카드
        ============================================================ */

        .startrail-page .rank-card {
            background: #15102F !important;
            border-radius: 24px;
            padding: 22px 18px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.10);
            position: relative;
            transition: 0.25s ease;
            min-height: 260px;
            box-shadow: 0 0 24px rgba(112, 53, 255, 0.14);
        }

        .startrail-page .rank-card:hover {
            border-color: rgba(240,140,255,0.72);
            transform: translateY(-2px);
        }

        .startrail-page .rank-badge {
            position: absolute;
            top: 15px;
            left: 15px;
            width: 34px;
            height: 34px;
            padding: 0;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 18px;
        }

        .startrail-page .rank-normal {
            background: rgba(255,255,255,0.09);
            color: #FFF9FF;
            border: 1px solid rgba(255,255,255,0.14);
        }

        .startrail-page .rank-gold {
            background: linear-gradient(135deg, #FFD45D, #C99700);
            color: #1a112f;
        }

        .startrail-page .rank-silver {
            background: linear-gradient(135deg, #F4E9FF, #B7A2DC);
            color: #1a112f;
        }

        .startrail-page .rank-bronze {
            background: linear-gradient(135deg, #D99666, #8B4A30);
            color: #ffffff;
        }

        .startrail-page .avatar-circle {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin: 0 auto 15px;
            border: 3px solid rgba(240, 140, 255, 0.28);
            background: #09051C;
            overflow: hidden;
            box-shadow: 0 0 18px rgba(240,140,255,0.16);
        }

        .startrail-page .avatar-circle img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .startrail-page .tag-segment {
            display: inline-block;
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 900;
            margin-top: 8px;
        }

        .startrail-page .tag-성단 {
            background: rgba(255,75,75,0.18);
            color:#FF8A8A;
            border:1px solid rgba(255,75,75,0.65);
        }

        .startrail-page .tag-프로토스타 {
            background: rgba(255,212,93,0.15);
            color:#FFD45D;
            border:1px solid rgba(255,212,93,0.60);
        }

        .startrail-page .tag-위성 {
            background: rgba(149,175,255,0.15);
            color:#95AFFF;
            border:1px solid rgba(149,175,255,0.60);
        }

        .startrail-page .tag-슈퍼노바 {
            background: rgba(152,255,171,0.13);
            color:#98FFAB;
            border:1px solid rgba(152,255,171,0.56);
        }

        .startrail-page .tag-코멧 {
            background: rgba(255,157,245,0.16);
            color:#FF9DF5;
            border:1px solid rgba(255,157,245,0.62);
        }

        /* ============================================================
           테이블 / 하단 제목
        ============================================================ */

        .startrail-page .custom-table {
            width: 100%;
            border-collapse: collapse;
            background: #15102F !important;
            border: 1px solid rgba(196, 143, 255, 0.20);
            border-radius: 20px;
            overflow: hidden;
        }

        .startrail-page .custom-table th {
            text-align: center;
            padding: 13px 12px;
            border-bottom: 1px solid rgba(196,143,255,0.22);
            color: #D9C8FF;
            font-size: 13px;
            font-weight: 900;
        }

        .startrail-page .custom-table td {
            text-align: center;
            padding: 13px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.07);
            font-size: 14px;
            color: #FFF9FF;
        }

        .startrail-page .bottom-title {
            height: 42px;
            display: flex;
            align-items: center;
            margin: 0 0 14px 0;
            font-size: 26px;
            font-weight: 950;
            color: #FFF9FF;
            letter-spacing: -0.5px;
        }

        /* ============================================================
           Tooltip
        ============================================================ */

        .startrail-page .tooltip-wrap {
            position: relative;
            display: inline-flex;
            margin-left: 6px;
        }

        .startrail-page .tooltip-icon {
            width: 17px;
            height: 17px;
            border-radius: 50%;
            border: 1px solid rgba(217,200,255,0.75);
            color: #D9C8FF;
            font-size: 11px;
            font-weight: 900;
            line-height: 17px;
            text-align: center;
            cursor: help;
        }

        .startrail-page .tooltip-text {
            visibility: hidden;
            opacity: 0;
            width: 230px;
            background: rgba(21,16,47,0.98);
            color: #D9CFE8;
            text-align: left;
            border: 1px solid rgba(196,143,255,0.34);
            border-radius: 12px;
            padding: 10px 12px;
            position: absolute;
            z-index: 9999;
            bottom: 135%;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            line-height: 1.45;
        }

        .startrail-page .tooltip-wrap:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        /* ============================================================
           반응형
        ============================================================ */

        @media (max-width: 1200px) {
            .startrail-page .hero-top-row {
                flex-direction: column;
                align-items: stretch;
            }

            .startrail-page .hero-right-area {
                width: 100%;
                align-items: stretch;
            }

            .startrail-page .trail-title-wrap {
                align-items: flex-start;
            }

            .startrail-page .hero-main-title-ko {
                font-size: 42px;
                letter-spacing: -2px;
            }

            .startrail-page .hero-main-title-en {
                font-size: 22px;
            }

            .startrail-page .trail-logo-box {
                width: 72px;
                height: 72px;
                min-width: 72px;
                font-size: 30px;
            }

            .startrail-hero {
            position: relative;
            z-index: 3;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 36px;
            margin-top: 2.4rem;
            margin-bottom: 28px;
        }
        
        .startrail-hero-left {
            flex: 1;
            min-width: 0;
        }
        
        .startrail-title-row {
            display: flex;
            align-items: center;
            gap: 26px;
        }
        
        .startrail-logo-box {
            width: 86px;
            height: 86px;
            border-radius: 18px;
            border: 2px solid rgba(255, 212, 93, 0.62);
            background:
                radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.16), transparent 28%),
                linear-gradient(145deg, rgba(42, 26, 74, 0.96), rgba(14, 12, 33, 0.96));
            box-shadow:
                0 0 24px rgba(255, 212, 93, 0.20),
                0 0 34px rgba(139, 92, 255, 0.22),
                inset 0 0 20px rgba(255, 255, 255, 0.04);
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
        }
        
        .startrail-logo-box i {
            font-size: 38px;
            color: #FFD45D;
            text-shadow:
                0 0 10px rgba(255, 212, 93, 0.85),
                0 0 22px rgba(255, 212, 93, 0.36);
        }
        
        .startrail-main-title {
            display: flex;
            align-items: baseline;
            gap: 14px;
            line-height: 1;
            margin-bottom: 10px;
        }
        
        .startrail-main-title-ko {
            font-size: 58px;
            font-weight: 950;
            letter-spacing: -2.8px;
            color: #FFF8FF;
            text-shadow:
                0 0 8px rgba(255,255,255,0.38),
                0 0 22px rgba(198,168,255,0.30);
        }
        
        .startrail-main-title-en {
            font-size: 32px;
            font-weight: 950;
            color: #FFD45D;
            letter-spacing: -1.2px;
            text-shadow:
                0 0 12px rgba(255, 212, 93, 0.45),
                0 0 22px rgba(255, 212, 93, 0.20);
        }
        
        .startrail-title-line {
            width: 285px;
            height: 3px;
            border-radius: 999px;
            margin-bottom: 14px;
            background: linear-gradient(90deg, #FFD45D, rgba(155, 107, 255, 0.18));
            box-shadow: 0 0 16px rgba(255, 212, 93, 0.42);
        }
        
        .startrail-main-subtitle {
            font-size: 18px;
            font-weight: 850;
            line-height: 1.45;
            color: rgba(255, 255, 255, 0.84);
            letter-spacing: -0.5px;
            word-break: keep-all;
        }
        
        .startrail-hero-right {
            width: 560px;
            flex: 0 0 560px;
            display: flex;
            justify-content: flex-end;
        }
        
        .startrail-period-card {
            width: 100%;
            min-height: 106px;
            border-radius: 22px;
            padding: 22px 26px;
            display: flex;
            align-items: center;
            gap: 20px;
            background:
                linear-gradient(135deg, rgba(255, 212, 93, 0.13), rgba(21, 16, 47, 0.82) 42%, rgba(14, 12, 33, 0.94));
            border: 1px solid rgba(255, 212, 93, 0.30);
            box-shadow:
                0 0 28px rgba(255, 212, 93, 0.10),
                0 0 34px rgba(139, 92, 255, 0.14),
                inset 0 0 22px rgba(255, 255, 255, 0.025);
        }
        
        .startrail-period-icon {
            width: 64px;
            height: 64px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                radial-gradient(circle at 34% 28%, rgba(255,255,255,0.85), transparent 16%),
                linear-gradient(135deg, #FFD45D, #9B6BFF);
            box-shadow:
                0 0 20px rgba(255, 212, 93, 0.34),
                inset 0 0 16px rgba(255, 255, 255, 0.14);
            flex: 0 0 auto;
        }
        
        .startrail-period-title {
            font-size: 17px;
            font-weight: 950;
            color: #FFF8FF;
            margin-bottom: 8px;
        }
        
        .startrail-period-desc {
            font-size: 14px;
            font-weight: 700;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.72);
            word-break: keep-all;
        }
        
        .startrail-period-desc span {
            color: #FFD45D;
            font-weight: 950;
            text-shadow: 0 0 10px rgba(255, 212, 93, 0.28);
        }
        
        @media (max-width: 1200px) {
            .startrail-hero {
                flex-direction: column;
            }
        
            .startrail-hero-right {
                width: 100%;
                flex-basis: auto;
            }
        
            .startrail-main-title-ko {
                font-size: 46px;
            }
        
            .startrail-main-title-en {
                font-size: 25px;
            }
        /* =========================================================
           Star Trail 상단: Star Seed 대시보드와 유사한 배치
           - 좌측: 아이콘 + 대형 타이틀 + 설명
           - 우측: 분석 기간 카드
           - 색감: 보라/골드
        ========================================================= */

        .startrail-page .trail-dashboard-hero {
            position: relative;
            z-index: 3;
            margin-top: 18px;
            margin-bottom: 26px;
        }

        .startrail-page .trail-hero-grid {
            display: grid;
            grid-template-columns: 1fr 0.58fr;
            gap: 36px;
            align-items: center;
        }

        .startrail-page .trail-title-wrap {
            display: flex;
            align-items: center;
            gap: 22px;
        }

        .startrail-page .trail-title-icon {
            width: 88px;
            height: 88px;
            border-radius: 18px;
            border: 2px solid rgba(255, 212, 93, 0.62);
            background:
                radial-gradient(circle at 38% 30%, rgba(255,255,255,0.42), transparent 18%),
                linear-gradient(135deg, rgba(255, 212, 93, 0.18), rgba(125, 66, 255, 0.18)),
                rgba(8, 16, 31, 0.86);
            box-shadow:
                0 0 22px rgba(255, 212, 93, 0.20),
                0 0 28px rgba(125, 66, 255, 0.22),
                inset 0 0 18px rgba(255,255,255,0.05);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 42px;
            color: #FFD45D;
        }

        .startrail-page .trail-title-main {
            display: flex;
            align-items: baseline;
            gap: 14px;
            flex-wrap: wrap;
        }

        .startrail-page .trail-title-ko {
            font-size: 54px;
            line-height: 1.02;
            font-weight: 950;
            letter-spacing: -2px;
            color: #FFF9FF;
            text-shadow:
                0 0 10px rgba(255,255,255,0.28),
                0 0 22px rgba(125,66,255,0.36);
        }

        .startrail-page .trail-title-en {
            font-size: 30px;
            line-height: 1;
            font-weight: 950;
            color: #FFD45D;
            text-shadow:
                0 0 12px rgba(255, 212, 93, 0.36),
                0 0 20px rgba(125, 66, 255, 0.28);
        }

        .startrail-page .trail-title-underline {
            width: 360px;
            height: 4px;
            border-radius: 999px;
            margin-top: 10px;
            background: linear-gradient(90deg, #FFD45D, #7D42FF, transparent);
            box-shadow:
                0 0 16px rgba(255, 212, 93, 0.34),
                0 0 18px rgba(125, 66, 255, 0.26);
        }

        .startrail-page .trail-title-desc {
            margin-top: 12px;
            font-size: 17px;
            font-weight: 800;
            line-height: 1.55;
            color: #E8DFFF;
            word-break: keep-all;
        }

        .startrail-page .trail-period-card {
            min-height: 116px;
            border-radius: 22px;
            padding: 22px 26px;
            display: flex;
            align-items: center;
            gap: 18px;
            background:
                linear-gradient(135deg, rgba(255, 212, 93, 0.12), rgba(125, 66, 255, 0.10)),
                rgba(8, 16, 31, 0.88);
            border: 1px solid rgba(255, 212, 93, 0.36);
            box-shadow:
                0 0 24px rgba(255, 212, 93, 0.12),
                0 0 24px rgba(125, 66, 255, 0.18),
                inset 0 0 18px rgba(255,255,255,0.025);
        }

        .startrail-page .trail-period-icon {
            min-width: 64px;
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background:
                radial-gradient(circle at 35% 30%, rgba(255,255,255,0.88), transparent 18%),
                linear-gradient(135deg, #FFD45D, #7D42FF);
            box-shadow:
                0 0 18px rgba(255, 212, 93, 0.32),
                0 0 22px rgba(125, 66, 255, 0.26);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: #140B2F;
            font-weight: 950;
        }

        .startrail-page .trail-period-title {
            font-size: 16px;
            font-weight: 950;
            color: #FFF9FF;
            margin-bottom: 7px;
        }

        .startrail-page .trail-period-desc {
            font-size: 13px;
            line-height: 1.55;
            color: rgba(255,255,255,0.76);
            font-weight: 700;
            word-break: keep-all;
        }

        .startrail-page .trail-period-date {
            color: #FFD45D;
            font-weight: 950;
        }

        @media (max-width: 1200px) {
            .startrail-page .trail-hero-grid {
                grid-template-columns: 1fr;
            }

            .startrail-page .trail-title-ko {
                font-size: 42px;
            }

            .startrail-page .trail-title-en {
                font-size: 24px;
            }

            .startrail-page .trail-title-icon {
                width: 74px;
                height: 74px;
                font-size: 34px;
            }
        }
        </style>
        """
    )


def render_startrail_dashboard():
    inject_startrail_css()
    st.markdown('<div class="startrail-page">', unsafe_allow_html=True)
    summary = load_startrail_summary_data()
    kpi = load_startrail_kpi_data()
    raw = load_startrail_raw_candidate_data()
    df = build_startrail_candidate_data(raw)
    constellation_df = load_startrail_constellation_data()
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not summary or not kpi:
        st.error("스타트레일 요약/KPI CSV를 찾지 못했습니다. `10_dashboard/data/startrail_대시보드요약.csv`, `startrail_핵심KPI.csv` 경로를 확인해주세요.")
        return

    if raw.empty:
        st.error("스타트레일 개인 후보 CSV를 찾지 못했습니다. `10_dashboard/data/startrail_개인후보통합테이블.csv` 경로를 확인해주세요.")
        return

    date_icon = startrail_img_to_base64(STARTRAIL_ASSET_FILES["calendar"])
    soop_icon = startrail_img_to_base64(STARTRAIL_ASSET_FILES["soop"])
    chzzk_icon = startrail_img_to_base64(STARTRAIL_ASSET_FILES["chzzk"])

    def _num(v, default=0):
        try:
            return float(str(v).replace(",", "").replace("₩", "").strip())
        except Exception:
            return default

    if "startrail_current_seg" not in st.session_state:
        st.session_state.startrail_current_seg = "프로토스타"

    if "startrail_show_detail" not in st.session_state:
        st.session_state.startrail_show_detail = False

    if "startrail_selected_streamer" not in st.session_state:
        st.session_state.startrail_selected_streamer = None

    st.markdown('<div class="startrail-page">', unsafe_allow_html=True)

    st.html(
        f"""
        <div class="trail-dashboard-hero">
            <div class="trail-hero-grid">

                <div class="trail-title-wrap">
                    <div class="trail-title-icon">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                    </div>

                    <div>
                        <div class="trail-title-main">
                            <span class="trail-title-ko">스타트레일</span>
                            <span class="trail-title-en">Star Trail</span>
                        </div>

                        <div class="trail-title-underline"></div>

                        <div class="trail-title-desc">
                            기존 플랫폼의 성과와 팬덤 궤적을 따라<br>
                            CIME 영입 우선 후보군을 찾습니다
                        </div>
                    </div>
                </div>

                <div class="trail-period-card">
                    <div class="trail-period-icon">
                        <i class="fa-regular fa-calendar-days"></i>
                    </div>

                    <div>
                        <div class="trail-period-title">분석 기간</div>
                        <div class="trail-period-desc">
                            기존 플랫폼의 활동 데이터를 기준으로<br>
                            <span class="trail-period-date">2025.01.01 ~ 2026.03.31</span> 기간의 후보군을 분석합니다.
                        </div>
                    </div>
                </div>

            </div>
        </div>
        """
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("총 분석 스트리머 수", f"{_num(kpi.get('총 분석 스트리머 수')):,.0f} 명")
    with k2:
        st.metric("평균 뷰어십", f"{_num(kpi.get('평균 뷰어십')):,.0f}")
    with k3:
        st.metric("평균 도네이션", f"₩ {_num(kpi.get('평균 도네이션')):,.0f}")

    st.write("---")

    st.write("### 🛸 세그먼트 전략")

    seg_data = {
        "성단": {"icon": "fa-solid fa-users", "count": f"{_num(summary.get('성단 그룹 후보 수')):,.0f}개", "desc": "그룹/소속 기반 팬덤 이동 가능성이 있는 후보군"},
        "프로토스타": {"icon": "fa-solid fa-leaf", "count": f"{_num(summary.get('프로토스타 S급 후보 수')):,.0f}명", "tooltip": "S급 기준", "desc": "현재 규모는 작지만 방송 반응이 좋은 성장형 후보군"},
        "위성": {"icon": "fa-solid fa-satellite", "count": f"{_num(summary.get('위성 후보 수')):,.0f}명", "desc": "소속 없이도 방송 성과가 검증된 개인형 후보군"},
        "슈퍼노바": {"icon": "fa-solid fa-star", "count": f"{_num(summary.get('슈퍼노바 핵심 후보 수')):,.0f}명", "tooltip": "핵심 후보군 기준", "desc": "대중성과 팬덤 규모가 큰 간판형 후보군"},
        "코멧": {"icon": "fa-solid fa-meteor", "count": f"{_num(summary.get('코멧 후보 수')):,.0f}명", "desc": "방송 외부 채널에서 인지도가 높은 발견형 후보군"},
    }

    segments = list(seg_data.keys())
    seg_cols = st.columns(5)

    for i, seg in enumerate(segments):
        with seg_cols[i]:
            info = seg_data[seg]
            active_class = f"active active-{seg}" if st.session_state.startrail_current_seg == seg else ""
            tooltip_html = ""

            if "tooltip" in info:
                tooltip_html = (
                    f'<span class="tooltip-wrap">'
                    f'<span class="tooltip-icon">?</span>'
                    f'<span class="tooltip-text">{info["tooltip"]}</span>'
                    f'</span>'
                )

            st.markdown(
                f"""
                <div class="segment-card {active_class}">
                    <i class="{info["icon"]} fa-2x"></i>
                    <div class="seg-name">{seg}{tooltip_html}</div>
                    <div class="seg-count">{info["count"]}</div>
                    <div class="seg-desc">{info["desc"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("선택", key=f"startrail_seg_btn_{seg}", use_container_width=True):
                st.session_state.startrail_current_seg = seg
                st.session_state.startrail_show_detail = False
                st.session_state.startrail_selected_streamer = None
                st.rerun()

    st.write("---")

    platform_filter = "전체"
    segment_detail_filter = "전체"

    if st.session_state.startrail_current_seg == "코멧":
        _, f1, f2 = st.columns([2, 1, 1])
        platform_filter = f1.selectbox("플랫폼 필터", ["전체", "SOOP", "CHZZK"], key="startrail_platform_filter_comet")
        segment_detail_filter = f2.selectbox("세그먼트 필터", ["전체", "X 강세형", "유튜브 강세형", "하이브리드"], key="startrail_segment_detail_filter")
    elif st.session_state.startrail_current_seg != "성단":
        _, _, f1 = st.columns([2, 1, 1])
        platform_filter = f1.selectbox("플랫폼 필터", ["전체", "SOOP", "CHZZK"], key="startrail_platform_filter")

    if st.session_state.startrail_current_seg == "성단":
        filtered_df = constellation_df.copy()
    else:
        filtered_df = df[df["세그먼트"] == st.session_state.startrail_current_seg].copy()

        if platform_filter != "전체" and "플랫폼" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["플랫폼"] == platform_filter].copy()

        if segment_detail_filter != "전체" and "세그먼트필터" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["세그먼트필터"] == segment_detail_filter].copy()

    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values("스코어", ascending=False).reset_index(drop=True)
        filtered_df["순위"] = filtered_df.index + 1
        filtered_df["상위퍼센트"] = (filtered_df["순위"] / len(filtered_df) * 100).round(2)
    else:
        filtered_df["순위"] = []
        filtered_df["상위퍼센트"] = []

    top_5 = filtered_df.head(5)

    st.write(f"### 🏆 **{st.session_state.startrail_current_seg}** TOP 5")

    if top_5.empty:
        st.warning("선택한 조건에 해당하는 후보가 없습니다.")
    else:
        card_cols = st.columns(5)

        for i, (_, row) in enumerate(top_5.iterrows()):
            if st.session_state.startrail_current_seg == "성단":
                display_name = row.get("소속", "-")
                display_segment = "성단"
                score_text = f'{row.get("스코어", 0):.0f}'
                avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={display_name}"
            else:
                display_name = row.get("스트리머", "-")
                display_segment = row.get("세그먼트", "-")
                score_text = f'{row.get("스코어", 0):.2f}'
                image_url = str(row.get("이미지URL", "")).strip()
                avatar_url = image_url if image_url and image_url.lower() != "nan" else f"https://api.dicebear.com/7.x/avataaars/svg?seed={display_name}"

            rank_class = "rank-gold" if i == 0 else "rank-silver" if i == 1 else "rank-bronze" if i == 2 else "rank-normal"

            with card_cols[i]:
                st.markdown(
                    f"""
                    <div class="rank-card">
                        <div class="rank-badge {rank_class}">{i + 1}</div>
                        <div class="avatar-circle"><img src="{avatar_url}" alt="avatar"></div>
                        <div style="font-weight:bold; font-size:18px;">{display_name}</div>
                        <div class="tag-segment tag-{display_segment}">{display_segment}</div>
                        <div style="margin-top:15px; font-size:12px; color:#8b949e;">스코어</div>
                        <div style="font-size:24px; font-weight:800; color:#ffbc00;">{score_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("상세 보기", key=f"startrail_streamer_btn_{display_segment}_{display_name}_{i}", use_container_width=True):
                    selected_data = row.to_dict()
                    if st.session_state.startrail_current_seg == "성단":
                        selected_data["세그먼트"] = "성단"
                        selected_data["표시이름"] = row.get("소속", "-")
                    else:
                        selected_data["표시이름"] = row.get("스트리머", "-")

                    st.session_state.startrail_selected_streamer = selected_data
                    st.session_state.startrail_show_detail = True
                    st.rerun()

    if st.session_state.startrail_show_detail and st.session_state.startrail_selected_streamer is not None:
        s = st.session_state.startrail_selected_streamer
        detail_name = s.get("표시이름", s.get("스트리머", s.get("소속", "-")))

        image_url = str(s.get("이미지URL", "")).strip()
        avatar_url = image_url if image_url and image_url.lower() != "nan" else f"https://api.dicebear.com/7.x/avataaars/svg?seed={detail_name}"

        if s.get("세그먼트") == "성단":
            detail_platform_img = ""
        elif s.get("플랫폼") == "SOOP":
            detail_platform_img = f'<img src="data:image/png;base64,{soop_icon}" style="height:28px; border-radius:8px; object-fit:contain;">'
        elif s.get("플랫폼") == "CHZZK":
            detail_platform_img = f'<img src="data:image/png;base64,{chzzk_icon}" style="height:28px; border-radius:8px; object-fit:contain;">'
        else:
            detail_platform_img = f'<span style="color:#8b949e; font-size:14px;">{s.get("플랫폼", "")}</span>'

        if s.get("세그먼트") == "성단":
            metrics = {
                "멤버 수": (_num(s.get("멤버수")), max(constellation_df["멤버수"].quantile(0.95), 1), "#00ff87"),
                "뷰어십 합계": (_num(s.get("합계_뷰어십")), max(constellation_df["합계_뷰어십"].quantile(0.95), 1), "#ff4b4b"),
                "도네이션 합계": (_num(s.get("합계_도네이션")), max(constellation_df["합계_도네이션"].quantile(0.95), 1), "#ffbc00"),
            }
            radar_metrics = {
                "플랫폼체급": (_num(s.get("플랫폼체급_점수")), 100),
                "ARPU": (_num(s.get("ARPU_점수")), 100),
                "외부인기": (_num(s.get("외부인기_점수")), 100),
                "대중성": (_num(s.get("대중성_점수")), 100),
            }
        else:
            metrics = {
                "뷰어십": (_num(s.get("뷰어십")), 17000000, "#ff4b4b"),
                "도네이션": (_num(s.get("도네이션")), 7000000, "#ffbc00"),
                "최고 팔로워": (_num(s.get("팔로워수")), 414000, "#00ff87"),
                "평균 시청자": (_num(s.get("평균시청자")), 47500, "#00f2ff"),
                "최고 시청자": (_num(s.get("최고시청자")), 50000, "#bf40bf"),
            }
            radar_metrics = {
                "대중성": (_num(s.get("대중성_표준점수")), 100),
                "방송화력": (_num(s.get("방송화력_표준점수")), 100),
                "팬덤결집력": (_num(s.get("팬덤결집력_표준점수")), 100),
                "수익성": (_num(s.get("수익성_표준점수")), 100),
                "외부유입가능성": (_num(s.get("외부유입가능성_표준점수")), 100),
            }

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        detail_box = st.container(border=True)

        with detail_box:
            st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
            detail_left, detail_mid, detail_right = st.columns([1.1, 1.8, 1.2])

            with detail_left:
                st.markdown(
                    f"""
                    <div style="width:190px; margin:22px auto 0 auto; text-align:center;">
                        <div class="avatar-circle" style="width:135px; height:135px; border:4px solid #00f2ff; margin:0 auto 14px auto;">
                            <img src="{avatar_url}" alt="avatar" style="width:100%; height:100%; object-fit:cover;">
                        </div>
                        <div style="width:190px; text-align:center; font-size:26px; font-weight:800; color:white; margin:0 0 6px 0; white-space:nowrap;">
                            {detail_name}
                        </div>
                        <div style="width:190px; display:flex; justify-content:center; gap:8px; align-items:center;">
                            <span class="tag-segment tag-{s.get("세그먼트", "-")}" style="height:30px; padding:0 12px; display:flex; align-items:center; justify-content:center; margin:0;">
                                {s.get("세그먼트", "-")}
                            </span>
                            {detail_platform_img}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with detail_mid:
                for m_name, (val, max_val, color) in metrics.items():
                    percent = min(val / max_val, 1.0) * 100 if max_val else 0
                    st.markdown(
                        f"""
                        <div style="margin-bottom:14px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <span style="font-size:14px; font-weight:bold; color:white;">{m_name}</span>
                                <span style="font-size:15px; font-weight:800; color:{color};">{val:,.0f}</span>
                            </div>
                            <div style="background:rgba(255,255,255,0.05); height:8px; border-radius:4px; overflow:hidden;">
                                <div style="background:{color}; height:100%; border-radius:4px; width:{percent}%;"></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with detail_right:
                radar_labels = list(radar_metrics.keys())
                radar_values = [min(val / max_val, 1.0) * 100 if max_val else 0 for val, max_val in radar_metrics.values()]
                radar_labels_closed = radar_labels + [radar_labels[0]]
                radar_values_closed = radar_values + [radar_values[0]]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_values_closed,
                    theta=radar_labels_closed,
                    fill="toself",
                    name="능력치",
                    line=dict(width=2),
                    opacity=0.85,
                ))

                fig_radar.update_layout(
                    polar=dict(
                        bgcolor=STARTRAIL_TRANSPARENT,
                        radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#8b949e"), gridcolor="rgba(255,255,255,0.15)"),
                        angularaxis=dict(tickfont=dict(size=14, color="white"), gridcolor="rgba(255,255,255,0.15)"),
                    ),
                    showlegend=False,
                    margin=dict(l=35, r=35, t=25, b=45),
                    paper_bgcolor=STARTRAIL_TRANSPARENT,
                    plot_bgcolor=STARTRAIL_TRANSPARENT,
                    font_color="white",
                    height=260,
                )

                st.plotly_chart(fig_radar, use_container_width=True)

            _, close_col = st.columns([5, 1])
            with close_col:
                if st.button("닫기", key="startrail_detail_close", use_container_width=True):
                    st.session_state.startrail_show_detail = False
                    st.session_state.startrail_selected_streamer = None
                    st.rerun()

    st.write("---")

    bot_left, spacer, bot_right = st.columns([1, 0.08, 1])

    with bot_left:
        st.markdown(f"<div class='bottom-title'>📋 {st.session_state.startrail_current_seg} 영입 우선순위 리스트</div>", unsafe_allow_html=True)

        table_html = "<table class='custom-table'><thead><tr>"

        if st.session_state.startrail_current_seg == "성단":
            table_html += "<th>순위</th><th>소속</th><th>스코어</th><th>상위 %</th><th>멤버 수</th><th>뷰어십 합계</th><th>도네이션 합계</th>"
        else:
            table_html += "<th>순위</th><th>스트리머명</th><th>플랫폼</th><th>스코어</th><th>상위 %</th><th>팔로워수</th><th>평균시청자</th><th>평균 도네이션</th>"

        table_html += "</tr></thead><tbody>"

        for _, row in filtered_df.head(10).iterrows():
            if st.session_state.startrail_current_seg == "성단":
                table_html += (
                    f"<tr><td>{row['순위']}</td><td><b>{row['소속']}</b></td>"
                    f"<td style='color:#00f2ff; font-weight:bold;'>{row['스코어']:.0f}</td>"
                    f"<td style='color:#ffbc00; font-weight:bold;'>상위 {row['상위퍼센트']:.1f}%</td>"
                    f"<td>{row['멤버수']:,.0f}</td><td>{row['합계_뷰어십']:,.0f}</td>"
                    f"<td>₩ {row['합계_도네이션']:,.0f}</td></tr>"
                )
            else:
                if row.get("플랫폼") == "SOOP":
                    platform_img = f'<img src="data:image/png;base64,{soop_icon}" style="height:24px; border-radius:8px; object-fit:contain;">'
                elif row.get("플랫폼") == "CHZZK":
                    platform_img = f'<img src="data:image/png;base64,{chzzk_icon}" style="height:24px; border-radius:8px; object-fit:contain;">'
                else:
                    platform_img = row.get("플랫폼", "-")

                table_html += (
                    f"<tr><td>{row['순위']}</td><td><b>{row['스트리머']}</b></td>"
                    f"<td>{platform_img}</td>"
                    f"<td style='color:#00f2ff; font-weight:bold;'>{row['스코어']:.2f}</td>"
                    f"<td style='color:#ffbc00; font-weight:bold;'>상위 {row['상위퍼센트']:.1f}%</td>"
                    f"<td style='text-align:right;'>{row['팔로워수']:,.0f}</td>"
                    f"<td style='text-align:right;'>{row['평균시청자']:,.0f}</td>"
                    f"<td style='text-align:right;'>₩ {row['평균도네이션']:,.0f}</td></tr>"
                )

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

    with bot_right:
        if st.session_state.startrail_current_seg == "성단":
            graph_title = "🌌 성단 TOP15 히트맵"
        elif st.session_state.startrail_current_seg == "코멧":
            graph_title = "🌌 코멧 타겟팅 맵"
        else:
            graph_title = f"🌌 {st.session_state.startrail_current_seg} 세그먼트 분석 분포"

        st.markdown(f"<div class='bottom-title'>{graph_title}</div>", unsafe_allow_html=True)

        if filtered_df.empty:
            st.warning("그래프를 표시할 데이터가 없습니다.")

        elif st.session_state.startrail_current_seg == "성단":
            heatmap_cols = ["플랫폼체급_점수", "ARPU_점수", "외부인기_점수", "대중성_점수", "영입우선_점수"]
            heatmap_labels = ["플랫폼체급", "ARPU", "외부인기", "대중성", "영입우선"]

            missing = [c for c in heatmap_cols if c not in filtered_df.columns]
            if missing:
                st.warning(f"히트맵 컬럼이 부족합니다: {missing}")
            else:
                heatmap_df = filtered_df.sort_values("영입우선_점수", ascending=False).head(15).set_index("소속")[heatmap_cols]

                fig = px.imshow(
                    heatmap_df,
                    text_auto=".0f",
                    aspect="auto",
                    color_continuous_scale="YlGnBu",
                    zmin=0,
                    zmax=100,
                    labels=dict(color="점수"),
                )

                fig.update_xaxes(ticktext=heatmap_labels, tickvals=list(range(len(heatmap_labels))), tickangle=0, automargin=True)
                fig.update_yaxes(automargin=True)
                fig.update_layout(
                    paper_bgcolor=STARTRAIL_TRANSPARENT,
                    plot_bgcolor=STARTRAIL_TRANSPARENT,
                    font_color="white",
                    margin=dict(l=85, r=95, t=55, b=95),
                    height=620,
                    coloraxis_colorbar=dict(title="점수", x=1.03, xanchor="left"),
                )
                st.plotly_chart(fig, use_container_width=True)

        elif st.session_state.startrail_current_seg == "코멧":
            comet_all_df = raw.copy()
            for col in ["유튜브_구독자", "X_팔로워", "최고_팔로워"]:
                if col not in comet_all_df.columns:
                    comet_all_df[col] = 0
                comet_all_df[col] = pd.to_numeric(comet_all_df[col], errors="coerce").fillna(0)

            comet_all_df["통합_외부화력"] = comet_all_df["유튜브_구독자"] + comet_all_df["X_팔로워"]

            plot_all_df = comet_all_df[(comet_all_df["최고_팔로워"] > 0) & (comet_all_df["통합_외부화력"] > 0)].copy()
            plot_comet_df = filtered_df.copy()

            for col in ["유튜브_구독자", "X_팔로워", "최고_팔로워"]:
                if col not in plot_comet_df.columns:
                    plot_comet_df[col] = 0
                plot_comet_df[col] = pd.to_numeric(plot_comet_df[col], errors="coerce").fillna(0)

            plot_comet_df["통합_외부화력"] = plot_comet_df["유튜브_구독자"] + plot_comet_df["X_팔로워"]
            plot_comet_df = plot_comet_df[(plot_comet_df["최고_팔로워"] > 0) & (plot_comet_df["통합_외부화력"] > 0)].copy()

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=plot_all_df["최고_팔로워"],
                y=plot_all_df["통합_외부화력"],
                mode="markers",
                name="일반 스트리머",
                marker=dict(size=6, color="rgba(217,217,217,0.35)"),
                text=plot_all_df["스트리머명"] if "스트리머명" in plot_all_df.columns else None,
                hovertemplate="<b>%{text}</b><br>최고 팔로워: %{x:,.0f}<br>통합 외부화력: %{y:,.0f}<extra></extra>",
            ))

            color_map = {"유튜브 강세형": "#FF8A8A", "X 강세형": "#95AFFF", "하이브리드": "#FF9DF5"}

            for route, color in color_map.items():
                if "코멧유입경로" not in plot_comet_df.columns:
                    continue
                temp = plot_comet_df[plot_comet_df["코멧유입경로"] == route].copy()
                if temp.empty:
                    continue

                fig.add_trace(go.Scatter(
                    x=temp["최고_팔로워"],
                    y=temp["통합_외부화력"],
                    mode="markers",
                    name=route,
                    marker=dict(size=14, color=color, line=dict(color="white", width=1.5)),
                    text=temp["스트리머"] if "스트리머" in temp.columns else None,
                    hovertemplate=f"<b>%{{text}}</b><br>유입경로: {route}<br>최고 팔로워: %{{x:,.0f}}<br>통합 외부화력: %{{y:,.0f}}<extra></extra>",
                ))

            if not plot_comet_df.empty:
                avg_broadcast = plot_comet_df["최고_팔로워"].mean()
                fig.add_vline(x=avg_broadcast, line_dash="dot", line_width=2, line_color="#c9d1d9", opacity=0.75)

            fig.update_layout(
                title=dict(text="외부 팬덤 vs 방송 체급", x=0.08, xanchor="left"),
                xaxis_title="방송 체급",
                yaxis_title="통합 외부 화력",
                xaxis_type="log",
                yaxis_type="log",
                paper_bgcolor=STARTRAIL_TRANSPARENT,
                plot_bgcolor=STARTRAIL_TRANSPARENT,
                font_color="white",
                margin=dict(l=80, r=140, t=75, b=95),
                height=620,
                legend=dict(title="코멧 유입경로", bgcolor=STARTRAIL_TRANSPARENT, x=1.03, y=0.98, xanchor="left", yanchor="top"),
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
            st.plotly_chart(fig, use_container_width=True)

        else:
            required_cols = ["평균시청자", "스코어", "뷰어십", "플랫폼", "스트리머"]
            missing = [c for c in required_cols if c not in filtered_df.columns]
            if missing:
                st.warning(f"산점도 컬럼이 부족합니다: {missing}")
            else:
                fig = px.scatter(
                    filtered_df,
                    x="평균시청자",
                    y="스코어",
                    size="뷰어십",
                    color="플랫폼",
                    hover_name="스트리머",
                    color_discrete_map={"SOOP": "#00f2ff", "CHZZK": "#bf40bf"},
                    template="plotly_dark",
                )

                fig.update_layout(
                    paper_bgcolor=STARTRAIL_TRANSPARENT,
                    plot_bgcolor=STARTRAIL_TRANSPARENT,
                    margin=dict(l=85, r=170, t=65, b=95),
                    height=620,
                    font_color="white",
                    legend=dict(bgcolor=STARTRAIL_TRANSPARENT, x=1.03, y=0.98, xanchor="left", yanchor="top"),
                )
                fig.update_xaxes(automargin=True, gridcolor="rgba(255,255,255,0.12)")
                fig.update_yaxes(automargin=True, gridcolor="rgba(255,255,255,0.12)")
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 페이지 라우팅
# =========================================================

if st.session_state.page == "대시보드 홈":
    render_home()
    st.stop()

elif st.session_state.page == "스타트레일":
    render_startrail_dashboard()
    st.stop()

elif st.session_state.page == "스타시드":
    # 기존 스타시드 본문을 함수화하지 않았다면 여기서는 pass가 맞음
    pass

# =========================================================
# 5. 스타시드 로딩 패널
# =========================================================

STARSEED_LOADING_HTML = """
<div class="starseed-loading-wrap">
    <div class="starseed-loading-orb"></div>
    <div class="starseed-loading-title">STAR SEED 데이터를 준비하는 중입니다</div>
    <div class="starseed-loading-sub">후보 CSV, 변화 추적 스냅샷, KPI 지표를 불러와<br>영입 우선순위 대시보드 화면을 구성하고 있습니다.</div>
    <div class="starseed-loading-steps">
        <span class="starseed-loading-chip">후보 데이터 로드</span><span class="starseed-loading-chip">KPI 계산</span><span class="starseed-loading-chip">TOP 후보 렌더링</span><span class="starseed-loading-chip">그래프 구성</span>
    </div>
</div>
"""

STARSEED_LOADING_PLACEHOLDER = None
if st.session_state.get("page") == "스타시드" and not st.session_state.get("starseed_first_load_done", False):
    STARSEED_LOADING_PLACEHOLDER = st.empty()
    STARSEED_LOADING_PLACEHOLDER.markdown(STARSEED_LOADING_HTML, unsafe_allow_html=True)

# =========================================================
# 6. 경로 및 데이터 로드
# =========================================================

def find_project_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here, Path.cwd(), Path.cwd().parent]
    for p in candidates:
        if (p / "10_dashboard").exists() or (p / "11_final").exists() or (p / "09_intermediate").exists():
            return p.resolve()
    return here.parent.resolve()

PROJECT_ROOT = find_project_root()


def resolve_existing_path(relative_path: str) -> Path:
    rel = Path(relative_path)
    candidates = [PROJECT_ROOT / rel, Path.cwd() / rel, Path(__file__).resolve().parent / rel, Path(__file__).resolve().parent.parent / rel]
    for p in candidates:
        if p.exists():
            return p.resolve()
    for root in [PROJECT_ROOT, Path.cwd(), Path(__file__).resolve().parent]:
        try:
            matches = list(root.rglob(rel.name))
            for m in matches:
                if str(m).replace("\\", "/").endswith(str(rel).replace("\\", "/")):
                    return m.resolve()
            if matches:
                return matches[0].resolve()
        except Exception:
            pass
    return PROJECT_ROOT / rel


def resolve_first_existing(relative_paths):
    for relative_path in relative_paths:
        path = resolve_existing_path(relative_path)
        if path.exists():
            return path
    return resolve_existing_path(relative_paths[0])

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
    try:
        return path.stat().st_mtime_ns if path.exists() else 0
    except Exception:
        return 0

@st.cache_data(show_spinner=False)
def load_data(candidate_mtime, segment_mtime, summary_mtime, tracking_mtime, reference_mtime, snapshot_mtime):
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

if st.session_state.get("page") == "스타시드":
    st.session_state["starseed_first_load_done"] = True
    if STARSEED_LOADING_PLACEHOLDER is not None:
        STARSEED_LOADING_PLACEHOLDER.empty()

# =========================================================
# 7. 유틸 함수
# =========================================================

def first_existing(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_score_to_100(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.dropna().empty:
        return s
    return s * 100 if s.max() <= 1.5 else s


def fmt_num(value, ndigits=0, suffix=""):
    if pd.isna(value):
        return "-"
    try:
        f = float(value)
        if ndigits == 0:
            return f"{int(round(f)):,}{suffix}"
        return f"{f:,.{ndigits}f}{suffix}"
    except Exception:
        return f"{value}{suffix}"


def fmt_int(x):
    return fmt_num(x, 0, "")


def fmt_float(x, ndigits=3):
    return fmt_num(x, ndigits, "")


def safe_html(value):
    return html_lib.escape(str(value if pd.notna(value) else "-"), quote=True)


def short_text(value, limit=42):
    text = str(value if pd.notna(value) else "-").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def delta_badge(delta, ndigits=0, suffix=""):
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


def is_unclassified_value(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().isin(["", "미분류", "None", "none", "nan", "NaN", "NULL", "null", "<NA>"])


def apply_unclassified_hold_rule(data: pd.DataFrame, seg_col: str | None, action_col_name: str | None, output_col: str = "검토단계_표시") -> pd.DataFrame:
    out = data.copy()
    out[output_col] = out[action_col_name] if action_col_name and action_col_name in out.columns else pd.NA
    out[output_col] = out[output_col].replace(["None", "nan", "NaN", "", None], pd.NA).fillna("미분류")
    if seg_col and seg_col in out.columns:
        out.loc[is_unclassified_value(out[seg_col]), output_col] = "보류"
    return out


def add_score_display_column(input_df: pd.DataFrame) -> pd.DataFrame:
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


def calc_kpi_values(kpi_df: pd.DataFrame) -> dict:
    if kpi_df is None or kpi_df.empty:
        return {"total": np.nan, "shortlist": np.nan, "avg_score": np.nan, "high_priority": np.nan}
    local_action_col = first_existing(kpi_df, ["검토단계_표시", "액션버킷", "action_bucket"])
    local_shortlist_col = first_existing(kpi_df, ["shortlist_선정여부", "shortlist", "shortlisted"])
    local_score_display_col = "최종점수_100점" if "최종점수_100점" in kpi_df.columns else None
    total = len(kpi_df)
    if local_shortlist_col:
        shortlist = int(kpi_df[local_shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"]).sum())
    elif local_action_col:
        shortlist = int(kpi_df[local_action_col].astype(str).str.contains("즉시검토|성장관찰|검증", na=False).sum())
    else:
        shortlist = 0
    avg_score = pd.to_numeric(kpi_df[local_score_display_col], errors="coerce").mean() if local_score_display_col else np.nan
    high_priority = int(kpi_df[local_action_col].astype(str).str.contains("즉시검토|영입제한|위성|Satellite", na=False).sum()) if local_action_col else 0
    return {"total": total, "shortlist": shortlist, "avg_score": avg_score, "high_priority": high_priority}


def snapshot_date_col(snap: pd.DataFrame):
    return first_existing(snap, ["snapshot_ts_kst", "snapshot_datetime", "snapshot_date", "스냅샷시각", "기준시각", "created_at"])


def prepare_snapshot_df(snap: pd.DataFrame) -> pd.DataFrame:
    if snap is None or snap.empty:
        return pd.DataFrame()
    out = snap.copy()
    date_col = snapshot_date_col(out)
    if date_col is None:
        return pd.DataFrame()
    raw_date_text = out[date_col].astype(str).str.strip()
    extracted_date = raw_date_text.str.extract(r"(20\d{2}-\d{2}-\d{2})", expand=False)
    out["__snapshot_dt__"] = pd.to_datetime(out[date_col], errors="coerce")
    out["__snapshot_date__"] = extracted_date
    missing_date_mask = out["__snapshot_date__"].isna() | (out["__snapshot_date__"].astype(str).str.strip() == "")
    out.loc[missing_date_mask, "__snapshot_date__"] = out.loc[missing_date_mask, "__snapshot_dt__"].dt.strftime("%Y-%m-%d")
    out["__snapshot_date_dt__"] = pd.to_datetime(out["__snapshot_date__"], errors="coerce")
    out = out.dropna(subset=["__snapshot_date_dt__"]).copy()
    if out.empty:
        return pd.DataFrame()
    out["__snapshot_dt__"] = out["__snapshot_dt__"].fillna(out["__snapshot_date_dt__"])
    out["__snapshot_date__"] = out["__snapshot_date_dt__"].dt.strftime("%Y-%m-%d")
    return out


def get_snapshot_by_date(snap: pd.DataFrame, date_label: str) -> pd.DataFrame:
    if snap is None or snap.empty or "__snapshot_date__" not in snap.columns:
        return pd.DataFrame()
    target = snap[snap["__snapshot_date__"] == date_label].copy()
    if target.empty:
        return pd.DataFrame()
    latest_dt = target["__snapshot_dt__"].max()
    target = target[target["__snapshot_dt__"] == latest_dt].copy()
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

# =========================================================
# 8. 데이터 없을 때
# =========================================================

if candidate_df.empty:
    st.error(
        "후보 데이터 CSV를 찾지 못했습니다. 먼저 파이프라인을 실행해서 "
        "`10_dashboard/data/dashboard_candidate_table.csv` 또는 "
        "`11_final/core_output/candidate_scored_final.csv`를 생성해주세요."
    )
    st.stop()

# =========================================================
# 9. 컬럼 매핑 / 기본 전처리
# =========================================================

df = candidate_df.copy()

channel_id_col = first_existing(df, ["채널ID", "channel_id"])
channel_name_col = first_existing(df, ["채널명", "channel_title", "채널명_clean"])
channel_thumbnail_col = first_existing(df, ["channel_thumbnail_url", "채널썸네일URL", "채널프로필이미지URL", "thumbnail_url"])
channel_url_col = first_existing(df, ["channel_url", "채널URL", "youtube_channel_url", "유튜브채널URL"])

score_col = first_existing(df, ["최종점수", "최종점수_100점", "영입적합도점수", "영입 적합도 점수", "영입종합점수", "영입 종합 점수", "위성점수_log_minmax", "final_score", "score"])
rank_col = first_existing(df, ["운영우선순위", "최종순위", "현재 필터 기준 순위", "순위", "rank", "final_rank"])
segment_col = first_existing(df, ["대표상위세그먼트", "주요 콘텐츠군", "상위 콘텐츠군", "대표세그먼트", "segment", "segment_unified", "대표상위세그먼트명"])
lower_segment_col = first_existing(df, ["대표하위세그먼트", "세부 콘텐츠 유형", "하위 콘텐츠군", "sub_segment", "대표하위세그먼트명", "segment_seed", "segment_seed_raw"])
action_col = first_existing(df, ["액션버킷", "검토 단계", "현재 검토 단계", "현재검토단계", "action_bucket"])
shortlist_col = first_existing(df, ["shortlist_선정여부", "shortlist 선정 여부", "shortlist", "is_shortlist", "shortlist_selected"])
subs_col = first_existing(df, ["채널구독자수", "채널 구독자 수", "구독자수", "구독자 수", "subscriber_count", "subscribers", "channel_subscriber_count"])
view_col = first_existing(df, ["최근영상조회수평균", "최근 영상 평균 조회수", "최근 조회수 평균", "recent_view_avg", "avg_recent_view_count", "view_count_mean", "평균조회수"])

growth_col = first_existing(df, ["성장성점수", "성장성", "growth_score", "growth_proxy", "성장성_score"])
fan_col = first_existing(df, ["팬밀도점수", "팬밀도", "fan_density_score", "fan_density", "팬밀도_score"])

if score_col is not None:
    df["_score_raw"] = pd.to_numeric(df[score_col], errors="coerce")
    df["최종점수_100점"] = normalize_score_to_100(df[score_col])
    df["_score_display"] = df["최종점수_100점"]
else:
    df["_score_raw"] = np.nan
    df["최종점수_100점"] = np.nan
    df["_score_display"] = np.nan

score_display_col = "최종점수_100점"
original_action_col = action_col
df = apply_unclassified_hold_rule(df, segment_col, original_action_col, output_col="검토단계_표시")
action_col = "검토단계_표시"

if rank_col is not None:
    df = df.sort_values(rank_col, ascending=True, na_position="last")
elif score_col is not None:
    df = df.sort_values("_score_display", ascending=False, na_position="last")
df = df.reset_index(drop=True)

snapshot_prepared_df = prepare_snapshot_df(snapshot_df)

# =========================================================
# 10. 사이드바 필터
# =========================================================

st.sidebar.markdown("---")
filtered = df.copy()

selected_segments = []
selected_lower = []
selected_actions = []
only_shortlist = False
hide_hold = True
score_filter_100 = None
min_subs = 0
min_views = 0
search_text = ""
top_n = 10

with st.sidebar.expander("스타시드 필터", expanded=False) as filter_panel:
    filter_panel.caption("상위 콘텐츠군, 검토 단계, 점수·규모 조건으로 후보군을 좁혀봅니다.")

    if segment_col:
        seg_values = sorted([x for x in filtered[segment_col].dropna().astype(str).unique()])
        selected_segments = filter_panel.multiselect("상위 콘텐츠군", options=seg_values, default=seg_values)
        if selected_segments:
            filtered = filtered[filtered[segment_col].astype(str).isin(selected_segments)]

    if lower_segment_col:
        lower_values = sorted([x for x in filtered[lower_segment_col].dropna().astype(str).unique()])
        selected_lower = filter_panel.multiselect("세부 콘텐츠 유형", options=lower_values, default=[])
        if selected_lower:
            filtered = filtered[filtered[lower_segment_col].astype(str).isin(selected_lower)]

    if action_col:
        action_values = sorted([x for x in filtered[action_col].dropna().astype(str).unique()])
        selected_actions = filter_panel.multiselect("검토 단계", options=action_values, default=action_values)
        if selected_actions:
            filtered = filtered[filtered[action_col].astype(str).isin(selected_actions)]

    if shortlist_col:
        only_shortlist = filter_panel.checkbox("shortlist 선정 후보만 보기", value=False)
        if only_shortlist:
            shortlist_bool = filtered[shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])
            filtered = filtered[shortlist_bool]

    hide_hold = filter_panel.checkbox("보류/제외 숨기기", value=True)
    if hide_hold and action_col:
        filtered = filtered[~filtered[action_col].astype(str).str.contains("보류|제외", na=False)]

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
            filtered = filtered[pd.to_numeric(filtered[score_display_col], errors="coerce") >= score_filter_100]

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
        filtered = filtered[filtered[channel_name_col].astype(str).str.contains(search_text, case=False, na=False)]

    top_n = filter_panel.slider("TOP N", min_value=5, max_value=50, value=10, step=5)

filtered = filtered.copy()
filtered["표시순위"] = np.arange(1, len(filtered) + 1)

# =========================================================
# 11. 변화 추적 기준
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
        .sort_values("__snapshot_date_dt__")["__snapshot_date__"]
        .tolist()
    )
    snapshot_dates = [d for d in snapshot_dates_all if pd.to_datetime(d, errors="coerce") >= MIN_TRACKING_DATE]

    if not snapshot_dates:
        change_panel.warning(f"{MIN_TRACKING_DATE_LABEL} 이후 snapshot 날짜가 없습니다. STEP11 snapshot append를 다시 누적하세요.")
        tracking_target_df = df.copy()
    else:
        target_options = snapshot_dates + ["현재"]
        tracking_target_label = change_panel.selectbox(
            "비교 대상 시점",
            options=target_options,
            index=len(target_options) - 1,
            help=f"{MIN_TRACKING_DATE_LABEL} 이후 snapshot 또는 현재 데이터를 비교 대상 시점으로 선택합니다.",
        )
        if tracking_target_label == "현재":
            tracking_target_df = df.copy()
            available_base_dates = snapshot_dates
        else:
            tracking_target_df = get_snapshot_by_date(snapshot_prepared_df, tracking_target_label)
            available_base_dates = [d for d in snapshot_dates if d <= tracking_target_label]

        if available_base_dates:
            if tracking_target_label == "현재":
                default_base_label = MIN_TRACKING_DATE_LABEL if MIN_TRACKING_DATE_LABEL in available_base_dates else available_base_dates[0]
            else:
                default_base_label = tracking_target_label
            if default_base_label not in available_base_dates:
                default_base_label = available_base_dates[-1]
            tracking_base_label = change_panel.selectbox(
                "기준 시점",
                options=available_base_dates,
                index=available_base_dates.index(default_base_label),
                help=f"{MIN_TRACKING_DATE_LABEL} 이후 날짜만 기준 시점으로 선택할 수 있습니다.",
            )
            tracking_base_df = get_snapshot_by_date(snapshot_prepared_df, tracking_base_label)
        else:
            change_panel.warning("비교 가능한 기준 snapshot 날짜가 없습니다.")
else:
    change_panel.warning("snapshot 파일이 없거나 날짜 컬럼을 찾지 못했습니다.")

# =========================================================
# 12. KPI 계산
# =========================================================

def apply_snapshot_filters_for_kpi(base_df: pd.DataFrame) -> pd.DataFrame:
    out = base_df.copy()
    local_segment_col = first_existing(out, ["대표상위세그먼트", "대표세그먼트", "segment", "대표상위세그먼트명"])
    local_lower_segment_col = first_existing(out, ["대표하위세그먼트", "sub_segment", "대표하위세그먼트명"])
    local_action_col = first_existing(out, ["검토단계_표시", "액션버킷", "action_bucket"])
    local_shortlist_col = first_existing(out, ["shortlist_선정여부", "shortlist", "shortlisted"])
    local_channel_name_col = first_existing(out, ["채널명", "channel_title", "채널명_clean"])
    local_subs_col = first_existing(out, ["채널구독자수", "채널 구독자 수", "구독자수", "구독자 수", "subscriber_count", "subscribers", "channel_subscriber_count"])
    local_view_col = first_existing(out, ["최근영상조회수평균", "avg_recent_views", "최근조회수평균"])

    if local_segment_col and selected_segments:
        out = out[out[local_segment_col].astype(str).isin(selected_segments)]
    if local_lower_segment_col and selected_lower:
        out = out[out[local_lower_segment_col].astype(str).isin(selected_lower)]
    if local_action_col and selected_actions:
        out = out[out[local_action_col].astype(str).isin(selected_actions)]
    if local_shortlist_col and only_shortlist:
        out = out[out[local_shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])]
    if local_action_col and hide_hold:
        out = out[~out[local_action_col].astype(str).str.contains("보류|제외", na=False)]
    if "최종점수_100점" in out.columns and score_filter_100 is not None:
        out = out[pd.to_numeric(out["최종점수_100점"], errors="coerce") >= score_filter_100]
    if local_subs_col and min_subs > 0:
        out = out[pd.to_numeric(out[local_subs_col], errors="coerce").fillna(0) >= min_subs]
    if local_view_col and min_views > 0:
        out = out[pd.to_numeric(out[local_view_col], errors="coerce").fillna(0) >= min_views]
    if local_channel_name_col and search_text:
        out = out[out[local_channel_name_col].astype(str).str.contains(search_text, case=False, na=False)]
    return out


def kpi_compare_note(base_label, target_label):
    base_txt = str(base_label or "").strip()
    target_txt = str(target_label or "").strip() or "현재"
    return "기준 시점 대비 변화" if not base_txt or base_txt == "-" else f"{base_txt} 대비 {target_txt} 변화"


target_all_kpi_df = add_score_display_column(tracking_target_df if not tracking_target_df.empty else df)
base_all_kpi_df = add_score_display_column(tracking_base_df) if not tracking_base_df.empty else pd.DataFrame()

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

compare_note = kpi_compare_note(tracking_base_label, tracking_target_label)

# =========================================================
# 13. 변화 추적 테이블 생성
# =========================================================

def standardize_for_tracking(source: pd.DataFrame, prefix: str) -> pd.DataFrame:
    if source is None or source.empty:
        return pd.DataFrame()
    src = source.copy()
    id_col = first_existing(src, ["채널ID", "channel_id"])
    name_col = first_existing(src, ["채널명", "channel_title", "채널명_clean"])
    rank_col_local = first_existing(src, ["운영우선순위", "최종순위", "rank", "순위"])
    score_col_local = first_existing(src, ["최종점수", "위성점수_log_minmax", "final_score", "score"])
    action_col_local = first_existing(src, ["검토단계_표시", "액션버킷", "action_bucket"])
    upper_col = first_existing(src, ["대표상위세그먼트", "대표세그먼트", "segment", "대표상위세그먼트명"])
    lower_col = first_existing(src, ["대표하위세그먼트", "sub_segment", "대표하위세그먼트명"])
    if id_col is None:
        return pd.DataFrame()
    src[id_col] = src[id_col].astype(str).str.strip()
    if rank_col_local is None:
        if score_col_local:
            src[score_col_local] = pd.to_numeric(src[score_col_local], errors="coerce")
            src = src.sort_values(score_col_local, ascending=False, na_position="last")
        src[f"{prefix}_운영우선순위"] = np.arange(1, len(src) + 1)
        rank_col_local = f"{prefix}_운영우선순위"
    keep = pd.DataFrame()
    keep["채널ID"] = src[id_col]
    keep[f"{prefix}_채널명"] = src[name_col] if name_col else pd.NA
    keep[f"{prefix}_운영우선순위"] = pd.to_numeric(src[rank_col_local], errors="coerce")
    keep[f"{prefix}_최종점수"] = normalize_score_to_100(src[score_col_local]) if score_col_local else np.nan
    keep[f"{prefix}_액션버킷"] = src[action_col_local] if action_col_local else pd.NA
    keep[f"{prefix}_대표상위세그먼트"] = src[upper_col] if upper_col else pd.NA
    keep[f"{prefix}_대표하위세그먼트"] = src[lower_col] if lower_col else pd.NA
    if f"{prefix}_대표상위세그먼트" in keep.columns:
        keep.loc[is_unclassified_value(keep[f"{prefix}_대표상위세그먼트"]), f"{prefix}_액션버킷"] = "보류"
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
    merged["운영우선순위변동"] = merged["기준_운영우선순위"] - merged["비교_운영우선순위"]
    merged["최종점수변동"] = merged["비교_최종점수"] - merged["기준_최종점수"]
    merged["신규진입여부"] = merged["기준_운영우선순위"].isna()
    merged["버킷변경여부"] = merged["기준_액션버킷"].fillna("신규") != merged["비교_액션버킷"].fillna("미분류")

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
        "기준시점", "비교시점", "채널명", "채널ID", "기준_운영우선순위", "비교_운영우선순위",
        "운영우선순위변동", "기준_최종점수", "비교_최종점수", "최종점수변동",
        "기준_액션버킷", "비교_액션버킷", "버킷변경여부", "신규진입여부",
        "비교_대표상위세그먼트", "비교_대표하위세그먼트", "변화요약",
    ]
    out = merged[[c for c in out_cols if c in merged.columns]].copy()
    return out.sort_values(["비교_운영우선순위", "비교_최종점수"], ascending=[True, False], na_position="last").reset_index(drop=True)

mini_tracking_df = pd.DataFrame()
if not tracking_base_df.empty and not tracking_target_df.empty:
    try:
        mini_tracking_df = build_tracking_between(tracking_base_df, tracking_target_df, tracking_base_label, tracking_target_label)
    except Exception:
        mini_tracking_df = pd.DataFrame()

if not mini_tracking_df.empty:
    mini_tracking_df = mini_tracking_df.rename(columns={
        "기준_운영우선순위": "이전순위", "비교_운영우선순위": "현재순위", "운영우선순위변동": "순위변동",
        "기준_최종점수": "이전점수", "비교_최종점수": "현재점수", "최종점수변동": "점수변동",
        "기준_액션버킷": "이전단계", "비교_액션버킷": "현재단계",
    })
    if "순위변동" in mini_tracking_df.columns:
        mini_tracking_df["순위변동"] = pd.to_numeric(mini_tracking_df["순위변동"], errors="coerce")
        mini_tracking_df = mini_tracking_df.sort_values("순위변동", ascending=False)

# =========================================================
# 14. HTML 렌더 보조 함수
# =========================================================

def seg_key(text):
    t = str(text or "")
    if any(k in t for k in ["음악", "보이스", "커버", "성우"]):
        return "music"
    if any(k in t for k in ["창작", "비주얼", "코스프레", "일러"]):
        return "visual"
    if any(k in t for k in ["버츄얼", "버튜", "VTuber"]):
        return "virtual"
    if any(k in t for k in ["게임", "롤", "실황"]):
        return "game"
    if any(k in t for k in ["서브컬처", "토크", "팬덤"]):
        return "subculture"
    return "etc"


def tag(value):
    text = str(value if pd.notna(value) and str(value).strip() else "미분류")
    return f'<span class="tag-pill seg-{seg_key(text)}" title="{safe_html(text)}">{safe_html(text)}</span>'


def action_tag(value):
    text = str(value if pd.notna(value) and str(value).strip() else "미분류")
    if "즉시" in text:
        cls = "action-immediate"
    elif "성장" in text:
        cls = "action-watch"
    elif "검증" in text:
        cls = "action-verify"
    else:
        cls = "action-hold"
    return f'<span class="tag-pill {cls}" title="{safe_html(text)}">{safe_html(text)}</span>'


def thumb_url(row):
    if channel_thumbnail_col and channel_thumbnail_col in row.index:
        url = str(row.get(channel_thumbnail_col, "") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            return url
    return ""


def avatar_small(row):
    url = thumb_url(row)
    name = str(row.get(channel_name_col, "?") if channel_name_col else "?")
    initial = safe_html(name[:1] if name else "?")
    if url:
        return f'<div class="mini-avatar-wrap"><img src="{safe_html(url)}" loading="lazy" referrerpolicy="no-referrer"></div>'
    return f'<div class="mini-avatar-wrap"><div class="mini-avatar-fallback">{initial}</div></div>'


def avatar_big(row):
    url = thumb_url(row)
    name = str(row.get(channel_name_col, "?") if channel_name_col else "?")
    initial = safe_html(name[:1] if name else "?")
    if url:
        return f'<div class="detail-avatar-big"><img src="{safe_html(url)}" loading="lazy" referrerpolicy="no-referrer"></div>'
    return f'<div class="detail-avatar-big"><div class="mini-avatar-fallback">{initial}</div></div>'


def channel_link(name, row):
    safe_name = safe_html(name)
    if channel_url_col and channel_url_col in row.index:
        url = str(row.get(channel_url_col, "") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            return f'<a href="{safe_html(url)}" target="_blank" style="color:inherit;text-decoration:none;">{safe_name}</a>'
    return safe_name


def reason_short(row):
    for c in ["추천사유", "자동판정근거", "주의사유", "변화요약"]:
        if c in row.index and pd.notna(row.get(c)) and str(row.get(c)).strip():
            return str(row.get(c))
    seg = row.get(segment_col, "") if segment_col else ""
    return f"{seg} 콘텐츠 적합도 우수"

# =========================================================
# 15. 스타시드 본문
# =========================================================

html(f"""
<div class="starseed-board">
    <div class="board-hero board-hero-compact">
        <div class="board-head-left">
            <div class="board-title-icon">{SEED_ICON_HTML}</div>
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
        <div class="board-kpi-card"><div class="board-kpi-icon">👥</div><div><div class="board-kpi-label">전체 분석 후보</div><div class="board-kpi-value">{fmt_num(target_all_kpi['total'], 0, '명')}</div>{delta_badge(delta_total, 0, '명')}<span class="board-kpi-note">{compare_note}</span></div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">▾</div><div><div class="board-kpi-label">1차 선별 후보</div><div class="board-kpi-value">{fmt_num(target_all_kpi['shortlist'], 0, '명')}</div>{delta_badge(delta_shortlist, 0, '명')}<span class="board-kpi-note">{compare_note}</span></div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">★</div><div><div class="board-kpi-label">평균 영입 점수</div><div class="board-kpi-value">{fmt_num(target_filtered_kpi['avg_score'], 1, '점')}</div>{delta_badge(delta_avg_score, 1, '점')}<span class="board-kpi-note">{compare_note}</span></div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">◎</div><div><div class="board-kpi-label">즉시 검토 후보</div><div class="board-kpi-value">{fmt_num(target_filtered_kpi['high_priority'], 0, '명')}</div>{delta_badge(delta_high_priority, 0, '명')}<span class="board-kpi-note">{compare_note}</span></div></div>
    </div>
</div>
""")

# TOP 5
top_candidates = filtered.head(5).copy()
mini_cards = []
for i, (_, row) in enumerate(top_candidates.iterrows()):
    name = row.get(channel_name_col, "-") if channel_name_col else "-"
    score = row.get("_score_display", np.nan)
    action = row.get(action_col, "") if action_col else ""
    mini_cards.append(
        f'<div class="mini-candidate-card"><div class="mini-rank">{i + 1}</div>{avatar_small(row)}<div class="mini-name">{channel_link(name, row)}</div><div class="mini-score">{fmt_num(score, 1, "점")}</div><span class="mini-stage">{safe_html(action or "검토")}</span></div>'
    )
html(f'<div class="board-panel"><div class="board-panel-title">✩ 우선 검토 추천 후보 TOP 5</div><div class="top5-grid">{"".join(mini_cards)}</div></div>')

# 우선순위 / 상세
priority_df = filtered.head(8).copy()
priority_rows = []
for i, (_, row) in enumerate(priority_df.iterrows()):
    name = row.get(channel_name_col, "-") if channel_name_col else "-"
    segment = row.get(segment_col, "-") if segment_col else "-"
    action = row.get(action_col, "-") if action_col else "-"
    score = row.get("_score_display", np.nan)
    priority_rows.append(
        f'<tr><td style="width:9%;">{i + 1}</td><td class="name" style="width:30%;">{channel_link(short_text(name, 18), row)}</td><td style="width:24%;">{tag(segment)}</td><td style="width:17%;">{action_tag(action)}</td><td class="priority-score" style="width:12%;">{fmt_num(score, 1, "")}</td></tr>'
    )

recent_priority_rows = []
if not mini_tracking_df.empty:
    for _, r in mini_tracking_df.head(8).iterrows():
        recent_priority_rows.append(
            f'<tr><td class="name" style="width:28%;">{safe_html(short_text(r.get("채널명", "-"), 18))}</td><td style="width:13%;">{fmt_num(r.get("이전순위", np.nan), 0, "")}</td><td style="width:13%;">{fmt_num(r.get("현재순위", np.nan), 0, "")}</td><td style="width:17%; color:#ff838d; font-weight:950;">▲ {fmt_num(abs(float(r.get("순위변동", 0) or 0)), 0, "")}</td><td class="priority-score" style="width:13%;">{fmt_num(r.get("현재점수", np.nan), 1, "")}</td><td style="width:16%;">{action_tag(r.get("현재단계", "-"))}</td></tr>'
        )

candidate_select_df = filtered.copy()
if channel_name_col and not candidate_select_df.empty:
    candidate_select_df = candidate_select_df[candidate_select_df[channel_name_col].notna()].copy()
    candidate_select_df[channel_name_col] = candidate_select_df[channel_name_col].astype(str)
    candidate_select_df = candidate_select_df.drop_duplicates(subset=[channel_name_col], keep="first")
    selected_options = candidate_select_df[channel_name_col].tolist()
else:
    selected_options = []

left_col, right_col = st.columns([0.58, 0.42], gap="small")

with left_col:
    def set_priority_mode(mode: str) -> None:
        st.session_state["priority_table_view_mode"] = mode

    current_priority_mode = st.session_state.get("priority_table_view_mode", "영입 우선순위 TOP")
    if current_priority_mode not in ["영입 우선순위 TOP", "최근 순위 상승 후보"]:
        current_priority_mode = "영입 우선순위 TOP"
        st.session_state["priority_table_view_mode"] = current_priority_mode

    title_col, mode_col_1, mode_col_2 = st.columns([0.42, 0.29, 0.29], gap="small")
    with mode_col_1:
        st.button("영입 우선순위 TOP", key="priority_mode_top_button", use_container_width=True, type="primary" if current_priority_mode == "영입 우선순위 TOP" else "secondary", on_click=set_priority_mode, args=("영입 우선순위 TOP",))
    with mode_col_2:
        st.button("최근 순위 상승 후보", key="priority_mode_recent_button", use_container_width=True, type="primary" if current_priority_mode == "최근 순위 상승 후보" else "secondary", on_click=set_priority_mode, args=("최근 순위 상승 후보",))

    priority_view_mode = st.session_state.get("priority_table_view_mode", "영입 우선순위 TOP")
    priority_title_label = "🏆 영입 우선순위 TOP" if priority_view_mode == "영입 우선순위 TOP" else "📈 최근 순위 상승 후보"
    with title_col:
        st.markdown(f'<div class="priority-header-title">{priority_title_label}</div>', unsafe_allow_html=True)

    if priority_view_mode == "영입 우선순위 TOP":
        html(f'<div class="board-panel priority-table-panel"><table class="priority-table"><thead><tr><th>순위</th><th>스트리머명</th><th>주요 콘텐츠군</th><th>검토단계</th><th>점수</th></tr></thead><tbody>{"".join(priority_rows)}</tbody></table></div>')
    else:
        if recent_priority_rows:
            html(f'<div class="board-panel priority-table-panel"><table class="priority-table"><thead><tr><th>후보</th><th>이전</th><th>현재</th><th>상승</th><th>점수</th><th>단계</th></tr></thead><tbody>{"".join(recent_priority_rows)}</tbody></table></div>')
        else:
            html('<div class="board-panel priority-table-panel"><div class="board-info-text">비교 가능한 최근 순위 상승 후보 데이터가 없습니다.</div></div>')

    with st.expander("표 보는 방법", expanded=False):
        if priority_view_mode == "영입 우선순위 TOP":
            st.markdown('<div class="explain-box"><b>읽는 법</b>: 현재 필터 조건에서 영입 우선순위가 높은 후보를 순위대로 보여줍니다. 점수뿐 아니라 주요 콘텐츠군과 검토단계를 함께 확인해야 합니다.<br><br><b>도출 가능한 인사이트</b>: 상위권에 반복적으로 등장하는 콘텐츠군은 우선 탐색 풀이 두꺼운 영역입니다. 점수가 높고 검토단계가 즉시검토인 후보는 우선 컨택 또는 수기 검증 대상으로 볼 수 있습니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="explain-box"><b>읽는 법</b>: 이전 시점 대비 현재 순위가 크게 상승한 후보를 보여줍니다. 상승 폭, 현재 점수, 현재 검토단계를 함께 확인합니다.<br><br><b>도출 가능한 인사이트</b>: 순위가 크게 오른 후보는 최근 데이터 반영 이후 주목도가 상승한 후보입니다. 다만 현재 단계가 보류라면 수치 상승 원인과 리스크 플래그를 먼저 검토하는 것이 좋습니다.</div>', unsafe_allow_html=True)

with right_col:
    if selected_options:
        st.markdown('<div class="candidate-select-top-spacer"></div>', unsafe_allow_html=True)
        previous_selected = st.session_state.get("mock_selected_candidate")
        selected_index = selected_options.index(previous_selected) if previous_selected in selected_options else 0
        selected_name = st.selectbox("선택 후보", options=selected_options, index=selected_index, key="mock_selected_candidate", label_visibility="collapsed")
        selected_match = candidate_select_df[candidate_select_df[channel_name_col].astype(str) == str(selected_name)]
        selected_row = selected_match.iloc[0] if not selected_match.empty else candidate_select_df.iloc[0]
        sel_name = selected_row.get(channel_name_col, "-") if channel_name_col else "-"
        sel_action = selected_row.get(action_col, "-") if action_col else "-"
        sel_score = selected_row.get("_score_display", np.nan)
        sel_growth = selected_row.get(growth_col, np.nan) if growth_col else np.nan
        sel_subs = selected_row.get(subs_col, np.nan) if subs_col else np.nan
        sel_fan = selected_row.get(fan_col, np.nan) if fan_col else np.nan
        bullets = [x.strip() for x in str(reason_short(selected_row)).replace("/", "|").split("|") if x.strip()][:4]
        if not bullets:
            bullets = ["최종점수 상위권", "콘텐츠 적합도 양호", "실전성 리스크 낮음"]
        reason_html = "".join([f'<div class="reason-bullet">{safe_html(short_text(b, 22))}</div>' for b in bullets])
        html(f"""
        <div class="board-panel detail-panel-v2">
            <div class="board-panel-title">👥 선택한 후보 상세 보기</div>
            <div class="detail-card-inner-v2">
                <div class="detail-avatar-area">{avatar_big(selected_row)}</div>
                <div class="detail-content-area">
                    <div class="detail-name-row"><div class="detail-name-main">{channel_link(sel_name, selected_row)}</div>{action_tag(sel_action)}</div>
                    <div class="detail-metric-grid">
                        <div class="detail-metric-box"><div class="detail-metric-label">추천 점수</div><div class="detail-metric-value">{fmt_num(sel_score, 1, '점')}</div></div>
                        <div class="detail-metric-box"><div class="detail-metric-label">성장성</div><div class="detail-metric-value">{fmt_num(sel_growth, 3, '')}</div></div>
                        <div class="detail-metric-box"><div class="detail-metric-label">구독자수</div><div class="detail-metric-value">{fmt_num(sel_subs, 0, '')}</div></div>
                        <div class="detail-metric-box"><div class="detail-metric-label">팬밀도</div><div class="detail-metric-value">{fmt_num(sel_fan, 3, '')}</div></div>
                    </div>
                </div>
                <div class="reason-panel detail-reason-bottom"><div class="reason-title">왜 추천되었나요?</div>{reason_html}</div>
            </div>
        </div>
        """)
    else:
        html('<div class="board-panel"><div class="board-panel-title">👥 선택 후보 상세</div><div class="board-info-text">표시할 후보가 없습니다.</div></div>')

# =========================================================
# 16. 후보군 비교 그래프
# =========================================================

classified_filtered = filtered.copy()
if segment_col and segment_col in classified_filtered.columns:
    unclassified_mask = classified_filtered[segment_col].fillna("미분류").astype(str).str.contains("미분류|None|nan", case=False, na=False)
    classified_filtered = classified_filtered[~unclassified_mask].copy()

GRAPH_OPTIONS = ["콘텐츠 유형별 추천 점수", "검토 단계별 후보 분포", "후보군 콘텐츠 비율"]

def set_graph_view(mode: str) -> None:
    st.session_state["mock_graph_view"] = mode

current_graph_view = st.session_state.get("mock_graph_view", GRAPH_OPTIONS[0])
if current_graph_view not in GRAPH_OPTIONS:
    current_graph_view = GRAPH_OPTIONS[0]
    st.session_state["mock_graph_view"] = current_graph_view

graph_title_col, graph_btn_col_1, graph_btn_col_2, graph_btn_col_3 = st.columns([0.34, 0.22, 0.22, 0.22], gap="small")
with graph_title_col:
    st.markdown('<div class="graph-header-title">📊 후보군 비교 그래프</div>', unsafe_allow_html=True)
with graph_btn_col_1:
    st.button("콘텐츠 유형별 추천 점수", key="graph_view_score_button", use_container_width=True, type="primary" if current_graph_view == "콘텐츠 유형별 추천 점수" else "secondary", on_click=set_graph_view, args=("콘텐츠 유형별 추천 점수",))
with graph_btn_col_2:
    st.button("검토 단계별 후보 분포", key="graph_view_bucket_button", use_container_width=True, type="primary" if current_graph_view == "검토 단계별 후보 분포" else "secondary", on_click=set_graph_view, args=("검토 단계별 후보 분포",))
with graph_btn_col_3:
    st.button("후보군 콘텐츠 비율", key="graph_view_ratio_button", use_container_width=True, type="primary" if current_graph_view == "후보군 콘텐츠 비율" else "secondary", on_click=set_graph_view, args=("후보군 콘텐츠 비율",))

graph_view = st.session_state.get("mock_graph_view", GRAPH_OPTIONS[0])
graph_left, graph_right = st.columns([0.23, 0.77], gap="small")

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
            seg_summary = seg_score.groupby("__segment__", dropna=False).agg(추천점수=("__score__", "mean"), 후보수=("__score__", "size")).reset_index().sort_values("추천점수", ascending=False).head(8)
            fig = px.bar(seg_summary, x="__segment__", y="추천점수", text="추천점수", custom_data=["후보수"], color="__segment__", color_discrete_sequence=COSMIC_COLORS, template="plotly_dark", height=282)
            fig.update_traces(texttemplate="%{y:.1f}", textposition="outside", cliponaxis=False, hovertemplate="콘텐츠군=%{x}<br>추천점수=%{y:.1f}<br>후보수=%{customdata[0]}명<extra></extra>")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=12, r=12, t=16, b=54), xaxis_title="", yaxis_title="추천 점수", xaxis=dict(tickangle=0, tickfont=dict(size=10, color="#d7cdeb")), yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")), font=dict(color="#eee8ff"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("콘텐츠군별 점수를 만들 수 있는 컬럼이 부족합니다.")
    elif graph_view == "검토 단계별 후보 분포":
        if action_col and action_col in filtered.columns:
            bucket_order = ["즉시검토", "성장관찰", "검증필요", "보류", "제외", "미분류"]
            bucket_df = filtered[action_col].fillna("미분류").astype(str).value_counts().rename_axis("검토단계").reset_index(name="후보수")
            bucket_df["정렬"] = bucket_df["검토단계"].apply(lambda x: bucket_order.index(x) if x in bucket_order else 999)
            bucket_df = bucket_df.sort_values(["정렬", "후보수"], ascending=[True, False])
            fig = px.bar(bucket_df, x="후보수", y="검토단계", orientation="h", text="후보수", color="검토단계", color_discrete_sequence=COSMIC_COLORS, template="plotly_dark", height=282)
            fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="검토단계=%{y}<br>후보수=%{x}명<extra></extra>")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=8, r=32, t=12, b=30), xaxis_title="", yaxis_title="", xaxis=dict(gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")), yaxis=dict(tickfont=dict(color="#d7cdeb")), font=dict(color="#eee8ff"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("검토 단계 컬럼이 없어 그래프를 만들 수 없습니다.")
    else:
        if segment_col and segment_col in classified_filtered.columns and not classified_filtered.empty:
            pie_df = classified_filtered[segment_col].fillna("미분류").astype(str).value_counts().reset_index()
            pie_df.columns = ["구분", "후보수"]
            fig = px.pie(pie_df, names="구분", values="후보수", hole=.58, color_discrete_sequence=COSMIC_COLORS, template="plotly_dark", height=282)
            fig.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color="rgba(7,10,24,.85)", width=2)), hovertemplate="콘텐츠군=%{label}<br>후보수=%{value}명<br>비중=%{percent}<extra></extra>")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=6, r=6, t=6, b=6), legend=dict(font=dict(size=12, color="#eee8ff"), title_font=dict(size=12, color="#eee8ff"), x=1.02, y=.5, yanchor="middle"), font=dict(color="#eee8ff"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("콘텐츠군 구성 비율을 만들 수 없습니다.")

# =========================================================
# 17. 설명 Expander
# =========================================================

with st.expander("KPI 해석 방법", expanded=False):
    st.markdown(
        '<div class="explain-box"><b>분석한 전체 채널</b>: 수집/전처리 후 대시보드에 올라온 전체 후보 수입니다.<br><br><b>1차 조건 통과 후보</b>: shortlist 또는 주요 액션버킷 기준으로 사람이 실제 검토할 수 있는 후보군입니다.<br><br><b>추천 점수 평균</b>: 현재 필터 조건에 남은 후보들의 평균 영입 점수입니다.<br><br><b>바로 검토할 후보</b>: 우선 컨택 또는 수기 검증을 빠르게 진행할 만한 후보 수입니다.</div>',
        unsafe_allow_html=True,
    )

with st.expander("영입 점수 설명", expanded=False):
    st.markdown(
        '<div class="explain-box"><b>기본 산식</b><br><code>영입점수 = 0.22×채널력 + 0.28×성장성 + 0.22×팬밀도 + 0.15×라이브친화 + 0.13×실전성 - 리스크 감점</code><br><br>성장성에 가장 높은 가중치를 둔 이유는 신생 플랫폼 입장에서 이미 너무 큰 채널보다, 최근 반응과 성장 흐름이 확인되는 후보가 영입 현실성이 높다고 보았기 때문입니다. 채널력과 팬밀도는 최소 체급과 팬덤 결집력을 균형 있게 반영하고, 라이브친화와 실전성은 실제 방송 전환 가능성과 운영 리스크를 보정합니다.</div>',
        unsafe_allow_html=True,
    )
