import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets padding/margins for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
    """Applies clean subtle borders to the table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_docx():
    doc = docx.Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(40, 40, 40)

    # ------------------ COVER PAGE ------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\n")
    r_inst.bold = True
    r_inst.font.size = Pt(13)
    r_inst.font.color.rgb = RGBColor(26, 54, 93)

    r_univ = p_inst.add_run("DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY (AKTU), LUCKNOW")
    r_univ.bold = True
    r_univ.font.size = Pt(11)
    r_univ.font.color.rgb = RGBColor(74, 85, 104)

    # Spacer
    for _ in range(3):
        doc.add_paragraph()

    # Main Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("SOFTWARE REQUIREMENTS\nSPECIFICATION (SRS)\n\n")
    r_title.bold = True
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    r_sub = p_title.add_run("Project Title: IoT Smart Home Automation & Energy Management System\n")
    r_sub.bold = True
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = RGBColor(30, 58, 138)

    r_std = p_title.add_run("Standard Academic Compliance: IEEE Std 830-1998")
    r_std.italic = True
    r_std.font.size = Pt(11)
    r_std.font.color.rgb = RGBColor(100, 116, 139)

    for _ in range(4):
        doc.add_paragraph()

    # Submission Table on Cover
    table_cov = doc.add_table(rows=1, cols=2)
    table_cov.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_cov.autofit = False

    cell_left = table_cov.rows[0].cells[0]
    cell_right = table_cov.rows[0].cells[1]
    cell_left.width = Inches(3.2)
    cell_right.width = Inches(3.2)

    p_sub = cell_left.paragraphs[0]
    p_sub.add_run("SUBMITTED BY:\n").bold = True
    p_sub.runs[0].font.size = Pt(11)
    p_sub.runs[0].font.color.rgb = RGBColor(15, 23, 42)
    p_sub.add_run("Parth Mishra\n").bold = True
    p_sub.add_run("Roll No: 2400320100789\n")
    p_sub.add_run("Degree: Bachelor of Technology (B.Tech)\n")
    p_sub.add_run("Academic Year: 2026 – 2027")

    p_gui = cell_right.paragraphs[0]
    p_gui.add_run("UNDER THE GUIDANCE OF:\n").bold = True
    p_gui.runs[0].font.size = Pt(11)
    p_gui.runs[0].font.color.rgb = RGBColor(15, 23, 42)
    p_gui.add_run("Ms. Anupam\n").bold = True
    p_gui.add_run("Assistant Professor\n")
    p_gui.add_run("Department of Computer Science & Engineering\n")

    p_foot = doc.add_paragraph()
    p_foot.paragraph_format.space_before = Pt(36)
    p_foot.add_run("Status: ").bold = True
    p_foot.add_run("3rd Year Project Specification Baseline\n")
    p_foot.add_run("Date of Submission: ").bold = True
    p_foot.add_run("01-October-2026")

    doc.add_page_break()

    # ------------------ REVISION HISTORY ------------------
    h2_rev = doc.add_heading("Document Revision & Approval History", level=2)
    h2_rev.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    rev_table = doc.add_table(rows=4, cols=5)
    rev_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    rev_table.autofit = True
    set_table_borders(rev_table)

    headers = ["Version", "Date", "Description / Major Changes", "Prepared By", "Reviewed By"]
    data = [
        ["0.1", "15-Sep-2026", "Initial Draft, Hardware Pinout & Scope Definition", "Parth Mishra", "Ms. Anupam"],
        ["0.5", "24-Sep-2026", "Telemetry Schema, MQTT Contract & DB Schema", "Parth Mishra", "Ms. Anupam"],
        ["1.0", "30-Sep-2026", "Final 3rd Year Mid-Term SRS Baseline", "Parth Mishra", "HOD / Committee"]
    ]

    for col_idx, h in enumerate(headers):
        cell = rev_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)

    for row_idx, row_data in enumerate(data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_data):
            cell = rev_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    # Guidance Box
    p_guide = doc.add_paragraph()
    p_guide.paragraph_format.space_before = Pt(14)
    p_guide.paragraph_format.space_after = Pt(14)
    r_gn = p_guide.add_run("Guidance Note: ")
    r_gn.bold = True
    r_gn.font.color.rgb = RGBColor(37, 99, 235)
    r_gt = p_guide.add_run(
        "This Software Requirements Specification document conforms to the IEEE 830-1998 standard recommended practice. "
        "All sections are strictly designed for 3rd-year university lab evaluation, project reviews, and system design baselines."
    )
    r_gt.italic = True

    # ------------------ SECTION 1: INTRODUCTION ------------------
    h1 = doc.add_heading("1. Introduction", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    h2 = doc.add_heading("1.1 Purpose", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    p = doc.add_paragraph(
        "The purpose of this Software Requirements Specification (SRS) document is to provide a complete, clear, and unambiguous definition "
        "of the functionality, external interfaces, performance targets, and constraints of the proposed system: 'IoT Smart Home Automation & Energy Management System'.\n\n"
        "This specification serves as a binding reference agreement between student developer Parth Mishra, academic supervisor Ms. Anupam, "
        "project evaluators, and prospective end users during the 3rd-year engineering curriculum."
    )

    h2 = doc.add_heading("1.2 Scope of the System", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph(
        "The proposed application is designed to solve domestic electrical wastage, uncoordinated manual switching, and absence of granular power "
        "telemetry by delivering an end-to-end automated platform connecting physical ESP32 microcontrollers, lightweight MQTT messaging, and an interactive real-time dashboard. "
        "Key boundary guidelines include:"
    )

    p_in = doc.add_paragraph(style='List Bullet')
    p_in.add_run("In-Scope Capabilities: ").bold = True
    p_in.add_run(
        "Centralized sensor data ingestion (Lux, PIR Motion, Ultrasonic Distance), remote and automated appliance actuation (Light, Fan), "
        "multi-tier system mode switching (Home, Away, Sleep), real-time intrusion alerting, cumulative kilowatt-hour (kWh) calculation, daily energy audit tracking, and dynamic threshold calibration."
    )

    p_out = doc.add_paragraph(style='List Bullet')
    p_out.add_run("Out-of-Scope Boundaries: ").bold = True
    p_out.add_run(
        "Industrial high-voltage three-phase motor interfacing, direct payment gateway processing for electricity bills (mock utility billing estimation utilized), "
        "and hardware fabrication beyond standard microcontroller and relay breakout boards."
    )

    p_ben = doc.add_paragraph(style='List Bullet')
    p_ben.add_run("Expected Benefits: ").bold = True
    p_ben.add_run(
        "Reduction of domestic power consumption by 30–40% via occupancy-based automatic cutoff, sub-second latency for manual control, complete operational transparency through audit logging, "
        "and immediate accessibility across devices."
    )

    h2 = doc.add_heading("1.3 Definitions, Acronyms, and Abbreviations", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    def_table = doc.add_table(rows=9, cols=3)
    def_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(def_table)
    def_headers = ["Category", "Term / Acronym", "Definition / Standard Context"]
    def_data = [
        ["Standard", "SRS", "Software Requirements Specification (IEEE Std 830-1998 format)."],
        ["Hardware", "ESP32", "Low-cost, low-power system on a chip with integrated Wi-Fi and Bluetooth by Espressif."],
        ["Hardware", "PIR", "Passive Infrared Sensor (HC-SR501) detecting human motion via infrared radiation changes."],
        ["Hardware", "LDR", "Light Dependent Resistor utilized for measuring ambient environmental luminosity (Lux)."],
        ["Protocol", "MQTT", "Message Queuing Telemetry Transport; lightweight pub/sub standard (ISO/IEC 20922)."],
        ["Security", "RBAC", "Role-Based Access Control enforcing permission barriers across user tiers."],
        ["Database", "CRUD / WAL", "Create, Read, Update, Delete / Write-Ahead Logging in SQLite for high concurrency."],
        ["Frontend", "Streamlit", "Python reactive dashboard framework rendering live telemetry and controls."]
    ]
    for col_idx, h in enumerate(def_headers):
        cell = def_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(def_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = def_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx in [0, 1]:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("1.4 References", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    refs = [
        "IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.",
        "Software Engineering (10th Edition): Ian Sommerville, Pearson Education.",
        "MQTT Specification v3.1.1: OASIS Standard, Edited by Andrew Banks and Rahul Gupta.",
        "Eclipse Paho: Paho Python MQTT Client Library (paho.mqtt.python).",
        "Espressif Systems: ESP32 Series Technical Reference Manual & Arduino Core Docs.",
        "SQLite Documentation: SQLite Database Engine Architectural Concurrency Model."
    ]
    for ref in refs:
        p_ref = doc.add_paragraph(style='List Bullet')
        p_ref.add_run(ref)

    h2 = doc.add_heading("1.5 Document Overview", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph(
        "The remainder of this SRS is partitioned into structural sections: Section 2 outlines the product perspective, target user personas, operational context, and design constraints. "
        "Section 3 itemizes detailed functional requirements organized into logical software modules. Section 4 specifies external interfaces (UI, Hardware, Software, Network). "
        "Section 5 defines non-functional attributes (Performance, Reliability, Security). Finally, Section 6 provides standard academic modeling diagrams, followed by Section 7 academic review signatures."
    )

    doc.add_page_break()

    # ------------------ SECTION 2: OVERALL DESCRIPTION ------------------
    h1 = doc.add_heading("2. Overall Description", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    h2 = doc.add_heading("2.1 Product Perspective", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph(
        "The project is structured as a self-contained, distributed multi-tier cyber-physical system comprising an edge sensing/actuation tier, an asynchronous message broker, "
        "a persistent timeseries database backend, and a reactive presentation layer."
    )

    # ASCII Architecture Box
    p_arch = doc.add_paragraph()
    p_arch.paragraph_format.space_before = Pt(8)
    p_arch.paragraph_format.space_after = Pt(8)
    r_arch = p_arch.add_run(
        "                    +------------------------------------+\n"
        "                    |  ESP32 Hardware / Simulator Twin   |\n"
        "                    |  (LDR, PIR, Ultrasonic, Relays)    |\n"
        "                    +-----------------+------------------+\n"
        "                                      |\n"
        "                       MQTT (home/room1/sensors, cmd, alerts)\n"
        "                                      |\n"
        "                    +-----------------v------------------+\n"
        "                    |         MQTT Message Broker        |\n"
        "                    |        (HiveMQ / Mosquitto)        |\n"
        "                    +-----------------+------------------+\n"
        "                                      |\n"
        "                   +------------------+------------------+\n"
        "                   |                                     |\n"
        "    +--------------v--------------+       +--------------v--------------+\n"
        "    |    Backend MQTT Listener    |       |     Streamlit Dashboard     |\n"
        "    | (backend/mqtt_listener.py)  |       |   (dashboard/app.py & pages)|\n"
        "    +--------------+--------------+       +--------------+--------------+\n"
        "                   |                                     ^\n"
        "              Writes To                              Reads From\n"
        "                   |                                     |\n"
        "                   +-------------> SQLite <--------------+\n"
        "                             (smart_home.db)\n"
    )
    r_arch.font.name = 'Courier New'
    r_arch.font.size = Pt(8.5)
    r_arch.font.color.rgb = RGBColor(30, 41, 59)

    h2 = doc.add_heading("2.2 User Classes and Characteristics", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    user_table = doc.add_table(rows=4, cols=3)
    user_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(user_table)
    u_headers = ["User Role / Persona", "Technical Proficiency", "Core Responsibilities & Rights"]
    u_data = [
        ["System Administrator", "High (DevOps / Hardware / DB)", "Complete access: sensor calibration, threshold adjustments, tariff rate configuration, raw telemetry auditing, and system maintenance."],
        ["Primary Resident", "Intermediate (General Web User)", "Authenticated dashboard access: viewing environmental telemetry, manual appliance switching, mode switching (Home/Away/Sleep), energy billing review, and alert acknowledgment."],
        ["Guest / Occupant", "Basic", "Read-only environmental status view with local room toggle capability; restricted from global settings, tariff rates, and security logs."]
    ]
    for col_idx, h in enumerate(u_headers):
        cell = user_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(u_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = user_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("2.3 Operating Environment", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    env_items = [
        ("Client Requirements: ", "Modern web browser (Google Chrome >= v110, Mozilla Firefox >= v108, Edge, Safari); minimum display resolution 1366x768 for desktop, responsive view down to 360x640."),
        ("Server Runtime Environment: ", "Microsoft Windows 10/11 or Linux (Ubuntu 22.04 LTS / Debian 12); Python 3.10+ runtime, Streamlit 1.30+, Paho-MQTT 1.6+/2.0+."),
        ("Database Storage Tier: ", "SQLite 3.38+ with Write-Ahead Logging (WAL) enabled for simultaneous concurrent reading and writing without database locks."),
        ("Edge Hardware Environment: ", "ESP32-WROOM-32 microcontroller node with 2.4 GHz 802.11 b/g/n Wi-Fi, 5V Dual Relay module, HC-SR501 PIR sensor, LDR sensor, HC-SR04 ultrasonic sensor.")
    ]
    for bold_txt, norm_txt in env_items:
        p_env = doc.add_paragraph(style='List Bullet')
        p_env.add_run(bold_txt).bold = True
        p_env.add_run(norm_txt)

    h2 = doc.add_heading("2.4 Design and Implementation Constraints", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    constraints = [
        ("Academic Budget Constraint: ", "Utilization of open-source libraries and zero-cost public/local broker infrastructure (HiveMQ public broker / Mosquitto), eliminating commercial cloud costs."),
        ("Security Compliance: ", "Safe parameterization of all database queries to prevent SQL injection; environment isolation of passwords and broker tokens in .env files."),
        ("Modularity Standards: ", "Strict modular separation of concerns between edge telemetry ingestion, rule evaluation, database persistence, and presentation."),
        ("Dual-Node Portability: ", "Firmware contract compatibility ensuring the system operates with identical behavior on the real ESP32 board or the high-fidelity Python edge twin.")
    ]
    for bold_txt, norm_txt in constraints:
        p_c = doc.add_paragraph(style='List Bullet')
        p_c.add_run(bold_txt).bold = True
        p_c.add_run(norm_txt)

    h2 = doc.add_heading("2.5 Assumptions and Dependencies", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    assumptions = [
        ("Assumptions: ", "Edge microcontroller and host server maintain Wi-Fi connectivity with minimal bandwidth of 512 Kbps; local client system clocks synchronized via NTP."),
        ("Dependencies: ", "High-availability uptime of the MQTT message broker on TCP Port 1883 or WebSocket Port 8884.")
    ]
    for bold_txt, norm_txt in assumptions:
        p_a = doc.add_paragraph(style='List Bullet')
        p_a.add_run(bold_txt).bold = True
        p_a.add_run(norm_txt)

    doc.add_page_break()

    # ------------------ SECTION 3: FUNCTIONAL REQUIREMENTS ------------------
    h1 = doc.add_heading("3. System Features and Functional Requirements", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)
    doc.add_paragraph("Requirements are categorized by functional subsystem modules with unique requirement identifiers (FR-x.x):")

    h2 = doc.add_heading("3.1 Module 1: System Mode Governance & Access Control", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    m1_table = doc.add_table(rows=6, cols=4)
    m1_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(m1_table)
    m_headers = ["Req ID", "Feature Description", "Input / Validation Rule", "Priority"]
    m1_data = [
        ["FR-1.1", "System Operating Mode Selector", "Accepts one of three predefined operational states: Home, Away, or Sleep.", "High"],
        ["FR-1.2", "Mode State Broadcast", "Dispatches MQTT message to home/room1/cmd with payload {\"device\":\"mode\", \"state\":\"<value>\"}.", "High"],
        ["FR-1.3", "Security Guarding (Away Mode)", "When mode is set to Away, any motion triggers a high-severity intrusion alert record.", "High"],
        ["FR-1.4", "Power Conservation (Sleep Mode)", "When mode transitions to Sleep, ambient appliances receive automatic turn-off triggers.", "Medium"],
        ["FR-1.5", "Heartbeat Silence Detection", "Flags edge node as Offline if zero telemetry packets are detected for > 10 seconds.", "Medium"]
    ]
    for col_idx, h in enumerate(m_headers):
        cell = m1_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(m1_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = m1_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx in [0, 3]:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("3.2 Module 2: IoT Telemetry Ingestion, Appliance Actuation & Rule Engine", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    m2_table = doc.add_table(rows=6, cols=4)
    m2_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(m2_table)
    m2_data = [
        ["FR-2.1", "Continuous Telemetry Ingestion", "Parses JSON from home/room1/sensors containing ts, motion, lux, distance_cm, light, fan, mode.", "High"],
        ["FR-2.2", "Manual Appliance Actuation", "Dispatches instantaneous JSON command to home/room1/cmd ({\"device\": \"light\"|\"fan\", \"state\": \"on\"|\"off\"}) in < 200ms.", "High"],
        ["FR-2.3", "Automated Light Control", "Turns Light on if lux < threshold AND motion == True; shuts off after inactivity timeout.", "High"],
        ["FR-2.4", "Automated Fan Regulation", "Turns Fan on if distance_cm <= threshold (presence at desk); turns off when vacant.", "Medium"],
        ["FR-2.5", "Actuation Event Auditing", "Writes every state transition to device_events with timestamp and source (auto, dashboard, manual).", "High"]
    ]
    for col_idx, h in enumerate(m_headers):
        cell = m2_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(m2_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = m2_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx in [0, 3]:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("3.3 Module 3: Energy Consumption Analytics, Anomaly Alerts & Calibration", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    m3_table = doc.add_table(rows=6, cols=4)
    m3_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(m3_table)
    m3_data = [
        ["FR-3.1", "Live Energy & Costing Calculation", "Calculates active operating minutes; computes kWh based on wattage; estimates financial bill based on tariff rate.", "High"],
        ["FR-3.2", "Day-by-Day Historical Breakdown", "Aggregates daily kWh from energy_log table; renders daily bar charts and appliance usage breakdown.", "Medium"],
        ["FR-3.3", "Security & System Alert Generation", "Detects intrusion, forgotten_device, and offline conditions; writes to alerts table.", "High"],
        ["FR-3.4", "Alert Triage & Acknowledgment", "Displays active alert cards with color severity; permits one-click user acknowledgment.", "Medium"],
        ["FR-3.5", "Dynamic System Calibration", "Adjusts Lux threshold (0–1000), distance threshold (10–200 cm), tariff rate ($/₹), and device wattages via UI.", "Medium"]
    ]
    for col_idx, h in enumerate(m_headers):
        cell = m3_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(m3_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = m3_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx in [0, 3]:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    doc.add_page_break()

    # ------------------ SECTION 4: INTERFACE REQUIREMENTS ------------------
    h1 = doc.add_heading("4. External Interface Requirements", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    h2 = doc.add_heading("4.1 User Interfaces (UI)", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph("The interface complies with modern responsive design principles:")
    uis = [
        ("Live Control View (app.py): ", "Top system mode selector, appliance cards for Light and Fan with toggle switches and state badges, and live sensor cards for Lux, Distance, and Motion."),
        ("Energy Analytics View (1_Energy.py): ", "Summary metrics (Total kWh, Total Cost, Active Load), 7-day usage trends, and device power distribution."),
        ("Alerts Center (2_Alerts.py): ", "Filterable incident table with severity badges and dismissal buttons."),
        ("Calibration Console (3_Settings.py): ", "Dynamic sliders for lux/distance thresholds and tariff multipliers.")
    ]
    for bold_txt, norm_txt in uis:
        p_u = doc.add_paragraph(style='List Bullet')
        p_u.add_run(bold_txt).bold = True
        p_u.add_run(norm_txt)

    h2 = doc.add_heading("4.2 Hardware Interfaces", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    hw_table = doc.add_table(rows=7, cols=4)
    hw_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(hw_table)
    hw_headers = ["Component", "Interface Type", "ESP32 GPIO Pin", "Operating Specification"]
    hw_data = [
        ["HC-SR501 PIR Sensor", "Digital Input", "GPIO 13", "High (3.3V) on motion detected; Low (0V) quiescent."],
        ["LDR Light Sensor", "Analog Input (ADC1)", "GPIO 34", "12-bit ADC mapping 0–4095 to 0–1000 Lux."],
        ["HC-SR04 Ultrasonic Trigger", "Digital Output", "GPIO 5", "10 µs trigger pulse to initiate sonic burst."],
        ["HC-SR04 Ultrasonic Echo", "Digital Input (Divider)", "GPIO 18", "Pulse width timing converted to distance in cm."],
        ["Relay 1 (Main Light)", "Digital Output", "GPIO 22", "Optocoupler-isolated relay switching domestic load."],
        ["Relay 2 (Room Fan)", "Digital Output", "GPIO 23", "Optocoupler-isolated relay switching motor load."]
    ]
    for col_idx, h in enumerate(hw_headers):
        cell = hw_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(hw_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = hw_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx in [0, 2]:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("4.3 Software & Communication Interfaces", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)
    softs = [
        ("Database Interface: ", "SQLite 3.38+ with transactional row factories and indexes on timestamps."),
        ("Messaging Protocol: ", "MQTT v3.1.1 over TCP Port 1883 or WebSocket Port 8884."),
        ("Data Serialization: ", "Lightweight UTF-8 JSON payloads for telemetry, commands, and alerts.")
    ]
    for bold_txt, norm_txt in softs:
        p_s = doc.add_paragraph(style='List Bullet')
        p_s.add_run(bold_txt).bold = True
        p_s.add_run(norm_txt)

    # ------------------ SECTION 5: NON-FUNCTIONAL REQUIREMENTS ------------------
    h1 = doc.add_heading("5. Non-Functional Requirements (NFRs)", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    nfr_table = doc.add_table(rows=5, cols=3)
    nfr_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(nfr_table)
    nfr_headers = ["Attribute", "Target Metric / Standard", "Verification & Testing Method"]
    nfr_data = [
        ["5.1 Performance", "• Telemetry to DB latency < 250ms.\n• Manual switch dispatch < 200ms.\n• Page initial load time < 2.0s.", "Timestamp difference logging; synthetic network latency benchmarking."],
        ["5.2 Security", "• Credentials isolated in .env.\n• Parameterized queries against SQL injection.\n• Sanitized topic routing.", "OWASP automated vulnerability inspection; static code audit."],
        ["5.3 Reliability", "• Availability >= 99.0% during review.\n• Automatic MQTT reconnection upon drop.\n• Crash-safe SQLite WAL journaling.", "48-hour soak testing; intentional Wi-Fi router disconnection and reconnection tests."],
        ["5.4 Portability", "• Operates identically on Windows, Linux, and macOS.\n• Transparent edge simulation twin.", "Multi-OS test runs and responsive viewport verification."]
    ]
    for col_idx, h in enumerate(nfr_headers):
        cell = nfr_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(nfr_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = nfr_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    doc.add_page_break()

    # ------------------ SECTION 6: DESIGN MODELS ------------------
    h1 = doc.add_heading("6. System Design and Analysis Models", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph("University evaluation rubrics require standard graphical analysis models illustrating the dynamic and static behavior of the application:")

    dm_table = doc.add_table(rows=6, cols=3)
    dm_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(dm_table)
    dm_headers = ["Diagram Type", "Objective & Scope", "Deliverable Format"]
    dm_data = [
        ["Use Case Diagram", "Maps actors (Resident, Admin, Edge Node) to functional operations.", "UML Standard diagram with boundary definitions."],
        ["Data Flow Diagram (Level 0)", "Illustrates high-level entity interactions and system data boundary.", "Context-level flow model."],
        ["Data Flow Diagram (Level 1)", "Decomposes system into telemetry ingestion, rule evaluation, and analytics.", "Modular decomposition flow model."],
        ["Entity-Relationship (ERD)", "Details database tables, attributes, primary/foreign keys, and cardinality.", "Crow's Foot notation schema with 3NF normalization."],
        ["Sequence Diagram", "Details chronological message exchanges during telemetry and actuation.", "UML Sequence diagram with error/exception handling."]
    ]
    for col_idx, h in enumerate(dm_headers):
        cell = dm_table.cell(0, col_idx)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].bold = True
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    for row_idx, row_val in enumerate(dm_data, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, val in enumerate(row_val):
            cell = dm_table.cell(row_idx, col_idx)
            cell.paragraphs[0].text = val
            if col_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    h2 = doc.add_heading("6.1 Entity-Relationship (Database Schema Specification)", level=2)
    h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

    erd_desc = doc.add_paragraph()
    r_erd = erd_desc.add_run(
        "1. sensor_readings: (id INTEGER PK AUTOINCREMENT, ts INTEGER, motion INTEGER, lux REAL, distance_cm REAL, light TEXT, fan TEXT, mode TEXT)\n"
        "2. device_events: (id INTEGER PK AUTOINCREMENT, ts INTEGER, device TEXT, state TEXT, source TEXT)\n"
        "3. alerts: (id INTEGER PK AUTOINCREMENT, ts INTEGER, type TEXT, severity TEXT, acknowledged INTEGER DEFAULT 0)\n"
        "4. energy_log: (date TEXT, device TEXT, on_minutes REAL, kwh REAL, PRIMARY KEY (date, device))\n"
        "5. settings: (key TEXT PRIMARY KEY, value TEXT)\n"
    )
    r_erd.font.name = 'Courier New'
    r_erd.font.size = Pt(9.5)

    # ------------------ SECTION 7: ACADEMIC REVIEW & SIGN-OFF ------------------
    h1 = doc.add_heading("7. Academic Review & Sign-Off", level=1)
    h1.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "This Software Requirements Specification document for the project titled 'IoT Smart Home Automation & Energy Management System' "
        "submitted by Parth Mishra (Roll No: 2400320100789) has been formally reviewed, evaluated, and approved by the academic supervisory "
        "committee for fulfillment of the 3rd-year engineering curriculum milestone."
    )

    sign_table = doc.add_table(rows=1, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_table.autofit = False

    for c in sign_table.rows[0].cells:
        c.width = Inches(2.1)

    s1 = sign_table.rows[0].cells[0].paragraphs[0]
    s1.paragraph_format.space_before = Pt(48)
    s1.add_run("___________________________\n").bold = True
    s1.add_run("Ms. Anupam\n").bold = True
    s1.add_run("Project Guide / Assistant Professor\n")
    s1.add_run("Dept. of Computer Science & Engg.\n")
    s1.add_run("Date: ____________________")

    s2 = sign_table.rows[0].cells[1].paragraphs[0]
    s2.paragraph_format.space_before = Pt(48)
    s2.add_run("___________________________\n").bold = True
    s2.add_run("Internal Examiner\n").bold = True
    s2.add_run("Dept. of Computer Science\n")
    s2.add_run("and Engineering\n")
    s2.add_run("Date: ____________________")

    s3 = sign_table.rows[0].cells[2].paragraphs[0]
    s3.paragraph_format.space_before = Pt(48)
    s3.add_run("___________________________\n").bold = True
    s3.add_run("Head of Department (HOD)\n").bold = True
    s3.add_run("Dept. of Computer Science\n")
    s3.add_run("and Engineering\n")
    s3.add_run("Date: ____________________")

    out_path = Path("SRS_DOCUMENT.docx")
    doc.save(str(out_path))
    print(f"Successfully generated {out_path.resolve()}")

if __name__ == "__main__":
    build_docx()
