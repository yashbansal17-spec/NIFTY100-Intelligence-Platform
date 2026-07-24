"""Shared visual theme for the NIFTY100 Intelligence Platform dashboard."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


BG = "#05070a"
PANEL = "#05070a"
INK = "#f6f8fb"
MUTED = "#cbd5e1"
LINE = "rgba(148, 163, 184, 0.18)"
ACCENT = "#00e676"
NEGATIVE = "#ff4d5e"


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
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
        }}
        .stApp {{
            background:
                radial-gradient(ellipse 85% 58% at 50% -10%, rgba(0,230,118,0.10), transparent 60%),
                radial-gradient(ellipse 70% 50% at 100% 100%, rgba(0,120,90,0.08), transparent 60%),
                var(--bg) !important;
        }}
        [data-testid="stHeader"] {{ background: transparent !important; }}

        html, body, [class*="css"] {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--ink) !important;
        }}
        .block-container {{
            max-width: 1480px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}

        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: #1c2430; border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #273244; }}

        h1, h2, h3 {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 850;
            letter-spacing: 0;
            text-transform: uppercase;
        }}
        h1, [data-testid="stMarkdownContainer"] h1 {{
            font-size: 2.8rem !important;
            line-height: 1.05 !important;
            margin-bottom: 0.4rem !important;
            color: var(--accent) !important;
            background: linear-gradient(180deg, #b8ffd3 0%, var(--accent) 55%, #00a653 100%) !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 24px rgba(0, 230, 118, 0.14);
        }}
        h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4 {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            background: none !important;
        }}

        p, span, label, div, small, strong,
        .stMarkdown, [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stCaptionContainer"],
        [data-testid="stDataFrame"] *,
        div[data-baseweb="select"] *,
        .stTextInput input,
        .stNumberInput input {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0a0d13 0%, #05070a 100%);
            border-right: 1px solid var(--line);
        }}
        .brand-block {{
            padding: 0.2rem 0 1.2rem 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1.2rem;
        }}
        .brand-title {{
            font-size: 1.65rem;
            line-height: 1.05;
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-shadow: none !important;
            background: none !important;
        }}
        .brand-title span {{
            color: var(--accent) !important;
            -webkit-text-fill-color: var(--accent) !important;
            background: none !important;
            text-shadow: none !important;
        }}
        .brand-subtitle {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            font-family: Consolas, "Cascadia Mono", monospace;
            font-size: 0.72rem;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        .live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent) !important;
            box-shadow: 0 0 0 4px rgba(0,230,118,0.16);
            display: inline-block;
        }}
        .sidebar-footer {{
            position: static;
            margin-top: 2rem;
            padding-top: 1rem;
            padding-bottom: 1rem;
            border-top: 1px solid var(--line);
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            font-size: 0.78rem;
            font-family: Consolas, "Cascadia Mono", monospace;
        }}
        [data-testid="stSidebar"] * {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }}
        [data-testid="stSidebar"] .brand-title span {{
            color: var(--accent) !important;
            -webkit-text-fill-color: var(--accent) !important;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] {{ gap: 0.15rem; }}
        [data-testid="stSidebar"] label {{
            padding: 0.55rem 0.7rem;
            border-radius: 8px;
            border-left: 2px solid transparent;
        }}
        [data-testid="stSidebar"] label:hover {{
            background: rgba(0,230,118,0.10);
            border-left: 2px solid var(--accent);
        }}

        .section-card, [data-testid="stMetric"], div[data-testid="stDataFrame"],
        .stPlotlyChart, [data-testid="stExpander"],
        div[data-baseweb="select"] > div,
        .stTextInput input, .stNumberInput input {{
            background: var(--panel) !important;
            border: 1px solid var(--line) !important;
            border-radius: 10px !important;
            box-shadow: none !important;
            transform: none !important;
            will-change: auto;
        }}
        .section-card:hover, [data-testid="stMetric"]:hover, div[data-testid="stDataFrame"]:hover,
        .stPlotlyChart:hover {{
            border-color: rgba(0,230,118,0.28) !important;
            box-shadow: none !important;
        }}
        [data-testid="stMetric"] {{
            padding: 0.9rem 1rem !important;
            min-height: 112px;
        }}
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }}
        [data-testid="stMetricLabel"] {{
            font-family: Consolas, "Cascadia Mono", monospace;
            font-size: 0.72rem !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        [data-testid="stMetricValue"] {{
            font-weight: 750 !important;
        }}

        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button,
        .stButton > button,
        .stDownloadButton > button {{
            background: #05070a !important;
            background-color: #05070a !important;
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            font-weight: 750 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        div[data-testid="stButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover,
        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            background: #0b0f16 !important;
            background-color: #0b0f16 !important;
            border-color: rgba(0,230,118,0.34) !important;
            box-shadow: none !important;
        }}
        div[data-testid="stButton"] button *,
        div[data-testid="stDownloadButton"] button *,
        .stButton > button *,
        .stDownloadButton > button * {{
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }}

        .stSlider [data-baseweb="slider"] div[role="slider"] {{
            background: var(--accent) !important;
            box-shadow: 0 0 0 4px rgba(0,230,118,0.18);
        }}
        .stSlider [data-baseweb="slider"] > div > div {{
            background: var(--accent) !important;
        }}
        div[data-baseweb="select"] > div:focus-within,
        .stTextInput input:focus,
        .stNumberInput input:focus {{
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 2px rgba(0,230,118,0.18) !important;
        }}

        .clean-rule {{
            height: 1px;
            background: linear-gradient(90deg, var(--line), transparent);
            margin: 1.1rem 0 1.4rem 0;
        }}
        .mf-pos {{ color: var(--accent) !important; font-weight: 600; }}
        .mf-neg {{ color: var(--negative) !important; font-weight: 600; }}

        /* Final accent overrides requested: only page titles and the sidebar "100". */
        h1,
        section.main h1,
        .main h1,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stMarkdownContainer"] h1 {{
            color: var(--accent) !important;
            background: linear-gradient(180deg, #b8ffd3 0%, var(--accent) 55%, #00a653 100%) !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 24px rgba(0, 230, 118, 0.14) !important;
        }}
        [data-testid="stSidebar"] .brand-title span,
        .brand-title span {{
            color: var(--accent) !important;
            -webkit-text-fill-color: var(--accent) !important;
            background: none !important;
            text-shadow: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_motion_fx() -> None:
    return


def render_page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <h1>{title}</h1>
        <p style="color:var(--ink);font-size:1rem;line-height:1.55;margin-top:0.15rem;margin-bottom:1.1rem;">
            {subtitle}
        </p>
        <div class="clean-rule"></div>
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
          <div id="market-tip"></div>
        </div>
        <style>
          html, body {{ margin:0; background:transparent; overflow:hidden; }}
          #market-hero {{
            position:relative;
            height:430px;
            width:100%;
            overflow:hidden;
            border-radius:14px;
            border:1px solid rgba(148,163,184,0.18);
            background:
              radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,230,118,0.14), transparent 62%),
              linear-gradient(135deg, #05070a 0%, #07110c 45%, #05070a 100%);
            box-shadow: inset 0 0 80px rgba(0,230,118,0.05);
            cursor: crosshair;
          }}
          #market-canvas {{ position:absolute; inset:0; width:100%; height:100%; }}
          .hero-vignette {{
            position:absolute; inset:0;
            background: linear-gradient(90deg, rgba(5,7,10,0.84) 0%, rgba(5,7,10,0.38) 48%, rgba(5,7,10,0.72) 100%);
            pointer-events:none;
          }}
          .hero-copy {{
            position:absolute;
            left:44px;
            top:50%;
            transform:translateY(-50%);
            width:min(720px, calc(100% - 88px));
            pointer-events:none;
          }}
          .hero-title {{
            font-family:'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: clamp(44px, 7vw, 82px);
            line-height:0.98;
            font-weight:900;
            letter-spacing:0;
            color:#00e676;
            background: linear-gradient(180deg, #b8ffd3 0%, #00e676 55%, #00a653 100%);
            -webkit-background-clip:text;
            background-clip:text;
            -webkit-text-fill-color:transparent;
            text-transform:uppercase;
            text-shadow:0 24px 60px rgba(0,0,0,0.55);
          }}
          .hero-subtitle {{
            margin-top:18px;
            max-width:660px;
            color:#f6f8fb;
            font: 500 16px/1.55 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
          }}
          #market-tip {{
            position:absolute;
            display:none;
            min-width:132px;
            padding:9px 11px;
            border-radius:8px;
            border:1px solid rgba(0,230,118,0.32);
            background:rgba(8,12,18,0.9);
            color:#f8fafc;
            font:12px/1.4 Consolas, 'Cascadia Mono', monospace;
            box-shadow:0 18px 42px rgba(0,0,0,0.36);
            pointer-events:none;
            white-space:nowrap;
          }}
        </style>
        <script>
        (() => {{
          const root = document.getElementById('market-hero');
          const canvas = document.getElementById('market-canvas');
          const tip = document.getElementById('market-tip');
          const ctx = canvas.getContext('2d');
          let w = 0, h = 0, dpr = 1;
          let mouse = {{ x: 0.64, y: 0.42, active: false }};
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

          root.addEventListener('mousemove', (event) => {{
            const rect = root.getBoundingClientRect();
            mouse.x = (event.clientX - rect.left) / rect.width;
            mouse.y = (event.clientY - rect.top) / rect.height;
            mouse.active = true;
          }});
          root.addEventListener('mouseleave', () => {{
            mouse.active = false;
            tip.style.display = 'none';
          }});

          const candles = Array.from({{ length: 46 }}, (_, i) => {{
            const drift = i * 0.018;
            const base = 0.68 - drift + Math.sin(i * 0.62) * 0.05;
            const body = 0.038 + Math.random() * 0.08;
            const up = i < 7 ? Math.random() > 0.45 : Math.random() > 0.27;
            return {{ i, base, body, up, phase: Math.random() * 6.28 }};
          }});

          function project(x, y, z) {{
            const tiltX = (mouse.x - 0.5) * 26;
            const tiltY = (mouse.y - 0.5) * 16;
            return {{
              x: x + z * tiltX,
              y: y + z * tiltY - z * 24,
              s: 1 + z * 0.11,
            }};
          }}

          function drawGrid() {{
            ctx.save();
            ctx.strokeStyle = 'rgba(148,163,184,0.06)';
            ctx.lineWidth = 1;
            const offsetX = (mouse.x - 0.5) * 22;
            const offsetY = (mouse.y - 0.5) * 14;
            for (let x = -80; x < w + 120; x += 58) {{
              ctx.beginPath();
              ctx.moveTo(x + offsetX, 0);
              ctx.lineTo(x + offsetX + 80, h);
              ctx.stroke();
            }}
            for (let y = 40; y < h; y += 52) {{
              ctx.beginPath();
              ctx.moveTo(0, y + offsetY);
              ctx.lineTo(w, y + offsetY);
              ctx.stroke();
            }}
            ctx.restore();
          }}

          function draw() {{
            time += 0.012;
            ctx.clearRect(0, 0, w, h);
            drawGrid();

            let nearest = null;
            let nearestDist = Infinity;
            const startX = w * 0.37;
            const step = Math.max(13, w * 0.013);
            const baseY = h * 0.74;
            const scaleY = h * 0.74;

            ctx.save();
            ctx.shadowBlur = 18;
            candles.forEach((c, idx) => {{
              const z = idx / candles.length;
              const px = startX + idx * step + Math.sin(time + c.phase) * 1.2;
              const py = baseY - (1 - c.base) * scaleY + Math.sin(time * 1.4 + c.phase) * 3;
              const bodyH = c.body * h * (0.86 + Math.sin(time + c.phase) * 0.05);
              const wickH = bodyH * (1.7 + Math.sin(time * 0.7 + c.phase) * 0.18);
              const p = project(px, py, z);
              const width = Math.max(6, step * 0.48) * p.s;
              const up = c.up;
              const color = up ? '#00e676' : '#ff4d5e';
              const dim = up ? 'rgba(0,230,118,0.18)' : 'rgba(255,77,94,0.16)';
              ctx.shadowColor = dim;

              const wickTop = p.y - wickH * 0.5 * p.s;
              const wickBottom = p.y + wickH * 0.5 * p.s;
              ctx.strokeStyle = up ? 'rgba(0,230,118,0.72)' : 'rgba(255,77,94,0.58)';
              ctx.lineWidth = Math.max(1, 1.2 * p.s);
              ctx.beginPath();
              ctx.moveTo(p.x, wickTop);
              ctx.lineTo(p.x, wickBottom);
              ctx.stroke();

              const y = up ? p.y - bodyH * 0.5 * p.s : p.y - bodyH * 0.08 * p.s;
              const height = Math.max(10, bodyH * p.s);
              const grad = ctx.createLinearGradient(p.x - width / 2, y, p.x + width / 2, y + height);
              grad.addColorStop(0, up ? 'rgba(170,255,213,0.92)' : 'rgba(255,172,181,0.9)');
              grad.addColorStop(0.42, color);
              grad.addColorStop(1, up ? 'rgba(0,121,63,0.9)' : 'rgba(117,28,39,0.9)');
              ctx.fillStyle = grad;
              ctx.strokeStyle = up ? 'rgba(179,255,219,0.55)' : 'rgba(255,191,198,0.48)';
              ctx.beginPath();
              ctx.roundRect(p.x - width / 2, y, width, height, 3);
              ctx.fill();
              ctx.stroke();

              const dist = Math.hypot(mouse.x * w - p.x, mouse.y * h - (y + height / 2));
              if (dist < nearestDist) {{
                nearestDist = dist;
                nearest = {{ x: p.x, y: y, idx, up, value: 100 + idx * 2.4 + Math.sin(c.phase) * 7 }};
              }}
            }});
            ctx.restore();

            ctx.save();
            ctx.strokeStyle = 'rgba(0,230,118,0.88)';
            ctx.lineWidth = 2.2;
            ctx.shadowColor = 'rgba(0,230,118,0.5)';
            ctx.shadowBlur = 12;
            ctx.beginPath();
            candles.forEach((c, idx) => {{
              const z = idx / candles.length;
              const px = startX + idx * step;
              const py = baseY - (1 - c.base) * scaleY - c.body * h * 0.16;
              const p = project(px, py, z);
              if (idx === 0) ctx.moveTo(p.x, p.y);
              else ctx.lineTo(p.x, p.y);
            }});
            ctx.stroke();
            ctx.restore();

            if (mouse.active && nearest && nearestDist < 48) {{
              tip.style.display = 'block';
              tip.style.left = Math.min(w - 160, nearest.x + 14) + 'px';
              tip.style.top = Math.max(16, nearest.y - 18) + 'px';
              tip.innerHTML = `Candle ${{nearest.idx + 1}}<br>${{nearest.up ? 'Bullish' : 'Bearish'}}<br>Index ${{nearest.value.toFixed(2)}}`;
            }} else {{
              tip.style.display = 'none';
            }}

            requestAnimationFrame(draw);
          }}
          draw();
        }})();
        </script>
        """,
        height=450,
    )
