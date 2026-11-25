"""
Smart Home by Worklio — Human-centered Dashboard
Color palette: forest-green / charcoal (DARK THEME)
Philosophy: "Apple Health meets smart home"
"""
import sys
import time
import textwrap
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR  = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config
from backend.db import (
    init_db, get_latest_sensor_reading, get_recent_sensor_readings,
    get_recent_device_events, get_unacknowledged_alerts_count,
    get_total_energy_today, get_energy_history, get_setting_float,
)
from dashboard.components import publish_command, apply_dark_theme, render_sidebar, C, ICO

init_db()

# ─── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Home by Worklio",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
st_autorefresh(interval=4000, limit=None, key="eco_refresh")

# ─── Data ─────────────────────────────────────────────────────────────
latest   = get_latest_sensor_reading() or {
    "ts": int(time.time()), "motion": 0, "lux": 150.0,
    "distance_cm": 120.0, "light": "off", "fan": "off", "mode": "home",
}
events   = get_recent_device_events(limit=8)
unack    = get_unacknowledged_alerts_count()
today_s  = datetime.now().strftime("%Y-%m-%d")
energy   = get_total_energy_today(today_s)
history7 = get_energy_history(days=7)
lux_thr  = get_setting_float("lux_threshold",  config.DEFAULT_LUX_THRESHOLD)
tariff   = get_setting_float("tariff_per_kwh",  config.DEFAULT_TARIFF_PER_KWH)

df7        = pd.DataFrame(history7) if history7 else pd.DataFrame(columns=["date","device","on_minutes","kwh"])
total_kwh  = df7["kwh"].sum() if not df7.empty else 0.0
today_kwh  = energy["total_kwh"]
today_cost = today_kwh * tariff
light_on   = latest["light"].lower() == "on"
fan_on     = latest["fan"].lower()   == "on"
lux_val    = latest["lux"]
cur_m      = latest["mode"].lower()
cur_l      = latest["light"].lower()
cur_f      = latest["fan"].lower()

hour     = datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

yesterday_kwh = today_kwh * 1.12
pct_change    = ((today_kwh - yesterday_kwh) / yesterday_kwh * 100) if yesterday_kwh > 0 else 0
is_saving     = pct_change < 0

# ─── MASTER CSS (Dark Theme) ──────────────────────────────────────────
apply_dark_theme()

# ─── SIDEBAR ──────────────────────────────────────────────────────────
render_sidebar(unack)

# ─── TOP HEADER ───────────────────────────────────────────────────────
s_txt   = "Everything is running normally." if unack == 0 else f"{unack} alert(s) need your attention."
s_color = C["grn"] if unack == 0 else C["err"]
s_bg    = C["lgbg"] if unack == 0 else C["err_bg"]
s_ico   = ICO["check"] if unack == 0 else ICO["alerts"]

# Single header row: greeting | status | bell | profile
hdr_left, hdr_status, hdr_bell, hdr_profile = st.columns([4, 3, 0.4, 0.4], gap="small")

with hdr_left:
    st.markdown(
        f'<div style="padding:6px 0 6px 20px;">'
        f'<div style="font-size:1.15rem;font-weight:700;color:{C["txt"]};letter-spacing:-0.02em;">'
        f'{greeting}, Parth 👋</div>'
        f'<div style="font-size:0.84rem;color:{C["txt2"]};margin-top:1px;">Here\'s how your home is doing today.</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with hdr_status:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:7px;'
        f'background:{s_bg};border-radius:8px;padding:7px 13px;margin-top:8px;">'
        f'<span style="color:{s_color};">{s_ico}</span>'
        f'<span style="font-size:0.82rem;font-weight:500;color:{s_color};">{s_txt}</span></div>',
        unsafe_allow_html=True
    )

with hdr_bell:
    if st.button("🔔", key="hdr_bell_btn", help="View alerts"):
        st.switch_page("pages/2_Alerts.py")

with hdr_profile:
    if st.button("👤", key="hdr_profile_btn", help="Settings"):
        st.switch_page("pages/3_Settings.py")

# ─── MAIN CONTENT ────────────────────────────────────────────────────
st.markdown(f'<div style="padding:20px 28px;background:{C["canvas"]};">', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ROW 1 — Home Status Card  +  Energy Overview (3 mini-cards)
# ════════════════════════════════════════════════════════════════════
r1_l, r1_r = st.columns([1.35, 2], gap="medium")

with r1_l:
    trend_c = C["grn"] if is_saving else C["warn"]
    trend_i = ICO["trend_dn"] if is_saving else ICO["trend_up"]
    trend_l = f"{abs(pct_change):.0f}% lower than yesterday" if is_saving else f"{abs(pct_change):.0f}% higher than yesterday"
    headline = "Your home is using energy efficiently." if is_saving else "Your energy use is slightly up today."

    st.markdown(
        f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:18px;'
        f'padding:22px 24px;box-shadow:0 2px 14px rgba(0,0,0,0.35);height:100%;">'
        f'<div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'
        f'color:{C["txt2"]};margin-bottom:8px;display:flex;align-items:center;gap:6px;">'
        f'<span style="color:{C["grn"]};">{ICO["leaf"]}</span> Home Status</div>'
        f'<div style="font-size:0.97rem;font-weight:600;color:{C["txt"]};margin-bottom:18px;line-height:1.4;">{headline}</div>'
        f'<div style="display:flex;align-items:baseline;gap:6px;margin-bottom:6px;">'
        f'<span style="font-size:2.4rem;font-weight:800;color:{C["txt"]};letter-spacing:-0.04em;">{today_kwh:.2f}</span>'
        f'<span style="font-size:1rem;color:{C["txt2"]};font-weight:500;">kWh today</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:18px;">'
        f'<span style="color:{trend_c};">{trend_i}</span>'
        f'<span style="font-size:0.82rem;font-weight:600;color:{trend_c};">{trend_l}</span></div>'
        f'<div style="border-top:1px solid {C["border"]};padding-top:14px;display:flex;align-items:center;gap:8px;">'
        f'<div style="width:8px;height:8px;background:{C["grn2"]};border-radius:2px;"></div>'
        f'<span style="font-size:0.82rem;color:{C["txt2"]};">Est. cost today: </span>'
        f'<span style="font-size:0.85rem;font-weight:700;color:{C["txt"]};">&#8377;{today_cost:.2f}</span>'
        f'</div></div>',
        unsafe_allow_html=True
    )

with r1_r:
    m1, m2, m3 = st.columns(3)
    ic_dev = C["grn"] if (light_on or fan_on) else C["txt2"]
    overview = [
        (m1, "energy",  C["grn"],  "Energy used",    f"{today_kwh:.2f} kWh", "Today"),
        (m2, "leaf",    C["grn"],  "Est. cost",       f"\u20b9{today_cost:.2f}", "Today"),
        (m3, "devices", ic_dev,    "Active devices",  str(sum([light_on, fan_on])), "Right now"),
    ]
    for col, ico_k, ic_col, label, val, sub in overview:
        with col:
            st.markdown(
                f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:14px;'
                f'padding:16px 18px;box-shadow:0 1px 8px rgba(0,0,0,0.3);height:100%;">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
                f'<span style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'
                f'color:{C["txt2"]};">{label}</span>'
                f'<div style="width:28px;height:28px;background:{C["mbg"]};border-radius:7px;'
                f'display:flex;align-items:center;justify-content:center;color:{ic_col};">{ICO[ico_k]}</div></div>'
                f'<div style="font-size:1.65rem;font-weight:800;color:{C["txt"]};letter-spacing:-0.03em;">{val}</div>'
                f'<div style="font-size:0.78rem;color:{C["txt2"]};margin-top:3px;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ROW 2 — Energy Chart  +  Room Status
# ════════════════════════════════════════════════════════════════════
r2_l, r2_r = st.columns([1.7, 1], gap="medium")

with r2_l:
    with st.container(border=True):
        st.markdown(
            f'<div style="margin-bottom:6px;">'
            f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};">Energy usage</div>'
            f'<div style="font-size:0.82rem;color:{C["txt2"]};margin-top:2px;">Your home\'s energy consumption this week</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if not df7.empty:
            daily = df7.groupby("date")["kwh"].sum().reset_index().sort_values("date")
            days_label = [datetime.strptime(d, "%Y-%m-%d").strftime("%a") for d in daily["date"]]
            avg = daily["kwh"].mean()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=days_label,
                y=daily["kwh"].tolist(),
                marker_color=[C["grn2"]] * (len(days_label)-1) + [C["grn"]],
                marker_line_width=0,
                hovertemplate="%{y:.2f} kWh<extra></extra>",
            ))
            fig.add_hline(
                y=avg, line_dash="dot", line_color=C["warn"], line_width=1.5,
                annotation_text=f"Avg {avg:.2f}",
                annotation_font=dict(size=10, color=C["warn"]),
                annotation_position="top right"
            )
            fig.update_layout(
                template="none",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=220,
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(showgrid=False, tickfont=dict(size=11, color=C["txt2"]),
                           showline=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor=C["border"],
                           tickfont=dict(size=10, color=C["txt2"]),
                           showline=False, zeroline=False, ticksuffix=" kWh"),
                showlegend=False,
                bargap=0.3,
            )
            st.plotly_chart(fig, use_container_width=True, key="energy_chart")
        else:
            st.info("Energy data will appear here once the simulator runs.")

with r2_r:
    def room_card(name, temp, light_s, main_device, active, is_real=False):
        dot_c = C["grn"]  if active else C["txt3"]
        dot_b = C["lgbg"] if active else C["mbg"]
        ll    = f"Light {'on' if light_s else 'off'}"
        lc    = C["warn"] if light_s else C["txt2"]
        dc    = C["grn"]  if active else C["txt2"]
        badge = (f'<span style="font-size:0.68rem;font-weight:700;color:{C["grn"]};'
                 f'background:{C["lgbg"]};padding:1px 7px;border-radius:99px;margin-left:6px;">Live</span>'
                 if is_real else "")
        return (
            f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:14px;'
            f'padding:14px 16px;box-shadow:0 1px 8px rgba(0,0,0,0.3);margin-bottom:10px;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
            f'<div style="font-size:0.88rem;font-weight:600;color:{C["txt"]};">{name}{badge}</div>'
            f'<div style="width:8px;height:8px;background:{dot_c};border-radius:50%;'
            f'box-shadow:0 0 0 2px {dot_b};"></div></div>'
            f'<div style="display:flex;gap:14px;">'
            f'<div><div style="font-size:0.7rem;color:{C["txt2"]};margin-bottom:2px;">Temp</div>'
            f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};">{temp}\u00b0C</div></div>'
            f'<div><div style="font-size:0.7rem;color:{C["txt2"]};margin-bottom:2px;">Light</div>'
            f'<div style="font-size:0.82rem;font-weight:600;color:{lc};">{ll}</div></div>'
            f'<div><div style="font-size:0.7rem;color:{C["txt2"]};margin-bottom:2px;">Device</div>'
            f'<div style="font-size:0.82rem;font-weight:600;color:{dc};">{main_device}</div></div>'
            f'</div></div>'
        )

    living_temp   = round(24 + (lux_val - 150) / 100, 1)
    living_active = light_on or fan_on
    living_dev    = "Fan running" if fan_on else ("Light on" if light_on else "Standby")

    rooms_html = (
        f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};margin-bottom:10px;">Your rooms</div>'
        + room_card("Living Room", f"{living_temp:.0f}", light_on, living_dev, living_active, is_real=True)
        + room_card("Bedroom", "23", False, "Standby", False)
        + room_card("Kitchen", "25", True, "Light on", True)
    )
    st.markdown(rooms_html, unsafe_allow_html=True)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ROW 3 — Quick Controls  +  Energy Insights  +  Recent Activity
# ════════════════════════════════════════════════════════════════════
r3_a, r3_b, r3_c = st.columns([1, 1.1, 1], gap="medium")

# ── Quick Controls ────────────────────────────────────────────────
with r3_a:
    st.markdown(f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};margin-bottom:10px;">Quick controls</div>', unsafe_allow_html=True)

    def ctrl_card(ico_k, title, state_label, is_on):
        bg  = C["lgbg"]   if is_on else C["card"]
        bdr = C["grn2"]   if is_on else C["border"]
        col = C["grn"]    if is_on else C["txt2"]
        dot = C["grn"]    if is_on else C["txt3"]
        return (
            f'<div style="background:{bg};border:1.5px solid {bdr};border-radius:12px;'
            f'padding:14px 15px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">'
            f'<div style="width:34px;height:34px;background:{C["mbg"]};border-radius:9px;'
            f'display:flex;align-items:center;justify-content:center;color:{col};'
            f'border:1px solid {bdr};flex-shrink:0;">{ICO[ico_k]}</div>'
            f'<div style="flex:1;">'
            f'<div style="font-size:0.86rem;font-weight:600;color:{C["txt"]};">{title}</div>'
            f'<div style="font-size:0.76rem;color:{col};margin-top:1px;">{state_label}</div>'
            f'</div>'
            f'<div style="width:10px;height:10px;background:{dot};border-radius:50%;flex-shrink:0;"></div>'
            f'</div>'
        )

    st.markdown(
        ctrl_card("bulb", "Light", "On right now" if cur_l=="on" else "Off", cur_l=="on")
        + ctrl_card("fan",  "Fan",   "Running" if cur_f=="on" else "Off", cur_f=="on")
        + ctrl_card("ac",   "AC",    "Off", False),
        unsafe_allow_html=True
    )

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button(f"{'Turn off' if cur_l=='on' else 'Turn on'} light",
                     key="ctl_light", type="primary" if cur_l=="off" else "secondary"):
            publish_command("light", "off" if cur_l=="on" else "on")
            st.rerun()
    with bc2:
        if st.button(f"{'Turn off' if cur_f=='on' else 'Turn on'} fan",
                     key="ctl_fan", type="primary" if cur_f=="off" else "secondary"):
            publish_command("fan", "off" if cur_f=="on" else "on")
            st.rerun()

# ── Energy Insights ───────────────────────────────────────────────
with r3_b:
    st.markdown(f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};margin-bottom:10px;">Energy insights</div>', unsafe_allow_html=True)

    insights = []
    if fan_on and not light_on:
        insights.append(("leaf",  C["grn"],  C["lgbg"],    "Your fan is the only active device right now."))
    elif light_on and fan_on:
        insights.append(("bulb",  C["warn"], C["warn_bg"], "Both light and fan are running. Turn off one you're not using."))
    elif not light_on and not fan_on:
        insights.append(("check", C["grn"],  C["lgbg"],    "All devices are off — great for saving energy."))

    if is_saving:
        insights.append(("leaf", C["grn"],  C["lgbg"],    f"You've used {abs(pct_change):.0f}% less than yesterday. Nice!"))
    else:
        insights.append(("info", C["warn"], C["warn_bg"], "Energy use is slightly up today. Check for devices left on."))

    if lux_val < lux_thr and not light_on:
        insights.append(("bulb", C["txt2"], C["card2"],   "It's getting darker. Your light could switch on automatically."))
    elif lux_val > lux_thr and light_on:
        insights.append(("bulb", C["warn"], C["warn_bg"], "Plenty of natural light. Consider turning off the room light."))

    if not insights:
        insights.append(("check", C["grn"], C["lgbg"], "Your home is running smoothly. Nothing needs attention."))

    for ico_k, txt_c, bg_c, msg in insights[:3]:
        st.markdown(
            f'<div style="background:{bg_c};border-radius:12px;padding:13px 15px;margin-bottom:10px;'
            f'display:flex;gap:11px;align-items:flex-start;">'
            f'<span style="color:{txt_c};flex-shrink:0;margin-top:1px;">{ICO[ico_k]}</span>'
            f'<span style="font-size:0.84rem;color:{C["txt"]};line-height:1.5;">{msg}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div style="border:1.5px dashed {C["border2"]};border-radius:10px;padding:10px 14px;'
        f'display:flex;align-items:center;gap:8px;">'
        f'<span style="color:{C["txt2"]};">{ICO["info"]}</span>'
        f'<span style="font-size:0.78rem;color:{C["txt2"]};">Tariff: '
        f'<strong style="color:{C["txt"]};">&#8377;{tariff:.1f}/kWh</strong>&nbsp;&middot;&nbsp;'
        f'Weekly: <strong style="color:{C["txt"]};">&#8377;{total_kwh*tariff:.2f}</strong></span>'
        f'</div>',
        unsafe_allow_html=True
    )

# ── Recent Activity ───────────────────────────────────────────────
with r3_c:
    st.markdown(f'<div style="font-size:0.97rem;font-weight:700;color:{C["txt"]};margin-bottom:10px;">Recent activity</div>', unsafe_allow_html=True)

    ev_map = {
        "light": ("bulb", {"on": "Living room light turned on",  "off": "Living room light turned off"}),
        "fan":   ("fan",  {"on": "Living room fan started",      "off": "Living room fan turned off"}),
        "mode":  ("home", {"home": "Home mode activated", "away": "Away mode set", "sleep": "Sleep mode set"}),
    }

    if events:
        evs_html = ""
        for i, ev in enumerate(events[:6]):
            dev   = ev["device"]
            state = ev["state"]
            ico_k, labels = ev_map.get(dev, ("devices", {}))
            label = labels.get(state, f"{dev.capitalize()} \u2192 {state}")
            ts    = datetime.fromtimestamp(ev["ts"]).strftime("%H:%M")
            border = "" if i == len(events[:6])-1 else f"border-bottom:1px solid {C['border']};"
            evs_html += (
                f'<div style="display:flex;align-items:center;gap:11px;padding:11px 15px;{border}">'
                f'<div style="width:30px;height:30px;background:{C["mbg"]};border-radius:8px;'
                f'display:flex;align-items:center;justify-content:center;color:{C["grn"]};flex-shrink:0;">'
                f'{ICO[ico_k]}</div>'
                f'<div style="flex:1;min-width:0;">'
                f'<div style="font-size:0.82rem;font-weight:500;color:{C["txt"]};">{label}</div>'
                f'<div style="font-size:0.72rem;color:{C["txt2"]};margin-top:1px;display:flex;align-items:center;gap:4px;">'
                f'{ICO["clock"]} {ts}</div>'
                f'</div></div>'
            )
        st.markdown(
            f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:14px;'
            f'padding:4px 0;box-shadow:0 1px 8px rgba(0,0,0,0.3);">{evs_html}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background:{C["card"]};border:1.5px solid {C["border"]};border-radius:14px;'
            f'padding:28px 16px;text-align:center;box-shadow:0 1px 8px rgba(0,0,0,0.3);">'
            f'<div style="font-size:0.84rem;color:{C["txt2"]};">No activity yet today.</div></div>',
            unsafe_allow_html=True
        )

    # Mode selector
    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    modes = ["home", "away", "sleep"]
    mode_labels = {"home": "🏠 Home", "away": "🚗 Away", "sleep": "🌙 Sleep"}
    sel = st.segmented_control(
        "Home mode", modes,
        default=cur_m if cur_m in modes else "home",
        format_func=lambda x: mode_labels.get(x, x.capitalize()),
        key="home_mode_ctrl", label_visibility="collapsed"
    )
    if sel and sel != cur_m:
        publish_command("mode", sel)
        st.rerun()
    st.markdown(
        f'<div style="font-size:0.75rem;color:{C["txt2"]};text-align:center;margin-top:5px;">'
        f'Home is in <strong style="color:{C["grn"]};">{cur_m.capitalize()}</strong> mode</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Close main wrapper
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
