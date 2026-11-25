"""
Smart Home by Worklio — Settings page
Human-centered, sage green / warm white aesthetic
"""
import sys
from pathlib import Path
import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR  = CURRENT_DIR.parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config
from backend.db import get_setting_float, get_setting_int, set_setting, get_unacknowledged_alerts_count
from dashboard.components import apply_dark_theme, render_sidebar, C

st.set_page_config(page_title="Settings — Smart Home by Worklio", page_icon="⚙️", layout="wide")

apply_dark_theme()
unack = get_unacknowledged_alerts_count()
render_sidebar(unack)

curr_lux     = get_setting_float("lux_threshold",               config.DEFAULT_LUX_THRESHOLD)
curr_timeout = get_setting_int  ("timeout_sec",                 config.DEFAULT_TIMEOUT_SEC)
curr_dist    = get_setting_float("intrusion_distance_threshold",config.DEFAULT_INTRUSION_DISTANCE_THRESHOLD)
curr_lw      = get_setting_float("light_watts",                 config.DEFAULT_LIGHT_WATTS)
curr_fw      = get_setting_float("fan_watts",                   config.DEFAULT_FAN_WATTS)
curr_tariff  = get_setting_float("tariff_per_kwh",              config.DEFAULT_TARIFF_PER_KWH)

st.markdown(f"""
<div style="margin-bottom:20px;">
  <div style="font-size:1.3rem;font-weight:700;color:{C['txt']};letter-spacing:-0.02em;">Settings</div>
  <div style="font-size:0.85rem;color:{C['txt2']};">Adjust how your home automation system behaves.</div>
</div>
""", unsafe_allow_html=True)

# Live summary row
s1, s2, s3 = st.columns(3)
summaries = [
    (s1, "💡 Lighting", f"{curr_lw:.0f} W", f"Auto-dims below {curr_lux:.0f} lux"),
    (s2, "🌀 Fan / AC",  f"{curr_fw:.0f} W", f"Turns off after {curr_timeout}s idle"),
    (s3, "💰 Billing",  f"&#8377;{curr_tariff:.3f}/kWh", "Current electricity tariff"),
]
for col, title, val, sub in summaries:
    with col:
        st.markdown(f"""
        <div style="background:{C['card']};border:1.5px solid {C['border']};border-radius:14px;padding:16px 18px;
             margin-bottom:16px;">
          <div style="font-size:0.82rem;font-weight:600;color:{C['txt2']};margin-bottom:6px;">{title}</div>
          <div style="font-size:1.5rem;font-weight:800;color:{C['txt']};letter-spacing:-0.02em;">{val}</div>
          <div style="font-size:0.78rem;color:{C['txt2']};margin-top:4px;">{sub}</div>
        </div>""", unsafe_allow_html=True)

# Form
st.markdown(f"""
<div style="background:{C['card']};border:1.5px solid {C['border']};border-radius:18px;padding:24px;">
""", unsafe_allow_html=True)

with st.form("settings_form"):
    st.markdown(f"<div style='font-size:0.95rem;font-weight:700;color:{C['txt']};margin-bottom:16px;'>Update settings</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"<div style='font-size:0.82rem;font-weight:600;color:{C['txt2']};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;'>Device Power Ratings</div>", unsafe_allow_html=True)
        new_lw      = st.number_input("Light power (Watts)", 1.0, 500.0, float(curr_lw), 1.0,
                                       help="How many watts your light uses when on")
        new_fw      = st.number_input("Fan / AC power (Watts)", 5.0, 3000.0, float(curr_fw), 5.0,
                                       help="How many watts your fan uses when running")
        st.markdown(f"<div style='font-size:0.82rem;font-weight:600;color:{C['txt2']};text-transform:uppercase;letter-spacing:0.05em;margin:14px 0 10px;'>Billing</div>", unsafe_allow_html=True)
        new_tariff  = st.number_input("Electricity tariff (&#8377;/kWh)", 0.01, 10.0, float(curr_tariff), 0.01, format="%.3f",
                                       help="The rate you pay per kWh of electricity")

    with col_b:
        st.markdown(f"<div style='font-size:0.82rem;font-weight:600;color:{C['txt2']};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;'>Automation Rules</div>", unsafe_allow_html=True)
        new_lux     = st.number_input("Light auto-on below (lux)", 0.0, 2000.0, float(curr_lux), 10.0,
                                       help="Light turns on automatically when ambient light drops below this level")
        new_timeout = st.number_input("Fan auto-off after no motion (seconds)", 5, 3600, int(curr_timeout), 5,
                                       help="How long after no motion before the fan turns off automatically")
        new_dist    = st.number_input("Intrusion detection distance (cm)", 5.0, 400.0, float(curr_dist), 5.0,
                                       help="Distance at which to trigger a possible intrusion alert")

        st.markdown(f"""
        <div style="margin-top:14px;background:{C['lgbg']};border:1.5px solid {C['border']};border-radius:10px;padding:11px 14px;">
          <div style="font-size:0.78rem;font-weight:600;color:{C['txt2']};margin-bottom:3px;">Connected broker</div>
          <div style="font-size:0.82rem;color:{C['txt']};font-weight:500;">{config.MQTT_BROKER}:{config.MQTT_PORT}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    if st.form_submit_button("Save settings", type="primary", use_container_width=True):
        set_setting("light_watts",                    new_lw)
        set_setting("fan_watts",                      new_fw)
        set_setting("tariff_per_kwh",                 new_tariff)
        set_setting("lux_threshold",                  new_lux)
        set_setting("timeout_sec",                    new_timeout)
        set_setting("intrusion_distance_threshold",   new_dist)
        st.success("Settings saved. Changes take effect immediately.")
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
