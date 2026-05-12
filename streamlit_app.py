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

    st.markdown(
        f"""
        <style>html body .stApp button[data-testid="stBaseButton-primary"],html body .stApp button[data-testid="baseButton-primary"],html body .stApp button[kind="primary"]{{background:{primary_bg}!important;background-color:transparent !important;color:#F8FFF9 !important;border:1px solid{primary_border}!important;box-shadow:{primary_shadow}!important}}html body .stApp button[data-testid="stBaseButton-primary"] *,html body .stApp button[data-testid="baseButton-primary"] *,html body .stApp button[kind="primary"] *{{color:#F8FFF9 !important;font-weight:900 !important}}html body .stApp button[data-testid="stBaseButton-primary"]:hover,html body .stApp button[data-testid="baseButton-primary"]:hover,html body .stApp button[kind="primary"]:hover{{background:{primary_bg_hover}!important;border-color:{primary_border_hover}!important}}html body .stApp button[data-testid="stBaseButton-secondary"],html body .stApp button[data-testid="baseButton-secondary"],html body .stApp button[kind="secondary"]{{background:rgba(7,18,34,0.86) !important;background-color:rgba(7,18,34,0.86) !important;color:#EDE5FF !important;border:1px solid{secondary_border}!important;box-shadow:none !important}}html body .stApp button[data-testid="stBaseButton-secondary"] *,html body .stApp button[data-testid="baseButton-secondary"] *,html body .stApp button[kind="secondary"] *{{color:#EDE5FF !important;font-weight:850 !important}}html body .stApp button[data-testid="stBaseButton-secondary"]:hover,html body .stApp button[data-testid="baseButton-secondary"]:hover,html body .stApp button[kind="secondary"]:hover{{background:rgba(13,34,42,0.92) !important;border-color:{secondary_hover_border}!important}}</style>
        """,
        unsafe_allow_html=True,
    )


inject_button_theme_by_page()


if "bg_html" not in st.session_state:
    random.seed(42)
    stars = []
    for _ in range(64):
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
        <style>#MainMenu,footer,[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stDeployButton"],[data-testid="stAppDeployButton"],.stDeployButton,.stAppDeployButton,button[title="Deploy"],button[aria-label="Deploy"],a[title="Deploy"],a[aria-label="Deploy"]{display:none !important;visibility:hidden !important;opacity:0 !important;pointer-events:none !important}:root{--cime-sidebar-width:300px;--cime-sidebar-toggle-top:22px;--cime-sidebar-toggle-size:34px;--cime-sidebar-toggle-left:16px;--seed-green:#83F6A0;--seed-purple-line:rgba(154,98,255,0.36)}header,header[data-testid="stHeader"],[data-testid="stHeader"]{display:block !important;visibility:visible !important;opacity:1 !important;pointer-events:none !important;height:2.4rem !important;min-height:2.4rem !important;max-height:2.4rem !important;overflow:visible !important;background:transparent !important;z-index:999990 !important}header [data-testid="stToolbar"],[data-testid="stToolbar"],.stAppToolbar,div[class*="stAppToolbar"]{display:none !important;visibility:hidden !important;opacity:0 !important;pointer-events:none !important;width:0 !important;height:0 !important;overflow:hidden !important}.stApp{background:radial-gradient(circle at 56% 31%,rgba(127,47,255,0.34),transparent 30%),radial-gradient(circle at 78% 7%,rgba(93,224,131,0.075),transparent 24%),radial-gradient(circle at 60% 79%,rgba(121,51,255,0.13),transparent 33%),linear-gradient(180deg,#050411 0%,#09051C 52%,#050411 100%) !important;color:#F8F2FF}.stApp::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background-image:radial-gradient(circle,rgba(255,255,255,0.60) 0.7px,transparent 1.2px),radial-gradient(circle,rgba(200,168,255,0.32) 0.6px,transparent 1.3px);background-size:72px 72px,128px 128px;background-position:0 0,18px 24px;opacity:0.08}.block-container{position:relative;z-index:1;max-width:1380px !important;padding-top:0 !important;padding-left:2rem !important;padding-right:2rem !important;padding-bottom:2.5rem !important}section[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(7,8,24,.99),rgba(4,6,18,.99)) !important;border-right:1px solid var(--seed-purple-line) !important;box-shadow:10px 0 32px rgba(0,0,0,.28) !important;z-index:999996 !important}section[data-testid="stSidebar"]>div:first-child{padding-top:4.1rem !important}@media (min-width:900px){section[data-testid="stSidebar"][aria-expanded="true"]{flex:0 0 var(--cime-sidebar-width) !important;width:var(--cime-sidebar-width) !important;min-width:var(--cime-sidebar-width) !important;max-width:var(--cime-sidebar-width) !important;overflow:hidden auto !important}}.star-layer{position:fixed;left:300px;top:0;right:0;bottom:0;pointer-events:none;z-index:0;overflow:hidden;opacity:.72}.twinkle-star{position:absolute;border-radius:50%;background:white;pointer-events:none;z-index:0;box-shadow:0 0 6px rgba(255,255,255,.55),0 0 12px rgba(198,168,255,.28);animation-name:twinkle;animation-timing-function:ease-in-out;animation-iteration-count:infinite}.twinkle-star:nth-child(3n){background:#C8A8FF}.twinkle-star:nth-child(5n){background:#FF9DF5}@keyframes twinkle{0%,100%{opacity:.12;transform:scale(.65)}45%{opacity:var(--max-opacity);transform:scale(1.35)}65%{opacity:.38;transform:scale(.95)}}.orbit-bg{position:fixed;left:300px;top:0;right:0;bottom:0;z-index:0;pointer-events:none;opacity:.28;background:linear-gradient(150deg,transparent 15%,rgba(157,88,255,.10) 15.4%,transparent 16.5%),linear-gradient(150deg,transparent 34%,rgba(157,88,255,.07) 34.4%,transparent 35.5%)}.sidebar-title{font-size:22px;font-weight:900;letter-spacing:1px;color:#FFF9FF;margin-bottom:18px}.sidebar-subtitle{font-size:10px;font-weight:800;letter-spacing:1.2px;color:var(--seed-green) !important;margin-bottom:64px}.sidebar-line{height:1px;background:rgba(185,147,255,.28);margin:0 0 24px 0}section[data-testid="stSidebar"] .stButton>button{width:100%;height:43px;border-radius:8px;font-size:16px;font-weight:850;letter-spacing:-.3px;margin-bottom:8px;transition:all .18s ease}section[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,rgba(28,174,88,.95),rgba(15,105,70,.96)) !important;color:#F5FFF7 !important;border:1px solid rgba(131,246,160,.42) !important;box-shadow:0 0 10px rgba(80,220,120,.12),inset 0 1px 0 rgba(255,255,255,.08) !important}section[data-testid="stSidebar"] .stButton>button[kind="secondary"]{background:rgba(20,16,48,.78) !important;color:#EDE5FF !important;border:1px solid rgba(196,143,255,.26) !important;box-shadow:none !important}section[data-testid="stSidebar"] div[data-testid="stExpander"]{background:rgba(18,13,44,.78) !important;border:1px solid rgba(199,168,255,.28) !important;border-radius:14px !important;margin:10px 0 !important}section[data-testid="stSidebar"] div[data-testid="stExpander"] summary{color:#F8F2FF !important;font-weight:900 !important}section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] .stCaptionContainer,section[data-testid="stSidebar"] .stMarkdown p{color:#DED5F8 !important}.main-wrap{position:relative;z-index:2;text-align:center}.hero-title{font-size:58px;font-weight:950;letter-spacing:9px;line-height:1;color:#FFF8FF;text-shadow:0 0 22px rgba(230,195,255,.35);margin:4px 0 14px}.hero-subtitle{font-size:19px;font-weight:750;color:#C6BBD9;margin-bottom:10px}.block-container:has(.planet-home-wrap){padding-top:0 !important;margin-top:0rem !important;padding-bottom:2.2rem !important}.planet-home-wrap{transform:translateY(0px) !important;margin-bottom:0px !important}.planet-area{position:relative;height:326px;display:flex;align-items:center;justify-content:center;margin-top:-12px;margin-bottom:-6px}.planet-glow{position:absolute;width:440px;height:440px;border-radius:50%;background:radial-gradient(circle,rgba(139,53,255,.45) 0%,rgba(139,53,255,.18) 34%,transparent 68%);filter:blur(14px)}.planet-orbit{position:absolute;width:790px;height:220px;border:2px solid rgba(179,93,255,.46);border-radius:50%;transform:rotate(-2deg);box-shadow:0 0 26px rgba(179,93,255,.16)}.planet-orbit.orbit-2{width:625px;height:176px;border-color:rgba(239,156,255,.42);transform:rotate(1deg)}.planet-orbit.orbit-3{width:920px;height:285px;border-color:rgba(125,66,255,.20);transform:rotate(-4deg)}.planet{position:relative;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle at 72% 28%,rgba(246,166,255,.55),transparent 20%),radial-gradient(circle at 58% 44%,rgba(147,55,255,.95),transparent 38%),radial-gradient(circle at 42% 58%,rgba(42,8,110,.95),transparent 48%),radial-gradient(circle at 50% 50%,#4812A7 0%,#270066 48%,#08011B 100%);box-shadow:0 0 34px rgba(246,166,255,.62),0 0 100px rgba(139,53,255,.55),inset 22px 18px 48px rgba(255,170,255,.20),inset -48px -44px 78px rgba(0,0,0,.55);overflow:hidden}.planet-logo{position:absolute;inset:0;z-index:2;display:flex;align-items:center;justify-content:center;font-size:45px;font-weight:950;letter-spacing:5px;color:#FFF8FF;text-shadow:0 0 10px rgba(255,255,255,.85),0 0 22px rgba(234,203,255,.9)}.satellite{position:absolute;width:16px;height:16px;border-radius:50%;box-shadow:0 0 18px currentColor}.sat-1{color:#FF6BF1;background:#FF6BF1;transform:translate(365px,8px)}.sat-2{color:#FFD45D;background:#FFD45D;transform:translate(-350px,62px)}.sat-3{color:#95AFFF;background:#95AFFF;transform:translate(-240px,-66px)}.sat-4{color:#C681FF;background:#C681FF;transform:translate(240px,-62px)}.sat-5{color:#7DFF8A;background:#7DFF8A;transform:translate(470px,-72px)}.mission-card{min-height:255px;border-radius:26px;background:rgba(21,16,47,.90);border:1px solid rgba(255,255,255,.08);box-shadow:0 0 28px rgba(112,53,255,.18),inset 0 0 28px rgba(255,255,255,.025);padding:28px 38px 76px;text-align:left;position:relative;overflow:hidden}.mission-card::before{content:"";position:absolute;left:28px;right:28px;top:22px;height:3px;border-radius:3px}.trail-card{border-color:rgba(255,212,93,.42)}.seed-card{border-color:rgba(152,255,171,.38)}.trail-card::before{background:#FFD45D;box-shadow:0 0 16px rgba(255,212,93,.55)}.seed-card::before{background:#98FFAB;box-shadow:0 0 16px rgba(152,255,171,.45)}.card-head{display:flex;align-items:center;gap:24px;margin-top:20px;margin-bottom:26px}.icon-box{width:66px;height:66px;border-radius:18px;display:flex;align-items:center;justify-content:center;overflow:hidden}.trail-icon-box{background:rgba(255,212,93,.12);border:1px solid rgba(255,212,93,.34)}.seed-icon-box{background:rgba(152,255,171,.10);border:1px solid rgba(152,255,171,.30)}.card-title{font-size:40px;font-weight:950;color:#FFF9FF;line-height:1.05}.card-en{font-size:27px;font-weight:900;margin-top:6px}.trail-en{color:#FFD45D}.seed-en{color:#98FFAB}.card-desc{font-size:19px;line-height:1.7;color:#D9CFE8;font-weight:560}.trail-point,.trail-soft-point{color:#FFD45D;font-weight:850}.seed-point,.seed-soft-point{color:#98FFAB;font-weight:750}section.main .stButton>button{width:100%;height:44px;border-radius:15px;background:rgba(255,255,255,.035) !important;color:#FFF9FF !important;border:1px solid rgba(255,255,255,.13) !important;font-size:16px;font-weight:850;margin-top:-60px;position:relative;z-index:20}.detail-box{position:relative;z-index:3;max-width:1380px;margin:42px auto 0;border-radius:26px;background:linear-gradient(135deg,rgba(21,16,47,.94),rgba(16,12,34,.94));border:1px solid rgba(196,143,255,.34);box-shadow:0 0 36px rgba(125,66,255,.20),inset 0 0 30px rgba(255,255,255,.025);padding:42px 48px 48px;text-align:left}.detail-phase-head{display:flex;align-items:center;gap:18px;margin-bottom:24px}.detail-phase-icon{width:54px;height:54px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}.detail-phase-title-row{display:flex;align-items:baseline;gap:12px;line-height:1.05}.detail-phase-ko{font-size:34px;font-weight:950;letter-spacing:-1.1px}.detail-phase-en{font-size:22px;font-weight:850;color:rgba(255,255,255,.90)}.detail-phase-trail .detail-phase-ko{color:#FFD45D}.detail-phase-seed .detail-phase-ko{color:#98FFAB}.detail-title{font-size:34px;line-height:1.35;font-weight:950;color:#FFF9FF;margin-bottom:24px}.detail-text{font-size:19px;line-height:1.9;color:#D9CFE8;font-weight:520;margin-bottom:34px;word-break:keep-all}.segment-grid,.seed-grid{display:grid;gap:18px;align-items:stretch;grid-template-columns:repeat(5,minmax(0,1fr))}.segment-card,.seed-step-card{position:relative;overflow:hidden;border-radius:18px;padding:28px 20px 26px;background:rgba(255,255,255,.038);border:1px solid rgba(255,255,255,.12);min-height:250px;display:flex;flex-direction:column;align-items:center;text-align:center}.seed-step-card{border-color:rgba(152,255,171,.18);background:radial-gradient(circle at 50% 0%,rgba(152,255,171,.085),transparent 42%),rgba(255,255,255,.038)}.segment-head{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;min-height:132px;margin-bottom:8px}.segment-icon-badge{width:58px;height:58px;border-radius:18px;display:flex;align-items:center;justify-content:center;margin:0 auto 15px;font-size:27px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05)}.icon-cluster{color:#FFD45D;background:rgba(255,212,93,.10);border-color:rgba(255,212,93,.25)}.icon-protostar{color:#98FFAB;background:rgba(152,255,171,.10);border-color:rgba(152,255,171,.25)}.icon-satellite{color:#8FB8FF;background:rgba(143,184,255,.10);border-color:rgba(143,184,255,.25)}.icon-supernova{color:#FF7AC8;background:rgba(255,122,200,.10);border-color:rgba(255,122,200,.25)}.icon-comet{color:#FF9E5E;background:rgba(255,158,94,.10);border-color:rgba(255,158,94,.25)}.segment-ko,.seed-title{color:#FFF9FF;font-size:20px;line-height:1.35;font-weight:950;margin-bottom:8px}.segment-en{color:#F08CFF;font-size:13px;font-weight:950;text-align:center}.segment-purpose{color:rgba(255,255,255,.82);font-size:14px;line-height:1.55;font-weight:760;padding:12px 13px;margin-bottom:20px;border-radius:12px;background:rgba(240,140,255,.10);border:1px solid rgba(240,140,255,.22);min-height:74px;display:flex;align-items:center;justify-content:center;text-align:center;word-break:keep-all}.purpose-key{display:inline-block;margin-top:2px;color:#fff;font-size:16px;font-weight:950}.field-label{color:#F0B5FF;font-size:12px;font-weight:950;margin-top:12px;margin-bottom:6px}.field-value{color:rgba(255,255,255,.76);font-size:14px;line-height:1.7;word-break:keep-all}.seed-desc{color:rgba(255,255,255,.76);font-size:15px;line-height:1.65;font-weight:560;word-break:keep-all;min-height:50px}.seed-icon-orbit{width:82px;height:82px;border-radius:999px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;background:radial-gradient(circle,rgba(152,255,171,.18) 0%,rgba(152,255,171,.06) 58%,transparent 72%);border:1px solid rgba(152,255,171,.28)}.seed-icon-badge{width:56px;height:56px;display:flex;align-items:center;justify-content:center;position:relative;background:transparent}.seed-icon-badge::before,.seed-icon-badge::after{content:"";position:absolute;box-sizing:border-box}.seed-icon-search::before{width:28px;height:28px;border:3.4px solid #98FFAB;border-radius:50%;left:10px;top:9px}.seed-icon-search::after{width:20px;height:3.4px;background:#98FFAB;border-radius:999px;left:33px;top:35px;transform:rotate(45deg)}.seed-icon-chat::before{width:34px;height:24px;border:3px solid #98FFAB;border-radius:9px;left:10px;top:14px}.seed-icon-chat::after{width:10px;height:10px;border-right:3px solid #98FFAB;border-bottom:3px solid #98FFAB;left:20px;top:34px;transform:rotate(45deg)}.seed-icon-live::before{width:30px;height:22px;border:3px solid #98FFAB;border-radius:7px;left:8px;top:17px}.seed-icon-live::after{width:15px;height:15px;border-top:3px solid #98FFAB;border-right:3px solid #98FFAB;left:34px;top:20px;transform:rotate(45deg)}.seed-icon-filter::before{width:38px;height:30px;border-top:4px solid #98FFAB;border-left:4px solid transparent;border-right:4px solid transparent;left:9px;top:13px}.seed-icon-filter::after{width:8px;height:20px;background:#98FFAB;border-radius:999px;left:24px;top:28px}.seed-icon-check::before{width:36px;height:36px;border:3.4px solid #98FFAB;border-radius:10px;left:10px;top:10px}.seed-icon-check::after{width:21px;height:12px;border-left:4.5px solid #98FFAB;border-bottom:4.5px solid #98FFAB;left:18px;top:21px;transform:rotate(-45deg)}.seed-mini-line{width:28px;height:2px;border-radius:999px;background:rgba(152,255,171,.92);margin:0 auto 14px}.empty-guide{position:relative;z-index:3;margin-top:34px;font-size:15px;color:rgba(191,181,213,.72);text-align:center}.page-panel{position:relative;z-index:3;border-radius:22px;background:rgba(21,16,47,.86);border:1px solid rgba(196,143,255,.26);padding:36px 40px;margin-top:30px;color:rgba(255,255,255,.78);line-height:1.8}.trail-spark-icon,.seed-search-icon{position:relative;width:56px;height:56px}.trail-spark-icon{color:#FFD45D}.seed-search-icon{color:#98FFAB}.trail-line{position:absolute;left:5px;height:3px;border-radius:999px;background:currentColor}.trail-line-1{top:22px;width:23px}.trail-line-2{top:31px;width:16px;opacity:.72}.trail-line-3{top:27px;left:13px;width:18px;opacity:.48}.trail-star{position:absolute;color:currentColor;line-height:1}.trail-star-main{left:30px;top:15px;font-size:30px}.trail-star-small{left:23px;top:6px;font-size:14px}.trail-star-tiny{left:17px;top:38px;font-size:10px}.trail-dot{position:absolute;width:3px;height:3px;border-radius:50%;background:currentColor}.trail-dot-1{left:44px;top:11px}.trail-dot-2{left:8px;top:40px;opacity:.75}.seed-lens{position:absolute;left:7px;top:7px;width:30px;height:30px;border:4px solid currentColor;border-radius:50%;box-sizing:border-box}.seed-handle{position:absolute;left:33px;top:35px;width:18px;height:4px;background:currentColor;border-radius:999px;transform:rotate(45deg);transform-origin:left center}.seed-star-core{position:absolute;left:15px;top:12px;font-size:18px;line-height:1;font-weight:900}.seed-sparkle-1{position:absolute;left:37px;top:7px;font-size:12px;line-height:1}.seed-sparkle-2{position:absolute;left:4px;top:35px;font-size:9px;line-height:1;opacity:.78}.seed-dot-1,.seed-dot-2{position:absolute;width:3px;height:3px;border-radius:50%;background:currentColor}.seed-dot-1{left:44px;top:18px}.seed-dot-2{left:11px;top:43px;opacity:.8}.starseed-loading-wrap{width:min(980px,92vw);margin:22vh auto 0;padding:34px 38px;border-radius:26px;border:1px solid rgba(118,242,226,.28);background:radial-gradient(circle at 16% 36%,rgba(95,255,232,.16),transparent 28%),radial-gradient(circle at 86% 20%,rgba(144,94,255,.24),transparent 30%),linear-gradient(145deg,rgba(9,22,42,.92),rgba(12,8,35,.92));box-shadow:0 24px 72px rgba(0,0,0,.42),inset 0 1px 0 rgba(255,255,255,.08);text-align:center;position:relative;overflow:hidden}.starseed-loading-orb{width:74px;height:74px;margin:0 auto 18px;border-radius:50%;background:radial-gradient(circle at 36% 30%,#fff 0 7%,#8cffb3 13%,#29d976 38%,#6b42ff 100%);box-shadow:0 0 18px rgba(140,255,179,.28),0 0 42px rgba(107,66,255,.20);position:relative;z-index:1}.starseed-loading-orb::after{content:"✦";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:white;font-size:30px}.starseed-loading-title{position:relative;z-index:1;font-size:32px;font-weight:950;color:#f6fffb;margin-bottom:10px}.starseed-loading-sub{position:relative;z-index:1;font-size:15px;line-height:1.65;color:#b8c9d8}.starseed-loading-steps{position:relative;z-index:1;display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:22px}.starseed-loading-chip{padding:7px 12px;border-radius:999px;background:rgba(95,255,232,.075);border:1px solid rgba(95,255,232,.18);color:#d9fff8;font-size:12px;font-weight:800}.startrail-loading-wrap{width:min(980px,92vw);margin:22vh auto 0;padding:34px 38px;border-radius:26px;border:1px solid rgba(255,212,93,.32);background:radial-gradient(circle at 18% 36%,rgba(255,212,93,.18),transparent 28%),radial-gradient(circle at 86% 20%,rgba(196,143,255,.22),transparent 30%),linear-gradient(145deg,rgba(25,18,38,.94),rgba(10,8,30,.94));box-shadow:0 24px 72px rgba(0,0,0,.42),0 0 38px rgba(255,212,93,.10),inset 0 1px 0 rgba(255,255,255,.08);text-align:center;position:relative;overflow:hidden}.startrail-loading-wrap::before{content:"";position:absolute;left:12%;right:12%;top:26px;height:3px;border-radius:999px;background:linear-gradient(90deg,transparent,rgba(255,212,93,.78),rgba(255,245,186,.92),rgba(255,212,93,.48),transparent);box-shadow:0 0 22px rgba(255,212,93,.28)}.startrail-loading-orb{width:74px;height:74px;margin:0 auto 18px;border-radius:50%;background:radial-gradient(circle at 34% 28%,#fff 0 8%,#fff1a8 15%,#ffd45d 42%,#8b5cf6 100%);box-shadow:0 0 20px rgba(255,212,93,.34),0 0 46px rgba(139,92,255,.18);position:relative;z-index:1}.startrail-loading-orb::before{content:"";position:absolute;left:-28px;top:34px;width:58px;height:4px;border-radius:999px;background:linear-gradient(90deg,transparent,rgba(255,212,93,.78));box-shadow:0 0 16px rgba(255,212,93,.30)}.startrail-loading-orb::after{content:"✦";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#fffef0;font-size:30px;text-shadow:0 0 14px rgba(255,212,93,.62)}.startrail-loading-title{position:relative;z-index:1;font-size:32px;font-weight:950;color:#fff9e7;margin-bottom:10px}.startrail-loading-sub{position:relative;z-index:1;font-size:15px;line-height:1.65;color:#d8ccae}.startrail-loading-steps{position:relative;z-index:1;display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:22px}.startrail-loading-chip{padding:7px 12px;border-radius:999px;background:rgba(255,212,93,.085);border:1px solid rgba(255,212,93,.24);color:#fff3bc;font-size:12px;font-weight:800}.block-container:has(.starseed-board){padding-top:0 !important;margin-top:-.6rem !important;padding-bottom:2.5rem !important}.starseed-board{width:100%;padding:0 0 18px;margin-top:10px !important;position:relative;z-index:2}.board-hero,.board-hero-compact{display:grid !important;grid-template-columns:minmax(0,1fr) 560px !important;column-gap:22px !important;align-items:center !important;margin:0 0 10px !important;padding:0 !important}.board-head-left{display:grid !important;grid-template-columns:86px minmax(0,1fr) !important;gap:20px !important;min-height:88px !important;align-items:center !important}.board-title-icon{width:72px !important;height:72px !important;border-radius:12px !important;display:flex !important;align-items:center !important;justify-content:center !important;background:radial-gradient(circle at 45% 30%,rgba(131,246,160,.14),transparent 56%),rgba(12,20,38,.86) !important;border:2px solid rgba(238,235,255,.82) !important;box-shadow:0 0 10px rgba(131,246,160,.10),inset 0 1px 0 rgba(255,255,255,.08) !important;overflow:hidden !important}.board-title-icon .seed-search-icon{transform:scale(1.02) !important;transform-origin:center center !important}.board-title,.board-title-ko{font-size:39px !important;font-weight:950 !important;letter-spacing:-.055em !important;line-height:1.03 !important;color:#FFF8FF !important;margin:0 0 7px !important;text-shadow:0 1px 0 rgba(255,255,255,.10) !important;display:flex !important;align-items:baseline !important;gap:10px !important;white-space:nowrap !important}.board-title span{color:var(--seed-green) !important;font-size:31px !important;font-weight:950 !important;letter-spacing:-.035em !important;text-shadow:0 0 4px rgba(131,246,160,.10) !important}.board-title-accent-line{width:235px !important;height:2px !important;margin:0 0 9px 2px !important;border-radius:999px !important;background:linear-gradient(90deg,rgba(126,255,153,.84) 0%,rgba(126,255,153,.48) 42%,rgba(126,255,153,.14) 78%,rgba(126,255,153,0) 100%) !important}.board-subtitle{margin:0 !important;font-size:14.2px !important;font-weight:720 !important;line-height:1.45 !important;letter-spacing:-.035em !important;color:#D8D0E7 !important;text-align:left !important;white-space:nowrap !important}.board-info-card{display:grid;grid-template-columns:54px minmax(0,1fr) !important;gap:14px !important;align-items:center;min-height:76px !important;width:100% !important;border-radius:12px !important;border:1px solid rgba(131,246,160,.30) !important;background:radial-gradient(circle at 9% 50%,rgba(131,246,160,.10),transparent 28%),linear-gradient(135deg,rgba(11,35,28,.74),rgba(18,16,45,.82)) !important;box-shadow:0 10px 24px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.06) !important;padding:14px 22px 14px 18px !important;box-sizing:border-box !important;overflow:visible !important}.board-info-icon{width:42px !important;height:42px !important;border-radius:999px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px !important;background:radial-gradient(circle at 34% 26%,#F1FFF4,#58E984 48%,#11894D 100%) !important;box-shadow:0 0 12px rgba(88,233,132,.16) !important}.board-info-title{color:#F5FFF7 !important;font-size:13.2px !important;font-weight:950 !important;margin-bottom:4px !important;white-space:normal !important}.board-info-text{color:#D6E5D8 !important;font-size:12px !important;line-height:1.45 !important;word-break:keep-all !important;overflow-wrap:break-word !important;white-space:normal !important;overflow:visible !important;text-overflow:unset !important}.board-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px !important;margin:12px 0 !important;overflow:visible !important}.board-kpi-card{position:relative;overflow:visible;display:grid;grid-template-columns:52px 1fr;gap:13px;align-items:center;min-height:82px;border-radius:14px;padding:13px 16px;border:1px solid rgba(131,246,160,.16) !important;background:radial-gradient(circle at 10% 28%,rgba(131,246,160,.055),transparent 32%),linear-gradient(180deg,rgba(14,18,43,.86),rgba(6,11,27,.94)) !important;box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 12px 26px rgba(0,0,0,.24) !important}.board-kpi-icon{width:48px;height:48px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:23px;background:radial-gradient(circle at 34% 24%,rgba(255,255,255,.28),rgba(48,190,102,.78) 50%,rgba(12,78,56,.92) 100%) !important;box-shadow:0 0 10px rgba(80,255,146,.16) !important}.board-kpi-label{color:#D5E6DD !important;font-size:12px;font-weight:850;margin-bottom:3px}.board-kpi-value{color:#fff !important;font-size:25px;font-weight:950;line-height:1.1;letter-spacing:-.03em}.board-kpi-delta{display:inline-flex;align-items:center;gap:2px;margin-top:3px;font-size:10px;font-weight:900;border-radius:999px;padding:2px 7px;background:rgba(255,255,255,.05)}.board-kpi-delta.up{color:#ff7b86;background:rgba(255,91,108,.12)}.board-kpi-delta.down{color:#72b8ff;background:rgba(79,150,255,.12)}.board-kpi-delta.flat{color:#c4bad8;background:rgba(185,170,230,.10)}.board-kpi-note{display:inline-block;margin-left:6px;color:#92A995 !important;font-size:10px;font-weight:700}.board-kpi-label{display:flex !important;align-items:center !important;gap:5px !important;overflow:visible !important}.board-kpi-label .trail-tooltip-wrap{transform:translateY(0) !important}.board-kpi-label .trail-tooltip-icon{width:15px !important;height:15px !important;min-width:15px !important;font-size:9px !important;line-height:13px !important;border-color:rgba(131,246,160,.58) !important;color:#CFFFE0 !important;background:rgba(8,24,28,.94) !important}.board-kpi-label .trail-tooltip-text{width:245px !important;border-color:rgba(131,246,160,.28) !important;background:rgba(7,20,28,.98) !important;color:#DFFFF0 !important}.board-kpi-tooltip-wrap{position:relative !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;width:15px !important;height:15px !important;min-width:15px !important;margin-left:5px !important;vertical-align:middle !important;overflow:visible !important;z-index:999 !important}.board-kpi-tooltip-icon{width:15px !important;height:15px !important;min-width:15px !important;border-radius:50% !important;border:1px solid rgba(131,246,160,.62) !important;color:#DFFFF0 !important;background:rgba(8,24,28,.94) !important;font-size:9px !important;font-weight:950 !important;line-height:13px !important;text-align:center !important;cursor:help !important;box-sizing:border-box !important}.board-kpi-tooltip-text{display:block !important;visibility:hidden !important;opacity:0 !important;pointer-events:none !important;position:absolute !important;left:50% !important;bottom:145% !important;transform:translateX(-50%) !important;width:255px !important;max-width:255px !important;padding:10px 12px !important;border-radius:12px !important;border:1px solid rgba(131,246,160,.30) !important;background:rgba(7,20,28,.98) !important;color:#DFFFF0 !important;font-size:12px !important;font-weight:700 !important;line-height:1.45 !important;text-align:left !important;white-space:normal !important;word-break:keep-all !important;box-shadow:0 10px 28px rgba(0,0,0,.45) !important;z-index:99999 !important}.board-kpi-tooltip-wrap:hover .board-kpi-tooltip-text{visibility:visible !important;opacity:1 !important}.board-panel{border-radius:16px;border:1px solid rgba(131,246,160,.16) !important;background:linear-gradient(180deg,rgba(14,18,43,.86),rgba(6,11,27,.94)) !important;box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 12px 26px rgba(0,0,0,.24) !important;padding:12px 14px}.board-panel-title{display:flex;align-items:center;gap:8px;color:#f5efff;font-size:15px;font-weight:950;margin:0 0 10px}.top5-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px !important}.mini-candidate-card{position:relative;min-height:92px;border-radius:12px;border:1px solid rgba(131,246,160,.16) !important;background:radial-gradient(circle at 22% 48%,rgba(131,246,160,.055),transparent 42%),linear-gradient(180deg,rgba(14,20,45,.86),rgba(8,12,31,.97)) !important;padding:13px 12px 11px 104px;overflow:hidden;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box}.mini-rank{position:absolute;top:9px;left:9px;width:20px;height:20px;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#ffd86b;border:1px solid rgba(255,216,107,.75);background:rgba(42,29,72,.78);font-size:11px;font-weight:950}.mini-avatar-wrap{position:absolute;left:38px;top:50%;transform:translateY(-50%);width:54px;height:54px;border-radius:999px;overflow:hidden;background:radial-gradient(circle at 32% 28%,#fff,#8b5cf6 42%,#25154d 100%);border:2px solid rgba(131,246,160,.38) !important;box-shadow:0 0 12px rgba(131,246,160,.12) !important}.mini-avatar-wrap img{width:100%;height:100%;object-fit:cover;display:block}.mini-avatar-fallback{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:950;font-size:20px}.mini-name{color:#fff;font-size:13.5px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.15;max-width:100%}.mini-name a{color:inherit;text-decoration:none}.mini-score{color:#fff;font-size:17px;font-weight:950;margin-top:3px;line-height:1.1;white-space:nowrap;letter-spacing:-.02em}.mini-stage{display:inline-flex;align-items:center;justify-content:center;width:fit-content;max-width:94px;color:#DFFFF0 !important;background:linear-gradient(135deg,rgba(26,158,91,.86),rgba(9,88,62,.88)) !important;border:1px solid rgba(131,246,160,.28) !important;border-radius:999px;padding:3px 9px;font-size:10px;font-weight:900;margin-top:5px;white-space:nowrap}.priority-header-title,.graph-header-title{color:#fff7ff !important;font-size:24px !important;font-weight:950 !important;letter-spacing:-.04em !important;line-height:38px !important;white-space:nowrap !important;margin:0 !important;padding:0 !important;text-shadow:0 0 8px rgba(131,246,160,.12) !important}div[data-testid="column"] .stButton>button[kind="primary"],button[kind="primary"][data-testid="baseButton-primary"]{min-height:38px !important;height:38px !important;padding:6px 16px !important;border-radius:999px !important;font-size:13px !important;font-weight:900 !important;white-space:nowrap !important;background:linear-gradient(135deg,rgba(26,158,91,.92),rgba(12,92,65,.94)) !important;border-color:rgba(131,246,160,.32) !important;color:#F7FFF8 !important;box-shadow:none !important}div[data-testid="column"] .stButton>button[kind="secondary"],button[kind="secondary"][data-testid="baseButton-secondary"]{min-height:38px !important;height:38px !important;padding:6px 16px !important;border-radius:999px !important;font-size:13px !important;font-weight:900 !important;white-space:nowrap !important;background:rgba(7,18,34,.84) !important;border-color:rgba(131,246,160,.20) !important;color:#EAF7EF !important;box-shadow:none !important}.priority-table-panel{margin-top:0 !important;padding-top:10px !important;min-height:228px}.priority-table{width:100%;border-collapse:collapse;overflow:hidden;border-radius:11px;table-layout:fixed;font-size:11px}.priority-table th{background:rgba(255,255,255,.075) !important;color:#E4E9E2 !important;font-weight:900;padding:7px 8px;border-bottom:1px solid rgba(131,246,160,.16) !important;text-align:center}.priority-table td{color:#f7f4ff;padding:4px 8px;border-bottom:1px solid rgba(131,246,160,.075) !important;text-align:center;font-weight:740;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.priority-table td.name{text-align:left;font-weight:900}.priority-score{color:#fff !important;font-weight:950 !important}.tag-pill{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;min-width:54px;max-width:118px;padding:3px 8px;font-size:10px;font-weight:950;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;box-shadow:inset 0 1px 0 rgba(255,255,255,.18)}.seg-music{background:linear-gradient(135deg,#7b5cff,#5840c6)}.seg-visual{background:linear-gradient(135deg,#d64b92,#963069)}.seg-virtual{background:linear-gradient(135deg,#d69428,#9d5f12)}.seg-game{background:linear-gradient(135deg,#2a9dd6,#1768a5)}.seg-subculture{background:linear-gradient(135deg,#ff9c55,#c96a28)}.seg-etc{background:linear-gradient(135deg,#7d8798,#4c5568)}.action-immediate{background:linear-gradient(135deg,rgba(26,158,91,.86),rgba(9,88,62,.88)) !important;color:#dffff8;border:1px solid rgba(131,246,160,.28) !important}.action-watch{background:linear-gradient(135deg,#6f83ee,#4350a5)}.action-verify{background:linear-gradient(135deg,#d75d86,#8e2d56)}.action-hold{background:linear-gradient(135deg,#7b8798,#4b5363)}.stSelectbox>div>div{background:rgba(6,18,26,.92) !important;border:1px solid rgba(131,246,160,.20) !important;border-radius:13px !important;box-shadow:none !important}.candidate-select-top-spacer{height:1px !important;min-height:1px !important;margin:0 !important;padding:0 !important}.priority-left-top-spacer{height:22px !important;min-height:22px !important;margin:0 !important;padding:0 !important}.detail-panel-v2{min-height:286px !important;border:1px solid rgba(131,246,160,.22) !important;background:radial-gradient(circle at 9% 45%,rgba(131,246,160,.055),transparent 30%),linear-gradient(180deg,rgba(8,25,27,.82),rgba(8,13,31,.96)) !important}.detail-card-inner-v2{display:grid !important;grid-template-columns:124px minmax(0,1fr) !important;grid-template-areas:"avatar content" "reason reason" !important;gap:14px 16px !important;align-items:center !important}.detail-avatar-area{grid-area:avatar}.detail-content-area{grid-area:content;min-width:0}.detail-reason-bottom{grid-area:reason}.detail-avatar-big{width:108px;height:108px;border-radius:999px;overflow:hidden;border:3px solid rgba(131,246,160,.38) !important;box-shadow:0 0 12px rgba(131,246,160,.12) !important;margin:0 auto;background:radial-gradient(circle at 32% 28%,#fff,#9c6aff 43%,#25154d 100%)}.detail-avatar-big img{width:100%;height:100%;object-fit:cover;display:block}.detail-name-row{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:nowrap !important;min-width:0 !important}.detail-name-main{flex:1 1 auto !important;min-width:0 !important;max-width:100% !important;color:#fff;font-size:20px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.detail-name-main a{color:inherit;text-decoration:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.detail-metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.detail-metric-box{border:1px solid rgba(131,246,160,.18) !important;background:rgba(131,246,160,.025) !important;border-radius:8px;padding:7px 9px;min-height:48px}.detail-metric-label{color:#C5DCCB !important;font-size:10px;font-weight:850}.detail-metric-value{color:#fff;font-size:18px;font-weight:950;line-height:1.2;margin-top:2px}.reason-panel{border:1px solid rgba(131,246,160,.18) !important;background:rgba(131,246,160,.025) !important;border-radius:12px;padding:10px 13px !important;min-height:auto !important}.reason-title{color:#F3FFF5 !important;font-size:12px;font-weight:950;margin-bottom:8px}.reason-bullet{display:inline-block;margin-right:14px;white-space:nowrap;color:#DDEBDD !important;font-size:11px;line-height:1.55}.reason-bullet::before{content:'●';color:var(--seed-green) !important;margin-right:7px}.graph-explain{min-height:360px !important;height:360px !important;box-sizing:border-box !important;border-radius:13px !important;border:1px solid rgba(131,246,160,.16) !important;background:radial-gradient(circle at 18% 20%,rgba(131,246,160,.070),transparent 36%),linear-gradient(180deg,rgba(14,18,43,.78),rgba(6,12,25,.88)) !important;padding:30px 28px !important;box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 12px 26px rgba(0,0,0,.18) !important;display:flex !important;flex-direction:column !important;justify-content:center !important}.graph-explain-title{color:#fff8ff !important;font-size:24px !important;font-weight:950 !important;line-height:1.25 !important;margin:0 0 22px !important;letter-spacing:-.045em !important;text-shadow:0 0 8px rgba(131,246,160,.14) !important;word-break:keep-all !important}.graph-explain-text{color:#c9c0dc !important;font-size:14.5px !important;line-height:1.9 !important;font-weight:700 !important;word-break:keep-all !important;max-width:none !important}.stPlotlyChart{min-height:300px !important;border-radius:13px !important;border:1px solid rgba(131,246,160,.16) !important;background:rgba(6,12,25,.66) !important;padding:8px 10px !important;box-shadow:none !important}div[data-testid="stExpander"]{border-color:rgba(131,246,160,.16) !important;background:rgba(8,18,34,.78) !important;border-radius:14px !important}.explain-box,.guide-box,.reason-box{border:1px solid rgba(131,246,160,.16) !important;background:rgba(7,20,28,.70) !important;border-radius:14px;padding:14px 16px;color:#d8deed;font-size:14px;line-height:1.65}@media (max-width:1200px){.board-hero,.board-hero-compact,.mid-grid,.graph-grid{grid-template-columns:1fr !important}.board-kpi-grid,.top5-grid,.segment-grid,.seed-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.board-subtitle,.board-info-text{white-space:normal !important}}@media (max-width:780px){.board-kpi-grid,.top5-grid,.segment-grid,.seed-grid{grid-template-columns:1fr}.board-title,.board-title-ko{font-size:30px !important}.board-title span{font-size:24px !important}.hero-title{font-size:42px;letter-spacing:5px}}</style>
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
        background: linear-gradient(135deg, #F4C542 0%, #D99A22 52%, #A96D12 100%) !important;
        color: #FFF9E8 !important;
        border: 1px solid rgba(255, 232, 150, 0.74) !important;
        box-shadow:
            0 0 20px rgba(255, 212, 93, 0.30),
            inset 0 1px 0 rgba(255,255,255,0.20) !important;
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
    <style>section[data-testid="stSidebar"] .stButton>button[kind="secondary"],section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]{{background:rgba(24,17,54,0.88) !important;color:#EDE5FF !important;border:1px solid rgba(196,143,255,0.28) !important;box-shadow:none !important}}section[data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover,section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover,section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover{{background:rgba(42,27,88,0.96) !important;color:#FFFFFF !important;border-color:rgba(228,205,255,0.58) !important;box-shadow:0 0 14px rgba(125,66,255,0.16) !important}}{sidebar_primary_css}section[data-testid="stSidebar"] .stButton>button[kind="primary"] *,section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] *{{color:inherit !important;font-weight:900 !important}}section[data-testid="stSidebar"] .stButton>button[kind="secondary"] *,section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] *,section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] *{{color:inherit !important;font-weight:850 !important}}</style>
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
            if page_name == "스타트레일":
                st.session_state.startrail_show_loading = True
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
        <style>.seed-icon-badge{width:56px;height:56px;display:flex;align-items:center;justify-content:center;position:relative;background:transparent;border:none;box-shadow:none;transform:scale(1.08);transform-origin:center center}.seed-icon-badge::before,.seed-icon-badge::after{content:"";position:absolute;box-sizing:border-box;filter:drop-shadow(0 0 6px rgba(152,255,171,0.22))}.seed-icon-search::before{width:29px;height:29px;border:3.6px solid #98FFAB;border-radius:50%;left:9px;top:9px}.seed-icon-search::after{width:21px;height:3.6px;background:#98FFAB;border-radius:999px;left:32px;top:35px;transform:rotate(45deg);transform-origin:left center}.seed-icon-chat::before{width:58px;height:58px;left:50%;top:50%;transform:translate(-50%,-50%);background:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223.1%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%2013h24a3.2%203.2%200%200%201%203.2%203.2v12.2a3.2%203.2%200%200%201-3.2%203.2H22.3l-7.4%205.2v-5.2H12a3.2%203.2%200%200%201-3.2-3.2V16.2A3.2%203.2%200%200%201%2012%2013Z%22%2F%3E%3Cpath%20d%3D%22M24%2026.6s-5-2.9-5-6.1c0-1.7%201.35-3%203-3%201.25%200%202.05.72%202.65%201.65.62-.93%201.43-1.65%202.65-1.65%201.65%200%203%201.3%203%203%200%203.25-5%206.1-5%206.1Z%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;border:none}.seed-icon-chat::after{display:none}.seed-icon-live::before{width:58px;height:58px;left:50%;top:50%;transform:translate(-50%,-50%);background:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20stroke%3D%22%2398FFAB%22%20stroke-width%3D%223.1%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%2214%22%20y%3D%2217%22%20width%3D%2216%22%20height%3D%2212%22%20rx%3D%222.8%22%2F%3E%3Cpath%20d%3D%22M30%2020l5.5-3.2v12.4L30%2026%22%2F%3E%3Cpath%20d%3D%22M11%2018.6c2.1-4.7%206.6-7.7%2011.7-7.9%22%2F%3E%3Cpath%20d%3D%22M19.4%208l4%202.4-3.9%202.5%22%2F%3E%3Cpath%20d%3D%22M37%2029.4c-2.1%204.7-6.6%207.7-11.7%207.9%22%2F%3E%3Cpath%20d%3D%22M28.6%2040l-4-2.4%203.9-2.5%22%2F%3E%3C%2Fsvg%3E") center / contain no-repeat;border:none}.seed-icon-live::after{display:none}.seed-icon-filter::before{width:42px;height:42px;left:50%;top:50%;transform:translate(-50%,-50%);border:3.3px solid #98FFAB;border-radius:50%}.seed-icon-filter::after{width:17px;height:3.6px;left:50%;top:50%;transform:translate(-50%,-50%);background:#98FFAB;border-radius:999px}.seed-icon-check::before{width:38px;height:38px;border:3.5px solid #98FFAB;border-radius:10px;left:9px;top:9px}.seed-icon-check::after{width:22px;height:13px;border-left:4.5px solid #98FFAB;border-bottom:4.5px solid #98FFAB;left:18px;top:21px;transform:rotate(-45deg)}</style>
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
    # 현재 Git 구조: 10_dashboard/data/startrail_{파일명}.csv
    # 팀원 개발본 호환: csv_folder/{파일명}.csv, 10_dashboard/data/{파일명}.csv
    "summary": [
        "10_dashboard/data/startrail_대시보드요약.csv",
        "10_dashboard/data/대시보드요약.csv",
        "csv_folder/대시보드요약.csv",
    ],
    "kpi": [
        "10_dashboard/data/startrail_핵심KPI.csv",
        "10_dashboard/data/핵심KPI.csv",
        "csv_folder/핵심KPI.csv",
    ],
    "candidate": [
        "10_dashboard/data/startrail_개인후보통합테이블.csv",
        "10_dashboard/data/개인후보통합테이블.csv",
        "csv_folder/개인후보통합테이블.csv",
    ],
    "constellation": [
        "10_dashboard/data/startrail_성단그룹후보테이블.csv",
        "10_dashboard/data/성단그룹후보테이블.csv",
        "csv_folder/성단그룹후보테이블.csv",
    ],
}

STARTRAIL_ASSET_FILES = {
    "calendar": "assets/달력.png",
    "soop": "assets/숲3.png",
    "chzzk": "assets/치지직3.png",
}

STARTRAIL_GRAPH_BG = "#15102F"
STARTRAIL_TRANSPARENT = "rgba(13,10,31,0.98)"


def startrail_resolve_path(relative_path) -> Path:
    """
    Streamlit Cloud/GitHub 배포 경로 차이를 흡수하는 경로 탐색기.
    - 문자열 1개 또는 후보 경로 리스트를 받을 수 있다.
    - assets/성단1.jpg처럼 새로 추가된 로컬 이미지도 여기서 탐색한다.
    """
    if isinstance(relative_path, (list, tuple)):
        fallback = None
        for item in relative_path:
            resolved = startrail_resolve_path(item)
            if resolved.exists():
                return resolved
            if fallback is None:
                fallback = resolved
        return fallback if fallback is not None else Path("")

    rel = Path(str(relative_path))
    if rel.is_absolute():
        return rel

    here = Path(__file__).resolve().parent

    search_roots = [here, here.parent, Path.cwd(), Path.cwd().parent]
    candidates = []
    for root in search_roots:
        candidates.extend([root / rel, root / rel.name])

    for p in candidates:
        if p.exists():
            return p.resolve()

    return here.parent / rel


@st.cache_data(show_spinner=False, max_entries=512)
def _startrail_file_to_base64_cached(abs_path: str, mtime_ns: int) -> str:
    """로컬 assets 이미지를 base64로 변환한다.

    Streamlit rerun 때 같은 이미지를 반복 인코딩하지 않도록 캐시한다.
    mtime_ns를 인자로 받아 assets 파일이 바뀌면 캐시가 자동 갱신된다.
    """
    try:
        return base64.b64encode(Path(abs_path).read_bytes()).decode()
    except Exception:
        return ""


def startrail_img_to_base64(relative_path: str) -> str:
    path = startrail_resolve_path(relative_path)
    fallback = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    try:
        if not path.exists() or not path.is_file():
            return fallback
        encoded = _startrail_file_to_base64_cached(str(path), path.stat().st_mtime_ns)
        return encoded or fallback
    except Exception:
        return fallback


def startrail_local_image_src(relative_path: str) -> str:
    """로컬 assets 이미지를 HTML img src에서 바로 쓸 수 있는 data URL로 변환한다."""
    if not relative_path:
        return ""

    text = str(relative_path).strip()
    if text.startswith(("http://", "https://", "data:image/")):
        return text

    path = startrail_resolve_path(text)
    if not path.exists() or not path.is_file():
        return text

    ext = path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in {"png", "jpeg", "webp", "gif", "svg"}:
        ext = "png"

    try:
        encoded = _startrail_file_to_base64_cached(str(path), path.stat().st_mtime_ns)
        if not encoded:
            return text
        return f"data:image/{ext};base64,{encoded}"
    except Exception:
        return text


def startrail_constellation_asset_path(rank) -> str:
    """성단 TOP 이미지 매핑: assets/성단{순위}.jpg 우선, 없으면 png/jpeg까지 확인."""
    try:
        rank = int(rank)
    except Exception:
        return ""

    candidates = [
        f"assets/성단{rank}.jpg",
        f"assets/성단{rank}.png",
        f"assets/성단{rank}.jpeg",
    ]

    # 팀원 개발본에서 11위는 png였던 케이스를 안전하게 지원
    if rank == 11:
        candidates = [f"assets/성단{rank}.png", f"assets/성단{rank}.jpg", f"assets/성단{rank}.jpeg"]

    for candidate in candidates:
        if startrail_resolve_path(candidate).exists():
            return candidate

    return candidates[0] if 1 <= rank <= 99 else ""


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

    # 팀원 보완본에서 추가한 assets/성단{순위}.jpg 이미지를 성단 후보에 연결한다.
    # 기존 CSV에 이미지URL이 있더라도 비어 있으면 순위 기반 로컬 asset으로 보완한다.
    if "이미지URL" not in const.columns:
        const["이미지URL"] = ""
    const["이미지URL"] = const["이미지URL"].fillna("").astype(str).str.strip()
    generated_assets = const["순위"].apply(startrail_constellation_asset_path)
    empty_image_mask = const["이미지URL"].isin(["", "nan", "None", "none", "-"])
    const.loc[empty_image_mask, "이미지URL"] = generated_assets[empty_image_mask]

    const["상위퍼센트"] = (const["순위"] / len(const) * 100).round(2) if len(const) else 0

    return const


@st.cache_data(show_spinner=False, ttl=600, max_entries=1)
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
        elif seg == "슈퍼노바":
            # 팀원 보완본 기준: 슈퍼노바 필터는 소속 여부로 개인/그룹 구분
            if "소속" in temp.columns:
                affiliation = temp["소속"].fillna("").astype(str).str.strip()
                temp["세그먼트필터"] = "개인"
                temp.loc[~affiliation.isin(["", "nan", "None", "none", "-"]), "세그먼트필터"] = "그룹"
            else:
                temp["세그먼트필터"] = "개인"
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
    """스타트레일 전용 화면 스타일. CSS가 화면에 노출되지 않도록 짧은 style block만 주입한다."""
    st.markdown("""
<style>.block-container:has(.startrail-page){max-width:1560px !important;padding-top:0.8rem !important;padding-left:2.8rem !important;padding-right:2.8rem !important;padding-bottom:4rem !important}.startrail-page{position:relative;z-index:3;color:#F8F2FF}.startrail-hero{margin:0 0 28px 0}.trail-hero-top{display:grid;grid-template-columns:minmax(0,1fr) 520px;gap:42px;align-items:start;margin-bottom:34px}.trail-title{font-size:clamp(58px,5.8vw,82px);line-height:0.95;font-weight:950;letter-spacing:0.19em;color:#FFF8FF;margin:0 0 16px 0;text-shadow:0 0 8px rgba(255,255,255,.62),0 0 24px rgba(214,187,255,.55),0 0 48px rgba(125,66,255,.46);white-space:nowrap}.trail-subtitle{font-size:18px;font-weight:850;line-height:1.55;color:#E8DFFF;margin:0 0 24px 0;word-break:keep-all}.trail-date-pill{display:inline-flex;align-items:center;gap:9px;height:42px;padding:0 18px;border-radius:999px;color:#EDE5FF;font-size:14px;font-weight:900;background:rgba(8,26,43,0.72);border:1px solid rgba(255,212,93,0.28);box-shadow:0 0 18px rgba(255,212,93,.10),inset 0 0 18px rgba(255,255,255,.025)}.trail-info-card{min-height:122px;border-radius:22px;padding:22px 26px;display:grid;grid-template-columns:62px minmax(0,1fr);gap:18px;align-items:center;background:radial-gradient(circle at 12% 44%,rgba(255,212,93,.10),transparent 32%),linear-gradient(135deg,rgba(21,16,47,.80),rgba(12,10,31,.94));border:1px solid rgba(196,143,255,.34);box-shadow:0 0 24px rgba(125,66,255,.18),inset 0 0 22px rgba(255,255,255,.025)}.trail-info-icon{width:58px;height:58px;border-radius:999px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:24px;background:radial-gradient(circle at 34% 26%,rgba(255,255,255,.92),transparent 15%),linear-gradient(135deg,#FFD45D,#8B5CF6 58%,#5B2AD8);box-shadow:0 0 22px rgba(255,212,93,.24),0 0 28px rgba(139,92,255,.24)}.trail-info-title{color:#FFF9FF;font-size:17px;font-weight:950;margin-bottom:7px}.trail-info-desc{color:rgba(255,255,255,.70);font-size:13px;line-height:1.62;font-weight:650;word-break:keep-all}.trail-kpi-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:0 0 34px 0}.trail-kpi-card{min-height:118px;border-radius:22px;padding:26px 28px;background:radial-gradient(circle at 12% 26%,rgba(255,212,93,.05),transparent 34%),linear-gradient(180deg,rgba(21,16,47,.88),rgba(9,8,28,.96));border:1px solid rgba(196,143,255,.26);box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 14px 30px rgba(0,0,0,.24),0 0 24px rgba(125,66,255,.12)}.trail-kpi-label{color:rgba(255,255,255,.76);font-size:14px;font-weight:900;margin-bottom:8px}.trail-kpi-value{color:#FFF9FF;font-size:32px;font-weight:950;line-height:1.06;letter-spacing:-.04em;text-shadow:0 0 16px rgba(255,255,255,.16)}.trail-divider{height:1px;width:100%;background:rgba(196,143,255,.23);margin:0 0 32px 0}.trail-section-title{display:flex;align-items:center;gap:10px;margin:0 0 18px 0;color:#FFF9FF;font-size:30px;line-height:1.2;font-weight:950;letter-spacing:-.04em}.trail-seg-card{position:relative;min-height:210px;border-radius:20px;padding:26px 18px 20px;text-align:center;background:rgba(21,16,47,.86);border:1px solid rgba(196,143,255,.18);box-shadow:0 0 24px rgba(112,53,255,.12),inset 0 0 24px rgba(255,255,255,.018);overflow:hidden}.trail-seg-card::before{content:"";position:absolute;left:22px;right:22px;top:16px;height:3px;border-radius:999px;background:rgba(240,140,255,.36)}.trail-seg-card.active{transform:translateY(-2px);border-color:rgba(255,212,93,.55);box-shadow:0 0 28px rgba(255,212,93,.18),0 0 34px rgba(125,66,255,.20),inset 0 0 26px rgba(255,255,255,.025)}.trail-seg-card.active::before{background:#FFD45D;box-shadow:0 0 18px rgba(255,212,93,.62)}.trail-seg-card.active-성단::before{background:#FF6B8A}.trail-seg-card.active-위성::before{background:#95AFFF}.trail-seg-card.active-슈퍼노바::before{background:#FF9DF5}.trail-seg-card.active-코멧::before{background:#FF9E5E}.trail-seg-icon{margin-top:22px;margin-bottom:16px;font-size:31px;color:#DDBBFF;text-shadow:0 0 18px rgba(221,187,255,.28)}.trail-seg-name{font-size:20px;font-weight:950;color:#FFF9FF;margin-bottom:10px}.trail-seg-count{font-size:28px;font-weight:950;color:#F08CFF;margin-bottom:14px;letter-spacing:-.02em}.trail-seg-desc{font-size:12px;line-height:1.55;font-weight:700;color:rgba(255,255,255,.66);word-break:keep-all}.trail-main-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:34px;align-items:start;margin-top:6px}.trail-filter-wrap{margin:0 0 18px 0}.trail-top5-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:16px;align-items:stretch}.trail-rank-card{position:relative;min-height:332px;height:332px;border-radius:20px;padding:20px 16px 16px;display:flex;flex-direction:column;align-items:center;text-align:center;box-sizing:border-box;background:radial-gradient(circle at 50% 18%,rgba(196,143,255,.10),transparent 36%),rgba(21,16,47,.88);border:1px solid rgba(196,143,255,.22);box-shadow:0 0 24px rgba(112,53,255,.14),inset 0 0 22px rgba(255,255,255,.018);overflow:hidden}.trail-rank-badge{position:absolute;top:18px;left:18px;z-index:2;width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:950;color:#1a112f;background:linear-gradient(135deg,#FFD45D,#C99700);box-shadow:0 0 16px rgba(255,212,93,.42)}.trail-rank-badge.rank-2{background:linear-gradient(135deg,#F4E9FF,#B7A2DC)}.trail-rank-badge.rank-3{background:linear-gradient(135deg,#D99666,#8B4A30);color:#fff}.trail-rank-badge.rank-normal{background:rgba(255,255,255,.10);color:#F8F2FF;border:1px solid rgba(255,255,255,.16)}.trail-avatar-wrap{width:118px;height:118px;min-width:118px;min-height:118px;border-radius:999px;margin:0 auto 18px;overflow:hidden;background:radial-gradient(circle at 32% 28%,#fff,#9c6aff 42%,#25154d 100%);border:3px solid rgba(255,212,93,.40);box-shadow:0 0 18px rgba(255,212,93,.16),0 0 22px rgba(125,66,255,.18)}.trail-avatar-wrap img{width:100%;height:100%;object-fit:cover;object-position:center center;display:block}.trail-rank-name{height:48px;display:flex;align-items:center;justify-content:center;color:#FFF9FF;font-size:20px;line-height:1.20;font-weight:950;word-break:keep-all;overflow:hidden}.trail-tag{display:inline-flex;align-items:center;justify-content:center;margin:8px auto 12px;padding:5px 12px;border-radius:999px;font-size:11px;line-height:1;font-weight:950;color:#FFD45D;background:rgba(255,212,93,.12);border:1px solid rgba(255,212,93,.42)}.trail-score-label{color:rgba(255,255,255,.42);font-size:12px;font-weight:850;margin-bottom:5px}.trail-score-value{color:#FFD45D;font-size:25px;font-weight:950;line-height:1.1}.trail-card-button{margin-top:auto;width:100%}.trail-side-card{border-radius:22px;padding:22px 26px 28px;min-height:620px;background:radial-gradient(circle at 50% 8%,rgba(196,143,255,.12),transparent 34%),rgba(21,16,47,.88);border:1px solid rgba(196,143,255,.28);box-shadow:0 0 28px rgba(112,53,255,.16),inset 0 0 22px rgba(255,255,255,.018)}.trail-side-title{color:#FFF9FF;font-size:21px;font-weight:950;line-height:1.2;margin:0 0 26px 0;letter-spacing:-.04em;text-align:left;text-shadow:0 0 10px rgba(255,255,255,.10)}.trail-side-filter-spacer{height:4px;min-height:4px;margin:0;padding:0}.trail-detail-avatar{width:132px;height:132px;border-radius:999px;overflow:hidden;margin:0 auto 18px;border:4px solid rgba(117,204,255,.84);box-shadow:0 0 18px rgba(117,204,255,.24)}.trail-detail-avatar img{width:100%;height:100%;object-fit:cover;object-position:center center;display:block}.trail-detail-name{color:#FFF9FF;font-size:24px;font-weight:950;text-align:center;margin-bottom:12px;word-break:keep-all}.trail-detail-tags{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 auto 22px;width:fit-content;max-width:100%}.trail-detail-tags .trail-tag{margin:0 !important;flex:0 0 auto}.trail-detail-tags img{height:28px;border-radius:8px;object-fit:contain;flex:0 0 auto;display:block}.trail-bar-row{margin:13px 0 16px}.trail-bar-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;gap:10px}.trail-bar-label{color:#FFF9FF;font-size:13px;font-weight:950}.trail-bar-value{font-size:13px;font-weight:950}.trail-bar-track{height:8px;border-radius:999px;overflow:hidden;background:rgba(255,255,255,.07)}.trail-bar-fill{height:100%;border-radius:999px}.trail-bottom-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);gap:28px;margin-top:34px}.trail-bottom-title{min-height:42px;display:flex;align-items:center;margin:0 0 14px 0;font-size:25px;font-weight:950;color:#FFF9FF;letter-spacing:-.05em;white-space:nowrap}.trail-table{width:100%;border-collapse:collapse;background:rgba(21,16,47,.78) !important;border:1px solid rgba(196,143,255,.20);border-radius:18px;overflow:hidden;table-layout:fixed}.trail-table th{text-align:center;padding:12px 8px;border-bottom:1px solid rgba(196,143,255,.22);color:#E8DFFF;font-size:12px;font-weight:950;background:rgba(255,255,255,.045)}.trail-table td{text-align:center;padding:11px 8px;border-bottom:1px solid rgba(255,255,255,.07);font-size:12px;color:#FFF9FF;font-weight:760;word-break:keep-all}div[data-testid="stPlotlyChart"]{background:rgba(21,16,47,.78) !important;border-radius:22px !important;overflow:hidden !important;padding:0 !important;border:1px solid rgba(196,143,255,.20) !important;box-shadow:0 0 24px rgba(125,66,255,.12),inset 0 0 18px rgba(255,255,255,.018) !important}div[data-testid="column"] .stButton>button{margin-top:0 !important}section.main .stButton>button{margin-top:0 !important}@media (max-width:1280px){.trail-hero-top{grid-template-columns:1fr}.trail-kpi-grid{grid-template-columns:1fr}.trail-main-grid{grid-template-columns:1fr}.trail-top5-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.trail-bottom-grid{grid-template-columns:1fr}}.trail-seg-card{min-height:218px !important;height:218px !important;padding:26px 18px 20px !important;display:flex !important;flex-direction:column !important;align-items:center !important;justify-content:flex-start !important}.trail-seg-card::before{left:28px !important;right:28px !important;top:18px !important;height:3px !important;background:rgba(156,82,182,.64) !important;box-shadow:0 0 14px rgba(196,143,255,.18) !important}.trail-seg-card.active-성단{border-color:rgba(255,107,138,.82) !important;box-shadow:0 0 28px rgba(255,107,138,.24),inset 0 0 24px rgba(255,107,138,.05) !important}.trail-seg-card.active-프로토스타{border-color:rgba(255,212,93,.82) !important;box-shadow:0 0 28px rgba(255,212,93,.22),inset 0 0 24px rgba(255,212,93,.05) !important}.trail-seg-card.active-위성{border-color:rgba(149,175,255,.74) !important;box-shadow:0 0 28px rgba(149,175,255,.20),inset 0 0 24px rgba(149,175,255,.05) !important}.trail-seg-card.active-슈퍼노바{border-color:rgba(255,157,245,.76) !important;box-shadow:0 0 28px rgba(255,157,245,.20),inset 0 0 24px rgba(255,157,245,.05) !important}.trail-seg-card.active-코멧{border-color:rgba(255,158,94,.76) !important;box-shadow:0 0 28px rgba(255,158,94,.20),inset 0 0 24px rgba(255,158,94,.05) !important}.trail-seg-card.active-성단::before{background:#FF6B8A !important;box-shadow:0 0 18px rgba(255,107,138,.62) !important}.trail-seg-card.active-프로토스타::before{background:#FFD45D !important;box-shadow:0 0 18px rgba(255,212,93,.62) !important}.trail-seg-card.active-위성::before{background:#95AFFF !important;box-shadow:0 0 18px rgba(149,175,255,.58) !important}.trail-seg-card.active-슈퍼노바::before{background:#FF9DF5 !important;box-shadow:0 0 18px rgba(255,157,245,.58) !important}.trail-seg-card.active-코멧::before{background:#FF9E5E !important;box-shadow:0 0 18px rgba(255,158,94,.58) !important}.trail-seg-icon-badge{width:68px !important;height:68px !important;margin:30px auto 18px !important;border-radius:999px !important;display:flex !important;align-items:center !important;justify-content:center !important;background:radial-gradient(circle at 36% 28%,rgba(255,255,255,.20),rgba(196,143,255,.10) 48%,rgba(21,16,47,.15) 100%) !important;border:1px solid rgba(196,143,255,.22) !important;box-shadow:0 0 20px rgba(196,143,255,.16),inset 0 0 20px rgba(255,255,255,.02) !important}.trail-seg-icon-badge i{font-size:30px !important;color:#DDBBFF !important;text-shadow:0 0 18px rgba(221,187,255,.36) !important}.trail-seg-card.active-성단 .trail-seg-icon-badge i,.trail-seg-card.active-성단 .trail-seg-name,.trail-seg-card.active-성단 .trail-seg-count{color:#FF7D98 !important}.trail-seg-card.active-프로토스타 .trail-seg-icon-badge i,.trail-seg-card.active-프로토스타 .trail-seg-name,.trail-seg-card.active-프로토스타 .trail-seg-count{color:#FFD45D !important}.trail-seg-card.active-위성 .trail-seg-icon-badge i,.trail-seg-card.active-위성 .trail-seg-name,.trail-seg-card.active-위성 .trail-seg-count{color:#95AFFF !important}.trail-seg-card.active-슈퍼노바 .trail-seg-icon-badge i,.trail-seg-card.active-슈퍼노바 .trail-seg-name,.trail-seg-card.active-슈퍼노바 .trail-seg-count{color:#FF9DF5 !important}.trail-seg-card.active-코멧 .trail-seg-icon-badge i,.trail-seg-card.active-코멧 .trail-seg-name,.trail-seg-card.active-코멧 .trail-seg-count{color:#FF9E5E !important}.trail-seg-name{display:inline-flex !important;align-items:center !important;justify-content:center !important;gap:6px !important;min-height:30px !important;font-size:20px !important;line-height:1.25 !important;white-space:normal !important}.trail-seg-count{font-size:30px !important;line-height:1.1 !important;margin-bottom:13px !important}.trail-seg-desc{max-width:210px !important;margin:0 auto !important;min-height:42px !important;display:flex !important;align-items:center !important;justify-content:center !important}.trail-tooltip-wrap{position:relative !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;vertical-align:middle !important}.trail-tooltip-icon{width:17px !important;height:17px !important;min-width:17px !important;border-radius:50% !important;border:1px solid rgba(217,200,255,.78) !important;color:#D9C8FF !important;font-size:10px !important;font-weight:950 !important;line-height:15px !important;text-align:center !important;cursor:help !important;background:rgba(12,10,31,.92) !important}.trail-tooltip-text{visibility:hidden !important;opacity:0 !important;width:220px !important;background:rgba(21,16,47,.98) !important;color:#D9CFE8 !important;text-align:left !important;border:1px solid rgba(196,143,255,.34) !important;border-radius:12px !important;padding:10px 12px !important;position:absolute !important;z-index:99999 !important;bottom:140% !important;left:50% !important;transform:translateX(-50%) !important;font-size:12px !important;line-height:1.45 !important;box-shadow:0 10px 28px rgba(0,0,0,.45) !important;white-space:normal !important}.trail-tooltip-wrap:hover .trail-tooltip-text{visibility:visible !important;opacity:1 !important}.trail-seg-card{min-height:245px !important;padding:26px 18px 22px !important;display:flex !important;flex-direction:column !important;align-items:center !important;justify-content:flex-start !important}.trail-seg-icon-badge{width:74px !important;height:74px !important;margin:32px auto 18px !important;border-radius:999px !important;display:flex !important;align-items:center !important;justify-content:center !important;background:radial-gradient(circle at 36% 28%,rgba(255,255,255,.24),rgba(196,143,255,.12) 48%,rgba(21,16,47,.18) 100%) !important;border:1px solid rgba(196,143,255,.28) !important;box-shadow:0 0 22px rgba(196,143,255,.18),inset 0 0 20px rgba(255,255,255,.025) !important}.trail-seg-emoji{display:block !important;font-size:34px !important;line-height:1 !important;filter:drop-shadow(0 0 12px rgba(221,187,255,.34));transform:translateY(1px)}.trail-seg-card.active-성단 .trail-seg-emoji{filter:drop-shadow(0 0 14px rgba(255,107,138,.55))}.trail-seg-card.active-프로토스타 .trail-seg-emoji{filter:drop-shadow(0 0 14px rgba(255,212,93,.58))}.trail-seg-card.active-위성 .trail-seg-emoji{filter:drop-shadow(0 0 14px rgba(149,175,255,.55))}.trail-seg-card.active-슈퍼노바 .trail-seg-emoji{filter:drop-shadow(0 0 14px rgba(255,157,245,.55))}.trail-seg-card.active-코멧 .trail-seg-emoji{filter:drop-shadow(0 0 14px rgba(255,158,94,.55))}.trail-seg-name{display:flex !important;align-items:center !important;justify-content:center !important;gap:6px !important;min-height:30px !important}.trail-seg-count{margin-top:2px !important}.trail-seg-desc{max-width:190px !important;margin:0 auto !important}.trail-bottom-grid{gap:24px !important;margin-top:26px !important;align-items:start !important}.trail-table th{padding:10px 7px !important;font-size:11px !important}.trail-table td{padding:10px 7px !important;font-size:11px !important;height:56px !important}.trail-bottom-title{min-height:36px !important;margin-bottom:10px !important;font-size:23px !important}.trail-side-card{min-height:560px !important;padding-bottom:32px !important}.trail-table{min-height:460px !important}.trail-table th{height:52px !important;vertical-align:middle !important}.trail-table td{height:72px !important;vertical-align:middle !important}.trail-bottom-title{min-height:40px !important;margin-bottom:12px !important}div[data-testid="stPlotlyChart"]{min-height:300px !important}.trail-radar-spacer{height:22px !important;min-height:22px !important;margin:0 !important;padding:0 !important}.startrail-page .trail-section-title,.trail-section-title{margin-top:0 !important;margin-bottom:18px !important}.trail-main-grid{grid-template-columns:minmax(0,1fr) 340px !important;gap:34px !important;align-items:start !important}.trail-filter-wrap,div[data-testid="stSelectbox"]{position:relative !important;z-index:20 !important}.trail-rank-card{min-height:328px !important;height:328px !important;padding:58px 14px 14px !important}.trail-rank-badge{top:20px !important;left:20px !important;width:36px !important;height:36px !important}.trail-avatar-wrap{width:104px !important;height:104px !important;min-width:104px !important;min-height:104px !important;margin-bottom:16px !important}.trail-rank-name{height:42px !important;font-size:19px !important}.trail-score-value{font-size:23px !important}.trail-card-button,.trail-rank-card + div,.trail-rank-card ~ div{margin-top:0 !important}.trail-side-card{min-height:560px !important;padding:22px 26px 28px !important}.trail-detail-tags{display:inline-flex !important;align-items:center !important;justify-content:center !important;gap:10px !important;width:100% !important;margin:0 auto 20px !important}.trail-detail-tags .trail-tag{margin:0 !important}.trail-detail-tags img{display:inline-block !important;vertical-align:middle !important}.trail-table{min-height:620px !important}.trail-table th{height:58px !important;padding:12px 7px !important;vertical-align:middle !important}.trail-table td{height:74px !important;padding:10px 7px !important;vertical-align:middle !important}.trail-chart-card,div[data-testid="stPlotlyChart"]{border-radius:24px !important;background:rgba(21,16,47,0.88) !important;border:1px solid rgba(196,143,255,0.18) !important;box-shadow:0 0 24px rgba(112,53,255,.12),inset 0 0 20px rgba(255,255,255,.018) !important}.trail-tooltip-text{width:310px !important;white-space:normal !important;word-break:keep-all !important;line-height:1.65 !important}.trail-seg-card,.trail-seg-card.active{overflow:visible !important;position:relative !important;z-index:1 !important}.trail-seg-card:has(.trail-tooltip-wrap:hover),.trail-seg-card:hover{z-index:9999 !important}.trail-seg-name{position:relative !important;overflow:visible !important}.trail-tooltip-wrap{position:relative !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;width:17px !important;height:17px !important;min-width:17px !important;margin-left:4px !important;vertical-align:middle !important;overflow:visible !important;z-index:10000 !important}.trail-tooltip-icon{display:inline-flex !important;align-items:center !important;justify-content:center !important;width:17px !important;height:17px !important;min-width:17px !important;border-radius:50% !important;border:1px solid rgba(217,200,255,.78) !important;color:#D9C8FF !important;background:rgba(12,10,31,.96) !important;font-size:10px !important;font-weight:950 !important;line-height:1 !important;cursor:help !important;box-sizing:border-box !important}.trail-tooltip-text{display:block !important;visibility:hidden !important;opacity:0 !important;pointer-events:none !important;position:absolute !important;left:50% !important;bottom:150% !important;transform:translateX(-50%) !important;width:260px !important;max-width:260px !important;padding:10px 12px !important;border-radius:12px !important;border:1px solid rgba(196,143,255,.38) !important;background:rgba(21,16,47,.98) !important;color:#D9CFE8 !important;font-size:12px !important;font-weight:700 !important;line-height:1.55 !important;text-align:left !important;white-space:normal !important;word-break:keep-all !important;box-shadow:0 10px 28px rgba(0,0,0,.45) !important;z-index:99999 !important}.trail-tooltip-wrap:hover .trail-tooltip-text{visibility:visible !important;opacity:1 !important}div[data-testid="column"]:first-child .trail-tooltip-text{left:0 !important;transform:translateX(-8px) !important}div[data-testid="column"]:last-child .trail-tooltip-text{left:auto !important;right:0 !important;transform:translateX(8px) !important}@media (max-width:1200px){.trail-main-grid{grid-template-columns:1fr !important}.trail-rank-card{height:auto !important;min-height:292px !important}}.trail-table{table-layout:fixed !important;width:100% !important}.trail-table th,.trail-table td{white-space:nowrap !important;word-break:keep-all !important;overflow:hidden !important;text-overflow:ellipsis !important;vertical-align:middle !important;line-height:1.18 !important;box-sizing:border-box !important}.trail-table th{font-size:10.4px !important;padding:9px 4px !important;height:46px !important;letter-spacing:-0.04em !important}.trail-table td{font-size:10.8px !important;padding:9px 4px !important;height:68px !important;letter-spacing:-0.035em !important}.trail-table td:nth-child(1),.trail-table th:nth-child(1),.trail-table td:nth-child(3),.trail-table th:nth-child(3),.trail-table td:nth-child(4),.trail-table th:nth-child(4),.trail-table td:nth-child(5),.trail-table th:nth-child(5){padding-left:2px !important;padding-right:2px !important}.trail-table td b{white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;display:block !important;max-width:100% !important}.trail-table .platform-logo,.trail-table img{max-width:26px !important;height:22px !important;object-fit:contain !important}.trail-table-team-style{width:100% !important;table-layout:fixed !important;border-radius:18px !important;overflow:hidden !important}.trail-table-team-style .col-rank{width:12% !important}.trail-table-team-style .col-name{width:28% !important}.trail-table-team-style .col-platform{width:14% !important}.trail-table-team-style .col-score{width:17% !important}.trail-table-team-style .col-percent{width:29% !important}.trail-table-team-style th{height:50px !important;padding:8px 8px !important;font-size:12.2px !important;letter-spacing:-0.035em !important;white-space:nowrap !important;word-break:keep-all !important;text-align:center !important}.trail-table-team-style td{height:52px !important;padding:6px 8px !important;font-size:12.4px !important;letter-spacing:-0.02em !important;white-space:nowrap !important;word-break:keep-all !important;overflow:hidden !important;text-overflow:ellipsis !important;text-align:center !important;vertical-align:middle !important}.trail-table-team-style .name-cell b{display:block !important;max-width:100% !important;white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;font-weight:950 !important}.trail-table-team-style .score-cell{color:#00F2FF !important;font-weight:950 !important}.trail-table-team-style .percent-cell{color:#FFD45D !important;font-weight:950 !important}.trail-table-team-style .platform-cell img,.trail-table-team-style .platform-logo{width:26px !important;max-width:26px !important;height:24px !important;object-fit:contain !important;border-radius:6px !important}.trail-platform-text{display:inline-flex !important;align-items:center !important;justify-content:center !important;min-width:42px !important;height:22px !important;padding:0 7px !important;border-radius:999px !important;border:1px solid rgba(255,212,93,.38) !important;color:#FFD45D !important;background:rgba(255,212,93,.10) !important;font-size:9.8px !important;font-weight:950 !important}.trail-detail-button-title{height:50px !important;display:flex !important;align-items:center !important;justify-content:center !important;color:#E8DFFF !important;font-size:13.4px !important;font-weight:950 !important;letter-spacing:-0.035em !important;white-space:nowrap !important}.trail-detail-button-title + div,.trail-detail-button-title ~ div{margin-top:0 !important}div[data-testid="column"]:has(.trail-detail-button-title) .stButton{height:49px !important;min-height:49px !important;display:flex !important;align-items:center !important;margin:0 !important}div[data-testid="column"]:has(.trail-detail-button-title) .stButton>button{height:36px !important;min-height:36px !important;margin-top:0 !important;margin-bottom:0 !important;border-radius:999px !important;padding:0 12px !important;font-size:16.4px !important;font-weight:950 !important;background:rgba(7,18,34,.86) !important;border:1px solid rgba(117,204,255,.36) !important;color:#EAF7FF !important;box-shadow:0 0 12px rgba(117,204,255,.08) !important}div[data-testid="column"]:has(.trail-detail-button-title){padding-top:0 !important}div[data-testid="column"]:has(.trail-detail-button-title) [data-testid="stVerticalBlock"],div[data-testid="column"]:has(.trail-detail-button-title) [data-testid="stVerticalBlock"]>div{gap:0 !important;row-gap:0 !important}div[data-testid="column"]:has(.trail-detail-button-title) .element-container{margin:0 !important;padding:0 !important}.trail-table-team-style tbody tr{height:49px !important}.trail-table-team-style thead tr{height:48px !important}.trail-table-team-style th{padding-top:8px !important;padding-bottom:8px !important}.trail-table-team-style td{padding-top:5px !important;padding-bottom:5px !important}.startrail-page{--trail-gold:#FFD45D;--trail-gold-soft:#FFE9A8;--trail-gold-deep:#B77A18;--trail-panel:rgba(18,16,34,.88);--trail-panel-strong:rgba(23,18,36,.94);--trail-border:rgba(255,212,93,.24)}.trail-title{color:#FFF9E8 !important;text-shadow:0 0 8px rgba(255,255,255,.52),0 0 26px rgba(255,212,93,.46),0 0 62px rgba(183,122,24,.36) !important}.trail-subtitle,.trail-info-desc,.trail-kpi-label,.trail-seg-desc{color:rgba(247,235,202,.78) !important}.trail-date-pill{color:#FFF1BC !important;background:rgba(34,25,26,.78) !important;border-color:rgba(255,212,93,.42) !important;box-shadow:0 0 18px rgba(255,212,93,.16),inset 0 1px 0 rgba(255,255,255,.08) !important}.trail-info-card,.trail-kpi-card,.trail-seg-card,.trail-rank-card,.trail-side-card,.trail-table,.trail-chart-card,div[data-testid="stPlotlyChart"]{border-color:var(--trail-border) !important;background:radial-gradient(circle at 11% 26%,rgba(255,212,93,.090),transparent 34%),linear-gradient(180deg,var(--trail-panel-strong),rgba(8,8,25,.96)) !important;box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 14px 30px rgba(0,0,0,.22),0 0 24px rgba(255,212,93,.09) !important}.trail-info-icon,.trail-seg-icon-badge,.trail-detail-avatar{background:radial-gradient(circle at 34% 26%,#FFF9D8,#FFD45D 48%,#B77A18 100%) !important;border-color:rgba(255,226,135,.48) !important;box-shadow:0 0 18px rgba(255,212,93,.22),inset 0 0 18px rgba(255,255,255,.08) !important}.trail-seg-emoji{filter:drop-shadow(0 0 13px rgba(255,212,93,.50)) !important}.trail-info-title,.trail-section-title,.trail-side-title,.trail-bottom-title{color:#FFF8E4 !important;text-shadow:0 0 10px rgba(255,212,93,.12) !important}.trail-kpi-value,.trail-seg-count,.trail-score-value,.trail-table-team-style .score-cell,.trail-table-team-style .percent-cell,.trail-detail-button-title{color:var(--trail-gold) !important}.trail-divider,.trail-seg-card::before{background:linear-gradient(90deg,rgba(255,212,93,0),rgba(255,212,93,.72),rgba(255,241,188,.92),rgba(255,212,93,.38),rgba(255,212,93,0)) !important;box-shadow:0 0 18px rgba(255,212,93,.18) !important}.trail-seg-card.active,.trail-seg-card.active-성단,.trail-seg-card.active-프로토스타,.trail-seg-card.active-위성,.trail-seg-card.active-슈퍼노바,.trail-seg-card.active-코멧{border-color:rgba(255,212,93,.82) !important;box-shadow:0 0 28px rgba(255,212,93,.22),inset 0 0 24px rgba(255,212,93,.055) !important}.trail-seg-card.active::before,.trail-seg-card.active-성단::before,.trail-seg-card.active-프로토스타::before,.trail-seg-card.active-위성::before,.trail-seg-card.active-슈퍼노바::before,.trail-seg-card.active-코멧::before{background:var(--trail-gold) !important;box-shadow:0 0 18px rgba(255,212,93,.66) !important}.trail-seg-card.active-성단 .trail-seg-name,.trail-seg-card.active-성단 .trail-seg-count,.trail-seg-card.active-프로토스타 .trail-seg-name,.trail-seg-card.active-프로토스타 .trail-seg-count,.trail-seg-card.active-위성 .trail-seg-name,.trail-seg-card.active-위성 .trail-seg-count,.trail-seg-card.active-슈퍼노바 .trail-seg-name,.trail-seg-card.active-슈퍼노바 .trail-seg-count,.trail-seg-card.active-코멧 .trail-seg-name,.trail-seg-card.active-코멧 .trail-seg-count{color:var(--trail-gold) !important}.trail-rank-badge,.trail-rank-badge.rank-1{color:#211609 !important;background:linear-gradient(135deg,#FFF0A8 0%,#FFD45D 48%,#B77A18 100%) !important;border:1px solid rgba(255,239,180,.72) !important;box-shadow:0 0 16px rgba(255,212,93,.42) !important}.trail-rank-badge.rank-2{color:#171724 !important;background:linear-gradient(135deg,#FFFFFF 0%,#DDE3EF 48%,#8D98AA 100%) !important;border:1px solid rgba(245,248,255,.72) !important;box-shadow:0 0 15px rgba(221,227,239,.32) !important}.trail-rank-badge.rank-3{color:#FFF7EF !important;background:linear-gradient(135deg,#E3A86F 0%,#B8733A 52%,#734421 100%) !important;border:1px solid rgba(232,176,119,.62) !important;box-shadow:0 0 15px rgba(184,115,58,.30) !important}.trail-rank-badge.rank-4,.trail-rank-badge.rank-5,.trail-rank-badge.rank-normal{color:#F6F1FF !important;background:linear-gradient(135deg,rgba(255,255,255,.20),rgba(126,118,148,.24)) !important;border:1px solid rgba(255,255,255,.28) !important;box-shadow:0 0 12px rgba(255,255,255,.10) !important}.trail-avatar-wrap{background:radial-gradient(circle at 32% 28%,#fff,#FFD45D 42%,#4A2E0C 100%) !important;border-color:rgba(255,212,93,.54) !important;box-shadow:0 0 18px rgba(255,212,93,.22) !important}.trail-tag,.trail-platform-text{color:#FFE9A8 !important;background:rgba(255,212,93,.12) !important;border-color:rgba(255,212,93,.46) !important}.trail-table th{color:#FFEFC8 !important;background:rgba(255,212,93,.065) !important;border-bottom-color:rgba(255,212,93,.18) !important}.trail-table td{border-bottom-color:rgba(255,212,93,.075) !important}div[data-testid="column"]:has(.trail-detail-button-title) .stButton>button{color:#FFF3C5 !important;background:rgba(34,25,26,.86) !important;border-color:rgba(255,212,93,.35) !important;box-shadow:0 0 12px rgba(255,212,93,.10) !important}</style>
""", unsafe_allow_html=True)



def inject_startrail_segment_tooltip_patch():
    """스타트레일 세그먼트 카드 tooltip을 카드 밖으로 확장되는 상세 팝업형으로 보정한다."""
    st.markdown(
        """
        <style>.startrail-page .trail-seg-card,.trail-seg-card{overflow:visible !important;z-index:3 !important}div[data-testid="column"]:has(.trail-seg-card){overflow:visible !important;position:relative !important;z-index:20 !important}div[data-testid="column"]:has(.trail-seg-card:hover),.trail-seg-card:hover{z-index:9999 !important}.trail-seg-name{position:relative !important;display:flex !important;align-items:center !important;justify-content:center !important;gap:6px !important;overflow:visible !important;z-index:5 !important}.trail-tooltip-wrap{position:relative !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;overflow:visible !important;z-index:10000 !important}.trail-tooltip-icon{width:17px !important;height:17px !important;min-width:17px !important;border-radius:999px !important;border:1px solid rgba(217,200,255,0.76) !important;color:#D9C8FF !important;background:rgba(10,8,28,0.78) !important;font-size:10px !important;font-weight:950 !important;line-height:15px !important;text-align:center !important;cursor:help !important;box-sizing:border-box !important}.trail-tooltip-text.trail-tooltip-rich{visibility:hidden !important;opacity:0 !important;pointer-events:none !important;position:absolute !important;z-index:100000 !important;bottom:145% !important;left:50% !important;transform:translateX(-50%) translateY(6px) !important;width:315px !important;max-width:min(315px,82vw) !important;padding:16px 18px !important;border-radius:18px !important;background:radial-gradient(circle at 16% 18%,rgba(196,143,255,.18),transparent 35%),linear-gradient(145deg,rgba(18,29,42,0.98),rgba(16,13,42,0.98)) !important;border:1px solid rgba(117,204,255,0.30) !important;box-shadow:0 18px 42px rgba(0,0,0,0.54),0 0 24px rgba(117,204,255,0.14),inset 0 1px 0 rgba(255,255,255,.08) !important;color:#EDE7FF !important;text-align:left !important;font-size:12px !important;line-height:1.55 !important;white-space:normal !important;word-break:keep-all !important;transition:opacity .16s ease,transform .16s ease,visibility .16s ease !important}.trail-tooltip-wrap:hover .trail-tooltip-text.trail-tooltip-rich{visibility:visible !important;opacity:1 !important;transform:translateX(-50%) translateY(0) !important}.trail-tooltip-wrap.tooltip-pos-0 .trail-tooltip-text.trail-tooltip-rich{left:0 !important;transform:translateX(-18%) translateY(6px) !important}.trail-tooltip-wrap.tooltip-pos-0:hover .trail-tooltip-text.trail-tooltip-rich{transform:translateX(-18%) translateY(0) !important}.trail-tooltip-wrap.tooltip-pos-4 .trail-tooltip-text.trail-tooltip-rich{left:100% !important;transform:translateX(-82%) translateY(6px) !important}.trail-tooltip-wrap.tooltip-pos-4:hover .trail-tooltip-text.trail-tooltip-rich{transform:translateX(-82%) translateY(0) !important}.trail-tooltip-title-panel{display:block !important;padding:12px 14px !important;margin:0 0 14px 0 !important;border-radius:12px !important;background:rgba(255,255,255,.075) !important;border:1px solid rgba(255,255,255,.12) !important;color:#FFF9FF !important;text-align:center !important;font-size:14px !important;font-weight:950 !important;line-height:1.55 !important}.trail-tooltip-label{display:block !important;margin:12px 0 5px !important;color:#F0B5FF !important;font-size:12px !important;font-weight:950 !important;line-height:1.35 !important}.trail-tooltip-body{display:block !important;color:rgba(255,255,255,.82) !important;font-size:12px !important;font-weight:700 !important;line-height:1.65 !important}.trail-tooltip-wrap.tooltip-seg-성단 .trail-tooltip-text.trail-tooltip-rich{border-color:rgba(255,107,138,.36) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(255,107,138,.15),inset 0 1px 0 rgba(255,255,255,.08) !important}.trail-tooltip-wrap.tooltip-seg-프로토스타 .trail-tooltip-text.trail-tooltip-rich{border-color:rgba(255,212,93,.38) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(255,212,93,.15),inset 0 1px 0 rgba(255,255,255,.08) !important}.trail-tooltip-wrap.tooltip-seg-위성 .trail-tooltip-text.trail-tooltip-rich{border-color:rgba(149,175,255,.38) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(149,175,255,.15),inset 0 1px 0 rgba(255,255,255,.08) !important}.trail-tooltip-wrap.tooltip-seg-슈퍼노바 .trail-tooltip-text.trail-tooltip-rich{border-color:rgba(255,157,245,.36) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(255,157,245,.15),inset 0 1px 0 rgba(255,255,255,.08) !important}.trail-tooltip-wrap.tooltip-seg-코멧 .trail-tooltip-text.trail-tooltip-rich{border-color:rgba(255,158,94,.36) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(255,158,94,.15),inset 0 1px 0 rgba(255,255,255,.08) !important}</style>
        """,
        unsafe_allow_html=True,
    )

def render_startrail_dashboard():
    inject_startrail_css()
    inject_startrail_segment_tooltip_patch()
    st.markdown(
        """
        <style>.startrail-page .trail-hero{position:relative !important}.startrail-page .trail-date-pill{position:absolute !important;top:0 !important;right:0 !important;z-index:20 !important;margin:0 !important}.startrail-page .trail-info-card{margin-top:76px !important}.startrail-page .trail-section-title,.startrail-page .trail-section-title *,.startrail-page .trail-panel-title,.startrail-page .trail-chart-title,.startrail-page .trail-table-title{color:#ffffff !important;text-shadow:0 0 14px rgba(255,255,255,0.22) !important}.startrail-page .trail-seg-icon-badge{width:62px !important;height:62px !important;min-width:62px !important;min-height:62px !important;border-radius:18px !important;display:flex !important;align-items:center !important;justify-content:center !important;margin:24px auto 18px auto !important;background:rgba(54,61,105,0.42) !important;border:1px solid rgba(165,176,255,0.35) !important;box-shadow:0 0 22px rgba(130,150,255,0.15),inset 0 0 18px rgba(255,255,255,0.05) !important;filter:none !important}.startrail-page .trail-seg-emoji{font-size:30px !important;line-height:1 !important;transform:none !important;filter:none !important}.startrail-page .trail-seg-card.active-성단 .trail-seg-icon-badge{background:rgba(78,63,49,.42) !important;border-color:rgba(255,218,107,.32) !important}.startrail-page .trail-seg-card.active-프로토스타 .trail-seg-icon-badge{background:rgba(38,78,68,.42) !important;border-color:rgba(94,220,155,.34) !important}.startrail-page .trail-seg-card.active-위성 .trail-seg-icon-badge{background:rgba(56,68,118,.46) !important;border-color:rgba(144,166,255,.38) !important}.startrail-page .trail-seg-card.active-슈퍼노바 .trail-seg-icon-badge{background:rgba(82,43,82,.42) !important;border-color:rgba(255,91,184,.34) !important}.startrail-page .trail-seg-card.active-코멧 .trail-seg-icon-badge{background:rgba(82,56,48,.42) !important;border-color:rgba(255,145,85,.34) !important}.startrail-page .trail-seg-card.active,.startrail-page .trail-seg-card.active-성단,.startrail-page .trail-seg-card.active-프로토스타,.startrail-page .trail-seg-card.active-위성,.startrail-page .trail-seg-card.active-슈퍼노바,.startrail-page .trail-seg-card.active-코멧{border-color:rgba(255,255,255,.62) !important;box-shadow:0 0 24px rgba(255,255,255,.08),inset 0 0 24px rgba(255,255,255,.025) !important}.startrail-page .trail-seg-card.active::before,.startrail-page .trail-seg-card.active-성단::before,.startrail-page .trail-seg-card.active-프로토스타::before,.startrail-page .trail-seg-card.active-위성::before,.startrail-page .trail-seg-card.active-슈퍼노바::before,.startrail-page .trail-seg-card.active-코멧::before{background:linear-gradient(90deg,transparent,rgba(255,255,255,.34),transparent) !important}html body .stApp .startrail-page .trail-seg-card .trail-seg-icon-badge,html body .stApp .trail-seg-card .trail-seg-icon-badge{width:58px !important;height:58px !important;min-width:58px !important;min-height:58px !important;border-radius:18px !important;margin:28px auto 17px auto !important;background:rgba(42,40,74,0.72) !important;border:1px solid rgba(165,176,255,0.30) !important;box-shadow:inset 0 1px 0 rgba(255,255,255,0.06),0 0 14px rgba(130,150,255,0.11) !important;filter:none !important}html body .stApp .startrail-page .trail-seg-card .trail-seg-emoji,html body .stApp .trail-seg-card .trail-seg-emoji{display:block !important;font-size:29px !important;line-height:1 !important;filter:none !important;text-shadow:none !important;transform:none !important}html body .stApp .trail-seg-card.active-성단 .trail-seg-icon-badge{background:rgba(255,212,93,.10) !important;border-color:rgba(255,212,93,.32) !important}html body .stApp .trail-seg-card.active-프로토스타 .trail-seg-icon-badge{background:rgba(152,255,171,.10) !important;border-color:rgba(152,255,171,.30) !important}html body .stApp .trail-seg-card.active-위성 .trail-seg-icon-badge{background:rgba(143,184,255,.10) !important;border-color:rgba(143,184,255,.32) !important}html body .stApp .trail-seg-card.active-슈퍼노바 .trail-seg-icon-badge{background:rgba(255,122,200,.10) !important;border-color:rgba(255,122,200,.30) !important}html body .stApp .trail-seg-card.active-코멧 .trail-seg-icon-badge{background:rgba(255,158,94,.10) !important;border-color:rgba(255,158,94,.30) !important}.startrail-page .trail-section-title,.startrail-page .trail-bottom-title,.startrail-page .trail-side-title,.startrail-page .trail-chart-title,.startrail-page .trail-table-title{color:#ffffff !important;text-shadow:0 0 14px rgba(255,255,255,0.20) !important}.startrail-page .trail-tooltip-text.trail-tooltip-rich,.trail-tooltip-text.trail-tooltip-rich{width:330px !important;max-width:min(330px,84vw) !important;padding:16px 18px !important;border-radius:18px !important;background:radial-gradient(circle at 16% 18%,rgba(117,204,255,.12),transparent 35%),linear-gradient(145deg,rgba(18,29,42,0.98),rgba(16,13,42,0.98)) !important;border:1px solid rgba(117,204,255,0.30) !important;box-shadow:0 18px 42px rgba(0,0,0,.54),0 0 24px rgba(117,204,255,.14),inset 0 1px 0 rgba(255,255,255,.08) !important}html body .stApp .startrail-page .trail-seg-card,html body .stApp .trail-seg-card{min-height:224px !important;height:224px !important;padding:16px 16px 16px !important;overflow:visible !important;background:radial-gradient(circle at 50% 16%,rgba(255,212,93,0.08),transparent 34%),linear-gradient(180deg,rgba(13,10,32,0.98),rgba(9,7,25,0.99)) !important;border-color:rgba(255,255,255,0.50) !important;box-shadow:0 0 20px rgba(0,0,0,0.30),inset 0 1px 0 rgba(255,255,255,0.06) !important}html body .stApp .startrail-page .trail-seg-card::before,html body .stApp .trail-seg-card::before,html body .stApp .startrail-page .trail-seg-card.active::before,html body .stApp .trail-seg-card.active::before,html body .stApp .startrail-page .trail-seg-card.active-성단::before,html body .stApp .trail-seg-card.active-성단::before,html body .stApp .startrail-page .trail-seg-card.active-프로토스타::before,html body .stApp .trail-seg-card.active-프로토스타::before,html body .stApp .startrail-page .trail-seg-card.active-위성::before,html body .stApp .trail-seg-card.active-위성::before,html body .stApp .startrail-page .trail-seg-card.active-슈퍼노바::before,html body .stApp .trail-seg-card.active-슈퍼노바::before,html body .stApp .startrail-page .trail-seg-card.active-코멧::before,html body .stApp .trail-seg-card.active-코멧::before{display:none !important;content:none !important;height:0 !important;opacity:0 !important;background:transparent !important;box-shadow:none !important}html body .stApp .startrail-page .trail-seg-icon-badge,html body .stApp .trail-seg-icon-badge{margin:8px auto 14px auto !important;width:60px !important;height:60px !important;min-width:60px !important;min-height:60px !important;background:rgba(44,42,78,0.92) !important;box-shadow:inset 0 1px 0 rgba(255,255,255,0.06),0 0 12px rgba(130,150,255,0.10) !important}html body .stApp .startrail-page .trail-seg-name,html body .stApp .trail-seg-name{margin-top:0 !important;margin-bottom:14px !important;line-height:1.15 !important}html body .stApp .startrail-page .trail-seg-count,html body .stApp .trail-seg-count{margin:0 0 8px 0 !important;line-height:1.05 !important}html body .stApp .startrail-page .trail-seg-desc,html body .stApp .trail-seg-desc{max-height:34px !important;min-height:0 !important;margin:0 !important;padding:0 6px !important;overflow:hidden !important;display:-webkit-box !important;-webkit-line-clamp:2 !important;-webkit-box-orient:vertical !important;line-height:1.28 !important;font-size:12px !important;word-break:keep-all !important}html body .stApp .startrail-page .trail-kpi-card,html body .stApp .startrail-page .trail-info-card,html body .stApp .startrail-page .trail-rank-card,html body .stApp .startrail-page .trail-side-card,html body .stApp .startrail-page .trail-chart-card,html body .stApp .startrail-page .trail-table,html body .stApp .startrail-page .trail-table-team-style,html body .stApp .startrail-page div[data-testid="stPlotlyChart"]{background:linear-gradient(180deg,rgba(14,10,33,0.98),rgba(8,7,24,0.99)) !important;backdrop-filter:none !important}html body .stApp .startrail-page .trail-filter-row{display:grid !important;grid-template-columns:repeat(2,minmax(0,1fr)) !important;gap:10px !important;align-items:end !important}@media (max-width:980px){.startrail-page .trail-date-pill{position:static !important;display:inline-flex !important;margin-top:18px !important}.startrail-page .trail-info-card{margin-top:24px !important}}</style>
        """,
        unsafe_allow_html=True,
    )
    # FINAL PATCH 2026-05-12: STAR TRAIL segment strategy card vertical fit
    # - 카드 하단 설명이 버튼 영역과 겹치거나 잘려 보이지 않도록 높이/내부 간격 보정
    # - 아이콘/이름/수치/설명 위치를 전체적으로 위로 당기되, 설명 가독성 유지
    st.markdown(
        """
        <style>html body .stApp .startrail-page .trail-seg-card,html body .stApp .trail-seg-card{height:252px !important;min-height:252px !important;padding:18px 15px 20px !important;display:flex !important;flex-direction:column !important;align-items:center !important;justify-content:flex-start !important;box-sizing:border-box !important;overflow:visible !important}html body .stApp .startrail-page .trail-seg-icon-badge,html body .stApp .trail-seg-icon-badge{width:54px !important;height:54px !important;min-width:54px !important;min-height:54px !important;margin:2px auto 13px auto !important;border-radius:17px !important}html body .stApp .startrail-page .trail-seg-emoji,html body .stApp .trail-seg-emoji{font-size:28px !important;line-height:1 !important}html body .stApp .startrail-page .trail-seg-name,html body .stApp .trail-seg-name{min-height:28px !important;margin:0 0 10px 0 !important;font-size:20px !important;line-height:1.18 !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;gap:6px !important}html body .stApp .startrail-page .trail-seg-count,html body .stApp .trail-seg-count{margin:0 0 13px 0 !important;font-size:29px !important;line-height:1.04 !important;letter-spacing:-0.03em !important}html body .stApp .startrail-page .trail-seg-desc,html body .stApp .trail-seg-desc{width:100% !important;max-width:210px !important;min-height:34px !important;max-height:none !important;margin:0 auto !important;padding:0 6px !important;display:flex !important;align-items:flex-start !important;justify-content:center !important;overflow:visible !important;-webkit-line-clamp:unset !important;-webkit-box-orient:unset !important;font-size:12.5px !important;line-height:1.42 !important;font-weight:800 !important;color:rgba(247,235,202,0.82) !important;word-break:keep-all !important;white-space:normal !important;text-align:center !important}html body .stApp div[data-testid="column"]:has(.trail-seg-card) .stButton>button{height:44px !important;min-height:44px !important;margin-top:0 !important;border-radius:0 0 10px 10px !important}@media (max-width:1280px){html body .stApp .startrail-page .trail-seg-card,html body .stApp .trail-seg-card{height:260px !important;min-height:260px !important}}</style>
        """,
        unsafe_allow_html=True,
    )



    # STABLE FINAL STARTRAIL PATCH 2026-05-12
    # - 기존 CSS 중복으로 인한 패널 투명도 덮어쓰기 방지
    # - 상단 시작점은 STAR SEED와 같은 -4.6rem 기준으로 통일
    # - 스타트레일 중하단 카드/테이블/그래프/상세박스를 불투명 패널로 통일
    st.markdown(
        """
        <style>html body .stApp .block-container:has(.startrail-page){padding-top:0 !important;margin-top:-4.6rem !important;max-width:1560px !important}html body .stApp .startrail-page .startrail-hero-modern,html body .stApp .startrail-page .trail-hero-top.startrail-hero-modern{display:grid !important;grid-template-columns:minmax(0,1fr) 560px !important;column-gap:44px !important;align-items:center !important;margin-top:0 !important;margin-bottom:28px !important}html body .stApp .startrail-page .trail-title-block{display:grid !important;grid-template-columns:106px minmax(0,1fr) !important;gap:24px !important;min-height:116px !important;align-items:center !important}html body .stApp .startrail-page .trail-title-icon{width:90px !important;height:90px !important;border-radius:16px !important;background:radial-gradient(circle at 45% 30%,rgba(255,212,93,.18),transparent 56%),rgba(18,16,34,.96) !important;border:2px solid rgba(255,248,225,.86) !important;box-shadow:0 0 16px rgba(255,212,93,.16),inset 0 1px 0 rgba(255,255,255,.10) !important}html body .stApp .startrail-page .trail-title-icon .trail-spark-icon{transform:scale(1.22) !important;transform-origin:center center !important}html body .stApp .startrail-page .trail-brand-title{font-size:52px !important;line-height:1.02 !important;font-weight:950 !important;letter-spacing:-0.06em !important;margin:0 0 9px 0 !important;color:#FFF8FF !important;text-shadow:0 0 16px rgba(255,255,255,.16),0 0 18px rgba(255,212,93,.14) !important;display:flex !important;align-items:baseline !important;gap:12px !important;white-space:nowrap !important}html body .stApp .startrail-page .trail-brand-title span{font-size:40px !important;color:#FFD45D !important;font-weight:950 !important;letter-spacing:-0.04em !important}html body .stApp .startrail-page .trail-title-accent-line{width:292px !important;height:2px !important;margin:0 0 10px 2px !important;background:linear-gradient(90deg,rgba(255,212,93,.88),rgba(255,212,93,.46),rgba(255,212,93,0)) !important}html body .stApp .startrail-page .trail-title-block .trail-subtitle{font-size:17px !important;line-height:1.45 !important;font-weight:780 !important;color:#E8DFFF !important;white-space:nowrap !important}html body .stApp .startrail-page .trail-date-pill{position:absolute !important;top:0 !important;right:0 !important;z-index:40 !important}html body .stApp .startrail-page .trail-info-card{margin-top:58px !important;background:radial-gradient(circle at 12% 44%,rgba(255,212,93,.10),transparent 32%),linear-gradient(135deg,rgba(18,15,38,.98),rgba(9,8,25,.99)) !important;backdrop-filter:none !important}html body .stApp .startrail-page .trail-rank-card,html body .stApp .startrail-page .trail-side-card,html body .stApp .startrail-page .trail-chart-card,html body .stApp .startrail-page .trail-table,html body .stApp .startrail-page .trail-table-team-style,html body .stApp .startrail-page .trail-radar-card,html body .stApp .startrail-page .trail-kpi-card,html body .stApp .startrail-page div[data-testid="stPlotlyChart"]{background:radial-gradient(circle at 50% 8%,rgba(196,143,255,.08),transparent 34%),linear-gradient(180deg,rgba(13,10,31,.985),rgba(7,6,22,.995)) !important;backdrop-filter:none !important;border-color:rgba(255,255,255,.32) !important;box-shadow:0 0 22px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.055) !important}html body .stApp .startrail-page .trail-table th,html body .stApp .startrail-page .trail-table-team-style th{background:rgba(31,30,51,.98) !important}html body .stApp .startrail-page .trail-table td,html body .stApp .startrail-page .trail-table-team-style td{background:rgba(8,8,26,.96) !important}html body .stApp .startrail-page .trail-bar-track{background:rgba(255,255,255,.095) !important}html body .stApp .startrail-page .trail-seg-card,html body .stApp .trail-seg-card{background:radial-gradient(circle at 50% 18%,rgba(196,143,255,.075),transparent 36%),linear-gradient(180deg,rgba(13,10,31,.985),rgba(7,6,22,.995)) !important;backdrop-filter:none !important;border-color:rgba(255,255,255,.50) !important}html body .stApp .startrail-page .trail-seg-card::before,html body .stApp .trail-seg-card::before{display:none !important;content:none !important;opacity:0 !important}@media (max-width:1200px){html body .stApp .startrail-page .trail-brand-title{font-size:42px !important}html body .stApp .startrail-page .trail-brand-title span{font-size:32px !important}html body .stApp .startrail-page .trail-title-icon{width:78px !important;height:78px !important}html body .stApp .startrail-page .trail-title-block{grid-template-columns:92px minmax(0,1fr) !important}}</style>
        """,
        unsafe_allow_html=True,
    )


    # FINAL PATCH 2026-05-12: STARTRAIL white text + opaque panel stabilization
    st.markdown(
        """
        <style>html body .stApp .startrail-page{--trail-opaque-panel:rgba(9,8,25,0.995);--trail-opaque-panel-2:rgba(13,10,31,0.995);--trail-white:#FFF9FF}html body .stApp .startrail-page .trail-section-title,html body .stApp .startrail-page .trail-section-title *,html body .stApp .startrail-page .trail-bottom-title,html body .stApp .startrail-page .trail-bottom-title *,html body .stApp .startrail-page .trail-side-title,html body .stApp .startrail-page .trail-side-title *,html body .stApp .startrail-page .trail-chart-title,html body .stApp .startrail-page .trail-chart-title *,html body .stApp .startrail-page .trail-table-title,html body .stApp .startrail-page .trail-table-title *,html body .stApp .startrail-page .priority-header-title,html body .stApp .startrail-page .priority-header-title *,html body .stApp .startrail-page .graph-header-title,html body .stApp .startrail-page .graph-header-title *{color:var(--trail-white) !important;text-shadow:0 0 14px rgba(255,255,255,0.18) !important}html body .stApp .startrail-page .trail-kpi-label,html body .stApp .startrail-page .trail-kpi-value,html body .stApp .startrail-page .trail-kpi-card,html body .stApp .startrail-page .trail-kpi-card *{color:var(--trail-white) !important}html body .stApp .startrail-page .trail-kpi-value{text-shadow:0 0 16px rgba(255,255,255,.16) !important}html body .stApp .startrail-page .trail-kpi-card,html body .stApp .startrail-page .trail-info-card,html body .stApp .startrail-page .trail-seg-card,html body .stApp .startrail-page .trail-rank-card,html body .stApp .startrail-page .trail-side-card,html body .stApp .startrail-page .trail-chart-card,html body .stApp .startrail-page .trail-table,html body .stApp .startrail-page .trail-table-team-style,html body .stApp .startrail-page .trail-radar-card,html body .stApp .startrail-page .trail-detail-panel,html body .stApp .startrail-page .trail-detail-card,html body .stApp .startrail-page .board-panel,html body .stApp .startrail-page .priority-table-panel,html body .stApp .startrail-page div[data-testid="stPlotlyChart"],html body .stApp .startrail-page [data-testid="stDataFrame"],html body .stApp .startrail-page [data-testid="stTable"]{background:radial-gradient(circle at 50% 8%,rgba(196,143,255,.065),transparent 35%),linear-gradient(180deg,var(--trail-opaque-panel-2),var(--trail-opaque-panel)) !important;background-color:var(--trail-opaque-panel) !important;backdrop-filter:none !important;-webkit-backdrop-filter:none !important;border-color:rgba(255,255,255,.34) !important;box-shadow:0 0 22px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.055) !important}html body .stApp .startrail-page div[data-testid="stPlotlyChart"]>div,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .js-plotly-plot,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .plot-container,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .svg-container{background:var(--trail-opaque-panel) !important;background-color:var(--trail-opaque-panel) !important;border-radius:18px !important}html body .stApp .startrail-page .trail-table th,html body .stApp .startrail-page .trail-table-team-style th{background:rgba(31,30,51,.995) !important;color:var(--trail-white) !important}html body .stApp .startrail-page .trail-table td,html body .stApp .startrail-page .trail-table-team-style td{background:rgba(8,8,26,.985) !important;color:var(--trail-white) !important}html body .stApp .startrail-page .trail-seg-card::before,html body .stApp .trail-seg-card::before,html body .stApp .startrail-page .trail-seg-card.active::before,html body .stApp .trail-seg-card.active::before,html body .stApp .startrail-page .trail-seg-card.active-성단::before,html body .stApp .trail-seg-card.active-성단::before,html body .stApp .startrail-page .trail-seg-card.active-프로토스타::before,html body .stApp .trail-seg-card.active-프로토스타::before,html body .stApp .startrail-page .trail-seg-card.active-위성::before,html body .stApp .trail-seg-card.active-위성::before,html body .stApp .startrail-page .trail-seg-card.active-슈퍼노바::before,html body .stApp .trail-seg-card.active-슈퍼노바::before,html body .stApp .startrail-page .trail-seg-card.active-코멧::before,html body .stApp .trail-seg-card.active-코멧::before{display:none !important;content:none !important;height:0 !important;opacity:0 !important;background:transparent !important;box-shadow:none !important}</style>
        """,
        unsafe_allow_html=True,
    )

    summary = load_startrail_summary_data()
    kpi = load_startrail_kpi_data()
    raw = load_startrail_raw_candidate_data()
    df = build_startrail_candidate_data(raw)
    constellation_df = load_startrail_constellation_data()

    if not summary or not kpi:
        st.error("스타트레일 요약/KPI CSV를 찾지 못했습니다. `10_dashboard/data/startrail_대시보드요약.csv`, `startrail_핵심KPI.csv` 경로를 확인해주세요.")
        return
    if raw.empty:
        st.error("스타트레일 개인 후보 CSV를 찾지 못했습니다. `10_dashboard/data/startrail_개인후보통합테이블.csv` 경로를 확인해주세요.")
        return

    soop_icon = startrail_img_to_base64(STARTRAIL_ASSET_FILES["soop"])
    chzzk_icon = startrail_img_to_base64(STARTRAIL_ASSET_FILES["chzzk"])

    def _num(v, default=0):
        try:
            if pd.isna(v):
                return default
            return float(str(v).replace(",", "").replace("₩", "").strip())
        except Exception:
            return default

    def _safe_text(v, default="-"):
        if v is None:
            return default
        try:
            if pd.isna(v):
                return default
        except Exception:
            pass
        text = str(v).strip()
        return text if text and text.lower() != "nan" else default

    def _display_name_from_row(row, current_segment=None, default="-"):
        """스타트레일 상세 패널/카드에서 사용할 표시 이름을 안정적으로 찾는다.
        - 과거 session_state에 표시이름이 '-'로 남아있는 경우를 방지
        - 개인 후보: 스트리머, 스트리머명, 채널명 등 후보 컬럼을 순차 fallback
        - 성단: 소속 우선
        """
        if row is None:
            return default

        segment_value = _safe_text(
            row.get("세그먼트", current_segment if current_segment is not None else ""),
            ""
        )

        if segment_value == "성단" or current_segment == "성단":
            candidate_cols = ["표시이름", "소속", "그룹명", "성단명"]
        else:
            candidate_cols = [
                "표시이름",
                "스트리머",
                "스트리머명",
                "채널명",
                "channel_title",
                "channel_name",
                "이름",
                "name",
            ]

        for col in candidate_cols:
            if hasattr(row, "get"):
                value = _safe_text(row.get(col, ""), "")
            else:
                value = ""
            if value and value != "-":
                return value

        return default

    def _esc(v):
        return html_lib.escape(_safe_text(v))

    def _avatar(row, name):
        image_url = _safe_text(row.get("이미지URL", ""), "")
        if image_url and image_url.lower() not in ["", "nan", "none", "-"]:
            return startrail_local_image_src(image_url)
        return f"https://api.dicebear.com/7.x/avataaars/svg?seed={html_lib.escape(str(name))}"

    def _platform_badge(platform):
        platform = _safe_text(platform, "")
        if platform == "SOOP":
            return f'<img src="data:image/png;base64,{soop_icon}" alt="SOOP" style="height:24px;border-radius:7px;object-fit:contain;">'
        if platform == "CHZZK":
            return f'<img src="data:image/png;base64,{chzzk_icon}" alt="CHZZK" style="height:24px;border-radius:7px;object-fit:contain;">'
        if platform:
            return f'<span style="color:#D9C8FF;font-size:13px;font-weight:850;">{html_lib.escape(platform)}</span>'
        return ""

    def _donation_to_krw(value):
        return _num(value) * 110

    def _format_krw_compact(value):
        amount = _num(value)
        for unit_value, unit_name in [
            (100_000_000, "억"),
            (10_000, "만"),
            (1_000, "천"),
            (100, "백"),
        ]:
            if abs(amount) >= unit_value:
                return f"{amount / unit_value:.1f}{unit_name} 원"
        return f"{amount:,.0f}원"

    def _metric_bar(label, value, max_value, color):
        value = _num(value)
        max_value = max(_num(max_value), 1)
        percent = max(0, min(value / max_value, 1.0)) * 100
        display_value = _format_krw_compact(_donation_to_krw(value)) if "도네이션" in label else f"{value:,.0f}"
        return f'''
        <div class="trail-bar-row">
            <div class="trail-bar-head">
                <span class="trail-bar-label">{html_lib.escape(label)}</span>
                <span class="trail-bar-value" style="color:{color};">{display_value}</span>
            </div>
            <div class="trail-bar-track"><div class="trail-bar-fill" style="width:{percent:.2f}%; background:{color};"></div></div>
        </div>
        '''

    def _metric_max(frame, columns, fallback=1):
        if frame is None or frame.empty:
            return max(_num(fallback), 1)
        values = []
        for column in columns:
            if column in frame.columns:
                values.append(pd.to_numeric(frame[column], errors="coerce"))
        if not values:
            return max(_num(fallback), 1)
        max_value = pd.concat(values, ignore_index=True).fillna(0).max()
        return max(_num(max_value, fallback), _num(fallback), 1)

    if "startrail_current_seg" not in st.session_state:
        st.session_state.startrail_current_seg = "프로토스타"
    if "startrail_selected_streamer" not in st.session_state:
        st.session_state.startrail_selected_streamer = None

    total_streamer = _num(kpi.get("총 분석 스트리머 수"))
    avg_viewership = _num(kpi.get("평균 뷰어십"))
    avg_donation = _num(kpi.get("평균 도네이션"))

    st.markdown(f'''
    <div class="startrail-page">
        <div class="startrail-hero">
            <div class="trail-date-pill">📅 2025.01.01 ~ 2026.03.31</div>
            <div class="trail-hero-top startrail-hero-modern">
                <div class="trail-title-block">
                    <div class="trail-title-icon">{TRAIL_ICON_HTML}</div>
                    <div>
                        <div class="trail-brand-title">스타트레일 <span>Star Trail</span></div>
                        <div class="trail-title-accent-line"></div>
                        <div class="trail-subtitle">기존 플랫폼의 데이터 궤적을 따라 CIME 영입 후보군을 찾습니다</div>
                    </div>
                </div>
                <div class="trail-info-card">
                    <div class="trail-info-icon">✦</div>
                    <div>
                        <div class="trail-info-title">스타트레일은 무엇을 찾나요?</div>
                        <div class="trail-info-desc">기존 플랫폼에서 이미 활동성과 팬덤이 확인된 스트리머를 대상으로<br>방송화력, 수익성, 외부유입 가능성을 함께 검토해 CIME 영입 후보를 선별합니다.</div>
                    </div>
                </div>
            </div>
            <div class="trail-kpi-grid">
                <div class="trail-kpi-card"><div class="trail-kpi-label">총 분석 스트리머 수</div><div class="trail-kpi-value">{total_streamer:,.0f} 명</div></div>
                <div class="trail-kpi-card"><div class="trail-kpi-label">평균 뷰어십</div><div class="trail-kpi-value">{avg_viewership:,.0f}</div></div>
                <div class="trail-kpi-card"><div class="trail-kpi-label">평균 도네이션(원화)</div><div class="trail-kpi-value">{_format_krw_compact(_donation_to_krw(avg_donation))}</div></div>
            </div>
            <div class="trail-divider"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    seg_data = {
        "성단": {
            "icon": "⭐",
            "count": f"{_num(summary.get('성단 그룹 후보 수')):,.0f}개",
            "tooltip_title": "팬덤이 함께 이동할 가능성이 높은<br>그룹형 후보군",
            "tooltip_criteria": "그룹/소속성, 팬덤 결집, 멤버 단위 이동 가능성",
            "tooltip_point": "여러 스트리머와 팬덤을 함께 유입시켜 초기 트래픽을 빠르게 확보합니다.",
            "desc": "소속 개인 수 : 455명",
        },
        "프로토스타": {
            "icon": "🌱",
            "count": f"{_num(summary.get('프로토스타 S급 후보 수')):,.0f}명",
            "tooltip_title": "현재 규모는 작지만 방송 반응이 좋은<br>성장형 후보군",
            "tooltip_criteria": "시청자 반응, 채팅, 뷰어십, 팔로워 대비 성과",
            "tooltip_point": "성장 가능성이 높은 후보를 조기에 발굴해 CIME의 육성 타깃으로 활용합니다.",
            "desc": "S급 후보 수",
        },
        "위성": {
            "icon": "🛰️",
            "count": f"{_num(summary.get('위성 후보 수')):,.0f}명",
            "tooltip_title": "소속 없이도 방송 성과가 검증된<br>개인형 후보군",
            "tooltip_criteria": "도네이션, 채팅화력, 평균 시청자, 개인 활동 여부",
            "tooltip_point": "검증된 개인 방송 화력을 바탕으로 안정적인 콘텐츠와 수익성을 확보합니다.",
            "desc": "",
        },
        "슈퍼노바": {
            "icon": "💥",
            "count": f"{_num(summary.get('슈퍼노바 핵심 후보 수')):,.0f}명",
            "tooltip_title": "대중성과 팬덤 규모가 큰<br>간판형 후보군",
            "tooltip_criteria": "팔로워, 최고 시청자, 유튜브 구독자, 팬덤지수, 방송화력",
            "tooltip_point": "인지도 높은 스트리머를 통해 플랫폼 주목도와 외부 유입을 높입니다.",
            "desc": "핵심 후보군 수",
        },
        "코멧": {
            "icon": "☄️",
            "count": f"{_num(summary.get('코멧 후보 수')):,.0f}명",
            "tooltip_title": "방송 외부 채널에서 인지도가 높은<br>발견형 후보군",
            "tooltip_criteria": "유튜브 구독자, X 팔로워, 외부 유입지수, 플랫폼 대비 외부 체급",
            "tooltip_point": "외부 팬덤을 CIME으로 연결해 새로운 이용자 유입을 만듭니다.",
            "desc": "",
        },
    }

    st.markdown('<div class="startrail-page"><div class="trail-section-title">🛸 세그먼트 전략</div></div>', unsafe_allow_html=True)
    seg_cols = st.columns(5)
    for i, seg in enumerate(seg_data.keys()):
        with seg_cols[i]:
            info = seg_data[seg]
            active_class = f"active active-{seg}" if st.session_state.startrail_current_seg == seg else ""
            icon_html = html_lib.escape(info.get("icon", "✦"))
            tooltip_title = str(info.get("tooltip_title", "")).replace("<br>", "__BR__")
            tooltip_title = html_lib.escape(tooltip_title).replace("__BR__", "<br>")
            tooltip_criteria = html_lib.escape(str(info.get("tooltip_criteria", "")))
            tooltip_point = html_lib.escape(str(info.get("tooltip_point", "")))
            tooltip_plain = html_lib.escape(
                f'{str(info.get("tooltip_title", "")).replace("<br>", " ")} / 주요 판단 기준: {info.get("tooltip_criteria", "")} / CIME 활용 포인트: {info.get("tooltip_point", "")}'
            )
            st.markdown(f'''
            <div class="trail-seg-card {active_class}">
                <div class="trail-seg-icon-badge"><span class="trail-seg-emoji">{icon_html}</span></div>
                <div class="trail-seg-name">
                    <span>{html_lib.escape(seg)}</span>
                    <span class="trail-tooltip-wrap tooltip-pos-{i} tooltip-seg-{html_lib.escape(seg)}" aria-label="{tooltip_plain}">
                        <span class="trail-tooltip-icon">?</span>
                        <span class="trail-tooltip-text trail-tooltip-rich">
                            <span class="trail-tooltip-title-panel">{tooltip_title}</span>
                            <span class="trail-tooltip-label">주요 판단 기준</span>
                            <span class="trail-tooltip-body">{tooltip_criteria}</span>
                            <span class="trail-tooltip-label">CIME 활용 포인트</span>
                            <span class="trail-tooltip-body">{tooltip_point}</span>
                        </span>
                    </span>
                </div>
                <div class="trail-seg-count">{info["count"]}</div>
                {f'<div class="trail-seg-desc">{html_lib.escape(info["desc"])}</div>' if str(info.get("desc", "")).strip() else ''}
            </div>
            ''', unsafe_allow_html=True)
            if st.button("선택", key=f"startrail_seg_btn_{seg}", use_container_width=True):
                st.session_state.startrail_current_seg = seg
                st.session_state.startrail_selected_streamer = None
                st.rerun()

    st.markdown('<div class="startrail-page"><div class="trail-divider" style="margin-top:28px;"></div></div>', unsafe_allow_html=True)

    current_seg = st.session_state.startrail_current_seg
    platform_filter = "전체"
    segment_detail_filter = "전체"

    if current_seg == "성단":
        filtered_df = constellation_df.copy()
    else:
        filtered_df = df[df["세그먼트"] == current_seg].copy() if "세그먼트" in df.columns else pd.DataFrame()

    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values("스코어", ascending=False).reset_index(drop=True)
        filtered_df["순위"] = filtered_df.index + 1
        filtered_df["상위퍼센트"] = (filtered_df["순위"] / len(filtered_df) * 100).round(2)
    else:
        filtered_df = pd.DataFrame(columns=list(filtered_df.columns) + ["순위", "상위퍼센트"] if hasattr(filtered_df, 'columns') else ["순위", "상위퍼센트"])

    # TOP5 영역과 우측 상세 패널을 큰 그리드로 묶음
    # 플랫폼 필터는 우측 상세 패널 위가 아니라 TOP5 영역 우상단에 배치한다.
    left_area, right_area = st.columns([2.35, 0.85], gap="large")

    with left_area:
        # 코멧/슈퍼노바는 플랫폼 필터와 세그먼트 필터를 좌우 2열로 배치한다.
        top_title_col, top_filter_col = st.columns([1.36, 1.08], gap="large")
        with top_title_col:
            st.markdown(
                f'<div class="startrail-page"><div class="trail-section-title">🏆 {html_lib.escape(current_seg)} TOP 5</div></div>',
                unsafe_allow_html=True,
            )
        with top_filter_col:
            if current_seg == "코멧":
                filter_col_1, filter_col_2 = st.columns(2, gap="small")
                with filter_col_1:
                    platform_filter = st.selectbox(
                        "플랫폼 필터",
                        ["전체", "SOOP", "CHZZK"],
                        key="startrail_platform_filter_comet",
                    )
                with filter_col_2:
                    segment_detail_filter = st.selectbox(
                        "세그먼트 필터",
                        ["전체", "X 강세형", "유튜브 강세형", "하이브리드"],
                        key="startrail_segment_detail_filter",
                    )
            elif current_seg == "슈퍼노바":
                filter_col_1, filter_col_2 = st.columns(2, gap="small")
                with filter_col_1:
                    platform_filter = st.selectbox(
                        "플랫폼 필터",
                        ["전체", "SOOP", "CHZZK"],
                        key="startrail_platform_filter_supernova",
                    )
                with filter_col_2:
                    segment_detail_filter = st.selectbox(
                        "세그먼트 필터",
                        ["전체", "개인", "그룹"],
                        key="startrail_supernova_segment_filter",
                    )
            elif current_seg != "성단":
                platform_filter = st.selectbox(
                    "플랫폼 필터",
                    ["전체", "SOOP", "CHZZK"],
                    key="startrail_platform_filter",
                )
            else:
                st.markdown('<div style="height:64px;"></div>', unsafe_allow_html=True)

    if current_seg != "성단" and not filtered_df.empty:
        if platform_filter != "전체" and "플랫폼" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["플랫폼"] == platform_filter].copy()
        if segment_detail_filter != "전체" and "세그먼트필터" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["세그먼트필터"] == segment_detail_filter].copy()
        filtered_df = filtered_df.sort_values("스코어", ascending=False).reset_index(drop=True)
        filtered_df["순위"] = filtered_df.index + 1
        filtered_df["상위퍼센트"] = (filtered_df["순위"] / len(filtered_df) * 100).round(2) if len(filtered_df) else 0

    segment_metric_df = filtered_df.head(10).copy()
    top_5 = filtered_df.head(5).copy()

    if st.session_state.startrail_selected_streamer is not None:
        selected = dict(st.session_state.startrail_selected_streamer)
    else:
        selected = None

    # 상세 정보는 사용자가 명시적으로 후보를 고른 뒤에만 표시한다.
    # 이전 버전에서 남은 stale session_state만 정리하고, TOP1 자동 선택은 하지 않는다.
    if selected is not None:
        selected = dict(selected)
        selected["세그먼트"] = "성단" if current_seg == "성단" else _safe_text(selected.get("세그먼트", current_seg))
        selected_name = _display_name_from_row(selected, current_seg, default="")
        if selected["세그먼트"] != current_seg or not selected_name:
            selected = None
            st.session_state.startrail_selected_streamer = None
        else:
            selected["표시이름"] = selected_name
            st.session_state.startrail_selected_streamer = selected

    with left_area:
        if top_5.empty:
            st.warning("선택한 조건에 해당하는 후보가 없습니다.")
        else:
            card_cols = st.columns(5, gap="medium")
            for i, (_, row) in enumerate(top_5.iterrows()):
                if current_seg == "성단":
                    display_name = _safe_text(row.get("소속", "-"))
                    display_segment = "성단"
                    score_text = f'{_num(row.get("스코어")):.0f}'
                    avatar_url = _avatar(row, display_name)
                else:
                    display_name = _display_name_from_row(row, current_seg)
                    display_segment = _safe_text(row.get("세그먼트", current_seg))
                    score_text = f'{_num(row.get("스코어")):.2f}'
                    avatar_url = _avatar(row, display_name)
                badge_class = f"rank-{i+1}" if i < 5 else "rank-normal"
                with card_cols[i]:
                    st.markdown(f"""
                    <div class="trail-rank-card">
                        <div class="trail-rank-badge {badge_class}">{i + 1}</div>
                        <div class="trail-avatar-wrap"><img src="{avatar_url}" alt="avatar"></div>
                        <div class="trail-rank-name">{html_lib.escape(display_name)}</div>
                        <div><span class="trail-tag">{html_lib.escape(display_segment)}</span></div>
                        <div class="trail-score-label">스코어</div>
                        <div class="trail-score-value">{score_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("상세 보기", key=f"startrail_streamer_btn_{display_segment}_{display_name}_{i}", use_container_width=True):
                        selected_data = row.to_dict()
                        selected_data["세그먼트"] = display_segment
                        selected_data["표시이름"] = display_name
                        st.session_state.startrail_selected_streamer = selected_data
                        st.rerun()

    with right_area:
        if selected is not None:
            s = selected
            detail_seg = _safe_text(s.get("세그먼트", current_seg))
            detail_name = _display_name_from_row(s, detail_seg)
            avatar_url = _avatar(s, detail_name)
            platform_html = "" if detail_seg == "성단" else _platform_badge(s.get("플랫폼", ""))
            if detail_seg == "성단":
                metrics = [
                    ("멤버 수", s.get("멤버수", 0), _metric_max(segment_metric_df, ["멤버수"], s.get("멤버수", 0)), "#83F6A0"),
                    ("뷰어십 합계", s.get("합계_뷰어십", 0), _metric_max(segment_metric_df, ["합계_뷰어십"], s.get("합계_뷰어십", 0)), "#FF7B86"),
                    ("도네이션 합계(원화)", s.get("합계_도네이션", 0), _metric_max(segment_metric_df, ["합계_도네이션"], s.get("합계_도네이션", 0)), "#FFD45D"),
                ]
                radar_metrics = {"플랫폼체급": (_num(s.get("플랫폼체급_점수")), 100), "ARPU": (_num(s.get("ARPU_점수")), 100), "외부인기": (_num(s.get("외부인기_점수")), 100), "대중성": (_num(s.get("대중성_점수")), 100)}
            else:
                metrics = [
                    ("뷰어십", s.get("뷰어십", 0), _metric_max(segment_metric_df, ["뷰어십"], s.get("뷰어십", 0)), "#FF7B86"),
                    ("도네이션(원화)", s.get("도네이션", 0), _metric_max(segment_metric_df, ["도네이션"], s.get("도네이션", 0)), "#FFD45D"),
                    ("최고 팔로워", s.get("팔로워수", s.get("최고_팔로워", 0)), _metric_max(segment_metric_df, ["팔로워수", "최고_팔로워"], s.get("팔로워수", s.get("최고_팔로워", 0))), "#83F6A0"),
                    ("평균 시청자", s.get("평균시청자", s.get("평균_시청자_최댓값", 0)), _metric_max(segment_metric_df, ["평균시청자", "평균_시청자_최댓값"], s.get("평균시청자", s.get("평균_시청자_최댓값", 0))), "#75CCFF"),
                    ("최고 시청자", s.get("최고시청자", s.get("최고_시청자", 0)), _metric_max(segment_metric_df, ["최고시청자", "최고_시청자"], s.get("최고시청자", s.get("최고_시청자", 0))), "#F08CFF"),
                ]
                radar_metrics = {"대중성": (_num(s.get("대중성_표준점수")), 100), "방송화력": (_num(s.get("방송화력_표준점수")), 100), "팬덤결집력": (_num(s.get("팬덤결집력_표준점수")), 100), "수익성": (_num(s.get("수익성_표준점수")), 100), "외부유입가능성": (_num(s.get("외부유입가능성_표준점수")), 100)}
            bar_html = "".join(_metric_bar(label, val, max_val, color) for label, val, max_val, color in metrics)
            html(f'''
            <div class="trail-side-card">
                <div class="trail-side-title">후보 상세 정보</div>
                <div class="trail-detail-avatar"><img src="{avatar_url}" alt="avatar"></div>
                <div class="trail-detail-name">{html_lib.escape(detail_name)}</div>
                <div class="trail-detail-tags"><span class="trail-tag">{html_lib.escape(detail_seg)}</span>{platform_html}</div>
                {bar_html}
            </div>
            ''')
            radar_labels = list(radar_metrics.keys())
            radar_values = [max(0, min(_num(v) / max(_num(m), 1), 1.0)) * 100 for v, m in radar_metrics.values()]
            if radar_labels:
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=radar_values + [radar_values[0]], theta=radar_labels + [radar_labels[0]], fill="toself", name="능력치", line=dict(width=2, color="#8FB8FF"), fillcolor="rgba(143,184,255,0.26)", opacity=0.92))
                # 우측 상세 오각형 그래프
                # - polar domain을 안쪽으로 살짝 줄여 축 라벨이 카드 밖으로 잘리지 않게 조정
                # - 좌/우/하단 margin을 늘려 "팬덤결집력", "외부유입가능성" 같은 긴 라벨 여백 확보
                fig_radar.update_layout(
                    polar=dict(
                        domain=dict(x=[0.13, 0.87], y=[0.13, 0.87]),
                        bgcolor=STARTRAIL_TRANSPARENT,
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100],
                            tickfont=dict(size=8, color="#8b949e"),
                            gridcolor="rgba(255,255,255,0.13)"
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=10, color="white"),
                            gridcolor="rgba(255,255,255,0.13)"
                        )
                    ),
                    showlegend=False,
                    margin=dict(l=34, r=34, t=24, b=36),
                    paper_bgcolor=STARTRAIL_TRANSPARENT,
                    plot_bgcolor=STARTRAIL_TRANSPARENT,
                    font_color="white",
                    height=340
                )
                # 상세 지표 박스와 오각형 그래프 사이 간격
                st.markdown(
                    "<div style='height:18px;'></div>",
                    unsafe_allow_html=True
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            html('''
            <div class="trail-side-card">
                <div class="trail-side-title">후보 상세 정보</div>
                <div style="text-align:center; padding:52px 14px 18px;">
                    <div style="font-size:38px; margin-bottom:14px;">✦</div>
                    <div style="font-size:14px; line-height:1.7; color:rgba(255,255,255,0.62); word-break:keep-all;">
                        TOP 5 카드나 우선순위 리스트에서<br>상세 보기를 선택하면 후보 정보가 표시됩니다.
                    </div>
                </div>
            </div>
            ''')

    with left_area:
        st.markdown('<div class="trail-divider" style="margin-top:34px;"></div>', unsafe_allow_html=True)
        table_col, graph_col = st.columns([1.02, 1.05], gap="large")
        with table_col:
            st.markdown(f"<div class='trail-bottom-title'>📋 {html_lib.escape(current_seg)} 영입 우선순위 리스트</div>", unsafe_allow_html=True)

            # 팀원 대시보드 형식: 표는 핵심 5개 컬럼만 두고, 상세보기는 표 오른쪽에 별도 버튼 열로 배치
            list_rows = filtered_df.head(10).copy()
            table_area, detail_btn_area = st.columns([0.84, 0.16], gap="small")

            with table_area:
                table_html = """
                <table class='trail-table trail-table-team-style'>
                    <colgroup>
                        <col class='col-rank'>
                        <col class='col-name'>
                        <col class='col-platform'>
                        <col class='col-score'>
                        <col class='col-percent'>
                    </colgroup>
                    <thead><tr>
                        <th>순위</th><th>스트리머명</th><th>플랫폼</th><th>스코어</th><th>상위 %</th>
                    </tr></thead><tbody>
                """

                for _, row in list_rows.iterrows():
                    rank_value = int(_num(row.get("순위"), 0))
                    if current_seg == "성단":
                        display_name = _safe_text(row.get("소속", row.get("표시이름", "-")))
                        platform_cell = "<span class='trail-platform-text'>GROUP</span>"
                        score_cell = f"{_num(row.get('스코어')):.0f}"
                    else:
                        display_name = _display_name_from_row(row, current_seg)
                        platform_cell = _platform_badge(row.get("플랫폼", ""))
                        score_cell = f"{_num(row.get('스코어')):.2f}"

                    percent_cell = f"{_num(row.get('상위퍼센트')):.1f}%"
                    table_html += (
                        f"<tr>"
                        f"<td class='rank-cell'>{rank_value}</td>"
                        f"<td class='name-cell'><b>{html_lib.escape(display_name)}</b></td>"
                        f"<td class='platform-cell'>{platform_cell}</td>"
                        f"<td class='score-cell'>{score_cell}</td>"
                        f"<td class='percent-cell'>{percent_cell}</td>"
                        f"</tr>"
                    )

                table_html += "</tbody></table>"
                st.markdown(table_html, unsafe_allow_html=True)

            with detail_btn_area:
                st.markdown("<div class='trail-detail-button-title'>상세 보기</div>", unsafe_allow_html=True)
                for btn_idx, (_, row) in enumerate(list_rows.iterrows(), start=1):
                    if current_seg == "성단":
                        display_name = _safe_text(row.get("소속", row.get("표시이름", "-")))
                        display_segment = "성단"
                    else:
                        display_name = _display_name_from_row(row, current_seg)
                        display_segment = _safe_text(row.get("세그먼트", current_seg))

                    if st.button(
                        f"{btn_idx}위",
                        key=f"startrail_table_detail_btn_{current_seg}_{btn_idx}_{display_name}",
                        use_container_width=True,
                    ):
                        selected_data = row.to_dict()
                        selected_data["세그먼트"] = display_segment
                        selected_data["표시이름"] = display_name
                        st.session_state.startrail_selected_streamer = selected_data
                        st.rerun()

        with graph_col:
            graph_title = "🌌 성단 TOP15 히트맵" if current_seg == "성단" else "🌌 코멧 타겟팅 맵" if current_seg == "코멧" else "🌌 위성 세그먼트 막대그래프" if current_seg == "위성" else f"🌌 {html_lib.escape(current_seg)} 세그먼트 분석 분포"
            st.markdown(f"<div class='trail-bottom-title'>{graph_title}</div>", unsafe_allow_html=True)
            if filtered_df.empty:
                st.warning("그래프를 표시할 데이터가 없습니다.")
            elif current_seg == "성단":
                heatmap_cols = ["플랫폼체급_점수", "ARPU_점수", "외부인기_점수", "대중성_점수", "영입우선_점수"]
                missing = [c for c in heatmap_cols if c not in filtered_df.columns]
                if missing:
                    st.warning(f"히트맵 컬럼이 부족합니다: {missing}")
                else:
                    fig = px.imshow(filtered_df.sort_values("영입우선_점수", ascending=False).head(15).set_index("소속")[heatmap_cols], text_auto=".0f", aspect="auto", color_continuous_scale="YlGnBu", zmin=0, zmax=100, labels=dict(color="점수"))
                    fig.update_layout(paper_bgcolor=STARTRAIL_TRANSPARENT, plot_bgcolor=STARTRAIL_TRANSPARENT, font_color="white", margin=dict(l=75, r=70, t=60, b=105), height=620)
                    st.plotly_chart(fig, use_container_width=True)
            elif current_seg == "코멧":
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
                if plot_all_df.empty and plot_comet_df.empty:
                    st.warning("코멧 타겟팅 맵을 그릴 수 있는 최고 팔로워/외부화력 값이 없습니다.")
                else:
                    fig = go.Figure()
                    if not plot_all_df.empty:
                        text_values = plot_all_df["스트리머명"] if "스트리머명" in plot_all_df.columns else None
                        fig.add_trace(go.Scatter(x=plot_all_df["최고_팔로워"], y=plot_all_df["통합_외부화력"], mode="markers", name="일반 스트리머", marker=dict(size=6, color="rgba(217,217,217,0.35)"), text=text_values, hovertemplate="<b>%{text}</b><br>최고 팔로워: %{x:,.0f}<br>통합 외부화력: %{y:,.0f}<extra></extra>"))
                    if "코멧유입경로" not in plot_comet_df.columns:
                        plot_comet_df["코멧유입경로"] = "해당 없음"
                    for route, color in {"유튜브 강세형":"#FF8A8A", "X 강세형":"#95AFFF", "하이브리드":"#FF9DF5", "해당 없음":"#FFD45D"}.items():
                        temp = plot_comet_df[plot_comet_df["코멧유입경로"].fillna("해당 없음") == route].copy()
                        if not temp.empty:
                            text_values = temp["스트리머"] if "스트리머" in temp.columns else None
                            fig.add_trace(go.Scatter(x=temp["최고_팔로워"], y=temp["통합_외부화력"], mode="markers", name=route, marker=dict(size=14, color=color, line=dict(color="white", width=1.4)), text=text_values, hovertemplate=f"<b>%{{text}}</b><br>유입경로: {route}<br>최고 팔로워: %{{x:,.0f}}<br>통합 외부화력: %{{y:,.0f}}<extra></extra>"))
                    if not plot_comet_df.empty and plot_comet_df["최고_팔로워"].mean() > 0:
                        fig.add_vline(x=plot_comet_df["최고_팔로워"].mean(), line_dash="dot", line_width=2, line_color="#c9d1d9", opacity=0.75)
                    fig.update_layout(title=dict(text="외부 팬덤 vs 방송 체급", x=0.06, xanchor="left"), xaxis_title="방송 체급", yaxis_title="통합 외부 화력", xaxis_type="log", yaxis_type="log", paper_bgcolor=STARTRAIL_TRANSPARENT, plot_bgcolor=STARTRAIL_TRANSPARENT, font_color="white", margin=dict(l=75, r=112, t=70, b=90), height=620, legend=dict(title="코멧 유입경로", bgcolor=STARTRAIL_TRANSPARENT, x=1.02, y=0.98, xanchor="left", yanchor="top"))
                    fig.update_xaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
                    fig.update_yaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
                    st.plotly_chart(fig, use_container_width=True)
            elif current_seg == "프로토스타":
                proto_order = ["S급 후보군", "A급 후보군", "기타 후보군"]
                proto_colors = {
                    "S급 후보군": "#FFD45D",
                    "A급 후보군": "#F08CFF",
                    "기타 후보군": "#75CCFF",
                }
                required = ["프로토스타_구분", "최고_팔로워", "평균_시청자_최댓값", "뷰어십", "6분_최고채팅", "프로토스타_score"]
                missing = [c for c in required if c not in raw.columns]
                if missing:
                    st.warning(f"프로토스타 그래프 컬럼이 부족합니다: {missing}")
                else:
                    proto_plot_df = raw[raw["프로토스타_구분"].isin(proto_order)].copy()
                    if platform_filter != "전체" and "플랫폼" in proto_plot_df.columns:
                        proto_plot_df = proto_plot_df[proto_plot_df["플랫폼"] == platform_filter].copy()
                    for col in ["최고_팔로워", "평균_시청자_최댓값", "뷰어십", "6분_최고채팅", "프로토스타_score"]:
                        proto_plot_df[col] = pd.to_numeric(proto_plot_df[col], errors="coerce").fillna(0)
                    proto_plot_df = proto_plot_df[(proto_plot_df["최고_팔로워"] > 0) & (proto_plot_df["평균_시청자_최댓값"] > 0)].copy()
                    if proto_plot_df.empty:
                        st.warning("프로토스타 그래프를 표시할 데이터가 없습니다.")
                    else:
                        fig = px.scatter(
                            proto_plot_df,
                            x="최고_팔로워",
                            y="평균_시청자_최댓값",
                            color="프로토스타_구분",
                            size="프로토스타_score",
                            hover_name="스트리머명" if "스트리머명" in proto_plot_df.columns else None,
                            category_orders={"프로토스타_구분": proto_order},
                            color_discrete_map=proto_colors,
                            template="plotly_dark",
                        )
                        fig.update_layout(
                            title=dict(text="프로토스타 팔로워 대비 평균 시청자", x=0.05, xanchor="left"),
                            xaxis_title="최고 팔로워",
                            yaxis_title="평균 시청자 최댓값",
                            paper_bgcolor=STARTRAIL_TRANSPARENT,
                            plot_bgcolor=STARTRAIL_TRANSPARENT,
                            font_color="white",
                            margin=dict(l=75, r=45, t=70, b=80),
                            height=620,
                            legend=dict(title="후보군", bgcolor=STARTRAIL_TRANSPARENT, x=1.02, y=0.98, xanchor="left", yanchor="top"),
                            uirevision=f"proto_{platform_filter}",
                        )
                        fig.update_xaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
                        fig.update_yaxes(gridcolor="rgba(255,255,255,0.12)", automargin=True)
                        st.plotly_chart(fig, use_container_width=True)

            elif current_seg == "위성":
                def _log_minmax_local(series):
                    s0 = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)
                    logged = np.log1p(s0)
                    min_v, max_v = logged.min(), logged.max()
                    if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
                        return pd.Series(0.0, index=series.index)
                    return (logged - min_v) / (max_v - min_v)

                def _score_0_1_local(series):
                    s0 = pd.to_numeric(series, errors="coerce").fillna(0)
                    min_v, max_v = s0.min(), s0.max()
                    if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
                        return pd.Series(0.0, index=series.index)
                    if min_v >= 0 and max_v <= 1:
                        return s0
                    if min_v >= 0 and max_v <= 100:
                        return s0 / 100
                    return (s0 - min_v) / (max_v - min_v)

                required = ["도네이션", "6분_최고채팅", "평균_시청자_최댓값", "팬덤지수", "최고_팔로워", "소속"]
                missing = [c for c in required if c not in raw.columns]
                if missing:
                    st.warning(f"위성 그래프 컬럼이 부족합니다: {missing}")
                else:
                    sat_df = raw[required].copy()
                    for col in ["도네이션", "6분_최고채팅", "평균_시청자_최댓값", "팬덤지수", "최고_팔로워"]:
                        sat_df[col] = pd.to_numeric(sat_df[col], errors="coerce").fillna(0)
                    affiliation = sat_df["소속"].fillna("").astype(str).str.strip()
                    sat_df["솔로성분류"] = np.where(affiliation.isin(["", "nan", "None", "none", "없음", "-"]), "솔로추정", "소속/그룹추정")
                    sat_df["도네이션_log_minmax"] = _log_minmax_local(sat_df["도네이션"])
                    sat_df["6분_최고채팅_log_minmax"] = _log_minmax_local(sat_df["6분_최고채팅"])
                    sat_df["평균_시청자_최댓값_log_minmax"] = _log_minmax_local(sat_df["평균_시청자_최댓값"])
                    sat_df["팬덤지수_minmax"] = _score_0_1_local(sat_df["팬덤지수"])
                    sat_df["위성점수_log_minmax"] = (
                        sat_df["도네이션_log_minmax"] * 0.30
                        + sat_df["6분_최고채팅_log_minmax"] * 0.30
                        + sat_df["평균_시청자_최댓값_log_minmax"] * 0.30
                        + sat_df["팬덤지수_minmax"] * 0.10
                    )
                    restrict_donation_cutoff = sat_df["도네이션"].quantile(0.95)
                    restrict_peak_chat_cutoff = sat_df["6분_최고채팅"].quantile(0.95)
                    satellite_donation_cutoff = sat_df["도네이션"].quantile(0.85)
                    satellite_peak_chat_cutoff = sat_df["6분_최고채팅"].quantile(0.85)
                    satellite_score_cutoff = sat_df["위성점수_log_minmax"].quantile(0.85)
                    sat_df["영입제한여부"] = (
                        (sat_df["솔로성분류"].isin(["솔로확정"]))
                        & (sat_df["도네이션"] >= restrict_donation_cutoff)
                        & (sat_df["6분_최고채팅"] >= restrict_peak_chat_cutoff)
                        & (sat_df["평균_시청자_최댓값"] >= 10000)
                        & (sat_df["위성점수_log_minmax"] >= 0.865)
                    ) | (
                        (sat_df["최고_팔로워"] >= 40000)
                        & (sat_df["솔로성분류"].isin(["솔로확정", "솔로추정"]))
                    )
                    sat_df["위성여부"] = (
                        ~sat_df["영입제한여부"]
                        & sat_df["솔로성분류"].isin(["솔로확정", "솔로추정"])
                        & (sat_df["도네이션"] >= satellite_donation_cutoff)
                        & (sat_df["6분_최고채팅"] >= satellite_peak_chat_cutoff)
                        & (sat_df["평균_시청자_최댓값"] >= 1000)
                        & (sat_df["위성점수_log_minmax"] >= satellite_score_cutoff)
                    )
                    sat_df["비교그룹_logmm"] = np.select(
                        [sat_df["영입제한여부"], sat_df["위성여부"]],
                        ["영입제한", "위성(Satellite)"],
                        default="기타",
                    )
                    metric_map = {
                        "도네이션": "도네이션_log_minmax",
                        "6분 최고채팅": "6분_최고채팅_log_minmax",
                        "평균 시청자": "평균_시청자_최댓값_log_minmax",
                        "팬덤지수": "팬덤지수_minmax",
                        "위성점수": "위성점수_log_minmax",
                    }
                    metric_summary = (
                        sat_df.groupby("비교그룹_logmm")[list(metric_map.values())]
                        .mean()
                        .reindex(["영입제한", "위성(Satellite)", "기타"])
                        .reset_index()
                        .rename(columns={v: k for k, v in metric_map.items()})
                    )
                    for col in metric_map.keys():
                        metric_summary[col] = pd.to_numeric(metric_summary[col], errors="coerce") * 100
                    metric_melt = metric_summary.melt(id_vars="비교그룹_logmm", var_name="지표", value_name="평균점수")
                    fig = px.bar(
                        metric_melt,
                        x="비교그룹_logmm",
                        y="평균점수",
                        color="지표",
                        barmode="group",
                        text="평균점수",
                        category_orders={"비교그룹_logmm": ["영입제한", "위성(Satellite)", "기타"], "지표": ["도네이션", "6분 최고채팅", "평균 시청자", "팬덤지수", "위성점수"]},
                        color_discrete_map={"도네이션": "#FF6B8A", "6분 최고채팅": "#75CCFF", "평균 시청자": "#FFD45D", "팬덤지수": "#98FFAB", "위성점수": "#FF9DF5"},
                        template="plotly_dark",
                    )
                    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
                    fig.update_layout(
                        title=dict(text="위성 구분별 핵심 지표 평균 비교", x=0.05, xanchor="left"),
                        xaxis_title="위성 구분",
                        yaxis_title="평균 점수(100점 기준)",
                        yaxis=dict(range=[0, 110], gridcolor="rgba(255,255,255,0.12)"),
                        paper_bgcolor=STARTRAIL_TRANSPARENT,
                        plot_bgcolor=STARTRAIL_TRANSPARENT,
                        font_color="white",
                        margin=dict(l=70, r=50, t=75, b=75),
                        height=620,
                        legend=dict(title="지표", bgcolor="rgba(21,16,47,0.86)", bordercolor="rgba(255,255,255,0.18)", borderwidth=1, x=0.98, y=0.98, xanchor="right", yanchor="top"),
                        uirevision=f"satellite_{platform_filter}",
                    )
                    fig.update_xaxes(automargin=True)
                    fig.update_yaxes(automargin=True)
                    st.plotly_chart(fig, use_container_width=True)

            else:
                required_cols = ["평균시청자", "스코어", "뷰어십", "플랫폼", "스트리머"]
                missing = [c for c in required_cols if c not in filtered_df.columns]
                if missing:
                    st.warning(f"산점도 컬럼이 부족합니다: {missing}")
                else:
                    fig = px.scatter(filtered_df, x="평균시청자", y="스코어", size="뷰어십", color="플랫폼", hover_name="스트리머", color_discrete_map={"SOOP":"#75CCFF", "CHZZK":"#bf40bf"}, template="plotly_dark")
                    fig.update_layout(paper_bgcolor=STARTRAIL_TRANSPARENT, plot_bgcolor=STARTRAIL_TRANSPARENT, margin=dict(l=70, r=110, t=55, b=70), height=620, font_color="white", legend=dict(bgcolor=STARTRAIL_TRANSPARENT, x=1.02, y=0.98, xanchor="left", yanchor="top"))
                    fig.update_xaxes(automargin=True, gridcolor="rgba(255,255,255,0.12)")
                    fig.update_yaxes(automargin=True, gridcolor="rgba(255,255,255,0.12)")
                    st.plotly_chart(fig, use_container_width=True)



# =========================================================
# FINAL PATCH 2026-05-12
# - STAR TRAIL 상단 타이틀을 STAR SEED 형식으로 정렬
# - STAR SEED 기간 pill 문구 고정
# - STAR TRAIL 세그먼트 카드 하단 설명/상단 라인 제거
# - STAR SEED 우선순위 테이블 5행 기준 가독성 보정
# =========================================================
st.markdown(
    """
    <style>.startrail-page .startrail-hero-modern{display:grid !important;grid-template-columns:minmax(0,1fr) 560px !important;column-gap:44px !important;align-items:center !important;margin-bottom:34px !important}.startrail-page .trail-title-block{display:grid !important;grid-template-columns:86px minmax(0,1fr) !important;gap:20px !important;min-height:96px !important;align-items:center !important}.startrail-page .trail-title-icon{width:72px !important;height:72px !important;border-radius:12px !important;display:flex !important;align-items:center !important;justify-content:center !important;background:radial-gradient(circle at 45% 30%,rgba(255,212,93,.16),transparent 56%),rgba(20,18,36,.88) !important;border:2px solid rgba(255,248,225,.78) !important;box-shadow:0 0 12px rgba(255,212,93,.14),inset 0 1px 0 rgba(255,255,255,.08) !important;overflow:hidden !important}.startrail-page .trail-title-icon .trail-spark-icon{transform:scale(1.02) !important;transform-origin:center center !important}.startrail-page .trail-brand-title{display:flex !important;align-items:baseline !important;gap:10px !important;color:#FFF8FF !important;font-size:39px !important;line-height:1.03 !important;font-weight:950 !important;letter-spacing:-0.055em !important;margin:0 0 7px 0 !important;text-shadow:0 1px 0 rgba(255,255,255,.10),0 0 14px rgba(255,212,93,.12) !important;white-space:nowrap !important}.startrail-page .trail-brand-title span{color:#FFD45D !important;font-size:31px !important;font-weight:950 !important;letter-spacing:-0.035em !important;text-shadow:0 0 4px rgba(255,212,93,.12) !important}.startrail-page .trail-title-accent-line{width:235px !important;height:2px !important;margin:0 0 9px 2px !important;border-radius:999px !important;background:linear-gradient(90deg,rgba(255,212,93,.84) 0%,rgba(255,212,93,.46) 42%,rgba(255,212,93,.12) 78%,rgba(255,212,93,0) 100%) !important}.startrail-page .trail-title-block .trail-subtitle{margin:0 !important;font-size:14.2px !important;font-weight:720 !important;line-height:1.45 !important;letter-spacing:-0.035em !important;color:#D8D0E7 !important;white-space:nowrap !important}.startrail-page .trail-info-card{margin-top:52px !important}.startrail-page .trail-date-pill{top:4px !important;right:0 !important}html body .stApp .startrail-page .trail-seg-card::before,html body .stApp .startrail-page .trail-seg-card.active::before,html body .stApp .startrail-page .trail-seg-card.active-성단::before,html body .stApp .startrail-page .trail-seg-card.active-프로토스타::before,html body .stApp .startrail-page .trail-seg-card.active-위성::before,html body .stApp .startrail-page .trail-seg-card.active-슈퍼노바::before,html body .stApp .startrail-page .trail-seg-card.active-코멧::before{display:none !important;content:none !important;opacity:0 !important;height:0 !important}html body .stApp .startrail-page .trail-seg-desc{display:none !important}html body .stApp .startrail-page .trail-seg-card{min-height:218px !important;height:218px !important;padding:28px 18px 20px !important}html body .stApp .startrail-page .trail-seg-icon-badge{margin:14px auto 20px auto !important;width:68px !important;height:68px !important;min-width:68px !important;min-height:68px !important;border-radius:18px !important}html body .stApp .startrail-page .trail-seg-count{margin-bottom:0 !important}.priority-table-panel{min-height:250px !important;padding:14px 16px !important;display:flex !important;align-items:stretch !important}.priority-table{width:100% !important;height:100% !important;min-height:222px !important;table-layout:fixed !important;font-size:13px !important}.priority-table th{font-size:13px !important;padding:10px 8px !important;height:44px !important;line-height:1.15 !important}.priority-table td{font-size:13.5px !important;padding:10px 8px !important;height:35px !important;line-height:1.15 !important;font-weight:850 !important}.priority-table td.rank,.priority-table th:nth-child(1){width:5% !important;padding-left:4px !important;padding-right:4px !important}.priority-table td.name,.priority-table th:nth-child(2){width:25% !important}.priority-table td.content,.priority-table th:nth-child(3){width:42% !important}.priority-table td.stage,.priority-table th:nth-child(4){width:20% !important}.priority-table .priority-score,.priority-table th:nth-child(5){width:8% !important;padding-left:4px !important;padding-right:4px !important}.priority-table .tag-pill{font-size:12.5px !important;max-width:190px !important;min-width:84px !important;padding:5px 12px !important;font-weight:850 !important}.priority-table .action-pill{font-size:12.5px !important;padding:5px 12px !important;font-weight:850 !important}@media (max-width:1200px){.startrail-page .startrail-hero-modern{grid-template-columns:1fr !important;row-gap:18px !important}.startrail-page .trail-title-block .trail-subtitle{white-space:normal !important}.startrail-page .trail-info-card{margin-top:18px !important}}</style>
    """,
    unsafe_allow_html=True,
)




# =========================================================
# PRE-ROUTING FINAL PATCH 2026-05-12
# - 홈 화면 기준 상단 여백으로 스타시드/스타트레일 정렬
# - 스타시드 날짜 pill ↔ 설명 카드 간격을 스타트레일과 통일
# - 스타트레일 TOP 카드/테이블/그래프/상세 패널 불투명 처리
#   ※ 페이지 라우팅 전에 주입해서 화면이 먼저 뜬 뒤 덮어씌워지는 현상을 줄인다.
# =========================================================
st.markdown(
    """
    <style>html body .stApp .block-container:has(.starseed-board),html body .stApp .block-container:has(.startrail-page){padding-top:0 !important;margin-top:-4.6rem !important}html body .stApp .starseed-board,html body .stApp .startrail-page{margin-top:0 !important;padding-top:0 !important}html body .stApp .startrail-page .startrail-hero,html body .stApp .startrail-hero{margin-top:0 !important;padding-top:0 !important}html body .stApp .starseed-board .starseed-date-pill{top:0 !important;right:0 !important;height:42px !important;min-height:42px !important;padding:0 18px !important;gap:9px !important;font-size:14px !important;line-height:42px !important}html body .stApp .starseed-board .starseed-criteria-card,html body .stApp .starseed-board .board-info-card{margin-top:44px !important}html body .stApp .startrail-page .trail-date-pill{top:0 !important;right:0 !important}html body .stApp .startrail-page .trail-info-card{margin-top:44px !important}html body .stApp .startrail-page .trail-section-title,html body .stApp .startrail-page .trail-section-title *,html body .stApp .startrail-page .trail-bottom-title,html body .stApp .startrail-page .trail-bottom-title *,html body .stApp .startrail-page .trail-side-title,html body .stApp .startrail-page .trail-side-title *,html body .stApp .startrail-page .trail-chart-title,html body .stApp .startrail-page .trail-chart-title *,html body .stApp .startrail-page .trail-table-title,html body .stApp .startrail-page .trail-table-title *,html body .stApp .trail-section-title,html body .stApp .trail-bottom-title,html body .stApp .trail-side-title,html body .stApp .trail-chart-title,html body .stApp .trail-table-title,html body .stApp .trail-kpi-card,html body .stApp .trail-kpi-card *,html body .stApp .trail-kpi-label,html body .stApp .trail-kpi-value{color:#FFF9FF !important;text-shadow:0 0 14px rgba(255,255,255,0.15) !important}html body .stApp .trail-kpi-card,html body .stApp .trail-info-card,html body .stApp .trail-seg-card,html body .stApp .trail-rank-card,html body .stApp .trail-side-card,html body .stApp .trail-chart-card,html body .stApp .trail-table,html body .stApp .trail-table-team-style,html body .stApp .trail-radar-card,html body .stApp .trail-detail-panel,html body .stApp .trail-detail-card,html body .stApp .trail-detail-button-title,html body .stApp .trail-main-grid div[data-testid="stPlotlyChart"],html body .stApp .startrail-page div[data-testid="stPlotlyChart"]{background:radial-gradient(circle at 50% 8%,rgba(196,143,255,.055),transparent 35%),linear-gradient(180deg,rgba(13,10,31,.995),rgba(7,6,22,.998)) !important;background-color:rgba(7,6,22,.998) !important;backdrop-filter:none !important;-webkit-backdrop-filter:none !important;border-color:rgba(255,255,255,.34) !important;box-shadow:0 0 22px rgba(0,0,0,.36),inset 0 1px 0 rgba(255,255,255,.055) !important}html body .stApp .trail-rank-card,html body .stApp .trail-side-card,html body .stApp .trail-chart-card,html body .stApp .trail-radar-card{border:1px solid rgba(255,255,255,.38) !important}html body .stApp .trail-table,html body .stApp .trail-table-team-style{border-collapse:collapse !important;background:rgba(7,6,22,.998) !important;background-color:rgba(7,6,22,.998) !important;overflow:hidden !important}html body .stApp .trail-table th,html body .stApp .trail-table-team-style th{background:rgba(31,30,51,.995) !important;color:#FFF9FF !important;border-color:rgba(255,255,255,.12) !important}html body .stApp .trail-table td,html body .stApp .trail-table-team-style td{background:rgba(8,8,26,.992) !important;color:#FFF9FF !important;border-color:rgba(255,255,255,.08) !important}html body .stApp .trail-main-grid div[data-testid="stPlotlyChart"]>div,html body .stApp .trail-main-grid div[data-testid="stPlotlyChart"] .js-plotly-plot,html body .stApp .trail-main-grid div[data-testid="stPlotlyChart"] .plot-container,html body .stApp .trail-main-grid div[data-testid="stPlotlyChart"] .svg-container,html body .stApp .startrail-page div[data-testid="stPlotlyChart"]>div,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .js-plotly-plot,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .plot-container,html body .stApp .startrail-page div[data-testid="stPlotlyChart"] .svg-container{background:rgba(7,6,22,.998) !important;background-color:rgba(7,6,22,.998) !important;border-radius:20px !important}html body .stApp .trail-seg-card::before,html body .stApp .trail-seg-card.active::before,html body .stApp .trail-seg-card.active-성단::before,html body .stApp .trail-seg-card.active-프로토스타::before,html body .stApp .trail-seg-card.active-위성::before,html body .stApp .trail-seg-card.active-슈퍼노바::before,html body .stApp .trail-seg-card.active-코멧::before{display:none !important;content:none !important;opacity:0 !important;height:0 !important;background:transparent !important;box-shadow:none !important}@media (max-width:1200px){html body .stApp .block-container:has(.starseed-board),html body .stApp .block-container:has(.startrail-page){padding-top:0 !important;margin-top:-2.2rem !important}}</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FINAL PATCH - STAR SEED date pill size sync
# - 스타시드 우측 상단 기간 pill 크기를 스타트레일 기간 pill과 동일하게 맞춤
# =========================================================
st.markdown(
    """
    <style>html body .stApp .starseed-board .starseed-date-pill,html body .stApp .starseed-date-pill{height:42px !important;min-height:42px !important;padding:0 18px !important;gap:9px !important;font-size:14px !important;font-weight:900 !important;line-height:42px !important;border-radius:999px !important;display:inline-flex !important;align-items:center !important;white-space:nowrap !important;box-sizing:border-box !important}html body .stApp .starseed-board .starseed-date-pill{top:0 !important;right:0 !important}@media (max-width:1200px){html body .stApp .starseed-board .starseed-date-pill,html body .stApp .starseed-date-pill{height:42px !important;min-height:42px !important;padding:0 18px !important;font-size:14px !important;line-height:42px !important}}</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 전역 Sidebar Toggle 통합 패치
# - 반드시 페이지 라우팅/st.stop() 이전에 실행되어야 함
# - 홈/스타트레일/스타시드 모두 동일한 open/close 토글 디자인 적용
# - Streamlit 기본 button 기능은 유지하고, 표시만 동일한 원형 햄버거 버튼으로 통일
# =========================================================
st.markdown(
    """
    <style>:root{--cime-sidebar-width:300px;--cime-toggle-size:42px;--cime-toggle-top:100px;--cime-toggle-open-left:18px;--cime-toggle-close-right-gap:18px;--cime-toggle-bg:rgba(24,14,46,0.96);--cime-toggle-border:rgba(184,132,255,0.78);--cime-toggle-glow:rgba(166,92,255,0.46);--cime-toggle-icon:#F8F1FF}html body .stApp header,html body .stApp [data-testid="stHeader"]{overflow:visible !important;z-index:999900 !important;background:transparent !important;pointer-events:none !important}html body .stApp header [data-testid="stToolbar"],html body .stApp [data-testid="stToolbar"],html body .stApp .stAppToolbar,html body .stApp div[class*="stAppToolbar"],html body .stApp [data-testid="stHeaderActionElements"]{display:none !important;visibility:hidden !important;opacity:0 !important;pointer-events:none !important;width:0 !important;height:0 !important;min-width:0 !important;min-height:0 !important;max-width:0 !important;max-height:0 !important;overflow:hidden !important}html body .stApp [data-testid="collapsedControl"],html body .stApp [data-testid="stSidebarCollapsedControl"],html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]{position:fixed !important;top:var(--cime-toggle-top) !important;width:var(--cime-toggle-size) !important;height:var(--cime-toggle-size) !important;min-width:var(--cime-toggle-size) !important;min-height:var(--cime-toggle-size) !important;max-width:var(--cime-toggle-size) !important;max-height:var(--cime-toggle-size) !important;display:flex !important;align-items:center !important;justify-content:center !important;visibility:visible !important;opacity:1 !important;pointer-events:auto !important;overflow:visible !important;margin:0 !important;padding:0 !important;transform:none !important;border:none !important;outline:none !important;background:transparent !important;box-shadow:none !important;box-sizing:border-box !important}html body .stApp [data-testid="collapsedControl"],html body .stApp [data-testid="stSidebarCollapsedControl"]{left:var(--cime-toggle-open-left) !important;z-index:1000002 !important}html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]{left:calc(var(--cime-sidebar-width) - var(--cime-toggle-size) - var(--cime-toggle-close-right-gap)) !important;z-index:1000003 !important}html body .stApp [data-testid="collapsedControl"]>button,html body .stApp [data-testid="stSidebarCollapsedControl"]>button,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]>button,html body .stApp button[aria-label="Open sidebar"],html body .stApp button[aria-label="Close sidebar"],html body .stApp button[aria-label="사이드바 열기"],html body .stApp button[aria-label="사이드바 닫기"]{position:absolute !important;inset:0 !important;width:100% !important;height:100% !important;min-width:100% !important;min-height:100% !important;max-width:100% !important;max-height:100% !important;display:flex !important;align-items:center !important;justify-content:center !important;visibility:visible !important;opacity:1 !important;pointer-events:auto !important;margin:0 !important;padding:0 !important;border-radius:999px !important;border:1px solid var(--cime-toggle-border) !important;outline:none !important;background:radial-gradient(circle at 34% 28%,rgba(205,176,255,0.30),transparent 42%),radial-gradient(circle at 70% 75%,rgba(123,69,255,0.22),transparent 50%),var(--cime-toggle-bg) !important;box-shadow:0 0 20px var(--cime-toggle-glow),inset 0 1px 0 rgba(255,255,255,0.16) !important;color:transparent !important;font-size:0 !important;line-height:0 !important;text-indent:-9999px !important;overflow:hidden !important;z-index:3 !important;box-sizing:border-box !important}html body .stApp [data-testid="collapsedControl"]>button:hover,html body .stApp [data-testid="stSidebarCollapsedControl"]>button:hover,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]>button:hover,html body .stApp button[aria-label="Open sidebar"]:hover,html body .stApp button[aria-label="Close sidebar"]:hover,html body .stApp button[aria-label="사이드바 열기"]:hover,html body .stApp button[aria-label="사이드바 닫기"]:hover{border-color:rgba(218,195,255,0.94) !important;box-shadow:0 0 28px rgba(166,92,255,0.58),inset 0 1px 0 rgba(255,255,255,0.22) !important}html body .stApp [data-testid="collapsedControl"] span,html body .stApp [data-testid="collapsedControl"] svg,html body .stApp [data-testid="stSidebarCollapsedControl"] span,html body .stApp [data-testid="stSidebarCollapsedControl"] svg,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,html body .stApp button[aria-label="Open sidebar"] span,html body .stApp button[aria-label="Open sidebar"] svg,html body .stApp button[aria-label="Close sidebar"] span,html body .stApp button[aria-label="Close sidebar"] svg,html body .stApp button[aria-label="사이드바 열기"] span,html body .stApp button[aria-label="사이드바 열기"] svg,html body .stApp button[aria-label="사이드바 닫기"] span,html body .stApp button[aria-label="사이드바 닫기"] svg{display:none !important;visibility:hidden !important;opacity:0 !important;width:0 !important;height:0 !important;min-width:0 !important;min-height:0 !important;max-width:0 !important;max-height:0 !important;overflow:hidden !important;pointer-events:none !important;color:transparent !important;font-size:0 !important;line-height:0 !important}html body .stApp [data-testid="collapsedControl"]>button::before,html body .stApp [data-testid="stSidebarCollapsedControl"]>button::before,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]>button::before,html body .stApp button[aria-label="Open sidebar"]::before,html body .stApp button[aria-label="Close sidebar"]::before,html body .stApp button[aria-label="사이드바 열기"]::before,html body .stApp button[aria-label="사이드바 닫기"]::before{content:"" !important;position:absolute !important;left:50% !important;top:50% !important;width:18px !important;height:13px !important;transform:translate(-50%,-50%) !important;background:linear-gradient(var(--cime-toggle-icon),var(--cime-toggle-icon)) 0 0 / 18px 3px no-repeat,linear-gradient(var(--cime-toggle-icon),var(--cime-toggle-icon)) 0 5px / 18px 3px no-repeat,linear-gradient(var(--cime-toggle-icon),var(--cime-toggle-icon)) 0 10px / 18px 3px no-repeat !important;border-radius:2px !important;filter:drop-shadow(0 0 6px rgba(255,255,255,0.86)) drop-shadow(0 0 12px rgba(184,132,255,0.64)) !important;pointer-events:none !important;z-index:4 !important}html body .stApp [data-testid="collapsedControl"]>button::after,html body .stApp [data-testid="stSidebarCollapsedControl"]>button::after,html body .stApp section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]>button::after,html body .stApp button[aria-label="Open sidebar"]::after,html body .stApp button[aria-label="Close sidebar"]::after,html body .stApp button[aria-label="사이드바 열기"]::after,html body .stApp button[aria-label="사이드바 닫기"]::after{content:none !important;display:none !important}</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# 페이지 라우팅
# =========================================================

if st.session_state.page == "대시보드 홈":
    render_home()
    st.stop()

elif st.session_state.page == "스타트레일":
    if st.session_state.get("startrail_show_loading", False):
        st.markdown(
            """
            <div class="startrail-loading-wrap">
                <div class="startrail-loading-orb"></div>
                <div class="startrail-loading-title">STAR TRAIL 데이터를 준비하는 중입니다</div>
                <div class="startrail-loading-sub">요약/KPI, 개인 후보, 성단 후보 데이터를 불러와<br>영입 우선순위 대시보드 화면을 구성하고 있습니다.</div>
                <div class="startrail-loading-steps">
                    <span class="startrail-loading-chip">후보 데이터 로드</span><span class="startrail-loading-chip">세그먼트 계산</span><span class="startrail-loading-chip">TOP 후보 렌더링</span><span class="startrail-loading-chip">그래프 구성</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.25)
        st.session_state.startrail_show_loading = False
        st.rerun()
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
    roots = [PROJECT_ROOT, Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent]
    candidates = []
    for root in roots:
        candidates.extend([root / rel, root / rel.name])
    for p in candidates:
        if p.exists():
            return p.resolve()
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
    segment = pd.DataFrame()
    summary = pd.DataFrame()
    tracking = pd.DataFrame()
    reference = pd.DataFrame()
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


def normalize_text_value(value) -> str:
    """화면/필터 판정용 문자열 정규화.

    - NaN/None 계열을 빈 문자열로 통일
    - zero-width, nbsp 등 눈에 잘 안 보이는 공백 제거
    - 내부 공백도 제거해서 '미 분류', '미분류 ' 같은 값을 잡는다.
    """
    if pd.isna(value):
        return ""
    text = str(value)
    for ch in ["\u200b", "\u200c", "\u200d", "\ufeff", "\xa0"]:
        text = text.replace(ch, "")
    return "".join(text.strip().split())


def is_unclassified_value(series: pd.Series) -> pd.Series:
    normalized = series.map(normalize_text_value)
    lowered = normalized.str.lower()
    return (
        normalized.eq("")
        | normalized.str.contains("미분류", na=False)
        | lowered.isin(["none", "nan", "null", "<na>", "na", "n/a", "unknown", "undefined", "-", "미정"])
    )


CONTENT_SEGMENT_COL_CANDIDATES = [
    "주요콘텐츠군",
    "주요 콘텐츠군",
    "주요콘텐츠군_표시",
    "주요 콘텐츠군_표시",
    "대표상위세그먼트",
    "상위 콘텐츠군",
    "콘텐츠군",
    "대표세그먼트",
    "segment",
    "segment_unified",
    "대표상위세그먼트명",
]


ACTION_COL_CANDIDATES = [
    "액션버킷",
    "검토 단계",
    "검토단계",
    "현재 검토 단계",
    "현재검토단계",
    "action_bucket",
]


def find_content_segment_columns(data: pd.DataFrame, seg_col: str | None = None) -> list[str]:
    """미분류 판정에 사용할 콘텐츠군/세그먼트 계열 컬럼을 최대한 넓게 찾는다."""
    check_cols: list[str] = []
    if seg_col and seg_col in data.columns:
        check_cols.append(seg_col)

    for col in CONTENT_SEGMENT_COL_CANDIDATES:
        if col in data.columns and col not in check_cols:
            check_cols.append(col)

    # 실제 파일마다 컬럼명이 조금씩 달라질 수 있어 키워드 기반으로도 보강한다.
    for col in data.columns:
        col_text = str(col).replace(" ", "")
        lower_col = col_text.lower()
        looks_like_content_col = (
            ("콘텐츠" in col_text and ("군" in col_text or "유형" in col_text or "분류" in col_text))
            or ("세그먼트" in col_text)
            or ("segment" in lower_col)
            or ("content" in lower_col)
        )
        # 추천사유/설명류 긴 텍스트 컬럼은 제외한다.
        excluded = any(k in col_text for k in ["추천사유", "주의사유", "설명", "요약", "근거", "비율"])
        if looks_like_content_col and not excluded and col not in check_cols:
            check_cols.append(col)
    return check_cols


def apply_unclassified_hold_rule(data: pd.DataFrame, seg_col: str | None, action_col_name: str | None, output_col: str = "검토단계_표시") -> pd.DataFrame:
    """주요 콘텐츠군이 미분류/공백이면 검토단계를 보류로 강제한다.

    기존 문제 원인:
    - 화면에는 `주요 콘텐츠군`이 미분류로 보이지만, 일부 파일에서는 컬럼명이 조금 다르거나
      zero-width/nbsp 공백이 섞여 기존 `== "미분류"` 판정에서 누락될 수 있었다.
    - 이후 TOP5/우선순위 표가 `즉시검토` 기준으로 먼저 필터링되면 미분류 후보가 계속 상단에 남았다.

    처리 방식:
    - 콘텐츠군/세그먼트 계열 컬럼을 넓게 탐색한다.
    - 값 정규화 후 미분류/공백/None/nan 계열이면 `검토단계_표시 = 보류`로 강제한다.
    - 화면에서 참조할 가능성이 있는 검토단계 계열 컬럼도 함께 보정해 후속 필터와 표시에 동일하게 반영한다.
    """
    out = data.copy()

    base_action = out[action_col_name] if action_col_name and action_col_name in out.columns else pd.Series(pd.NA, index=out.index)
    out[output_col] = base_action.replace(["None", "none", "nan", "NaN", "", None], pd.NA).fillna("미분류")

    check_cols = find_content_segment_columns(out, seg_col)
    if check_cols:
        hold_mask = pd.Series(False, index=out.index)
        for col in check_cols:
            hold_mask = hold_mask | is_unclassified_value(out[col])

        out.loc[hold_mask, output_col] = "보류"
        out.loc[hold_mask, "미분류_보류강제"] = True
        out.loc[~hold_mask, "미분류_보류강제"] = False

        # 이후 코드가 원본 action_col 또는 다른 검토단계 컬럼을 참조해도 같은 결과가 나오도록 보정한다.
        for col in ACTION_COL_CANDIDATES:
            if col in out.columns:
                out.loc[hold_mask, col] = "보류"

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
segment_col = first_existing(df, CONTENT_SEGMENT_COL_CANDIDATES)
lower_segment_col = first_existing(df, ["대표하위세그먼트", "세부 콘텐츠 유형", "하위 콘텐츠군", "sub_segment", "대표하위세그먼트명", "segment_seed", "segment_seed_raw"])
action_col = first_existing(df, ACTION_COL_CANDIDATES)
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
# 10. 스타시드 기본 필터 상태
# - 사이드바의 "스타시드 필터" UI는 제거
# - 기존 기본값과 동일하게 보류/제외 숨김만 내부 적용
# =========================================================

filtered = df.copy()

action_col = "검토단계_표시"

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

if hide_hold and action_col:
    filtered = filtered[~filtered[action_col].astype(str).str.contains("보류|제외", na=False)]

    # 최종 안전장치: 주요 콘텐츠군/세그먼트가 미분류인 후보는 화면 TOP 후보군에서 제외한다.
    # 이 조건이 있어야 `미분류 + 즉시검토`가 원본 데이터에 남아 있어도 추천 후보 TOP/우선순위 표에 섞이지 않는다.
    content_check_cols = find_content_segment_columns(filtered, segment_col)
    if content_check_cols:
        unclassified_any_mask = pd.Series(False, index=filtered.index)
        for _col in content_check_cols:
            unclassified_any_mask = unclassified_any_mask | is_unclassified_value(filtered[_col])
        filtered = filtered[~unclassified_any_mask]

filtered = filtered.copy()
filtered["표시순위"] = np.arange(1, len(filtered) + 1)

# =========================================================
# 11. 변화 추적 기준
# - 사이드바의 "변화 추적 기준" UI는 제거
# - 현재 데이터와 2026-05-01 이후 첫 snapshot을 자동 비교
# =========================================================

tracking_base_df = pd.DataFrame()
tracking_target_df = df.copy()
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
    snapshot_dates = [
        d for d in snapshot_dates_all
        if pd.to_datetime(d, errors="coerce") >= MIN_TRACKING_DATE
    ]

    if snapshot_dates:
        tracking_base_label = MIN_TRACKING_DATE_LABEL if MIN_TRACKING_DATE_LABEL in snapshot_dates else snapshot_dates[0]
        tracking_base_df = get_snapshot_by_date(snapshot_prepared_df, tracking_base_label)

# =========================================================
# 12. KPI 계산
# =========================================================

def apply_snapshot_filters_for_kpi(base_df: pd.DataFrame) -> pd.DataFrame:
    out = base_df.copy()
    local_segment_col = first_existing(out, CONTENT_SEGMENT_COL_CANDIDATES)
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
    upper_col = first_existing(src, CONTENT_SEGMENT_COL_CANDIDATES)
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


# =========================================================
# STAR SEED 상단 히어로 오버라이드
# - STAR TRAIL처럼 영문 글로우 타이틀 적용
# - 기존 부가 설명과 기준 카드 문구는 유지
# =========================================================
st.markdown(
    """
    <style>.block-container:has(.starseed-board){padding-top:0.8rem !important;margin-top:0 !important;max-width:1560px !important;padding-left:2.8rem !important;padding-right:2.8rem !important}.starseed-board{margin-top:0 !important;padding-top:0 !important}.starseed-board .starseed-hero-modern{display:grid !important;grid-template-columns:minmax(0,1fr) 560px !important;column-gap:44px !important;align-items:center !important;margin:0 0 18px 0 !important;padding:0 0 8px 0 !important}.starseed-board .starseed-title-block{display:grid !important;grid-template-columns:86px minmax(0,1fr) !important;gap:20px !important;min-height:96px !important;align-items:center !important}.starseed-board .board-title-icon{display:flex !important}.starseed-board .starseed-glow-title{display:block !important;margin:0 0 16px 0 !important;padding:0 !important;color:#FFF8FF !important;font-size:clamp(58px,5.6vw,92px) !important;line-height:0.96 !important;font-weight:950 !important;letter-spacing:0.22em !important;white-space:nowrap !important;text-transform:uppercase !important;text-shadow:0 0 8px rgba(255,255,255,0.70),0 0 24px rgba(180,255,197,0.42),0 0 46px rgba(131,246,160,0.28),0 0 70px rgba(125,66,255,0.30) !important}.starseed-board .starseed-glow-subtitle{margin:0 !important;color:#E8DFFF !important;font-size:18px !important;line-height:1.55 !important;font-weight:850 !important;letter-spacing:-0.035em !important;text-align:left !important;white-space:normal !important;word-break:keep-all !important;text-shadow:0 0 12px rgba(131,246,160,0.12) !important}.starseed-board .starseed-criteria-card{min-height:112px !important;border-radius:22px !important;padding:22px 28px !important;grid-template-columns:62px minmax(0,1fr) !important;border:1px solid rgba(131,246,160,0.30) !important;background:radial-gradient(circle at 10% 45%,rgba(131,246,160,0.13),transparent 32%),linear-gradient(135deg,rgba(11,35,28,0.76),rgba(18,16,45,0.86)) !important;box-shadow:0 0 22px rgba(131,246,160,0.08),inset 0 1px 0 rgba(255,255,255,0.06) !important}.starseed-board .starseed-criteria-card .board-info-icon{width:54px !important;height:54px !important;font-size:24px !important;box-shadow:0 0 18px rgba(88,233,132,0.22) !important}.starseed-board .starseed-criteria-card .board-info-title{font-size:15px !important;margin-bottom:6px !important}.starseed-board .starseed-criteria-card .board-info-text{font-size:12.5px !important;line-height:1.55 !important}@media (max-width:1200px){.starseed-board .starseed-hero-modern{grid-template-columns:1fr !important;row-gap:18px !important}.starseed-board .starseed-glow-title{font-size:clamp(44px,9vw,72px) !important;letter-spacing:0.14em !important}}</style>
    """,
    unsafe_allow_html=True,
)




st.markdown(
    """
    <style>.starseed-board .starseed-criteria-card{margin-top:44px !important}.starseed-board .starseed-brand-title{display:flex !important;align-items:baseline !important;gap:10px !important;color:#FFF8FF !important;font-size:39px !important;line-height:1.03 !important;font-weight:950 !important;letter-spacing:-0.055em !important;margin:0 0 7px 0 !important;text-shadow:0 1px 0 rgba(255,255,255,.10) !important;white-space:nowrap !important}.starseed-board .starseed-brand-title span{color:var(--seed-green) !important;font-size:31px !important;font-weight:950 !important;letter-spacing:-.035em !important}.starseed-board .starseed-brand-subtitle{margin:0 !important;font-size:14.2px !important;font-weight:720 !important;line-height:1.45 !important;color:#D8D0E7 !important;white-space:nowrap !important}</style>
    """,
    unsafe_allow_html=True,
)

def kpi_tooltip_label(label: str, desc: str) -> str:
    safe_label = safe_html(label)
    safe_desc = html_lib.escape(desc)
    return (
        f'<div class="board-kpi-label">'
        f'<span class="board-kpi-label-text">{safe_label}</span>'
        f'<span class="board-kpi-tooltip-wrap" aria-label="{safe_desc}">'
        f'<span class="board-kpi-tooltip-icon">?</span>'
        f'<span class="board-kpi-tooltip-text">{safe_desc}</span>'
        f'</span>'
        f'</div>'
    )

def detail_metric_help_label(label: str, desc: str) -> str:
    safe_label = safe_html(label)
    safe_desc = html_lib.escape(desc)
    return (
        f'<div class="detail-metric-label detail-metric-label-with-help">'
        f'<span>{safe_label}</span>'
        f'<span class="detail-help-wrap" aria-label="{safe_desc}">'
        f'<span class="detail-help-icon">?</span>'
        f'<span class="detail-help-text">{safe_desc}</span>'
        f'</span>'
        f'</div>'
    )

kpi_tooltips = {
    "전체 분석 후보": "수집/전처리 후 대시보드에 올라온 전체 후보 수입니다.",
    "1차 선별 후보": "shortlist 또는 주요 액션버킷 기준으로 사람이 실제 검토할 수 있는 후보군입니다.",
    "평균 영입 점수": "현재 필터 조건에 남은 후보들의 평균 영입 점수입니다.",
    "즉시 검토 후보": "우선 컨택 또는 수기 검증을 빠르게 진행할 만한 후보 수입니다.",
}


st.markdown(
    """
    <style>.starseed-board{position:relative !important}.starseed-date-pill{position:absolute !important;top:0 !important;right:0 !important;z-index:60 !important;display:inline-flex !important;align-items:center !important;gap:9px !important;height:42px !important;min-height:42px !important;padding:0 18px !important;border-radius:999px !important;background:rgba(8,26,43,0.82) !important;border:1px solid rgba(131,246,160,0.30) !important;color:#E8FFF0 !important;font-size:14px !important;font-weight:900 !important;line-height:42px !important;box-shadow:0 0 18px rgba(131,246,160,0.12),inset 0 1px 0 rgba(255,255,255,0.05) !important;white-space:nowrap !important}.starseed-board .starseed-hero-modern{padding-top:0 !important;grid-template-columns:minmax(0,1fr) 560px !important;column-gap:44px !important;align-items:center !important}.starseed-board .starseed-title-block{grid-template-columns:86px minmax(0,1fr) !important;gap:20px !important;min-height:96px !important}.starseed-board .board-title-icon{display:flex !important}.starseed-board .starseed-criteria-card{margin-top:44px !important}.starseed-board .starseed-brand-title{display:flex !important;align-items:baseline !important;gap:10px !important;color:#FFF8FF !important;font-size:39px !important;line-height:1.03 !important;font-weight:950 !important;letter-spacing:-0.055em !important;margin:0 0 7px 0 !important;text-shadow:0 1px 0 rgba(255,255,255,.10) !important;white-space:nowrap !important}.starseed-board .starseed-brand-title span{color:var(--seed-green) !important;font-size:31px !important;font-weight:950 !important;letter-spacing:-.035em !important}.starseed-board .starseed-brand-subtitle{margin:0 !important;font-size:14.2px !important;font-weight:720 !important;line-height:1.45 !important;color:#D8D0E7 !important;white-space:nowrap !important;letter-spacing:-.035em !important}.board-kpi-note{display:none !important}.board-kpi-card .board-kpi-icon{color:#fff !important;font-size:22px !important;background:radial-gradient(circle at 34% 24%,rgba(255,255,255,.28),rgba(48,190,102,.78) 50%,rgba(12,78,56,.92) 100%) !important;box-shadow:0 0 10px rgba(80,255,146,.16) !important}.detail-metric-label-with-help{display:flex !important;align-items:center !important;gap:6px !important;overflow:visible !important}.detail-help-wrap{position:relative !important;display:inline-flex !important;align-items:center !important;justify-content:center !important;overflow:visible !important;z-index:20 !important}.detail-help-icon{width:15px !important;height:15px !important;min-width:15px !important;border-radius:999px !important;border:1px solid rgba(131,246,160,.50) !important;background:rgba(8,24,28,.86) !important;color:#DFFFF0 !important;font-size:9px !important;font-weight:950 !important;line-height:13px !important;text-align:center !important;cursor:help !important}.detail-help-text{visibility:hidden !important;opacity:0 !important;pointer-events:none !important;position:absolute !important;left:50% !important;bottom:145% !important;transform:translateX(-50%) translateY(6px) !important;width:230px !important;max-width:70vw !important;padding:10px 12px !important;border-radius:12px !important;border:1px solid rgba(131,246,160,.30) !important;background:rgba(7,20,28,.98) !important;color:#DFFFF0 !important;font-size:11px !important;font-weight:700 !important;line-height:1.5 !important;text-align:left !important;white-space:normal !important;word-break:keep-all !important;box-shadow:0 10px 28px rgba(0,0,0,.45) !important;z-index:99999 !important}.detail-help-wrap:hover .detail-help-text{visibility:visible !important;opacity:1 !important;transform:translateX(-50%) translateY(0) !important}.priority-table th,.priority-table td{font-size:11px !important;padding-left:6px !important;padding-right:6px !important}.priority-table td.name{font-weight:760 !important;letter-spacing:-.02em !important}.priority-table .tag-pill{font-weight:780 !important;max-width:132px !important;min-width:62px !important}@media (max-width:1200px){.starseed-date-pill{position:static !important;margin:0 0 16px 0 !important}.starseed-board .starseed-hero-modern{grid-template-columns:1fr !important}.starseed-board .starseed-criteria-card{margin-top:18px !important}.starseed-board .starseed-brand-subtitle{white-space:normal !important}}</style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>html body .stApp .block-container:has(.starseed-board){padding-top:0 !important;margin-top:-4.6rem !important;max-width:1560px !important}html body .stApp .starseed-board{margin-top:0 !important;padding-top:0 !important}html body .stApp .starseed-board .starseed-hero-modern{align-items:center !important;margin-top:0 !important;margin-bottom:14px !important;padding-top:0 !important}html body .stApp .starseed-board .board-head-left,html body .stApp .starseed-board .starseed-title-block{grid-template-columns:96px minmax(0,1fr) !important;gap:23px !important;min-height:104px !important;align-items:center !important}html body .stApp .starseed-board .board-title-icon{width:82px !important;height:82px !important;border-radius:14px !important}html body .stApp .starseed-board .board-title-icon .seed-search-icon{transform:scale(1.14) !important;transform-origin:center center !important}html body .stApp .starseed-board .board-title,html body .stApp .starseed-board .board-title-ko,html body .stApp .starseed-board .starseed-brand-title{font-size:45px !important;line-height:1.02 !important;margin-bottom:8px !important}html body .stApp .starseed-board .board-title span,html body .stApp .starseed-board .starseed-brand-title span{font-size:36px !important}html body .stApp .starseed-board .board-title-accent-line{width:270px !important;height:2px !important;margin-bottom:10px !important}html body .stApp .starseed-board .board-subtitle,html body .stApp .starseed-board .starseed-brand-subtitle{font-size:15.8px !important;line-height:1.45 !important;font-weight:760 !important}html body .stApp .starseed-board .starseed-date-pill{top:0 !important;right:0 !important;height:42px !important;min-height:42px !important;padding:0 18px !important;gap:9px !important;font-size:14px !important;line-height:42px !important}</style>
    """,
    unsafe_allow_html=True,
)

html(f"""
<div class="starseed-board">
    <div class="starseed-date-pill">📅 2026.05.01 ~ 2026.05.09</div>
    <div class="board-hero board-hero-compact starseed-hero-modern">
        <div class="board-head-left starseed-title-block">
            <div class="board-title-icon">{SEED_ICON_HTML}</div>
            <div>
                <div class="board-title board-title-ko starseed-brand-title">스타시드 <span>Star Seed</span></div>
                <div class="board-title-accent-line"></div>
                <div class="board-subtitle starseed-brand-subtitle">유튜브 기반 성장 잠재력과 라이브 전환 가능성을 분석해, 차세대 후보군을 발굴합니다</div>
            </div>
        </div>
        <div class="board-info-card starseed-criteria-card">
            <div class="board-info-icon">✦</div>
            <div>
                <div class="board-info-title">후보를 선별하는 기준</div>
                <div class="board-info-text">팬 반응 밀도, 라이브 전환성, 실전 리스크, 액션버킷을 함께 확인해<br>CIME가 우선 검토할 예비 스트리머 후보군을 정리합니다.</div>
            </div>
        </div>
    </div>
    <div class="board-kpi-grid">
        <div class="board-kpi-card"><div class="board-kpi-icon">👥</div><div>{kpi_tooltip_label("전체 분석 후보", kpi_tooltips["전체 분석 후보"])}<div class="board-kpi-value">{fmt_num(target_all_kpi['total'], 0, '명')}</div>{delta_badge(delta_total, 0, '명')}</div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">▾</div><div>{kpi_tooltip_label("1차 선별 후보", kpi_tooltips["1차 선별 후보"])}<div class="board-kpi-value">{fmt_num(target_all_kpi['shortlist'], 0, '명')}</div>{delta_badge(delta_shortlist, 0, '명')}</div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">★</div><div>{kpi_tooltip_label("평균 영입 점수", kpi_tooltips["평균 영입 점수"])}<div class="board-kpi-value">{fmt_num(target_filtered_kpi['avg_score'], 1, '점')}</div>{delta_badge(delta_avg_score, 1, '점')}</div></div>
        <div class="board-kpi-card"><div class="board-kpi-icon">◎</div><div>{kpi_tooltip_label("즉시 검토 후보", kpi_tooltips["즉시 검토 후보"])}<div class="board-kpi-value">{fmt_num(target_filtered_kpi['high_priority'], 0, '명')}</div>{delta_badge(delta_high_priority, 0, '명')}</div></div>
    </div>
</div>
""")

with st.expander("영입 점수 설명", expanded=False):
    st.markdown(
        '<div class="explain-box"><b>기본 산식</b><br><code>영입점수 = 0.22×채널력 + 0.28×성장성 + 0.22×팬밀도 + 0.15×라이브친화 + 0.13×실전성 - 리스크 감점</code><br><br>성장성에 가장 높은 가중치를 둔 이유는 신생 플랫폼 입장에서 이미 너무 큰 채널보다, 최근 반응과 성장 흐름이 확인되는 후보가 영입 현실성이 높다고 보았기 때문입니다. 채널력과 팬밀도는 최소 체급과 팬덤 결집력을 균형 있게 반영하고, 라이브친화와 실전성은 실제 방송 전환 가능성과 운영 리스크를 보정합니다.</div>',
        unsafe_allow_html=True,
    )

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
priority_df = filtered.head(5).copy()
priority_rows = []
for i, (_, row) in enumerate(priority_df.iterrows()):
    name = row.get(channel_name_col, "-") if channel_name_col else "-"
    segment = row.get(segment_col, "-") if segment_col else "-"
    action = row.get(action_col, "-") if action_col else "-"
    score = row.get("_score_display", np.nan)
    priority_rows.append(
        f'<tr><td class="rank" style="width:5%;">{i + 1}</td><td class="name" style="width:25%;">{channel_link(short_text(name, 18), row)}</td><td class="content" style="width:42%;">{tag(segment)}</td><td class="stage" style="width:20%;">{action_tag(action)}</td><td class="priority-score" style="width:8%;">{fmt_num(score, 1, "")}</td></tr>'
    )

recent_priority_rows = []
if not mini_tracking_df.empty:
    for _, r in mini_tracking_df.head(5).iterrows():
        recent_priority_rows.append(
            f'<tr><td class="name recent-candidate">{safe_html(str(r.get("채널명", "-")))}</td><td class="recent-numeric">{fmt_num(r.get("이전순위", np.nan), 0, "")}</td><td class="recent-numeric">{fmt_num(r.get("현재순위", np.nan), 0, "")}</td><td class="recent-numeric recent-rise">▲ {fmt_num(abs(float(r.get("순위변동", 0) or 0)), 0, "")}</td><td class="priority-score recent-numeric">{fmt_num(r.get("현재점수", np.nan), 1, "")}</td><td class="recent-stage">{action_tag(r.get("현재단계", "-"))}</td></tr>'
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
    st.markdown('<div class="priority-left-top-spacer"></div>', unsafe_allow_html=True)

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
            html(f'<div class="board-panel priority-table-panel recent-table-panel"><table class="priority-table recent-priority-table"><colgroup><col class="recent-col-candidate"><col class="recent-col-prev"><col class="recent-col-current"><col class="recent-col-rise"><col class="recent-col-score"><col class="recent-col-stage"></colgroup><thead><tr><th>후보</th><th>이전</th><th>현재</th><th>상승</th><th>점수</th><th>단계</th></tr></thead><tbody>{"".join(recent_priority_rows)}</tbody></table></div>')
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
                        <div class="detail-metric-box"><div class="detail-metric-label">영입 점수</div><div class="detail-metric-value">{fmt_num(sel_score, 1, '점')}</div></div>
                        <div class="detail-metric-box">{detail_metric_help_label('성장성', '최근 반응과 성장 흐름을 점수화한 값입니다. 높을수록 차세대 후보로 육성할 가능성이 큽니다.')}<div class="detail-metric-value">{fmt_num(sel_growth, 3, '')}</div></div>
                        <div class="detail-metric-box"><div class="detail-metric-label">구독자수</div><div class="detail-metric-value">{fmt_num(sel_subs, 0, '')}</div></div>
                        <div class="detail-metric-box">{detail_metric_help_label('팬밀도', '조회수 대비 좋아요·댓글 등 팬 반응의 밀도를 나타냅니다. 높을수록 작지만 결집력 있는 팬덤일 가능성이 큽니다.')}<div class="detail-metric-value">{fmt_num(sel_fan, 3, '')}</div></div>
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

GRAPH_OPTIONS = ["콘텐츠 유형별 영입 점수", "검토 단계별 후보 분포", "후보군 콘텐츠 비율"]

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
    st.button("콘텐츠 유형별 영입 점수", key="graph_view_score_button", use_container_width=True, type="primary" if current_graph_view == "콘텐츠 유형별 영입 점수" else "secondary", on_click=set_graph_view, args=("콘텐츠 유형별 영입 점수",))
with graph_btn_col_2:
    st.button("검토 단계별 후보 분포", key="graph_view_bucket_button", use_container_width=True, type="primary" if current_graph_view == "검토 단계별 후보 분포" else "secondary", on_click=set_graph_view, args=("검토 단계별 후보 분포",))
with graph_btn_col_3:
    st.button("후보군 콘텐츠 비율", key="graph_view_ratio_button", use_container_width=True, type="primary" if current_graph_view == "후보군 콘텐츠 비율" else "secondary", on_click=set_graph_view, args=("후보군 콘텐츠 비율",))

graph_view = st.session_state.get("mock_graph_view", GRAPH_OPTIONS[0])
graph_left, graph_right = st.columns([0.23, 0.77], gap="small")

with graph_left:
    if graph_view == "콘텐츠 유형별 영입 점수":
        html('<div class="graph-explain"><div class="graph-explain-title">콘텐츠 유형별 영입 점수</div><div class="graph-explain-text">어떤 콘텐츠군의 후보가 평균적으로 높은 영입 점수를 받는지 비교합니다. 점수가 높은 콘텐츠군은 우선 탐색 영역으로 볼 수 있습니다.</div></div>')
    elif graph_view == "검토 단계별 후보 분포":
        html('<div class="graph-explain"><div class="graph-explain-title">검토 단계별 후보 분포</div><div class="graph-explain-text">즉시검토, 성장관찰, 검증필요 등 운영 단계별 후보 수를 비교합니다. 검증필요가 많으면 리스크 검토 공수가 큽니다.</div></div>')
    else:
        html('<div class="graph-explain"><div class="graph-explain-title">후보군 콘텐츠 비율</div><div class="graph-explain-text">현재 후보 풀이 특정 콘텐츠군에 쏠려 있는지 확인합니다. 쏠림이 크면 수집 키워드와 필터 편향을 점검합니다.</div></div>')

with graph_right:
    if graph_view == "콘텐츠 유형별 영입 점수":
        if segment_col and score_display_col and not classified_filtered.empty:
            seg_score = classified_filtered.copy()
            seg_score["__score__"] = pd.to_numeric(seg_score[score_display_col], errors="coerce")
            seg_score["__segment__"] = seg_score[segment_col].fillna("미분류").astype(str)
            seg_summary = seg_score.groupby("__segment__", dropna=False).agg(추천점수=("__score__", "mean"), 후보수=("__score__", "size")).reset_index().sort_values("추천점수", ascending=False).head(8)
            fig = px.bar(seg_summary, x="__segment__", y="추천점수", text="추천점수", custom_data=["후보수"], color="__segment__", color_discrete_sequence=COSMIC_COLORS, template="plotly_dark", height=360)
            fig.update_traces(texttemplate="%{y:.1f}", textposition="outside", cliponaxis=False, hovertemplate="콘텐츠군=%{x}<br>추천점수=%{y:.1f}<br>후보수=%{customdata[0]}명<extra></extra>")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=12, r=12, t=16, b=54), xaxis_title="", yaxis_title="영입 점수", xaxis=dict(tickangle=0, tickfont=dict(size=10, color="#d7cdeb")), yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")), font=dict(color="#eee8ff"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("콘텐츠군별 점수를 만들 수 있는 컬럼이 부족합니다.")
    elif graph_view == "검토 단계별 후보 분포":
        if action_col and action_col in filtered.columns:
            bucket_order = ["즉시검토", "성장관찰", "검증필요", "보류", "제외", "미분류"]
            bucket_df = filtered[action_col].fillna("미분류").astype(str).value_counts().rename_axis("검토단계").reset_index(name="후보수")
            bucket_df["정렬"] = bucket_df["검토단계"].apply(lambda x: bucket_order.index(x) if x in bucket_order else 999)
            bucket_df = bucket_df.sort_values(["정렬", "후보수"], ascending=[True, False])
            fig = px.bar(bucket_df, x="후보수", y="검토단계", orientation="h", text="후보수", color="검토단계", color_discrete_sequence=COSMIC_COLORS, template="plotly_dark", height=360)
            fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="검토단계=%{y}<br>후보수=%{x}명<extra></extra>")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=8, r=32, t=12, b=30), xaxis_title="", yaxis_title="", xaxis=dict(gridcolor="rgba(255,255,255,.08)", tickfont=dict(color="#d7cdeb")), yaxis=dict(tickfont=dict(color="#d7cdeb")), font=dict(color="#eee8ff"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("검토 단계 컬럼이 없어 그래프를 만들 수 없습니다.")
    else:
        if segment_col and segment_col in classified_filtered.columns and not classified_filtered.empty:
            treemap_df = classified_filtered[segment_col].fillna("미분류").astype(str).value_counts().reset_index()
            treemap_df.columns = ["구분", "후보수"]
            treemap_df = treemap_df.sort_values("후보수", ascending=False).reset_index(drop=True)
            total_candidates = max(float(treemap_df["후보수"].sum()), 1.0)
            treemap_df["비중"] = treemap_df["후보수"] / total_candidates * 100

            # 상위 부모 노드인 '전체 후보군'을 만들지 않고, 콘텐츠군만 최상위 박스로 표시한다.
            # 이렇게 해야 보라색 parent/root 바가 화면에 노출되지 않는다.
            treemap_colors = [COSMIC_COLORS[i % len(COSMIC_COLORS)] for i in range(len(treemap_df))]
            fig = go.Figure(
                go.Treemap(
                    labels=treemap_df["구분"],
                    parents=[""] * len(treemap_df),
                    values=treemap_df["후보수"],
                    customdata=np.round(treemap_df["비중"], 1),
                    marker=dict(
                        colors=treemap_colors,
                        line=dict(color="rgba(7,10,24,.85)", width=2),
                    ),
                    texttemplate="%{label}<br>%{value:,}명<br>%{customdata:.1f}%",
                    textfont=dict(size=15, color="#F8F2FF"),
                    hovertemplate="콘텐츠군=%{label}<br>후보수=%{value:,}명<br>비중=%{customdata:.1f}%<extra></extra>",
                    tiling=dict(pad=2),
                )
            )
            fig.update_layout(
                template="plotly_dark",
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=8, r=8, t=8, b=8),
                font=dict(color="#eee8ff"),
                uniformtext=dict(minsize=11, mode="hide"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
        else:
            st.info("콘텐츠군 구성 비율을 만들 수 없습니다.")

# =========================================================
# 17. 설명 Expander
# - KPI 해석은 각 KPI 카드의 ? 툴팁으로 이동
# - 영입 점수 설명은 KPI 카드 바로 아래로 이동
# =========================================================


# =========================================================
# FINAL PATCH 2026-05-12 PM
# - 스타시드/스타트레일 상단 여백 축소 및 타이틀 블록 확대
# - 최근 순위 상승 후보 테이블 전용 컬럼 폭/가독성 분리
# =========================================================
st.markdown(
    """
    <style>.block-container:has(.starseed-board),.block-container:has(.startrail-page){padding-top:0 !important;margin-top:-4.6rem !important}.starseed-board{margin-top:0 !important;padding-top:0 !important}.startrail-page .startrail-hero{padding-top:0 !important;margin-top:0 !important}.starseed-board .starseed-hero-modern{align-items:center !important;margin-top:0 !important;margin-bottom:14px !important}.starseed-board .board-head-left,.starseed-board .starseed-title-block{grid-template-columns:96px minmax(0,1fr) !important;gap:23px !important;min-height:104px !important;align-items:center !important}.starseed-board .board-title-icon{width:82px !important;height:82px !important;border-radius:14px !important}.starseed-board .board-title-icon .seed-search-icon{transform:scale(1.14) !important;transform-origin:center center !important}.starseed-board .board-title,.starseed-board .board-title-ko,.starseed-board .starseed-brand-title{font-size:45px !important;line-height:1.02 !important;margin-bottom:8px !important}.starseed-board .board-title span,.starseed-board .starseed-brand-title span{font-size:36px !important}.starseed-board .board-title-accent-line{width:270px !important;height:2px !important;margin-bottom:10px !important}.starseed-board .board-subtitle,.starseed-board .starseed-brand-subtitle{font-size:15.8px !important;line-height:1.45 !important;font-weight:760 !important}.starseed-board .starseed-date-pill{top:0 !important;right:0 !important;height:42px !important;min-height:42px !important;padding:0 18px !important;gap:9px !important;font-size:14px !important;line-height:42px !important}.startrail-page .startrail-hero-modern{align-items:center !important;margin-top:0 !important;margin-bottom:30px !important}.startrail-page .trail-title-block{grid-template-columns:96px minmax(0,1fr) !important;gap:23px !important;min-height:104px !important;align-items:center !important}.startrail-page .trail-title-icon{width:82px !important;height:82px !important;border-radius:14px !important}.startrail-page .trail-title-icon .trail-spark-icon{transform:scale(1.14) !important;transform-origin:center center !important}.startrail-page .trail-brand-title{font-size:45px !important;line-height:1.02 !important;margin-bottom:8px !important}.startrail-page .trail-brand-title span{font-size:36px !important}.startrail-page .trail-title-accent-line{width:270px !important;height:2px !important;margin-bottom:10px !important}.startrail-page .trail-title-block .trail-subtitle{font-size:15.8px !important;line-height:1.45 !important;font-weight:760 !important}.startrail-page .trail-date-pill{top:0 !important;right:0 !important}.startrail-page .trail-info-card{margin-top:44px !important}.recent-table-panel{min-height:228px !important;overflow:hidden !important}.recent-priority-table{table-layout:fixed !important;width:100% !important;font-size:12px !important}.recent-priority-table col.recent-col-candidate{width:34% !important}.recent-priority-table col.recent-col-prev,.recent-priority-table col.recent-col-current,.recent-priority-table col.recent-col-rise,.recent-priority-table col.recent-col-score{width:12% !important}.recent-priority-table col.recent-col-stage{width:18% !important}.recent-priority-table th,.recent-priority-table td{padding-left:8px !important;padding-right:8px !important;text-align:center !important;vertical-align:middle !important;white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important}.recent-priority-table td.recent-candidate,.recent-priority-table th:first-child{text-align:left !important;font-weight:900 !important;padding-left:12px !important}.recent-priority-table td.recent-numeric,.recent-priority-table .priority-score{font-weight:950 !important;letter-spacing:-0.01em !important}.recent-priority-table td.recent-rise{color:#ff838d !important;font-weight:950 !important}.recent-priority-table td.recent-stage .action-pill,.recent-priority-table td.recent-stage .tag-pill{max-width:86px !important;min-width:58px !important;font-size:10.5px !important;padding:3px 8px !important}@media (max-width:1200px){.block-container:has(.starseed-board),.block-container:has(.startrail-page){margin-top:-2.2rem !important}.starseed-board .board-title,.starseed-board .board-title-ko,.starseed-board .starseed-brand-title,.startrail-page .trail-brand-title{font-size:38px !important}.starseed-board .board-title span,.starseed-board .starseed-brand-title span,.startrail-page .trail-brand-title span{font-size:30px !important}}</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# POST-RENDER SAFETY PATCH - STAR SEED date pill size sync
# =========================================================
st.markdown(
    """
    <style>html body .stApp .starseed-board .starseed-date-pill,html body .stApp .starseed-date-pill{height:42px !important;min-height:42px !important;padding:0 18px !important;gap:9px !important;font-size:14px !important;font-weight:900 !important;line-height:42px !important;border-radius:999px !important;display:inline-flex !important;align-items:center !important;white-space:nowrap !important;box-sizing:border-box !important}</style>
    """,
    unsafe_allow_html=True,
)

