"""
Smart Home by Worklio — Energy page
Human-centered, sage green / warm white aesthetic
"""
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR  = CURRENT_DIR.parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config
from backend.db import get_energy_history, get_setting_float, get_total_energy_today, get_unacknowledged_alerts_count
from dashboard.components import apply_dark_theme, render_sidebar, C

st.set_page_config(page_title="Energy — Smart Home by Worklio", page_icon="⚡", layout="wide")

apply_dark_theme()
unack = get_unacknowledged_alerts_count()
render_sidebar(unack)

tariff    = get_setting_float("tariff_per_kwh", config.DEFAULT_TARIFF_PER_KWH)
today_str = datetime.now().strftime("%Y-%m-%d")
energy    = get_total_energy_today(today_str)
history   = get_energy_history(days=7)

st.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="font-size:1.3rem;font-weight:700;color:{C['txt']};letter-spacing:-0.02em;">Energy</div>
  <div style="font-size:0.85rem;color:{C['txt2']};">A clear picture of how your home uses power.</div>
</div>
""", unsafe_allow_html=True)

if not history:
    st.info("No energy data yet. Run the simulator to generate data.")
    st.stop()

df = pd.DataFrame(history)
df["cost"] = df["kwh"] * tariff
total_kwh = df["kwh"].sum()
total_cost = df["cost"].sum()
light_kwh = df[df["device"]=="light"]["kwh"].sum() if not df.empty else 0
fan_kwh   = df[df["device"]=="fan"]["kwh"].sum()   if not df.empty else 0

# KPI row
c1,c2,c3,c4 = st.columns(4)
kpis = [
    (c1, "This week", f"{total_kwh:.2f} kWh", f"&#8377;{total_cost:.2f} estimated cost"),
    (c2, "Today",     f"{energy['total_kwh']:.2f} kWh", f"&#8377;{energy['total_kwh']*tariff:.3f} today"),
    (c3, "Lighting",  f"{light_kwh:.2f} kWh", f"{light_kwh/total_kwh*100 if total_kwh else 0:.0f}% of total"),
    (c4, "Climate",   f"{fan_kwh:.2f} kWh",   f"{fan_kwh/total_kwh*100 if total_kwh else 0:.0f}% of total"),
]
for col, label, val, sub in kpis:
    with col:
        st.markdown(f"""
        <div style="background:{C['card']};border:1.5px solid {C['border']};border-radius:14px;padding:18px;
             margin-bottom:16px;">
          <div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;
               color:{C['txt2']};margin-bottom:8px;">{label}</div>
          <div style="font-size:1.7rem;font-weight:800;color:{C['txt']};letter-spacing:-0.03em;">{val}</div>
          <div style="font-size:0.78rem;color:{C['txt2']};margin-top:4px;">{sub}</div>
        </div>""", unsafe_allow_html=True)

# Charts
ch1, ch2 = st.columns([2, 1], gap="medium")
with ch1:
    with st.container(border=True):
        st.markdown(f"""
        <div style="margin-bottom:8px;">
          <div style="font-size:0.95rem;font-weight:700;color:{C['txt']};">Daily energy breakdown</div>
          <div style="font-size:0.8rem;color:{C['txt2']};margin-top:2px;">Which devices used the most energy each day</div>
        </div>
        """, unsafe_allow_html=True)
        fig_bar = px.bar(df.sort_values("date"), x="date", y="kwh", color="device", barmode="stack",
                         color_discrete_map={"light":C['grn2'],"fan":C['grn']},
                         labels={"kwh":"kWh","date":"","device":""})
        fig_bar.update_layout(template="none", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=280, margin=dict(l=8,r=8,t=8,b=8),
                              xaxis=dict(showgrid=False, tickfont=dict(size=10,color=C['txt2'])),
                              yaxis=dict(showgrid=True, gridcolor=C['border'], tickfont=dict(size=10,color=C['txt2']),
                                         ticksuffix=" kWh"),
                              legend=dict(orientation="h",y=-0.2,font=dict(size=11,color=C['txt2'])),
                              bargap=0.28)
        st.plotly_chart(fig_bar, use_container_width=True, key="e_bar")

with ch2:
    with st.container(border=True):
        st.markdown(f"""
        <div style="margin-bottom:8px;">
          <div style="font-size:0.95rem;font-weight:700;color:{C['txt']};">Where energy goes</div>
          <div style="font-size:0.8rem;color:{C['txt2']};margin-top:2px;">Share by device</div>
        </div>
        """, unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            values=[light_kwh, fan_kwh, max(0.001, total_kwh-light_kwh-fan_kwh)],
            labels=["Lighting","Climate","Other"],
            hole=0.62,
            marker_colors=[C['grn2'], C['grn'], C['border2']],
            textfont_size=11,
            hovertemplate="%{label}: %{value:.2f} kWh<extra></extra>"
        ))
        fig_pie.add_annotation(text=f"<b>{total_kwh:.1f}</b><br>kWh", x=0.5, y=0.5,
                               font=dict(size=14, color=C['txt']), showarrow=False)
        fig_pie.update_layout(template="none", paper_bgcolor="rgba(0,0,0,0)", height=280,
                              margin=dict(l=8,r=8,t=8,b=8),
                              showlegend=True,
                              legend=dict(orientation="h",y=-0.15,font=dict(size=11,color=C['txt2'])))
        st.plotly_chart(fig_pie, use_container_width=True, key="e_pie")

# Table
st.markdown(f"""
<div style="margin-top:16px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;">
  <div>
    <div style="font-size:0.97rem;font-weight:700;color:{C['txt']};letter-spacing:-0.02em;">Day-by-day breakdown</div>
    <div style="font-size:0.78rem;color:{C['txt2']};margin-top:2px;">Daily runtime, energy consumption and estimated cost by device</div>
  </div>
</div>
""", unsafe_allow_html=True)

df_t = df.copy().sort_values(["date", "device"], ascending=[False, True])
df_t["Device"] = df_t["device"].str.capitalize()
df_t["Hours"]  = (df_t["on_minutes"]/60).round(2)
df_t["kWh"]    = df_t["kwh"].round(3)
df_t["Cost"]   = df_t["cost"].apply(lambda c: f"&#8377;{c:.2f}")

rows_html = "".join([
    f'<tr style="border-bottom:1px solid {C["border"]};">'
    f'<td style="padding:11px 16px;font-size:0.83rem;color:{C["txt"]};font-weight:500;">{row["date"]}</td>'
    f'<td style="padding:11px 16px;"><span style="background:{C["mbg"]};color:{C["grn2"] if row["device"]=="light" else C["grn"]};padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;border:1px solid {C["border"]};">{row["Device"]}</span></td>'
    f'<td style="padding:11px 16px;font-size:0.83rem;color:{C["txt2"]};">{row["Hours"]} hrs</td>'
    f'<td style="padding:11px 16px;font-size:0.83rem;color:{C["txt"]};font-weight:600;">{row["kWh"]:.3f} kWh</td>'
    f'<td style="padding:11px 16px;font-size:0.83rem;color:{C["grn"]};font-weight:700;">{row["Cost"]}</td>'
    f'</tr>'
    for _, row in df_t.iterrows()
])

table_html = (
    f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:14px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,0.3);margin-bottom:24px;">'
    f'<div style="overflow-x:auto;max-height:360px;">'
    f'<table style="width:100%;border-collapse:collapse;text-align:left;">'
    f'<thead>'
    f'<tr style="background:{C["mbg"]};border-bottom:1.5px solid {C["border"]};">'
    f'<th style="padding:11px 16px;font-size:0.72rem;font-weight:700;color:{C["txt2"]};text-transform:uppercase;letter-spacing:0.06em;">Date</th>'
    f'<th style="padding:11px 16px;font-size:0.72rem;font-weight:700;color:{C["txt2"]};text-transform:uppercase;letter-spacing:0.06em;">Device</th>'
    f'<th style="padding:11px 16px;font-size:0.72rem;font-weight:700;color:{C["txt2"]};text-transform:uppercase;letter-spacing:0.06em;">Runtime</th>'
    f'<th style="padding:11px 16px;font-size:0.72rem;font-weight:700;color:{C["txt2"]};text-transform:uppercase;letter-spacing:0.06em;">Consumption</th>'
    f'<th style="padding:11px 16px;font-size:0.72rem;font-weight:700;color:{C["txt2"]};text-transform:uppercase;letter-spacing:0.06em;">Est. Cost</th>'
    f'</tr>'
    f'</thead>'
    f'<tbody>{rows_html}</tbody>'
    f'</table>'
    f'</div></div>'
)
st.markdown(table_html, unsafe_allow_html=True)
