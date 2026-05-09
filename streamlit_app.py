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
    page_title="CIME 영입후보 대시보드",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


CANDIDATE_DASHBOARD_PATH = resolve_existing_path("10_dashboard/data/dashboard_candidate_table.csv")
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


@st.cache_data(show_spinner=False)
def load_data():
    candidate = read_csv_safe(CANDIDATE_DASHBOARD_PATH)

    if candidate.empty:
        candidate = read_csv_safe(CANDIDATE_SCORED_FINAL_PATH)

    segment = read_csv_safe(SEGMENT_DASHBOARD_PATH)
    summary = read_csv_safe(SUMMARY_DASHBOARD_PATH)
    tracking = read_csv_safe(SHORTLIST_TRACKING_PATH)
    reference = read_csv_safe(REFERENCE_DASHBOARD_PATH)
    snapshot = read_csv_safe(CANDIDATE_SCORED_SNAPSHOT_PATH)

    return candidate, segment, summary, tracking, reference, snapshot


candidate_df, segment_df, summary_df, tracking_df, reference_df, snapshot_df = load_data()


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
        sign = "+" if value > 0 else ""
        if ndigits == 0:
            return f"{sign}{int(round(value)):,}{suffix}"
        return f"{sign}{value:,.{ndigits}f}{suffix}"
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
    local_subs_col = first_existing(out, ["채널구독자수", "subscriber_count", "구독자수"])
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
            <div class="kpi-sub">{sub}</div>
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
rank_col = first_existing(df, ["운영우선순위", "최종순위", "rank", "순위"])
score_col = first_existing(df, ["최종점수", "위성점수_log_minmax", "final_score", "score"])
action_col = first_existing(df, ["액션버킷", "action_bucket"])
segment_col = first_existing(df, ["대표상위세그먼트", "대표세그먼트", "segment", "대표상위세그먼트명"])
lower_segment_col = first_existing(df, ["대표하위세그먼트", "sub_segment", "대표하위세그먼트명"])
shortlist_col = first_existing(df, ["shortlist_선정여부", "shortlist", "shortlisted"])
shortlist_type_col = first_existing(df, ["shortlist_유형", "shortlist_type"])

subs_col = first_existing(df, ["채널구독자수", "subscriber_count", "구독자수"])
view_col = first_existing(df, ["최근영상조회수평균", "avg_recent_views", "최근조회수평균"])
eng_col = first_existing(df, ["최근영상참여율평균", "avg_engagement_rate", "참여율"])
growth_col = first_existing(df, ["성장성점수", "growth_score"])
fan_col = first_existing(df, ["팬밀도점수", "fan_density_score"])
live_col = first_existing(df, ["라이브친화점수", "live_fit_score"])
practical_col = first_existing(df, ["실전성점수", "practical_score"])
channel_power_col = first_existing(df, ["채널력점수", "channel_power_score"])

recommend_col = first_existing(df, ["추천사유", "recommend_reason"])
caution_col = first_existing(df, ["주의사유", "caution_reason"])
basis_col = first_existing(df, ["자동판정근거", "판정근거"])
change_col = first_existing(df, ["변화요약", "change_summary"])

risk_col = first_existing(df, ["운영제외리스크", "operation_exclusion_risk"])
verify_risk_col = first_existing(df, ["검증필요리스크", "verification_risk"])

numeric_candidates = [
    rank_col,
    score_col,
    subs_col,
    view_col,
    eng_col,
    growth_col,
    fan_col,
    live_col,
    practical_col,
    channel_power_col,
    risk_col,
    verify_risk_col,
]

df = to_numeric_if_exists(df, numeric_candidates)

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

if rank_col is not None:
    df = df.sort_values(rank_col, ascending=True, na_position="last")
elif score_col is not None:
    df = df.sort_values(score_col, ascending=False, na_position="last")

df = df.reset_index(drop=True)

# Snapshot 테이블 준비
snapshot_prepared_df = prepare_snapshot_df(snapshot_df)


# =========================================================
# 6. 사이드바 필터
# =========================================================

st.sidebar.markdown(
    """
    <div class="mission-sidebar-title">
        <div class="mission-sidebar-logo">🪐 CIME</div>
        <div class="mission-sidebar-sub">MISSION CONTROL</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("### 🚀 필터")

filtered = df.copy()

if segment_col:
    seg_values = sorted([x for x in filtered[segment_col].dropna().astype(str).unique()])
    selected_segments = st.sidebar.multiselect(
        "대표상위세그먼트",
        options=seg_values,
        default=seg_values,
    )
    if selected_segments:
        filtered = filtered[filtered[segment_col].astype(str).isin(selected_segments)]

if lower_segment_col:
    lower_values = sorted([x for x in filtered[lower_segment_col].dropna().astype(str).unique()])
    selected_lower = st.sidebar.multiselect(
        "대표하위세그먼트",
        options=lower_values,
        default=[],
    )
    if selected_lower:
        filtered = filtered[filtered[lower_segment_col].astype(str).isin(selected_lower)]

if action_col:
    action_values = sorted([x for x in filtered[action_col].dropna().astype(str).unique()])
    selected_actions = st.sidebar.multiselect(
        "액션버킷",
        options=action_values,
        default=action_values,
    )
    if selected_actions:
        filtered = filtered[filtered[action_col].astype(str).isin(selected_actions)]

if shortlist_col:
    only_shortlist = st.sidebar.checkbox("shortlist 선정 후보만 보기", value=False)
    if only_shortlist:
        shortlist_bool = filtered[shortlist_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])
        filtered = filtered[shortlist_bool]

hide_hold = st.sidebar.checkbox("보류/제외 숨기기", value=True)

if hide_hold and action_col:
    filtered = filtered[
        ~filtered[action_col].astype(str).str.contains("보류|제외", na=False)
    ]

# 점수 필터를 사용하지 못하는 상황에서도 KPI 비교 로직이 안전하게 동작하도록 기본값 지정
score_filter_100 = None

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

        score_filter_100 = st.sidebar.slider(
            "최소 최종점수(100점 기준)",
            min_value=float(np.floor(min_score_100)),
            max_value=float(np.ceil(max_score_100)),
            value=float(np.floor(min_score_100)),
            step=1.0,
        )

        filtered = filtered[
            pd.to_numeric(filtered[score_display_col], errors="coerce") >= score_filter_100
        ]

if subs_col:
    min_subs = int(st.sidebar.number_input("최소 구독자 수", min_value=0, value=0, step=1000))
    if min_subs > 0:
        filtered = filtered[pd.to_numeric(filtered[subs_col], errors="coerce").fillna(0) >= min_subs]

if view_col:
    min_views = int(st.sidebar.number_input("최소 최근영상조회수평균", min_value=0, value=0, step=1000))
    if min_views > 0:
        filtered = filtered[pd.to_numeric(filtered[view_col], errors="coerce").fillna(0) >= min_views]

search_text = st.sidebar.text_input("채널명 검색", placeholder="채널명을 입력하세요")

if search_text and channel_name_col:
    filtered = filtered[
        filtered[channel_name_col].astype(str).str.contains(search_text, case=False, na=False)
    ]

# =========================================================
# 필터 적용 후 화면 표시용 순위 재부여
# =========================================================

filtered = filtered.copy()
filtered["표시순위"] = np.arange(1, len(filtered) + 1)

top_n = st.sidebar.slider("TOP N", min_value=5, max_value=50, value=10, step=5)

# =========================================================
# 변화 추적 기준 시점 필터
# - 2026-05-01 이전 snapshot은 선택 불가
# - 비교 대상 시점/기준 시점 모두 최소 날짜를 2026-05-01로 제한
# =========================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 변화 추적 기준")

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
        st.sidebar.warning(
            f"{MIN_TRACKING_DATE_LABEL} 이후 snapshot 날짜가 없습니다. "
            "STEP11 snapshot append를 다시 누적하세요."
        )
        tracking_target_df = df.copy()
        tracking_target_label = "현재"
    else:
        target_options = snapshot_dates + ["현재"]

        default_target_idx = len(target_options) - 1

        tracking_target_label = st.sidebar.selectbox(
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

            tracking_base_label = st.sidebar.selectbox(
                "기준 시점",
                options=available_base_dates,
                index=default_base_idx,
                help=f"{MIN_TRACKING_DATE_LABEL} 이후 날짜만 기준 시점으로 선택할 수 있습니다.",
            )

            tracking_base_df = get_snapshot_by_date(snapshot_prepared_df, tracking_base_label)
        else:
            st.sidebar.warning("비교 가능한 기준 snapshot 날짜가 없습니다.")
else:
    st.sidebar.warning("snapshot 파일이 없거나 날짜 컬럼을 찾지 못했습니다.")

st.sidebar.markdown("---")
if st.sidebar.button("데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

with st.sidebar.expander("최신 파이프라인 결과 반영 방법", expanded=False):
    st.markdown(
        """
        1. 로컬 원본 프로젝트에서 최신 파이프라인을 실행합니다.  
        2. 생성된 `10_dashboard/data/*.csv`, `11_final/core_output/*.csv`, `09_intermediate/snapshots/*.csv`를 배포용 repo에 복사합니다.  
        3. GitHub에 commit/push합니다.  
        4. Streamlit Cloud에서 자동 재배포 후, 필요 시 `데이터 새로고침`으로 캐시를 비웁니다.  

        이 대시보드는 API를 직접 실행하지 않고, 파이프라인 산출 CSV를 읽는 조회형 구조입니다.
        """
    )


# =========================================================
# 7. 헤더
# =========================================================

now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
st.markdown(
    f"""
    <div class="mission-hero">
        <div class="mission-title"><span class="mission-highlight">CIME</span> STREAM PLANET</div>
        <div class="mission-subtitle">데이터 우주에서 다음 플랫폼의 중심 별을 찾다</div>
        <div class="mission-desc">
            유튜브 API 기반 후보 데이터를 바탕으로 성장성, 팬 반응, 라이브 전환 가능성, 영입 현실성을 종합해
            CIME가 검토할 잠재 스트리머 후보를 탐색합니다.
        </div>
        <div style="margin-top: 16px; position: relative; z-index: 1;">
            <span class="mission-time-pill">🟢 데이터 정상 로드 · 마지막 화면 갱신(KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
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

with st.expander("스코어링 방식 설명: 휴리스틱 기반 운영 점수", expanded=False):
    st.markdown(
        """
        <div class="explain-box">
        현재 점수는 실제 영입 성공 데이터를 학습한 머신러닝 모델이 아니라, CIME의 초기 영입 전략을 반영한 <b>휴리스틱 기반 운영 점수</b>입니다.<br><br>
        단순 조회수/구독자 수만 보는 것이 아니라, <b>채널력, 성장성, 팬밀도, 라이브친화도, 실전성</b>을 함께 반영합니다.<br><br>
        <code>최종점수_raw = 0.22×채널력점수 + 0.28×성장성점수 + 0.22×팬밀도점수 + 0.15×라이브친화점수 + 0.13×실전성점수</code><br><br>
        이후 <code>수기제외채널</code>, <code>운영제외리스크</code>, <code>검증필요리스크</code>를 감점합니다. 따라서 최종점수는 후보 정렬용 기준이고, 실제 판단은 <b>검토 단계, 추천사유, 주의사유</b>와 함께 봐야 합니다.<br><br>
        이 가중치는 확정된 정답이 아니라 1차 운영 기준입니다. 향후 사람 검토 라벨이나 실제 컨택 결과가 쌓이면 가중치 민감도 분석 또는 지도학습으로 보정할 수 있습니다.
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

        st.markdown(
            f"""
            <div class="candidate-card">
                <div class="rank-badge">{fmt_int(rank_value)}</div>
                <div class="candidate-avatar">{get_initial(name)}</div>
                <div class="candidate-name">{name}</div>
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
# =========================================================

main_left, main_right = st.columns([0.68, 0.32])


# =========================================================
# 10-1. 좌측: 테이블 + 세그먼트별 점수 분포
# =========================================================

with main_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🛰️ 영입 우선순위 TOP")
    st.caption("현재 필터 조건에서 검토 우선순위가 높은 후보를 보여줍니다. 표의 순위는 전체 원본 순위가 아니라 현재 필터 결과 기준입니다.")

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
        shortlist_type_col,
        recommend_col,
        caution_col,
        change_col,
    ]

    display_cols = [c for c in display_cols if c and c in filtered.columns]

    table_df = filtered[display_cols].head(top_n).copy()

    display_rename_map = {
        "표시순위": "현재 필터 기준 순위",
        score_display_col: "영입 적합도 점수",
        channel_name_col: "채널명",
        segment_col: "주요 콘텐츠군",
        lower_segment_col: "세부 콘텐츠 유형",
        subs_col: "구독자 수",
        view_col: "최근 영상 평균 조회수",
        eng_col: "평균 참여율",
        action_col: "검토 단계",
        shortlist_type_col: "shortlist 유형",
        recommend_col: "추천 사유",
        caution_col: "주의 사유",
        change_col: "변화 요약",
    }
    display_rename_map = {k: v for k, v in display_rename_map.items() if k and k in table_df.columns}
    table_df = table_df.rename(columns=display_rename_map)

    if "영입 적합도 점수" in table_df.columns:
        table_df["영입 적합도 점수"] = pd.to_numeric(table_df["영입 적합도 점수"], errors="coerce").round(1)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
    )

    csv_download = table_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "현재 TOP 후보 CSV 다운로드",
        data=csv_download,
        file_name="cime_top_candidates.csv",
        mime="text/csv",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =====================================================
    # 후보 분포: 상위 콘텐츠별 최종점수 분포
    # - 전체 후보를 기본으로 그림
    # - 현재 필터 조건에 포함된 후보는 세그먼트별 색상
    # - 필터에서 제외된 후보는 회색 처리
    # =====================================================

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🌌 상위 콘텐츠별 영입 후보 점수 분포")
    st.caption("각 점은 후보 채널 1개를 의미합니다. x축은 상위 콘텐츠군, y축은 영입 적합도 점수입니다.")

    if segment_col and score_col:
        plot_all = df.copy()
        plot_all = plot_all.reset_index().rename(columns={"index": "__original_index__"})

        # filtered는 기존 df의 index를 유지하고 있으므로, 현재 필터에 남은 행을 표시
        selected_index_set = set(filtered.index.tolist())
        plot_all["__is_selected__"] = plot_all["__original_index__"].isin(selected_index_set)

        # 점수 컬럼 정리: 그래프도 100점 기준으로 고정
        plot_all["__score_plot__"] = pd.to_numeric(plot_all[score_display_col], errors="coerce")
        y_axis_title = "최종점수(100점 기준)"

        plot_all["__segment__"] = plot_all[segment_col].fillna("미분류").astype(str)

        # 현재 필터에서 선택된 후보가 있는 세그먼트를 우선 정렬
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

        # 공이 완전히 겹치지 않도록 x축에 약간의 jitter 추가
        rng = np.random.default_rng(42)
        plot_all["__x_jitter__"] = plot_all["__x_base__"] + rng.normal(
            loc=0,
            scale=0.08,
            size=len(plot_all)
        )

        # 세그먼트별 색상 팔레트
        palette = px.colors.qualitative.Safe + px.colors.qualitative.Set3 + px.colors.qualitative.Pastel
        seg_color_map = {
            seg: palette[i % len(palette)]
            for i, seg in enumerate(segment_order)
        }

        # 선택 후보: 세그먼트별 색상
        selected_plot = plot_all[plot_all["__is_selected__"] == True].copy()

        # 필터 제외 후보: 회색
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

        # 1) 필터 제외 후보: 회색 배경 점
        if not unselected_plot.empty:
            fig.add_trace(
                go.Scatter(
                    x=unselected_plot["__x_jitter__"],
                    y=unselected_plot["__score_plot__"],
                    mode="markers",
                    name="필터 제외",
                    marker=dict(
                        size=7,
                        color="rgba(150,150,150,0.28)",
                        line=dict(width=0),
                    ),
                    customdata=unselected_plot[hover_cols].astype(str).values if hover_cols else None,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        + "세그먼트: %{customdata[1]}<br>" if len(hover_cols) >= 2 else ""
                    )
                    + "점수: %{y:.2f}<br>"
                    + "<extra>필터 제외</extra>",
                    showlegend=True,
                )
            )

        # 2) 필터 선택 후보: 세그먼트별 색상
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
                        line=dict(
                            width=0.8,
                            color="rgba(255,255,255,0.35)"
                        ),
                    ),
                    customdata=seg_df[hover_cols].astype(str).values if hover_cols else None,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        + "상위세그먼트: %{customdata[1]}<br>" if len(hover_cols) >= 2 else ""
                    )
                    + (
                        "하위세그먼트: %{customdata[2]}<br>" if len(hover_cols) >= 3 else ""
                    )
                    + (
                        "액션버킷: %{customdata[3]}<br>" if len(hover_cols) >= 4 else ""
                    )
                    + "점수: %{y:.2f}<br>"
                    + "<extra></extra>",
                )
            )

        fig.update_layout(
            template="plotly_dark",
            height=460,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
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
            yaxis=dict(
                title=y_axis_title,
                gridcolor="rgba(255,255,255,0.12)",
                zeroline=False,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "해석 포인트: 어느 상위 콘텐츠군에 고득점 후보가 많은지, 특정 상위 콘텐츠군이 낮은 점수대에 몰려 있는지, "
            "현재 필터에서 제외된 후보가 얼마나 많은지 확인할 수 있습니다. "
            "색상 점은 현재 필터에 포함된 후보, 회색 점은 필터에서 제외된 후보입니다."
        )

    else:
        st.info("상위 콘텐츠별 점수 분포를 만들기 위해서는 대표상위세그먼트 컬럼과 최종점수 컬럼이 필요합니다.")

    st.markdown("</div>", unsafe_allow_html=True)



# =========================================================
# 10-2. 우측: 후보 상세
# =========================================================

with main_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🔭 선택 후보 상세")

    if channel_name_col:
        candidate_names = filtered[channel_name_col].dropna().astype(str).tolist()

        if candidate_names:
            selected_name = st.selectbox("후보 선택", candidate_names, index=0)
            selected_row = filtered[filtered[channel_name_col].astype(str) == selected_name].iloc[0]

            st.markdown(
                f"""
                <div class="detail-title">{selected_row.get(channel_name_col, '-')}</div>
                <div class="small-muted">{selected_row.get(channel_id_col, '') if channel_id_col else ''}</div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            metric_cols = st.columns(2)

            with metric_cols[0]:
                st.metric("점수(100점)", fmt_float(selected_row.get(score_display_col), 1) if score_col else "-")
                st.metric("구독자 수", fmt_int(selected_row.get(subs_col)) if subs_col else "-")
                st.metric("최근 조회수 평균", fmt_int(selected_row.get(view_col)) if view_col else "-")

            with metric_cols[1]:
                st.metric("성장성", fmt_float(selected_row.get(growth_col), 3) if growth_col else "-")
                st.metric("팬밀도", fmt_float(selected_row.get(fan_col), 3) if fan_col else "-")
                st.metric("라이브친화", fmt_float(selected_row.get(live_col), 3) if live_col else "-")

            st.markdown(
                f"""
                <div style="margin-top:10px;">
                    <span class="segment-pill">{selected_row.get(segment_col, '-') if segment_col else '-'}</span>
                    <span class="segment-pill">{selected_row.get(action_col, '-') if action_col else '-'}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            reason_text = selected_row.get(recommend_col, "-") if recommend_col else "-"
            caution_text = selected_row.get(caution_col, "-") if caution_col else "-"
            basis_text = selected_row.get(basis_col, "-") if basis_col else "-"
            change_text = selected_row.get(change_col, "-") if change_col else "-"

            st.markdown(
                f"""
                <div class="reason-box">
                    <b>추천사유</b><br>{reason_text}
                </div>
                <div class="reason-box">
                    <b>주의사유</b><br>{caution_text}
                </div>
                <div class="reason-box">
                    <b>자동판정근거</b><br>{basis_text}
                </div>
                <div class="reason-box">
                    <b>변화요약</b><br>{change_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("현재 필터 조건에 해당하는 후보가 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 10-3. 후보 구성 요약: 3칸 정렬 그래프
# - 액션버킷별 후보 수 / 세그먼트별 평균 점수 / 세그먼트 분포를
#   같은 라인에 3개 카드로 배치해 경계와 높이를 맞춘다.
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🧭 후보군 운영 현황 요약")
st.caption("현재 필터 조건에서 후보군이 어떤 검토 단계와 콘텐츠군으로 구성되어 있는지 요약합니다.")

chart_col1, chart_col2, chart_col3 = st.columns(3)

# ---------------------------------------------------------
# 1) 액션버킷별 후보 수
# ---------------------------------------------------------
with chart_col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🚦 검토 단계별 후보 수")

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

        bucket_df["정렬순서"] = bucket_df["액션버킷"].apply(
            lambda x: bucket_order.index(x) if x in bucket_order else 999
        )
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
            height=360,
            color="액션버킷",
            color_discrete_map=color_map_bucket,
        )

        fig_bucket.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="액션버킷=%{y}<br>후보수=%{x}명<extra></extra>",
        )

        fig_bucket.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=5, r=35, t=10, b=30),
            xaxis_title="후보 수",
            yaxis_title="",
            yaxis=dict(
                categoryorder="array",
                categoryarray=list(reversed(bucket_df["액션버킷"].tolist())),
            ),
        )

        st.plotly_chart(fig_bucket, use_container_width=True)
        st.caption("즉시검토, 성장관찰, 검증필요, 보류, 제외 중 후보가 어디에 몰려 있는지 확인합니다.")
    else:
        st.info("액션버킷 컬럼이 없어 시각화를 만들 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2) 대표상위세그먼트별 평균 최종점수
# ---------------------------------------------------------
with chart_col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### ✨ 콘텐츠군별 평균 영입 점수")

    if segment_col and score_display_col and segment_col in filtered.columns and score_display_col in filtered.columns:
        seg_score_df = filtered.copy()
        seg_score_df["__score__"] = pd.to_numeric(seg_score_df[score_display_col], errors="coerce")
        seg_score_df["__segment__"] = seg_score_df[segment_col].fillna("미분류").astype(str)

        seg_summary = (
            seg_score_df.groupby("__segment__", dropna=False)
            .agg(
                평균최종점수=("__score__", "mean"),
                후보수=("__score__", "size"),
            )
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
            height=360,
            color="__segment__",
        )

        fig_seg_score.update_traces(
            texttemplate="%{y:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "대표상위세그먼트=%{x}<br>"
                "평균최종점수=%{y:.1f}<br>"
                "후보수=%{customdata[0]}명<extra></extra>"
            ),
        )

        fig_seg_score.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=5, r=5, t=10, b=80),
            xaxis_title="",
            yaxis_title="평균 점수",
            xaxis=dict(tickangle=-35),
            yaxis=dict(range=[0, max(100, float(seg_summary["평균최종점수"].max(skipna=True) or 0) * 1.15)]),
        )

        st.plotly_chart(fig_seg_score, use_container_width=True)
    else:
        st.info("세그먼트 컬럼 또는 점수 컬럼이 없어 시각화를 만들 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3) 세그먼트/액션버킷 분포 도넛
# ---------------------------------------------------------
with chart_col3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 🪐 콘텐츠군 구성 비율")

    pie_col = action_col if action_col else segment_col

    if pie_col:
        pie_data = (
            filtered[pie_col]
            .fillna("미분류")
            .astype(str)
            .value_counts()
            .reset_index()
        )
        pie_data.columns = ["구분", "후보수"]

        fig_pie = px.pie(
            pie_data,
            names="구분",
            values="후보수",
            hole=0.55,
            template="plotly_dark",
            height=360,
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="구분=%{label}<br>후보수=%{value}명<br>비중=%{percent}<extra></extra>",
        )

        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=5, r=5, t=10, b=20),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        )

        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("현재 후보군이 어떤 콘텐츠군 또는 검토 단계에 많이 분포하는지 확인합니다. 특정 영역 쏠림 여부를 점검하는 용도입니다.")
    else:
        st.info("세그먼트 분포를 만들 컬럼이 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)



# =========================================================
# 10-4. 후보 클러스터 포지셔닝 맵
# - 팬 반응 밀도와 라이브 전환 가능성을 기준으로 후보군을 운영형 클러스터로 해석
# - 별도 머신러닝 의존성 없이 중앙값 기준 사분면 클러스터를 생성한다.
# =========================================================

add_section_divider()
st.markdown("### 🗺️ 후보 클러스터 포지셔닝 맵")
st.caption(
    "팬 반응 밀도와 라이브 전환 가능성을 기준으로 후보를 4개 운영형 클러스터로 나눠 봅니다. "
    "엄밀한 머신러닝 군집화라기보다는, 영입 검토 액션을 쉽게 정하기 위한 해석형 클러스터링입니다."
)

with st.expander("클러스터 해석 방법", expanded=False):
    st.markdown(
        """
        - **코어 라이브 팬덤형**: 팬 반응과 라이브 전환 가능성이 모두 높은 후보입니다. 우선 컨택 또는 상세 검토 대상입니다.
        - **팬덤 수익화형**: 팬 반응은 강하지만 라이브 신호는 상대적으로 약한 후보입니다. 굿즈, 후원, 커뮤니티형 수익화 제안에 적합합니다.
        - **라이브 전환 실험형**: 라이브 신호는 있으나 팬 반응 밀도는 아직 낮은 후보입니다. 파일럿 방송 또는 성장관찰 대상으로 볼 수 있습니다.
        - **관찰/저신호형**: 두 신호가 모두 낮은 후보입니다. 현재는 우선순위를 낮추고 추후 성장 여부를 관찰합니다.

        기준선은 현재 필터 결과의 **팬 반응 밀도 중앙값**과 **라이브 전환 가능성 중앙값**입니다. 필터를 바꾸면 클러스터 기준도 함께 바뀝니다.
        """
    )

if fan_col and live_col and fan_col in filtered.columns and live_col in filtered.columns:
    position_df = filtered.copy()
    position_df["__fan__"] = pd.to_numeric(position_df[fan_col], errors="coerce")
    position_df["__live__"] = pd.to_numeric(position_df[live_col], errors="coerce")
    position_df["__growth__"] = pd.to_numeric(position_df[growth_col], errors="coerce") if growth_col in position_df.columns else np.nan
    position_df["__score__"] = pd.to_numeric(position_df[score_display_col], errors="coerce") if score_display_col in position_df.columns else np.nan
    position_df["__segment__"] = position_df[segment_col].fillna("미분류").astype(str) if segment_col else "미분류"
    position_df["__name__"] = position_df[channel_name_col].astype(str) if channel_name_col else "-"
    position_df["__action__"] = position_df[action_col].fillna("미분류").astype(str) if action_col else "미분류"
    position_df = position_df.dropna(subset=["__fan__", "__live__"])

    if not position_df.empty:
        fan_cut = float(position_df["__fan__"].median())
        live_cut = float(position_df["__live__"].median())

        def assign_cluster(row):
            fan_high = row["__fan__"] >= fan_cut
            live_high = row["__live__"] >= live_cut
            if fan_high and live_high:
                return "🚀 코어 라이브 팬덤형"
            if fan_high and not live_high:
                return "💎 팬덤 수익화형"
            if (not fan_high) and live_high:
                return "🛰️ 라이브 전환 실험형"
            return "🌑 관찰/저신호형"

        position_df["__cluster__"] = position_df.apply(assign_cluster, axis=1)
        position_df["__score_size__"] = position_df["__score__"].fillna(position_df["__score__"].median())
        if position_df["__score_size__"].dropna().empty:
            position_df["__score_size__"] = 1

        cluster_order = [
            "🚀 코어 라이브 팬덤형",
            "💎 팬덤 수익화형",
            "🛰️ 라이브 전환 실험형",
            "🌑 관찰/저신호형",
        ]

        color_mode = st.radio(
            "포지셔닝 맵 색상 기준",
            options=["클러스터", "주요 콘텐츠군", "검토 단계"],
            horizontal=True,
            index=0,
        )

        if color_mode == "클러스터":
            color_col = "__cluster__"
            legend_title = "후보 클러스터"
            color_map = {
                "🚀 코어 라이브 팬덤형": "#2fffd3",
                "💎 팬덤 수익화형": "#b66cff",
                "🛰️ 라이브 전환 실험형": "#4da3ff",
                "🌑 관찰/저신호형": "#6b7280",
            }
        elif color_mode == "검토 단계":
            color_col = "__action__"
            legend_title = "검토 단계"
            color_map = None
        else:
            color_col = "__segment__"
            legend_title = "주요 콘텐츠군"
            color_map = None

        fig_position = px.scatter(
            position_df,
            x="__fan__",
            y="__live__",
            color=color_col,
            size="__score_size__",
            size_max=20,
            hover_name="__name__",
            hover_data={
                "__cluster__": True,
                "__segment__": True,
                "__action__": True,
                "__score__": ":.1f",
                "__growth__": ":.3f",
                "__fan__": ":.3f",
                "__live__": ":.3f",
            },
            template="plotly_dark",
            height=470,
            color_discrete_map=color_map,
            category_orders={"__cluster__": cluster_order},
        )

        # 중앙값 기준선: 클러스터의 기준을 눈에 보이게 표시
        fig_position.add_vline(
            x=fan_cut,
            line_width=1,
            line_dash="dash",
            line_color="rgba(255,255,255,0.35)",
        )
        fig_position.add_hline(
            y=live_cut,
            line_width=1,
            line_dash="dash",
            line_color="rgba(255,255,255,0.35)",
        )

        fig_position.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=40),
            xaxis_title="팬 반응 밀도",
            yaxis_title="라이브 전환 가능성",
            legend_title_text=legend_title,
        )
        fig_position.update_xaxes(gridcolor="rgba(255,255,255,0.12)", zeroline=False)
        fig_position.update_yaxes(gridcolor="rgba(255,255,255,0.12)", zeroline=False)
        st.plotly_chart(fig_position, use_container_width=True)

        st.caption(
            "오른쪽 위는 팬 반응과 라이브 전환 가능성이 모두 높은 영역입니다. "
            "점 크기는 영입 적합도 점수이며, 점을 클릭/호버하면 후보명과 검토 단계, 콘텐츠군을 확인할 수 있습니다."
        )

        cluster_summary = (
            position_df.groupby("__cluster__", dropna=False)
            .agg(
                후보수=("__name__", "count"),
                평균점수=("__score__", "mean"),
                평균성장성=("__growth__", "mean"),
                즉시검토수=("__action__", lambda x: x.astype(str).str.contains("즉시검토", na=False).sum()),
                검증필요수=("__action__", lambda x: x.astype(str).str.contains("검증필요", na=False).sum()),
            )
            .reset_index()
            .rename(columns={
                "__cluster__": "후보 클러스터",
                "후보수": "후보 수",
                "평균점수": "평균 영입 적합도",
                "평균성장성": "평균 성장성",
                "즉시검토수": "즉시검토 수",
                "검증필요수": "검증필요 수",
            })
        )
        cluster_summary["정렬순서"] = cluster_summary["후보 클러스터"].apply(
            lambda x: cluster_order.index(x) if x in cluster_order else 999
        )
        cluster_summary = cluster_summary.sort_values("정렬순서").drop(columns=["정렬순서"])
        for c in ["평균 영입 적합도", "평균 성장성"]:
            if c in cluster_summary.columns:
                cluster_summary[c] = pd.to_numeric(cluster_summary[c], errors="coerce").round(2)

        st.markdown("#### 클러스터별 운영 요약")
        st.dataframe(cluster_summary, use_container_width=True, hide_index=True)
        st.caption(
            "클러스터 요약은 어떤 유형의 후보가 현재 필터 결과에서 많은지, 그리고 어떤 클러스터에 즉시검토 후보가 몰려 있는지 확인하는 용도입니다."
        )
    else:
        st.info("포지셔닝 맵을 만들 수 있는 후보 데이터가 부족합니다.")
else:
    st.info("후보 클러스터 포지셔닝 맵을 만들기 위해서는 팬밀도점수와 라이브친화점수 컬럼이 필요합니다.")

# =========================================================
# 11. 하단: Snapshot 기반 변화 추적
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)
add_section_divider()
st.markdown("### 📡 최근 주목 후보 변화")
st.markdown(
    """
    <div class="guide-box">
    <b>표 해석법</b><br>
    - <b>순위 변동</b>이 양수이면 이전 시점보다 순위가 상승한 후보입니다.<br>
    - <b>점수 변동</b>이 양수이면 영입 적합도 점수가 상승한 후보입니다.<br>
    - <b>검토 단계</b>가 보류 → 성장관찰, 검증필요 → 즉시검토처럼 개선되면 우선 확인 대상입니다.<br>
    - <b>신규진입</b>은 기준 시점에는 없었지만 비교 시점에 새로 등장한 후보입니다.
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
            only_new = st.checkbox("신규진입만", value=False)
        with tracking_filter_cols[1]:
            only_bucket_changed = st.checkbox("버킷변경만", value=False)
        with tracking_filter_cols[2]:
            only_rank_up = st.checkbox("순위상승만", value=False)
        with tracking_filter_cols[3]:
            max_tracking_rows = st.number_input("표시 행 수", min_value=10, max_value=500, value=100, step=10)

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

        st.dataframe(
            tracking_display,
            use_container_width=True,
            hide_index=True,
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
