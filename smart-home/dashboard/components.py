import json
import random
import time
import streamlit as st
import paho.mqtt.publish as publish
import sys
from pathlib import Path

# Add smart-home root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config

# ─── Shared Dark Theme Tokens ─────────────────────────────────────────
C = {
    "canvas":   "#0D1612",
    "sidebar":  "#111A16",
    "card":     "#192220",
    "card2":    "#1A2922",
    "border":   "#253529",
    "border2":  "#2A3D30",
    "lgbg":     "#1E3028",
    "mbg":      "#162319",
    "txt":      "#DFF0E6",
    "txt2":     "#7E9E88",
    "txt3":     "#4A6B54",
    "grn":      "#5BAF72",
    "grn2":     "#3D8A58",
    "warn":     "#E8A832",
    "warn_bg":  "#251E0F",
    "err":      "#D95555",
    "err_bg":   "#2A1414",
    "plot_bg":  "#141F1B",
}

ICO = {
    "leaf":     "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z'/><path d='M2 22l10-10'/></svg>",
    "home":     "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/></svg>",
    "energy":   "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/></svg>",
    "rooms":    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/></svg>",
    "devices":  "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='3' width='20' height='14' rx='2'/><line x1='8' y1='21' x2='16' y2='21'/><line x1='12' y1='17' x2='12' y2='21'/></svg>",
    "alerts":   "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/></svg>",
    "settings": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/></svg>",
    "bell":     "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/></svg>",
    "check":    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'/></svg>",
    "trend_up": "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='23 6 13.5 15.5 8.5 10.5 1 18'/><polyline points='17 6 23 6 23 12'/></svg>",
    "trend_dn": "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='23 18 13.5 8.5 8.5 13.5 1 6'/><polyline points='17 18 23 18 23 12'/></svg>",
    "bulb":     "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='9' y1='18' x2='15' y2='18'/><line x1='10' y1='22' x2='14' y2='22'/><path d='M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14'/></svg>",
    "fan":      "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M10.05 4.575a1.575 1.575 0 1 0 3.9 0l-.585 1.95C12.96 8 12 8.925 12 10.5V12'/><path d='M10.05 4.575C9.075 1.5 5.1.9 3.525 3.6c-.975 1.65.3 3.825 2.1 3.9l2.025-.075C8.55 7.35 9.9 7.8 10.65 9L12 12'/><path d='M19.95 4.575a1.575 1.575 0 1 1-3.9 0l.585 1.95C15.75 8.1 15 8.925 15 10.5V12'/><circle cx='12' cy='12' r='2'/><path d='M12 12c0 1.5-.75 2.55-1.95 3.6L8.1 17.4c-.975.9-.75 2.4.525 3.075C10.2 21 11.4 20.7 12 19.5'/><path d='M12 12c1.5 0 2.55.75 3.6 1.95l1.8 1.95c.9.975 2.4.75 3.075-.525.525-1.575.225-2.775-.975-3.375'/></svg>",
    "ac":       "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='6' width='20' height='10' rx='2'/><path d='M12 16v2'/><path d='M6 16v2'/><path d='M18 16v2'/><path d='M7 11h10'/></svg>",
    "clock":    "<svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'/><polyline points='12 6 12 12 16 14'/></svg>",
    "info":     "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'/><line x1='12' y1='16' x2='12' y2='12'/><line x1='12' y1='8' x2='12.01' y2='8'/></svg>",
}

def apply_dark_theme():
    """Inject the shared dark-theme CSS into any Streamlit page."""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ font-family: 'Inter', system-ui, sans-serif; box-sizing: border-box; }}
html, body, .stApp {{ background: {C['canvas']} !important; color: {C['txt']} !important; }}

/* Header: transparent, zero-height, but allow overflow so expand button paints */
header[data-testid="stHeader"], .stApp > header {{
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: visible !important;
    z-index: 999 !important;
    pointer-events: none !important;
}}
/* Re-enable pointer-events on ALL interactive children inside the header */
header[data-testid="stHeader"] *,
.stApp > header * {{
    pointer-events: auto !important;
}}
/* Toolbar: same transparent/zero-height, overflow visible for sidebar btn only */
[data-testid="stToolbar"] {{
    background: transparent !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: visible !important;
    pointer-events: none !important;
}}
/* Hide ALL chrome except sidebar controls */
#MainMenu, footer, .stDeployButton, [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stMainMenu"],
[data-testid="stAppDeployButton"], .stAppDeployButton {{
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}}
/* Hide toolbar actions/right content (deploy, etc.) but NOT the sidebar expand */
[data-testid="stToolbarRightContent"],
[data-testid="stToolbarActions"] {{
    display: none !important;
    visibility: hidden !important;
}}

/* Kill all default spacing */
.main .block-container, .stMainBlockContainer,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
.stApp [data-testid="stAppViewBlockContainer"] {{
    padding: 0 !important; margin: 0 !important;
    max-width: 100% !important; min-width: 0 !important;
}}
.stMain, [data-testid="stMain"], [data-testid="stAppViewContainer"] {{
    background: {C['canvas']} !important; padding: 0 !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {C['card']} !important;
    border: 1.5px solid {C['border']} !important;
    border-radius: 18px !important;
    box-shadow: 0 1px 8px rgba(0,0,0,0.3) !important;
    padding: 18px 20px !important;
    margin: 0 !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: transparent !important;
}}
[data-testid="stHorizontalBlock"] {{ gap: 12px !important; padding: 0 !important; }}
[data-testid="stColumn"] > div {{ padding: 0 !important; }}
.stApp > div:first-child {{ padding-top: 0 !important; margin-top: 0 !important; }}

/* ── Sidebar: expanded state ────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {C['sidebar']} !important;
    box-shadow: none !important; z-index: 100; top: 0 !important;
    transition: width 0.25s ease, min-width 0.25s ease, transform 0.25s ease !important;
}}
section[data-testid="stSidebar"][aria-expanded="true"] {{
    border-right: 1px solid {C['border']} !important;
    width: 220px !important; min-width: 220px !important;
    transform: translateX(0) !important;
}}
/* ── Sidebar: collapsed state (use transform, NOT display:none) ── */
section[data-testid="stSidebar"][aria-expanded="false"] {{
    width: 0 !important; min-width: 0 !important; max-width: 0 !important;
    transform: translateX(-260px) !important;
    border-right: none !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0 !important; background: {C['sidebar']} !important;
}}
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* Eliminate top blank space in sidebar, but let collapse button overflow */
[data-testid="stSidebarHeader"],
header[data-testid="stSidebarHeader"] {{
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: visible !important;
    position: relative !important;
    z-index: 103 !important;
    pointer-events: none !important;
}}
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarContent"] > div,
[data-testid="stSidebar"] div[class*="st-emotion-cache"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
[data-testid="stSidebarContent"] {{
    padding: 0 !important;
    padding-bottom: 24px !important;
    background: {C['sidebar']} !important;
}}
/* Collapse button inside expanded sidebar — must escape 0-height header */
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {{
    position: absolute !important;
    top: 14px !important;
    right: 8px !important;
    z-index: 105 !important;
    color: {C['txt2']} !important;
    pointer-events: auto !important;
    overflow: visible !important;
}}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {{
    background: {C['card']} !important;
    border: 1px solid {C['border2']} !important;
    border-radius: 8px !important;
    color: {C['txt2']} !important;
    padding: 4px !important;
    cursor: pointer !important;
    pointer-events: auto !important;
}}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:hover {{
    background: {C['lgbg']} !important;
    border-color: {C['grn']} !important;
    color: {C['grn']} !important;
}}

/* ── Expand button: force-show when sidebar is collapsed ───────── */
[data-testid="stSidebarCollapsedControl"],
.stSidebarCollapsedControl {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 999999 !important;
    pointer-events: auto !important;
    overflow: visible !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: auto !important;
    height: auto !important;
}}
[data-testid="stSidebarCollapsedControl"] button,
button[data-testid="stExpandSidebarButton"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: relative !important;
    z-index: 999999 !important;
    background: {C['card']} !important;
    border: 1.5px solid {C['border2']} !important;
    border-radius: 9px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    align-items: center !important;
    justify-content: center !important;
    color: {C['txt']} !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.55) !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    padding: 0 !important;
    margin: 0 !important;
    pointer-events: auto !important;
}}
[data-testid="stSidebarCollapsedControl"] button:hover,
button[data-testid="stExpandSidebarButton"]:hover {{
    background: {C['lgbg']} !important;
    border-color: {C['grn']} !important;
    color: {C['grn']} !important;
}}
[data-testid="stSidebarCollapsedControl"] button svg,
button[data-testid="stExpandSidebarButton"] svg {{
    stroke: {C['txt']} !important;
    fill: none !important;
    color: {C['txt']} !important;
    width: 18px !important;
    height: 18px !important;
}}
[data-testid="stSidebarCollapsedControl"] button:hover svg,
button[data-testid="stExpandSidebarButton"]:hover svg {{
    stroke: {C['grn']} !important;
    color: {C['grn']} !important;
}}

/* Page link styling in sidebar */
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
    background: transparent !important; border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 8px 8px 0 !important;
    margin: 1px 10px 1px 0 !important; padding: 9px 14px !important;
    color: {C['txt2']} !important; font-size: 0.875rem !important;
    font-weight: 500 !important; text-decoration: none !important;
    transition: background 0.12s !important; width: 100% !important;
    display: flex !important; gap: 10px !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
    background: {C['card2']} !important; color: {C['txt']} !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
    background: {C['lgbg']} !important;
    border-left: 3px solid {C['grn']} !important;
    color: {C['grn']} !important; font-weight: 700 !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] svg {{
    display: none !important;
}}

/* Buttons */
.stButton > button {{
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.83rem !important; padding: 9px 16px !important;
    border: 1.5px solid {C['border2']} !important;
    background: {C['card']} !important; color: {C['grn']} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
    transition: all 0.15s ease !important; width: 100% !important;
}}
.stButton > button:hover {{
    background: {C['lgbg']} !important; border-color: {C['grn']} !important;
    color: {C['txt']} !important;
}}
.stButton > button[kind="primary"] {{
    background: {C['grn2']} !important; color: {C['txt']} !important;
    border-color: {C['grn2']} !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {C['grn']} !important; border-color: {C['grn']} !important;
}}

/* Charts */
.js-plotly-plot .plotly {{ background: transparent !important; }}

/* Divider, segmented control, scrollbar */
hr {{ border-color: {C['border']} !important; margin: 16px 0 !important; }}
div[data-testid="stSegmentedControl"] {{
    background: {C['mbg']} !important; border-radius: 10px !important;
    border: 1.5px solid {C['border']} !important; padding: 3px !important;
}}
div[data-testid="stSegmentedControl"] button {{ color: {C['txt2']} !important; }}
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {{
    background: {C['lgbg']} !important; color: {C['grn']} !important;
}}
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {C['canvas']}; }}
::-webkit-scrollbar-thumb {{ background: {C['border2']}; border-radius: 99px; }}

/* Alerts */
[data-testid="stAlertContainer"] {{
    background: {C['lgbg']} !important; border-color: {C['grn2']} !important;
    color: {C['txt']} !important; border-radius: 10px !important;
}}

/* No white flashes */
.stApp, .main, [data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"], .element-container {{ background: transparent !important; }}
</style>
<script>
// Toggle expand-button visibility based on sidebar state
(function() {{
    function syncExpandBtn() {{
        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
        const ctrl = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
        if (!sidebar || !ctrl) return;
        const expanded = sidebar.getAttribute('aria-expanded') === 'true';
        ctrl.style.display = expanded ? 'none' : 'flex';
        ctrl.style.visibility = expanded ? 'hidden' : 'visible';
    }}
    // Run on load
    syncExpandBtn();
    // Observe sidebar attribute changes
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {{
        new MutationObserver(syncExpandBtn).observe(sidebar, {{ attributes: true, attributeFilter: ['aria-expanded'] }});
    }}
    // Fallback: re-check periodically in case DOM rebuilds
    setInterval(syncExpandBtn, 500);
}})();
</script>
""", unsafe_allow_html=True)


def apply_custom_styles():
    """Legacy wrapper — now applies dark theme."""
    apply_dark_theme()


def render_sidebar(unack: int = 0):
    """Render the standard dark theme sidebar for all pages."""
    with st.sidebar:
        # ── Brand header ──
        st.markdown(
            f'<div style="padding:20px 16px 16px;border-bottom:1px solid {C["border"]};">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="width:32px;height:32px;background:{C["lgbg"]};border-radius:9px;'
            f'display:flex;align-items:center;justify-content:center;color:{C["grn"]};">{ICO["leaf"]}</div>'
            f'<div><div style="font-size:0.9rem;font-weight:700;color:{C["txt"]};letter-spacing:-0.02em;">Smart Home</div>'
            f'<div style="font-size:0.7rem;color:{C["txt2"]};">by Worklio</div></div></div></div>',
            unsafe_allow_html=True
        )

        st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Nav links (real clickable page_link) ──
        nav_config = [
            ("home",     "Dashboard",  "app.py",               True),
            ("energy",   "Energy",     "pages/1_Energy.py",    True),
            ("rooms",    "Rooms",      None,                    False),
            ("devices",  "Devices",    None,                    False),
            ("alerts",   "Alerts",     "pages/2_Alerts.py",    True),
            ("settings", "Settings",   "pages/3_Settings.py",  True),
        ]

        for ico_key, label, page_path, has_page in nav_config:
            icon_html = ICO[ico_key]
            if has_page and page_path:
                # Real clickable nav link
                badge_html = ""
                if ico_key == "alerts" and unack > 0:
                    badge_html = (f'<span style="margin-left:auto;background:{C["err"]};color:#fff;'
                                 f'font-size:0.68rem;font-weight:700;padding:1px 6px;border-radius:99px;">'
                                 f'{unack}</span>')

                # Show icon + badge as HTML before the page_link
                if badge_html:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.page_link(page_path, label=f"  {label}", icon=None)
                    with c2:
                        st.markdown(
                            f'<div style="display:flex;align-items:center;justify-content:center;'
                            f'height:38px;">{badge_html}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.page_link(page_path, label=f"  {label}", icon=None)
            else:
                # Disabled label for pages not yet built
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:9px 14px;'
                    f'border-left:3px solid transparent;border-radius:0 8px 8px 0;'
                    f'margin:1px 10px 1px 0;color:{C["txt3"]};font-size:0.875rem;'
                    f'font-weight:500;opacity:0.5;cursor:not-allowed;">'
                    f'<span style="flex-shrink:0;">{icon_html}</span>{label}'
                    f'<span style="margin-left:auto;font-size:0.6rem;color:{C["txt3"]};">Soon</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ── Zone footer ──
        st.markdown(
            f'<div style="margin-top:20px;margin-bottom:14px;padding:11px 13px;'
            f'background:{C["card"]};border:1px solid {C["border"]};border-radius:10px;'
            f'margin-left:10px;margin-right:10px;">'
            f'<div style="display:flex;align-items:center;gap:9px;">'
            f'<div style="width:7px;height:7px;background:{C["grn"]};border-radius:50%;'
            f'box-shadow:0 0 0 2px {C["lgbg"]};flex-shrink:0;"></div>'
            f'<div><div style="font-size:0.78rem;font-weight:600;color:{C["txt"]};">Zone 1 &middot; Living Room</div>'
            f'<div style="font-size:0.68rem;color:{C["txt2"]};">Connected &amp; active</div>'
            f'</div></div></div>',
            unsafe_allow_html=True
        )

def publish_command(device: str, state: str, source: str = "dashboard") -> bool:
    """Publish a command to MQTT via paho publish.single (fire-and-forget, safe for Streamlit)."""
    try:
        client_id = f"{config.MQTT_CLIENT_PREFIX}_dash_{random.randint(1000, 9999)}"
        payload = {"device": device, "state": state, "source": source, "ts": int(time.time())}
        publish.single(
            topic=config.TOPIC_CMD,
            payload=json.dumps(payload),
            hostname=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            client_id=client_id,
            keepalive=10
        )
        return True
    except Exception as e:
        print(f"[ERROR] Failed to publish MQTT command: {e}")
        return False
