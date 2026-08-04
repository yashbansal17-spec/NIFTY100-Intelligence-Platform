"""Shared visual theme and animated UI components for NIFTY100 Intelligence Platform."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils.live_data import check_api_server_status

BG = "#05070a"
PANEL = "#090d14"
INK = "#f6f8fb"
MUTED = "#94a3b8"
LINE = "rgba(148, 163, 184, 0.16)"
ACCENT = "#00e676"
NEGATIVE = "#ff4d5e"


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

        :root {{
            --bg: {BG};
            --panel: {PANEL};
            --ink: {INK};
            --muted: {MUTED};
            --line: {LINE};
            --accent: {ACCENT};
            --negative: {NEGATIVE};
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: transparent !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        .stApp {{
            background:
                radial-gradient(ellipse 90% 60% at 50% -12%, rgba(0,230,118,0.12), transparent 65%),
                radial-gradient(ellipse 75% 50% at 100% 100%, rgba(0,120,90,0.09), transparent 65%),
                radial-gradient(ellipse 50% 40% at 0% 50%, rgba(15,23,42,0.6), transparent 70%),
                var(--bg) !important;
            background-attachment: fixed !important;
        }}

        [data-testid="stHeader"] {{ background: transparent !important; }}

        .block-container {{
            max-width: 1520px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent); }}

        /* Smooth CSS Keyframe Animations */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translate3d(0, 16px, 0); }}
            to {{ opacity: 1; transform: translate3d(0, 0, 0); }}
        }}

        @keyframes pulseGlow {{
            0% {{ box-shadow: 0 0 0 0 rgba(0,230,118,0.4); }}
            70% {{ box-shadow: 0 0 0 8px rgba(0,230,118,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(0,230,118,0); }}
        }}

        /* Dynamic Typography */
        h1, h2, h3, h4 {{
            font-family: 'Inter', -apple-system, sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
        }}

        h1, [data-testid="stMarkdownContainer"] h1 {{
            font-size: 2.6rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0.4rem !important;
            background: linear-gradient(180deg, #ffffff 0%, #b8ffd3 50%, var(--accent) 100%) !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 30px rgba(0, 230, 118, 0.2);
            animation: fadeInUp 0.5s ease-out forwards;
        }}

        /* Sidebar Styling & Glassmorphism */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(10, 14, 22, 0.95) 0%, rgba(5, 7, 10, 0.98) 100%) !important;
            border-right: 1px solid var(--line) !important;
            backdrop-filter: blur(16px);
        }}

        .brand-block {{
            padding: 0.6rem 0 1.2rem 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }}

        .brand-title {{
            font-size: 1.6rem;
            font-weight: 900;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
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
            background: var(--accent) !important;
            box-shadow: 0 0 10px var(--accent);
            display: inline-block;
            animation: pulseGlow 2s infinite;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label {{
            padding: 0.65rem 0.85rem !important;
            border-radius: 10px !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            font-weight: 500 !important;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(0, 230, 118, 0.08) !important;
            border-left: 3px solid var(--accent) !important;
            transform: translate3d(3px, 0, 0);
        }}

        /* Card Glassmorphism & Hover Micro-Animations */
        .section-card, [data-testid="stMetric"], div[data-testid="stDataFrame"],
        .stPlotlyChart, [data-testid="stExpander"],
        div[data-baseweb="select"] > div,
        .stTextInput input, .stNumberInput input {{
            background: rgba(9, 13, 20, 0.75) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid var(--line) !important;
            border-radius: 12px !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            will-change: transform, box-shadow, border-color;
        }}

        [data-testid="stMetric"]:hover, .section-card:hover, .stPlotlyChart:hover {{
            border-color: rgba(0, 230, 118, 0.35) !important;
            box-shadow: 0 8px 30px -10px rgba(0, 230, 118, 0.2) !important;
            transform: translate3d(0, -3px, 0) !important;
        }}

        [data-testid="stMetric"] {{
            padding: 1.1rem 1.2rem !important;
            min-height: 115px;
        }}

        [data-testid="stMetricLabel"] {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.74rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            color: var(--muted) !important;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            letter-spacing: -0.02em !important;
        }}

        /* Sleek Button Interactions */
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button,
        .stButton > button,
        .stDownloadButton > button {{
            background: linear-gradient(180deg, #0d131f 0%, #080c14 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(0, 230, 118, 0.3) !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.2rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            font-size: 0.8rem !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}

        div[data-testid="stButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover,
        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            background: linear-gradient(180deg, rgba(0,230,118,0.2) 0%, rgba(0,180,90,0.25) 100%) !important;
            border-color: var(--accent) !important;
            box-shadow: 0 6px 20px rgba(0, 230, 118, 0.3) !important;
            transform: translate3d(0, -2px, 0) !important;
        }}

        /* Metric Pill Badges */
        .badge-pos {{
            background: rgba(0, 230, 118, 0.14);
            color: var(--accent);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid rgba(0, 230, 118, 0.25);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .badge-neg {{
            background: rgba(255, 77, 94, 0.14);
            color: var(--negative);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid rgba(255, 77, 94, 0.25);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .clean-rule {{
            height: 1px;
            background: linear-gradient(90deg, var(--line), rgba(0,230,118,0.2), transparent);
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

            document.querySelectorAll('[data-testid="stMetric"], .section-card, .stPlotlyChart').forEach(el => {
                el.style.opacity = '0.92';
                el.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
                observer.observe(el);
            });
        });
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <h1>{title}</h1>
        <p style="color:var(--muted);font-size:1.02rem;line-height:1.55;margin-top:0.2rem;margin-bottom:1rem;max-width:900px;">
            {subtitle}
        </p>
        <div class="clean-rule"></div>
        """,
        unsafe_allow_html=True,
    )


def render_live_ticker(df: pd.DataFrame) -> None:
    """Renders a clean, animated horizontal marquee ticker using iframe component."""
    if df.empty:
        return

    items_html = ""
    # Render all companies for a continuous scroller of the universe
    for _, row in df.iterrows():
        tid = row["company_id"]
        close_price = f"₹{row['current_price']:,.2f}"
        open_price = f"₹{row['open_price']:,.2f}" if "open_price" in row else close_price
        ret = row["return_1m_pct"]
        color = "#00e676" if ret >= 0 else "#ff4d5e"
        bg = "rgba(0, 230, 118, 0.12)" if ret >= 0 else "rgba(255, 77, 94, 0.12)"
        border = "rgba(0, 230, 118, 0.25)" if ret >= 0 else "rgba(255, 77, 94, 0.25)"
        sign = "+" if ret >= 0 else ""
        items_html += f"""<div style="display:inline-flex;align-items:center;gap:6px;padding:0 18px;font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:#f1f5f9;"><strong style="color:#ffffff;">{tid}</strong><span style="color:#94a3b8;font-size:0.75rem;margin-left:4px;">O:</span><span style="color:#cbd5e1;">{open_price}</span><span style="color:#94a3b8;font-size:0.75rem;margin-left:4px;">C:</span><span style="color:#cbd5e1;">{close_price}</span><span style="background:{bg};color:{color};border:1px solid {border};padding:2px 7px;border-radius:6px;font-weight:700;margin-left:4px;">{sign}{ret:.2f}% 1M</span></div>"""

    ticker_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{ margin: 0; background: transparent; overflow: hidden; font-family: sans-serif; }}
    .ticker-wrap {{ width: 100%; overflow: hidden; background: rgba(9, 13, 20, 0.85); border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 10px; padding: 7px 0; white-space: nowrap; box-sizing: border-box; }}
    .ticker-move {{ display: inline-block; white-space: nowrap; padding-left: 100%; animation: marqueeScroll 90s linear infinite; }}
    .ticker-move:hover {{ animation-play-state: paused; }}
    @keyframes marqueeScroll {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-50%, 0, 0); }} }}
    </style>
    </head>
    <body>
    <div class="ticker-wrap"><div class="ticker-move">{items_html}{items_html}</div></div>
    </body>
    </html>
    """
    components.html(ticker_code, height=46)


def render_api_status_widget() -> None:
    """Renders API Connection and Key Configuration widget in the sidebar."""
    st.sidebar.markdown('<div style="margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 0.8rem;"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size: 0.78rem; font-weight: 700; font-family: \'JetBrains Mono\', monospace; color: var(--muted); text-transform: uppercase; margin-bottom: 0.4rem;">API & Connection Settings</div>', unsafe_allow_html=True)

    base_url = st.sidebar.text_input("API Base URL", value="http://localhost:8000", key="api_base_url_input")
    api_key = st.sidebar.text_input("API Key (Optional)", value="", type="password", key="api_key_input")

    status = check_api_server_status(base_url, api_key)
    if status["online"]:
        st.sidebar.markdown(
            f"""
            <div style="background: rgba(0,230,118,0.1); border: 1px solid rgba(0,230,118,0.3); padding: 8px 12px; border-radius: 8px; font-size: 0.78rem;">
                <span style="color:#00e676; font-weight:700;">🟢 Connected</span> &middot; FastAPI active<br>
                <span style="color:#94a3b8; font-family: monospace;">Uptime: {status['uptime']:.1f}s</span> &middot; <a href="{base_url}/docs" target="_blank" style="color:#00e676;">Docs ↗</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"""
            <div style="background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.3); padding: 8px 12px; border-radius: 8px; font-size: 0.76rem;">
                <span style="color:#eab308; font-weight:700;">🟡 Standalone Mode</span> (Direct DB)<br>
                <span style="color:#cbd5e1;">API URL: {base_url}</span><br>
                <span style="color:#94a3b8; font-size:0.7rem;">To start backend server:<br><code style="color:#00e676;">uvicorn src.api.main:app --port 8000</code></span>
            </div>
            """,
            unsafe_allow_html=True,
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
        <div style="background: linear-gradient(135deg, rgba(9, 13, 20, 0.9) 0%, rgba(15, 23, 42, 0.85) 100%);
                    border: 1px solid rgba(0, 230, 118, 0.25); border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; backdrop-filter: blur(12px);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.8rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.25rem; color: #ffffff; display: flex; align-items: center; gap: 0.6rem;">
                        📅 Monthly Market Stats & Recent Updates
                    </h3>
                    <div style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); margin-top: 0.2rem;">
                        Auto-Updated for recent stats &middot; As of {as_of} &middot; <span style="color:var(--accent);">{data_source_badge}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.8rem;">
                    <div style="text-align: right;">
                        <div style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); text-transform: uppercase;">Average 1M Return</div>
                        <div class="{ret_cls}" style="font-size: 1.1rem; margin-top: 2px;">{sign}{avg_ret:.2f}%</div>
                    </div>
                    <div style="text-align: right; margin-left: 1rem;">
                        <div style="font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--muted); text-transform: uppercase;">Advancing Stocks</div>
                        <div style="font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{pct_adv}%</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(eyebrow: str, title_lines: list[str], subtitle: str, stats: list[tuple] | None = None) -> None:
    title_html = "<br>".join(title_lines)
    components.html(
        f"""
        <div id="market-hero">
          <canvas id="market-canvas"></canvas>
          <div class="hero-vignette"></div>
          <div class="hero-copy">
            <div class="hero-title">{title_html}</div>
            <div class="hero-subtitle">{subtitle}</div>
          </div>
        </div>
        <style>
          html, body {{ margin:0; background:transparent; overflow:hidden; font-family:'Inter', sans-serif; }}
          #market-hero {{
            position:relative;
            height:340px;
            width:100%;
            overflow:hidden;
            border-radius:14px;
            border:1px solid rgba(0,230,118,0.22);
            background:
              radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,230,118,0.16), transparent 65%),
              linear-gradient(135deg, #05070a 0%, #07110c 45%, #05070a 100%);
            box-shadow: 0 10px 40px -15px rgba(0,230,118,0.15);
          }}
          #market-canvas {{ position:absolute; inset:0; width:100%; height:100%; }}
          .hero-vignette {{
            position:absolute; inset:0;
            background: linear-gradient(90deg, rgba(5,7,10,0.86) 0%, rgba(5,7,10,0.35) 50%, rgba(5,7,10,0.75) 100%);
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
            font-size: clamp(36px, 5.5vw, 68px);
            line-height:0.98;
            font-weight:900;
            letter-spacing:-0.03em;
            color:#00e676;
            background: linear-gradient(180deg, #ffffff 0%, #b8ffd3 45%, #00e676 100%);
            -webkit-background-clip:text;
            background-clip:text;
            -webkit-text-fill-color:transparent;
            text-transform:uppercase;
          }}
          .hero-subtitle {{
            margin-top:14px;
            max-width:680px;
            color:#e2e8f0;
            font: 400 15px/1.55 'Inter', sans-serif;
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
            const base = 0.65 - i * 0.015 + Math.sin(i * 0.5) * 0.06;
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
              const color = up ? '#00e676' : '#ff4d5e';
              
              ctx.strokeStyle = up ? 'rgba(0,230,118,0.65)' : 'rgba(255,77,94,0.55)';
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
        height=355,
    )
