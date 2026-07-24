from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = PROJECT_ROOT / "pages"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import theme as theme_mod

PAGES = {
    "Home": "01_home.py",
    "Company Profile": "02_profile.py",
    "Screener": "03_screener.py",
    "Peers": "04_peers.py",
    "Trends": "05_trends.py",
    "Sectors": "06_sectors.py",
    "Capital Allocation": "07_capital.py",
    "Reports": "08_reports.py",
}

NAV_ICONS = {
    "Home": "Overview",
    "Company Profile": "Company Profile",
    "Screener": "Screener",
    "Peers": "Peer Groups",
    "Trends": "Trend Analysis",
    "Sectors": "Sector Analysis",
    "Capital Allocation": "Capital Allocation",
    "Reports": "Annual Reports",
}


def load_page(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load dashboard page: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    st.set_page_config(
        page_title="NIFTY 100 Analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme_mod.inject_theme()
    st.sidebar.markdown(
        """
        <div class="brand-block">
          <div class="brand-title">NIFTY <span>100</span></div>
          <div class="brand-title">Analytics</div>
          <div class="brand-subtitle"><span class="live-dot"></span>&nbsp; Live &middot; Intelligence Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_label = st.sidebar.radio(
        "Navigation",
        [NAV_ICONS[name] for name in PAGES.keys()],
        label_visibility="collapsed",
    )
    selected = dict(zip(NAV_ICONS.values(), NAV_ICONS.keys()))[selected_label]
    page = load_page(PAGES_DIR / PAGES[selected])
    page.render()
    st.sidebar.markdown('<div class="sidebar-footer">By - Yash Vardhan Bansal</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
