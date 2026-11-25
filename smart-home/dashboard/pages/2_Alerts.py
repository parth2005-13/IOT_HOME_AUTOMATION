"""
Smart Home by Worklio — Alerts page
Human-centered, sage green / warm white aesthetic
"""
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR  = CURRENT_DIR.parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from backend.db import get_alerts, acknowledge_alert, acknowledge_all_alerts, get_unacknowledged_alerts_count
from dashboard.components import apply_dark_theme, render_sidebar, C

st.set_page_config(page_title="Alerts — Smart Home by Worklio", page_icon="🔔", layout="wide")

apply_dark_theme()
unack = get_unacknowledged_alerts_count()
render_sidebar(unack)

st.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="font-size:1.3rem;font-weight:700;color:{C['txt']};letter-spacing:-0.02em;">Alerts</div>
  <div style="font-size:0.85rem;color:{C['txt2']};">Things that need your attention.</div>
</div>
""", unsafe_allow_html=True)

# Filters row
f1, f2, spacer, f3 = st.columns([1, 1, 2, 1])
with f1:
    status_f = st.selectbox("Show", ["All","Unresolved","Resolved"], key="alt_status")
with f2:
    sev_f = st.selectbox("Severity", ["All","high","medium","low"], key="alt_sev")
with f3:
    if st.button("✓ Resolve all", type="primary", use_container_width=True):
        n = acknowledge_all_alerts()
        st.success(f"Resolved {n} alert(s).")
        st.rerun()

ack_arg = None
if status_f == "Unresolved": ack_arg = False
elif status_f == "Resolved":  ack_arg = True
alerts = get_alerts(limit=100, acknowledged=ack_arg)
if sev_f != "All":
    alerts = [a for a in alerts if a["severity"].lower() == sev_f]

total = len(alerts)
unack = sum(1 for a in alerts if not a["acknowledged"])
high  = sum(1 for a in alerts if a["severity"]=="high")

# KPI
m1,m2,m3 = st.columns(3)
for col, label, val, note in [
    (m1, "Total shown", total,  "matching filters"),
    (m2, "Need action", unack,  "unresolved"),
    (m3, "High severity",high,  "requires prompt attention"),
]:
    bdr = C['err'] if label=="High severity" and val>0 else C['border']
    with col:
        st.markdown(f"""
        <div style="background:{C['card']};border:1.5px solid {bdr};border-radius:14px;padding:16px 18px;
             margin-bottom:16px;">
          <div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;
               color:{C['txt2']};margin-bottom:6px;">{label}</div>
          <div style="font-size:1.8rem;font-weight:800;color:{C['txt']};">{val}</div>
          <div style="font-size:0.78rem;color:{C['txt2']};margin-top:3px;">{note}</div>
        </div>""", unsafe_allow_html=True)

if not alerts:
    st.markdown(f"""
    <div style="background:{C['card']};border:1.5px solid {C['border']};border-radius:16px;padding:40px;
         text-align:center;">
      <div style="font-size:1.5rem;margin-bottom:10px;">✓</div>
      <div style="font-size:1rem;font-weight:600;color:{C['txt']};margin-bottom:4px;">All clear</div>
      <div style="font-size:0.85rem;color:{C['txt2']};">Nothing needs your attention right now.</div>
    </div>""", unsafe_allow_html=True)
else:
    sev_cfg = {
        "high":   (C['err'], C['err_bg'], C['border2']),
        "medium": (C['warn'], C['warn_bg'], C['border2']),
        "low":    (C['txt2'], C['lgbg'], C['border']),
    }
    for a in alerts:
        a_id   = a["id"]
        a_type = a["type"].replace("_"," ").capitalize()
        # Human language descriptions
        human_map = {
            "intrusion_alert":    "Someone may be near your door",
            "motion_detected":    "Movement was detected in the room",
            "low_light_alert":    "The room lights may need to come on",
            "energy_threshold":   "Energy usage crossed your set limit",
        }
        a_desc = human_map.get(a["type"], a_type)
        a_sev  = a["severity"].lower()
        a_time = datetime.fromtimestamp(a["ts"]).strftime("%H:%M · %d %b")
        a_ack  = bool(a["acknowledged"])
        txt_c, bg_c, bdr_c = sev_cfg.get(a_sev, sev_cfg["low"])

        row_l, row_r = st.columns([5.5, 1])
        with row_l:
            resolved_tag = f'<span style="font-size:0.76rem;font-weight:600;color:{C["grn"]};background:{C["mbg"]};padding:3px 10px;border-radius:99px;">Resolved</span>' if a_ack else ""
            st.markdown(f"""
            <div style="background:{bg_c};border:1.5px solid {bdr_c};border-radius:14px;
                 padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;">
              <div style="width:8px;height:8px;background:{txt_c};border-radius:50%;flex-shrink:0;"></div>
              <div style="flex:1;">
                <div style="font-size:0.88rem;font-weight:600;color:{C['txt']};">{a_desc}</div>
                <div style="font-size:0.77rem;color:{C['txt2']};margin-top:3px;">{a_time} · Ref #{a_id}</div>
              </div>
              <div style="display:flex;gap:8px;align-items:center;">
                <span style="font-size:0.76rem;font-weight:600;color:{txt_c};border:1px solid {txt_c}44;
                     padding:3px 10px;border-radius:99px;">{a_sev.capitalize()}</span>
                {resolved_tag}
              </div>
            </div>""", unsafe_allow_html=True)
        with row_r:
            if not a_ack:
                if st.button("Resolve", key=f"ack_{a_id}", use_container_width=True):
                    acknowledge_alert(a_id); st.rerun()
