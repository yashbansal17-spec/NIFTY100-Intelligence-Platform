from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.utils import db
from dashboard.utils import theme as theme_mod
from dashboard.utils import live_data


def mover_card_html(row: pd.Series, positive: bool) -> str:
    color = theme_mod.ACCENT_2 if positive else theme_mod.NEGATIVE
    border = "rgba(16, 185, 129, 0.28)" if positive else "rgba(244, 63, 94, 0.28)"
    bg = "rgba(16, 185, 129, 0.08)" if positive else "rgba(244, 63, 94, 0.08)"
    sign = "+" if row["return_1m_pct"] >= 0 else ""
    return f"""
    <div style="background:{bg};border-left:4px solid {color};border-radius:10px;padding:0.75rem 1rem;
                margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;
                border-top:1px solid {border};border-right:1px solid {border};border-bottom:1px solid {border};">
        <div>
            <b style="color:#f8fafc;font-size:1rem;font-family:{theme_mod.FONT_MONO};">{row['company_id']}</b>
            <div style="color:#8B98AC;font-size:0.8rem;">{row['company_name']}</div>
        </div>
        <div style="text-align:right;">
            <span style="color:#f8fafc;font-weight:700;font-size:1rem;font-family:{theme_mod.FONT_MONO};">₹{row['current_price']:,.2f}</span>
            <div style="color:{color};font-weight:700;font-size:0.85rem;font-family:{theme_mod.FONT_MONO};">{sign}{row['return_1m_pct']:.2f}% 1M</div>
        </div>
    </div>
    """


def render() -> None:
    live_df = live_data.get_cached_live_market()
    monthly_summary = live_data.get_cached_monthly_summary()
    companies = db.get_companies()

    if not live_df.empty and not companies.empty:
        if "broad_sector" not in live_df.columns and "company_id" in live_df.columns:
            sec_map = dict(zip(companies["company_id"], companies["broad_sector"]))
            live_df["broad_sector"] = live_df["company_id"].map(sec_map).fillna("Unassigned")

    theme_mod.render_live_ticker(live_df)

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(8, 11, 17, 0.9) 100%);
                    border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <span style="background: rgba(16, 185, 129, 0.14); color: #10B981; font-size: 0.75rem; font-weight: 700;
                                 padding: 0.25rem 0.75rem; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;
                                 border: 1px solid rgba(16, 185, 129, 0.28); font-family: {theme_mod.FONT_MONO};">
                        Real-Time &amp; Daily yfinance Engine
                    </span>
                    <h1 style="margin: 0.5rem 0 0.25rem 0;">Daily Market Dashboard</h1>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        is_live_status = monthly_summary.get("is_live_data", True)
        as_of = monthly_summary.get("as_of_date", datetime.now().strftime("%Y-%m-%d %H:%M"))
        status_color = theme_mod.ACCENT_2 if is_live_status else theme_mod.WARNING
        status_text = "LIVE Yahoo Finance Feed Active" if is_live_status else "Cached / Fallback Mode"

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.75rem; background: rgba(15, 23, 42, 0.6); padding: 0.6rem 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);">
                <span style="height: 10px; width: 10px; background-color: {status_color}; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px {status_color};"></span>
                <span style="color: #e2e8f0; font-size: 0.875rem; font-weight: 600;">{status_text}</span>
                <span style="color: #64748b; font-size: 0.85rem;">|</span>
                <span style="color: #8B98AC; font-size: 0.85rem;">Last Updated: <b>{as_of}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_col2:
        if st.button("Fetch Data", width="stretch", type="primary"):
            with st.spinner("Downloading fresh quotes & history from Yahoo Finance..."):
                live_data.get_cached_live_market(force_refresh=True)
                st.cache_data.clear()
                st.toast("Fetched latest daily market quotes from yfinance!", icon="✅")
                st.rerun()

    st.markdown('<div style="margin-bottom: 1.25rem;"></div>', unsafe_allow_html=True)

    avg_1m = monthly_summary.get("avg_1m_return", 0.0)
    adv_pct = monthly_summary.get("pct_advancing", 0.0)
    near_hi_cnt = len(monthly_summary.get("near_52w_high", []))
    near_lo_cnt = len(monthly_summary.get("near_52w_low", []))

    top_g = monthly_summary.get("top_gainers")
    g_text = "N/A"
    g_delta = None
    if top_g is not None and not top_g.empty:
        g_ticker = top_g.iloc[0]["company_id"]
        g_ret = top_g.iloc[0]["return_1m_pct"]
        g_text = g_ticker
        g_delta = f"{g_ret:+.1f}% 1M Top Performer"

    theme_mod.render_kpi_row(
        [
            {"title": "1M Market Average Return", "value": f"{avg_1m:+.2f}%", "delta": f"{adv_pct:.1f}% Advancing", "positive": avg_1m >= 0},
            {"title": "Stocks Near 52W High (≤5%)", "value": f"{near_hi_cnt}", "delta": "Bullish Momentum", "positive": True},
            {"title": "Stocks Near 52W Low (≤5%)", "value": f"{near_lo_cnt}", "delta": "-Value Alert" if near_lo_cnt > 0 else "Low Risk", "positive": False if near_lo_cnt > 0 else True},
            {"title": "Top Monthly Gainer", "value": g_text, "delta": g_delta, "positive": True if g_delta else None},
        ]
    )

    st.markdown('<div class="clean-rule"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([" Market Movers & Breakouts", "Single Stock yfinance Chart", "Complete NIFTY 100 Screener"])

    # ---------------- TAB 1: MARKET MOVERS & BREAKOUTS ----------------
    with tab1:
        st.markdown("### Market Gainers & Losers (1-Month Return)")
        col_g, col_l = st.columns(2, gap="medium")

        with col_g:
            st.markdown("#### 🟢 Top 5 Gainers")
            top_gainers_df = live_df.sort_values("return_1m_pct", ascending=False).head(5)
            for _, r in top_gainers_df.iterrows():
                st.markdown(mover_card_html(r, positive=True), unsafe_allow_html=True)

        with col_l:
            st.markdown("#### 🔴 Top 5 Losers")
            top_losers_df = live_df.sort_values("return_1m_pct", ascending=True).head(5)
            for _, r in top_losers_df.iterrows():
                st.markdown(mover_card_html(r, positive=False), unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown("### 52-Week Breakout & Value Candidates")
        b1, b2 = st.columns(2, gap="medium")

        with b1:
            st.markdown("#### Near 52-Week High (≤ 5% Distance)")
            near_hi = live_df[live_df["pct_from_52w_high"] >= -5.0].sort_values("pct_from_52w_high", ascending=False)
            if not near_hi.empty:
                display_hi = near_hi[["company_id", "company_name", "current_price", "high_52w", "pct_from_52w_high"]].head(8)
                display_hi.columns = ["Ticker", "Company", "Current (₹)", "52W High (₹)", "% From 52W High"]
                st.dataframe(
                    display_hi,
                    use_container_width=True,
                    height=280,
                    hide_index=True,
                    column_config={
                        "Current (₹)": st.column_config.NumberColumn("Current (₹)", format="₹%.2f"),
                        "52W High (₹)": st.column_config.NumberColumn("52W High (₹)", format="₹%.2f"),
                        "% From 52W High": st.column_config.NumberColumn("% From 52W High", format="%+.2f%%"),
                    },
                )
            else:
                st.info("No stocks currently within 5% of 52-week high.")

        with b2:
            st.markdown("#### Near 52-Week Low (≤ 5% Distance)")
            near_lo = live_df[live_df["pct_from_52w_low"] <= 5.0].sort_values("pct_from_52w_low", ascending=True)
            if not near_lo.empty:
                display_lo = near_lo[["company_id", "company_name", "current_price", "low_52w", "pct_from_52w_low"]].head(8)
                display_lo.columns = ["Ticker", "Company", "Current (₹)", "52W Low (₹)", "% From 52W Low"]
                st.dataframe(
                    display_lo,
                    use_container_width=True,
                    height=280,
                    hide_index=True,
                    column_config={
                        "Current (₹)": st.column_config.NumberColumn("Current (₹)", format="₹%.2f"),
                        "52W Low (₹)": st.column_config.NumberColumn("52W Low (₹)", format="₹%.2f"),
                        "% From 52W Low": st.column_config.NumberColumn("% From 52W Low", format="%+.2f%%"),
                    },
                )
            else:
                st.info("No stocks currently within 5% of 52-week low.")

    # ---------------- TAB 2: SINGLE STOCK YFINANCE DEEP DIVE ----------------
    with tab2:
        st.markdown("###  Stock Chart & Interactive yfinance Price History")
        company_list = companies["company_id"].tolist() if not companies.empty else live_df["company_id"].tolist()

        c_sel1, c_sel2 = st.columns([2, 1])
        with c_sel1:
            selected_stock = st.selectbox(
                "Select Company Ticker:",
                options=company_list,
                index=0 if company_list else None,
            )
        with c_sel2:
            period_choice = st.radio(
                "Timeframe:",
                options=["1mo", "6mo", "1y", "5y"],
                index=2,
                horizontal=True,
            )

        if selected_stock:
            stock_row = live_df[live_df["company_id"] == selected_stock]
            if not stock_row.empty:
                s = stock_row.iloc[0]
                cname = s["company_name"]
                cprice = s["current_price"]
                chg_rs = s["day_change_rs"]
                chg_pct = s["day_change_pct"]
                oprice = s["open_price"]
                hprice = s["high_price"]
                lprice = s["low_price"]
                hi_52 = s["high_52w"]
                lo_52 = s["low_52w"]
                ret_1m = s["return_1m_pct"]
                ret_1y = s["return_1y_pct"]

                chg_color = theme_mod.ACCENT_2 if chg_rs >= 0 else theme_mod.NEGATIVE
                chg_sign = "+" if chg_rs >= 0 else ""

                rbar_html = theme_mod.range_bar(cprice, lo_52, hi_52, f"52W Low ₹{lo_52:,.0f}", f"52W High ₹{hi_52:,.0f}")
                st.markdown(
                    f'<div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; backdrop-filter: blur(12px);">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
                    f'<div>'
                    f'<h3 style="color: #f8fafc; margin: 0; font-size: 1.4rem;">{selected_stock} &middot; <span style="color: #8B98AC; font-weight: 400;">{cname}</span></h3>'
                    f'<div style="color: #64748b; font-size: 0.85rem; margin-top: 0.2rem;">NSE Ticker: <b>{selected_stock}.NS</b></div>'
                    f'</div>'
                    f'<div style="text-align: right;">'
                    f'<div style="font-size: 1.8rem; font-weight: 800; color: #f8fafc; font-family:{theme_mod.FONT_MONO};">₹{cprice:,.2f}</div>'
                    f'<div style="color: {chg_color}; font-size: 1rem; font-weight: 700; font-family:{theme_mod.FONT_MONO};">'
                    f'{chg_sign}₹{chg_rs:,.2f} ({chg_sign}{chg_pct:.2f}%) Today'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                    f'<div style="margin-top:14px;">{rbar_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                sc1.metric("Open Price", f"₹{oprice:,.2f}")
                sc2.metric("Day Range", f"₹{lprice:,.2f} - ₹{hprice:,.2f}")
                sc3.metric("52W Range", f"₹{lo_52:,.2f} - ₹{hi_52:,.2f}")
                sc4.metric("1-Month Return", f"{ret_1m:+.2f}%")
                sc5.metric("1-Year Return", f"{ret_1y:+.2f}%")

                chart_df = live_data.get_company_chart_data(selected_stock, period=period_choice)

                if not chart_df.empty and "Close" in chart_df.columns:
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.08,
                        row_heights=[0.75, 0.25],
                        subplot_titles=(f"{selected_stock} Price History ({period_choice.upper()})", "Trading Volume"),
                    )

                    if "Open" in chart_df.columns and "High" in chart_df.columns and "Low" in chart_df.columns:
                        fig.add_trace(
                            go.Candlestick(
                                x=chart_df["Date"],
                                open=chart_df["Open"],
                                high=chart_df["High"],
                                low=chart_df["Low"],
                                close=chart_df["Close"],
                                name="Price (OHLC)",
                                increasing_line_color=theme_mod.ACCENT_2,
                                decreasing_line_color=theme_mod.NEGATIVE,
                            ),
                            row=1, col=1,
                        )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df["Date"],
                                y=chart_df["Close"],
                                mode="lines",
                                name="Close Price",
                                line=dict(color=theme_mod.ACCENT, width=2),
                            ),
                            row=1, col=1,
                        )

                    if len(chart_df) >= 20:
                        chart_df["SMA20"] = chart_df["Close"].rolling(20).mean()
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df["Date"],
                                y=chart_df["SMA20"],
                                mode="lines",
                                name="20-Day SMA",
                                line=dict(color=theme_mod.WARNING, width=1.5, dash="dash"),
                            ),
                            row=1, col=1,
                        )

                    if "Volume" in chart_df.columns:
                        colors = [
                            theme_mod.ACCENT_2 if c >= o else theme_mod.NEGATIVE
                            for c, o in zip(chart_df["Close"], chart_df.get("Open", chart_df["Close"]))
                        ]
                        fig.add_trace(
                            go.Bar(
                                x=chart_df["Date"],
                                y=chart_df["Volume"],
                                name="Volume",
                                marker_color=colors,
                                opacity=0.7,
                                yaxis="y2",
                            ),
                            row=2, col=1,
                        )

                    theme_mod.style_plotly_chart(fig, height=550)
                    fig.update_layout(xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Could not load historical chart data for {selected_stock}. Click 'Fetch Daily Data' above to refresh.")

    # ---------------- TAB 3: COMPLETE NIFTY 100 SCREENER ----------------
    with tab3:
        st.markdown("###  Complete NIFTY 100 Daily Market Data Table")

        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1.5])
        with f_col1:
            search_query = st.text_input("🔍 Search Company / Ticker:", placeholder="e.g. RELIANCE, TCS, HDFC...")
        with f_col2:
            sectors_available = ["All Sectors"] + sorted(list(live_df["broad_sector"].unique())) if "broad_sector" in live_df.columns else ["All Sectors"]
            selected_sec = st.selectbox("Filter Sector:", options=sectors_available)
        with f_col3:
            filter_cat = st.selectbox("Category Filter:", options=["All Stocks", "Gainers Today (>0%)", "Losers Today (<0%)", "Near 52W High (≤5%)", "Near 52W Low (≤5%)"])

        filtered_df = live_df.copy()
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["company_id"].str.lower().str.contains(sq) |
                filtered_df["company_name"].str.lower().str.contains(sq)
            ]

        if selected_sec != "All Sectors" and "broad_sector" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["broad_sector"] == selected_sec]

        if filter_cat == "Gainers Today (>0%)":
            filtered_df = filtered_df[filtered_df["day_change_pct"] > 0]
        elif filter_cat == "Losers Today (<0%)":
            filtered_df = filtered_df[filtered_df["day_change_pct"] < 0]
        elif filter_cat == "Near 52W High (≤5%)":
            filtered_df = filtered_df[filtered_df["pct_from_52w_high"] >= -5.0]
        elif filter_cat == "Near 52W Low (≤5%)":
            filtered_df = filtered_df[filtered_df["pct_from_52w_low"] <= 5.0]

        st.caption(f"Showing **{len(filtered_df)}** of **{len(live_df)}** companies")

        disp_cols = [
            "company_id", "company_name", "current_price", "day_change_rs", "day_change_pct",
            "open_price", "high_price", "low_price", "high_52w", "low_52w",
            "return_1m_pct", "return_1y_pct", "volume"
        ]
        if "broad_sector" in filtered_df.columns:
            disp_cols.insert(2, "broad_sector")

        existing_cols = [c for c in disp_cols if c in filtered_df.columns]
        view_table = filtered_df[existing_cols].copy()

        col_rename = {
            "company_id": "Ticker",
            "company_name": "Company Name",
            "broad_sector": "Sector",
            "current_price": "Price (₹)",
            "day_change_rs": "Change (₹)",
            "day_change_pct": "Change (%)",
            "open_price": "Open (₹)",
            "high_price": "Day High (₹)",
            "low_price": "Day Low (₹)",
            "high_52w": "52W High (₹)",
            "low_52w": "52W Low (₹)",
            "return_1m_pct": "1M Return (%)",
            "return_1y_pct": "1Y Return (%)",
            "volume": "Volume",
        }
        view_table.rename(columns=col_rename, inplace=True)

        st.dataframe(
            view_table,
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config={
                "Price (₹)": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "Change (₹)": st.column_config.NumberColumn("Change (₹)", format="%+.2f"),
                "Change (%)": st.column_config.NumberColumn("Change (%)", format="%+.2f%%"),
                "Open (₹)": st.column_config.NumberColumn("Open (₹)", format="₹%.2f"),
                "Day High (₹)": st.column_config.NumberColumn("Day High (₹)", format="₹%.2f"),
                "Day Low (₹)": st.column_config.NumberColumn("Day Low (₹)", format="₹%.2f"),
                "52W High (₹)": st.column_config.NumberColumn("52W High (₹)", format="₹%.2f"),
                "52W Low (₹)": st.column_config.NumberColumn("52W Low (₹)", format="₹%.2f"),
                "1M Return (%)": st.column_config.NumberColumn("1M Return (%)", format="%+.2f%%"),
                "1Y Return (%)": st.column_config.NumberColumn("1Y Return (%)", format="%+.2f%%"),
                "Volume": st.column_config.NumberColumn("Volume", format="%d"),
            },
        )

        csv_data = view_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Daily Market Data (CSV)",
            data=csv_data,
            file_name=f"NIFTY100_Daily_Market_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    render()
