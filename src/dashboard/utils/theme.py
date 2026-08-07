"""Shared visual theme, glassmorphic components, and Plotly styling for
the NIFTY100 Intelligence Platform. Fintech-grade dark UI inspired by
TradingView / Bloomberg Terminal / Stripe Dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils.live_data import check_api_server_status

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
BG = "#080B11"
PANEL = "rgba(15, 23, 42, 0.75)"
PANEL_SOLID = "#0F172A"
INK = "#F8FAFC"
MUTED = "#8B98AC"
LINE = "rgba(255, 255, 255, 0.08)"
GRID = "rgba(255, 255, 255, 0.05)"
ACCENT = "#10B981"      # emerald (bullish primary)
ACCENT_2 = "#22C55E"    # bright green secondary
NEGATIVE = "#F43F5E"    # rose
WARNING = "#F59E0B"

FONT_UI = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"

PLOTLY_SEQUENCE = ["#10B981", "#22C55E", "#34D399", "#F59E0B", "#F43F5E", "#4ADE80", "#84CC16"]


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        :root {{
            --bg: {BG};
            --panel: {PANEL};
            --panel-solid: {PANEL_SOLID};
            --ink: {INK};
            --muted: {MUTED};
            --line: {LINE};
            --grid: {GRID};
            --accent: {ACCENT};
            --accent-2: {ACCENT_2};
            --negative: {NEGATIVE};
            --warning: {WARNING};
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: transparent !important;
            font-family: {FONT_UI} !important;
            color: var(--ink) !important;
        }}

        .stApp {{
            background:
                radial-gradient(ellipse 85% 55% at 15% -10%, rgba(16,185,129,0.10), transparent 60%),
                radial-gradient(ellipse 75% 55% at 100% 0%, rgba(16,185,129,0.08), transparent 60%),
                radial-gradient(ellipse 60% 45% at 50% 100%, rgba(15,23,42,0.6), transparent 70%),
                var(--bg) !important;
            background-attachment: fixed !important;
        }}

        /* Hide default Streamlit chrome — cosmetic only. We deliberately do
           NOT touch stToolbar/stHeader interactivity or add custom
           visibility/z-index rules for the sidebar collapse control: that
           control's data-testid differs across Streamlit versions
           (collapsedControl / stSidebarCollapsedControl / etc.), and any
           visibility:hidden on a parent toolbar is inherited by it, which
           previously broke the sidebar toggle. Only hide the hamburger
           menu, footer credit line, and the thin top decoration bar —
           nothing that lives inside the header/toolbar hierarchy. */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        [data-testid="stDecoration"] {{ display: none !important; }}
        [data-testid="stHeader"] {{ background: transparent !important; }}

        .block-container {{
            max-width: 1560px;
            padding-top: 1.0rem;
            padding-bottom: 3rem;
        }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent); }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translate3d(0, 14px, 0); }}
            to {{ opacity: 1; transform: translate3d(0, 0, 0); }}
        }}
        @keyframes pulseGlow {{
            0% {{ box-shadow: 0 0 0 0 rgba(16,185,129,0.45); }}
            70% {{ box-shadow: 0 0 0 8px rgba(16,185,129,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16,185,129,0); }}
        }}

        h1, h2, h3, h4 {{
            font-family: {FONT_UI} !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            color: var(--ink) !important;
        }}

        h1, [data-testid="stMarkdownContainer"] h1 {{
            font-size: 2.4rem !important;
            line-height: 1.12 !important;
            margin-bottom: 0.35rem !important;
            background: linear-gradient(180deg, #ffffff 0%, #cdeeff 45%, var(--accent) 100%) !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            animation: fadeInUp 0.45s ease-out forwards;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(8, 11, 17, 0.97) 0%, rgba(5, 7, 11, 0.99) 100%) !important;
            border-right: 1px solid var(--line) !important;
            backdrop-filter: blur(16px);
        }}

        .brand-block {{
            padding: 0.6rem 0 1.1rem 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }}
        .brand-title {{
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.05;
            color: #fff !important;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            letter-spacing: -0.03em;
        }}
        .brand-title span {{
            color: var(--accent) !important;
            -webkit-text-fill-color: var(--accent) !important;
        }}
        .brand-subtitle {{
            color: var(--muted) !important;
            font-family: {FONT_MONO};
            font-size: 0.7rem;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-2) !important;
            box-shadow: 0 0 10px var(--accent-2);
            display: inline-block;
            animation: pulseGlow 2s infinite;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label {{
            padding: 0.6rem 0.85rem !important;
            border-radius: 10px !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            font-weight: 500 !important;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(16, 185, 129, 0.08) !important;
            border-left: 3px solid var(--accent) !important;
            transform: translate3d(3px, 0, 0);
        }}

        /* Glassmorphic surfaces */
        .section-card, [data-testid="stMetric"], div[data-testid="stDataFrame"],
        .stPlotlyChart, [data-testid="stExpander"],
        div[data-baseweb="select"] > div,
        .stTextInput input, .stNumberInput input {{
            background: var(--panel) !important;
            backdrop-filter: blur(14px) !important;
            border: 1px solid var(--line) !important;
            border-radius: 14px !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        [data-testid="stMetric"]:hover, .section-card:hover, .stPlotlyChart:hover {{
            border-color: rgba(16, 185, 129, 0.35) !important;
            box-shadow: 0 8px 30px -10px rgba(16, 185, 129, 0.22) !important;
            transform: translate3d(0, -2px, 0) !important;
        }}
        [data-testid="stMetric"] {{ padding: 1.05rem 1.2rem !important; min-height: 112px; }}
        [data-testid="stMetricLabel"] {{
            font-family: {FONT_MONO} !important;
            font-size: 0.72rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            color: var(--muted) !important;
        }}
        [data-testid="stMetricValue"] {{
            font-family: {FONT_MONO} !important;
            font-size: 1.7rem !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            letter-spacing: -0.01em !important;
        }}

        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button,
        .stButton > button,
        .stDownloadButton > button {{
            background: linear-gradient(180deg, #10151f 0%, #0a0e16 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(16, 185, 129, 0.3) !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.2rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            font-size: 0.78rem !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        div[data-testid="stButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover,
        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            background: linear-gradient(180deg, rgba(16,185,129,0.2) 0%, rgba(16,185,129,0.22) 100%) !important;
            border-color: var(--accent) !important;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.28) !important;
            transform: translate3d(0, -2px, 0) !important;
        }}

        .badge-pos {{
            background: rgba(16, 185, 129, 0.14);
            color: var(--accent-2);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.76rem;
            font-family: {FONT_MONO};
            border: 1px solid rgba(16, 185, 129, 0.28);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .badge-neg {{
            background: rgba(244, 63, 94, 0.14);
            color: var(--negative);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.76rem;
            font-family: {FONT_MONO};
            border: 1px solid rgba(244, 63, 94, 0.28);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .badge-neutral {{
            background: rgba(139, 152, 172, 0.12);
            color: var(--muted);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.76rem;
            font-family: {FONT_MONO};
            border: 1px solid rgba(139, 152, 172, 0.24);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .filter-pill {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent);
            border: 1px solid rgba(16, 185, 129, 0.28);
            padding: 4px 11px;
            border-radius: 999px;
            font-family: {FONT_MONO};
            font-size: 0.74rem;
            font-weight: 600;
            margin: 0 6px 6px 0;
        }}

        .kpi-card {{
            background: var(--panel);
            backdrop-filter: blur(14px);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .kpi-card:hover {{
            border-color: rgba(16, 185, 129, 0.35);
            box-shadow: 0 8px 30px -10px rgba(16, 185, 129, 0.22);
            transform: translate3d(0, -2px, 0);
        }}
        .kpi-title {{
            font-family: {FONT_MONO};
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: var(--muted);
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-family: {FONT_MONO};
            font-size: 1.65rem;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.01em;
        }}

        .clean-rule {{
            height: 1px;
            background: linear-gradient(90deg, var(--line), rgba(16,185,129,0.25), transparent);
            margin: 1.2rem 0 1.5rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_motion_fx() -> None:
    st.markdown(
        """
        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translate3d(0, 0, 0)';
                    }
                });
            }, { threshold: 0.1 });
            document.querySelectorAll('[data-testid="stMetric"], .section-card, .stPlotlyChart, .kpi-card').forEach(el => {
                el.style.opacity = '0.92';
                el.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
                observer.observe(el);
            });
        });
        </script>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Plotly styling helper
# ---------------------------------------------------------------------------
def style_plotly_chart(fig, height: int = 400):
    """Apply the platform's consistent dark/glassmorphic styling to any
    Plotly figure. Returns the same figure for chaining."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_UI, color=INK, size=12),
        colorway=PLOTLY_SEQUENCE,
        hoverlabel=dict(
            bgcolor=PANEL_SOLID,
            bordercolor="rgba(16,185,129,0.35)",
            font=dict(family=FONT_MONO, color="#F8FAFC", size=12),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_UI, size=11, color=MUTED),
        ),
        margin=dict(l=45, r=25, t=60, b=45),
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor=GRID,
        linecolor=LINE,
        tickfont=dict(family=FONT_MONO, size=11, color=MUTED),
        title_font=dict(family=FONT_UI, size=12, color=MUTED),
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor=GRID,
        linecolor=LINE,
        tickfont=dict(family=FONT_MONO, size=11, color=MUTED),
        title_font=dict(family=FONT_UI, size=12, color=MUTED),
    )
    return fig


# ---------------------------------------------------------------------------
# Reusable HTML components
# ---------------------------------------------------------------------------
def render_page_header(eyebrow: str, title: str, subtitle: str) -> None:
    eyebrow_html = (
        f'<div style="font-family:{FONT_MONO};font-size:0.72rem;color:var(--accent);'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">{eyebrow}</div>'
        if eyebrow else ""
    )
    st.markdown(
        f"""
        {eyebrow_html}
        <h1>{title}</h1>
        <p style="color:var(--muted);font-size:1.0rem;line-height:1.55;margin-top:0.2rem;margin-bottom:1rem;max-width:900px;">
            {subtitle}
        </p>
        <div class="clean-rule"></div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(title: str, value: str, delta: str | None = None, positive: bool | None = None) -> str:
    """Return HTML for a single glassmorphic KPI card."""
    delta_html = ""
    if delta is not None:
        if positive is None:
            cls = "badge-neutral"
        else:
            cls = "badge-pos" if positive else "badge-neg"
        delta_html = f'<div style="margin-top:8px;"><span class="{cls}">{delta}</span></div>'
    return (
        f'<div class="kpi-card"><div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value}</div>{delta_html}</div>'
    )


def render_kpi_row(cards: list[dict]) -> None:
    """cards: list of {title, value, delta (optional), positive (optional bool)}"""
    cols = st.columns(len(cards), gap="medium")
    for col, card in zip(cols, cards):
        col.markdown(
            kpi_card(
                card.get("title", ""),
                card.get("value", "N/A"),
                card.get("delta"),
                card.get("positive"),
            ),
            unsafe_allow_html=True,
        )


def badge(value: float | None, suffix: str = "%", decimals: int = 2) -> str:
    """Return a badge-pos/badge-neg HTML pill for a signed numeric value."""
    if value is None or value != value:
        return '<span class="badge-neutral">N/A</span>'
    cls = "badge-pos" if value >= 0 else "badge-neg"
    sign = "+" if value >= 0 else ""
    return f'<span class="{cls}">{sign}{value:.{decimals}f}{suffix}</span>'


def render_filter_pills(pills: list[str]) -> None:
    if not pills:
        return
    html = "".join(f'<span class="filter-pill">{p}</span>' for p in pills)
    st.markdown(f'<div style="margin-bottom:0.9rem;">{html}</div>', unsafe_allow_html=True)


def range_bar(current: float, low: float, high: float, label_low: str = "", label_high: str = "") -> str:
    """52-week style range indicator bar."""
    if high <= low:
        pct = 50.0
    else:
        pct = max(0.0, min(100.0, (current - low) / (high - low) * 100.0))
    return (
        f'<div style="width:100%;">'
        f'<div style="position:relative;height:6px;border-radius:4px;'
        f'background:linear-gradient(90deg, rgba(244,63,94,0.35), rgba(16,185,129,0.35), rgba(16,185,129,0.35));">'
        f'<div style="position:absolute;top:-4px;left:{pct}%;transform:translateX(-50%);'
        f'width:14px;height:14px;border-radius:50%;background:#fff;'
        f'border:2px solid var(--accent);box-shadow:0 0 8px rgba(16,185,129,0.6);"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:6px;'
        f'font-family:{FONT_MONO};font-size:0.72rem;color:var(--muted);">'
        f'<span>{label_low}</span><span>{label_high}</span>'
        f'</div>'
        f'</div>'
    )


def render_live_ticker(df: pd.DataFrame) -> None:
    """Renders a clean, animated horizontal marquee ticker using an iframe component."""
    if df.empty:
        return

    items_html = ""
    for _, row in df.iterrows():
        tid = row["company_id"]
        close_price = f"₹{row['current_price']:,.2f}"
        open_price = f"₹{row['open_price']:,.2f}" if "open_price" in row else close_price
        ret = row["return_1m_pct"]
        color = ACCENT_2 if ret >= 0 else NEGATIVE
        bg = "rgba(16, 185, 129, 0.12)" if ret >= 0 else "rgba(244, 63, 94, 0.12)"
        border = "rgba(16, 185, 129, 0.28)" if ret >= 0 else "rgba(244, 63, 94, 0.28)"
        sign = "+" if ret >= 0 else ""
        items_html += (
            f'<div style="display:inline-flex;align-items:center;gap:6px;padding:0 18px;'
            f'font-family:\'JetBrains Mono\',monospace;font-size:0.82rem;color:#f1f5f9;">'
            f'<strong style="color:#ffffff;">{tid}</strong>'
            f'<span style="color:#8B98AC;font-size:0.75rem;margin-left:4px;">O:</span>'
            f'<span style="color:#cbd5e1;">{open_price}</span>'
            f'<span style="color:#8B98AC;font-size:0.75rem;margin-left:4px;">C:</span>'
            f'<span style="color:#cbd5e1;">{close_price}</span>'
            f'<span style="background:{bg};color:{color};border:1px solid {border};padding:2px 7px;'
            f'border-radius:6px;font-weight:700;margin-left:4px;">{sign}{ret:.2f}% 1M</span></div>'
        )

    ticker_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{ margin: 0; background: transparent; overflow: hidden; font-family: sans-serif; }}
    .ticker-wrap {{ width: 100%; overflow: hidden; background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 7px 0; white-space: nowrap; box-sizing: border-box; }}
    .ticker-move {{ display: inline-block; white-space: nowrap; padding-left: 100%; animation: marqueeScroll 280s linear infinite; }}
    .ticker-move:hover {{ animation-play-state: paused; }}
    @keyframes marqueeScroll {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-50%, 0, 0); }} }}
    </style>
    </head>
    <body>
    <div class="ticker-wrap"><div class="ticker-move">{items_html}{items_html}</div></div>
    </body>
    </html>
    """
    st.html(ticker_code, unsafe_allow_javascript=True)


def render_api_status_widget() -> None:
    """Renders API Connection and Key Configuration widget in the sidebar."""
    st.sidebar.markdown('<div style="margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 0.8rem;"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div style="font-size: 0.76rem; font-weight: 700; font-family: \'JetBrains Mono\', monospace; '
        'color: var(--muted); text-transform: uppercase; margin-bottom: 0.4rem;">API & Connection Settings</div>',
        unsafe_allow_html=True,
    )

    base_url = st.sidebar.text_input("API Base URL", value="http://localhost:8000", key="api_base_url_input")
    api_key = st.sidebar.text_input("API Key (Optional)", value="", type="password", key="api_key_input")

    status = check_api_server_status(base_url, api_key)
    if status["online"]:
        st.sidebar.markdown(
            f"""
            <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); padding: 8px 12px; border-radius: 8px; font-size: 0.78rem;">
                <span style="color:#10B981; font-weight:700;">🟢 Connected</span> &middot; FastAPI active<br>
                <span style="color:#8B98AC; font-family: monospace;">Uptime: {status['uptime']:.1f}s</span> &middot; <a href="{base_url}/docs" target="_blank" style="color:#10B981;">Docs ↗</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"""
            <div style="background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); padding: 8px 12px; border-radius: 8px; font-size: 0.76rem;">
                <span style="color:#F59E0B; font-weight:700;">🟡 Standalone Mode</span> (Direct DB)<br>
                <span style="color:#cbd5e1;">API URL: {base_url}</span><br>
                <span style="color:#8B98AC; font-size:0.7rem;">To start backend server:<br><code style="color:#10B981;">uvicorn src.api.main:app --port 8000</code></span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero(eyebrow: str, title_lines: list[str], subtitle: str, stats: list[tuple] | None = None) -> None:
    title_html = "<br>".join(title_lines)
    stats_html = ""
    if stats:
        cells = "".join(
            f'<div style="text-align:left;"><div style="font-family:{FONT_MONO};font-size:0.68rem;'
            f'color:#8B98AC;text-transform:uppercase;letter-spacing:0.08em;">{label}</div>'
            f'<div style="font-family:{FONT_MONO};font-size:1.15rem;font-weight:700;color:#fff;margin-top:2px;">{val}</div></div>'
            for label, val in stats
        )
        stats_html = f'<div style="display:flex;gap:2.2rem;margin-top:18px;flex-wrap:wrap;">{cells}</div>'

    st.html(
        f"""
        <div id="market-hero">
          <canvas id="market-canvas"></canvas>
          <div class="hero-vignette"></div>
          <div class="hero-copy">
            <div class="hero-title">{title_html}</div>
            <div class="hero-subtitle">{subtitle}</div>
            {stats_html}
          </div>
        </div>
        <style>
          html, body {{ margin:0; background:transparent; overflow:hidden; font-family:'Plus Jakarta Sans', sans-serif; }}
          #market-hero {{
            position:relative;
            height:340px;
            width:100%;
            overflow:hidden;
            border-radius:16px;
            border:1px solid rgba(16,185,129,0.22);
            background:
              radial-gradient(ellipse 80% 60% at 50% 0%, rgba(16,185,129,0.14), transparent 65%),
              linear-gradient(135deg, #080B11 0%, #0a1420 45%, #080B11 100%);
            box-shadow: 0 10px 40px -15px rgba(16,185,129,0.15);
          }}
          #market-canvas {{ position:absolute; inset:0; width:100%; height:100%; }}
          .hero-vignette {{
            position:absolute; inset:0;
            background: linear-gradient(90deg, rgba(8,11,17,0.88) 0%, rgba(8,11,17,0.4) 50%, rgba(8,11,17,0.78) 100%);
            pointer-events:none;
          }}
          .hero-copy {{
            position:absolute;
            left:36px;
            top:50%;
            transform:translateY(-50%);
            width:min(760px, calc(100% - 72px));
            pointer-events:none;
          }}
          .hero-title {{
            font-size: clamp(34px, 5.2vw, 62px);
            line-height:0.98;
            font-weight:800;
            letter-spacing:-0.03em;
            background: linear-gradient(180deg, #ffffff 0%, #cdeeff 45%, #10B981 100%);
            -webkit-background-clip:text;
            background-clip:text;
            -webkit-text-fill-color:transparent;
            text-transform:uppercase;
          }}
          .hero-subtitle {{
            margin-top:12px;
            max-width:680px;
            color:#cbd5e1;
            font: 400 14px/1.55 'Plus Jakarta Sans', sans-serif;
          }}
        </style>
        <script>
        (() => {{
          const root = document.getElementById('market-hero');
          const canvas = document.getElementById('market-canvas');
          const ctx = canvas.getContext('2d');
          let w = 0, h = 0, dpr = 1;
          let time = 0;

          function resize() {{
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            w = root.clientWidth;
            h = root.clientHeight;
            canvas.width = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          }}
          resize();
          window.addEventListener('resize', resize);

          const candles = Array.from({{ length: 42 }}, (_, i) => {{
            const base = 0.62 - i * 0.014 + Math.sin(i * 0.5) * 0.06;
            const body = 0.04 + Math.random() * 0.07;
            const up = Math.random() > 0.32;
            return {{ i, base, body, up, phase: Math.random() * 6.28 }};
          }});

          function draw() {{
            time += 0.015;
            ctx.clearRect(0, 0, w, h);

            const startX = w * 0.38;
            const step = Math.max(14, w * 0.014);
            const baseY = h * 0.72;
            const scaleY = h * 0.68;

            ctx.save();
            candles.forEach((c, idx) => {{
              const px = startX + idx * step;
              const py = baseY - (1 - c.base) * scaleY + Math.sin(time * 1.5 + c.phase) * 3;
              const bodyH = c.body * h * (0.88 + Math.sin(time + c.phase) * 0.06);
              const wickH = bodyH * 1.8;
              const up = c.up;
              const color = up ? '#10B981' : '#F43F5E';

              ctx.strokeStyle = up ? 'rgba(16,185,129,0.65)' : 'rgba(244,63,94,0.55)';
              ctx.lineWidth = 1.2;
              ctx.beginPath();
              ctx.moveTo(px, py - wickH * 0.5);
              ctx.lineTo(px, py + wickH * 0.5);
              ctx.stroke();

              const width = Math.max(6, step * 0.48);
              const y = py - bodyH * 0.5;
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.roundRect(px - width / 2, y, width, Math.max(8, bodyH), 3);
              ctx.fill();
            }});
            ctx.restore();

            requestAnimationFrame(draw);
          }}
          draw();
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def render_monthly_update_summary(summary: dict) -> None:
    """Renders an animated monthly update summary banner."""
    if not summary:
        return

    as_of = summary.get("as_of_date", "")
    avg_ret = summary.get("avg_1m_return", 0.0)
    pct_adv = summary.get("pct_advancing", 0.0)
    data_source_badge = "🟢 Live Market Feed" if summary.get("is_live_data") else "⚡ Dynamic Auto-Sync Engine"

    ret_cls = "badge-pos" if avg_ret >= 0 else "badge-neg"
    sign = "+" if avg_ret >= 0 else ""

    st.markdown(
        f"""
        <div style="background: var(--panel);
                    border: 1px solid rgba(16, 185, 129, 0.22); border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; backdrop-filter: blur(14px);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.2rem; color: #ffffff;">📅 Monthly Market Stats & Recent Updates</h3>
                    <div style="font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); margin-top: 0.2rem;">
                        As of {as_of} &middot; <span style="color:var(--accent);">{data_source_badge}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.8rem;">
                    <div style="text-align: right;">
                        <div style="font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); text-transform: uppercase;">Average 1M Return</div>
                        <div class="{ret_cls}" style="font-size: 1.05rem; margin-top: 2px;">{sign}{avg_ret:.2f}%</div>
                    </div>
                    <div style="text-align: right; margin-left: 1rem;">
                        <div style="font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); text-transform: uppercase;">Advancing Stocks</div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{pct_adv}%</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )