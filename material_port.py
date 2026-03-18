import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# CONFIG
# -----------------------------

SMTP_EMAIL = "prakhar.chandel@jute-india.com"
SMTP_PASSWORD = "yees jhwl rnxj jeyy"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

ADMIN_EMAILS = [
    "soham.panda@jute-india.com",
    "payal.sinha@jute-india.com",
    "anushka.dutta@jute-india.com",
    "nitin.pandey@jute-india.com"
]

REQUEST_FILE = "material_requests.xlsx"

# -----------------------------
# DATA
# -----------------------------

DEPT_DEFAULT_MAP = {
    "Batching": ["002","023"],
    "Carding": ["002"],
    "Drawing": ["002"],
    "Spinning": ["002"],
    "Winding": ["002"],
    "Twisting": ["002"]
}

GLOBAL_CLASSES = ["001","019","032"]

SUBCLASS_DATA = {
    "001": ["CL_FACTORY_CLASS","FG_CLASS","JUTE_CLASS","CL_MATERIAL_CLASS"],
    "019": ["WC_STIL"],
    "032": ["PO_RELEASE","PR_RELEASE"],
    "023": ["BATCH_CLASS","FG_BATCH_CLASS","SPRDER_MAT_CLASS"],
    "002":[
        "CL_CARD_MIJM","CL_CARD_SGJM","CL_CARD_SHJM","CL_CARD_ALL_MILLS",
        "CL_COP_MIJM","CL_COP_SGJM","CL_COP_SHJM",
        "CL_DRAW_MIJM","CL_DRAW_SGJM","CL_DRAW_SHJM","CL_DRAW_ALL_MILLS",
        "CL_SOFT_MIJM","CL_SOFT_SGJM","CL_SOFT_SHJM",
        "CL_SPIN_MIJM","CL_SPIN_SGJM","CL_SPIN_SHJM","CL_SPIN_ALL_MILLS",
        "CL_SPOOL_MIJM","CL_SPOOL_SGJM","CL_SPOOL_SHJM",
        "CL_SPREAD_MIJM","CL_SPREAD_SGJM","CL_SPREAD_SHJM",
        "CL_WINDING_ALL_MILLS","CL_TWISTING_ALL_MILLS",
        "CL_FACTORY_CLASS"
    ]
}

DEPT_KEYWORDS = {
    "Batching":["SOFT","SPREAD"],
    "Carding":["CARD"],
    "Drawing":["DRAW"],
    "Spinning":["SPIN"],
    "Winding":["COP","SPOOL","WINDING"],
    "Twisting":["TWISTING"]
}

# -----------------------------
# SESSION STATE
# -----------------------------

if "materials" not in st.session_state:
    st.session_state.materials = []

# -----------------------------
# FUNCTIONS
# -----------------------------

def generate_request_id():
    if not os.path.exists(REQUEST_FILE):
        return "MAT-0001"

    df = pd.read_excel(REQUEST_FILE, engine="openpyxl")

    if df.empty:
        return "MAT-0001"

    last = df["Request_ID"].iloc[-1]
    number = int(last.split("-")[1]) + 1

    return f"MAT-{number:04d}"


def save_request(data):
    df = pd.DataFrame([data])

    if os.path.exists(REQUEST_FILE):
        old = pd.read_excel(REQUEST_FILE, engine="openpyxl")
        df = pd.concat([old, df], ignore_index=True)

    df.to_excel(REQUEST_FILE, index=False)


def send_admin_email(data):

    materials_text = "\n".join(
        [f"{m['attr']} ({m['unit']})" for m in data['Attributes']]
    )

    body = f"""
Material Creation Request

Request ID: {data['Request_ID']}
Date: {data['Date']}

Mill: {data['Mill']}
Department: {data['Department']}

Requested By(dept): {data['Requested_By_dept']}
Requested By: {data['Requested_By']}
Requester Email: {data['Requester_Email']}

Machine: {data['Machine']}

Class: {data['Class']}
Subclass: {data['Subclass']}

Materials:
{materials_text}

Reason:
{data['Reason']}
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Material Request {data['Request_ID']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(ADMIN_EMAILS)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, ADMIN_EMAILS, msg.as_string())
        server.quit()
    except:
        pass


def get_subclass_options(mill, dept, selected_class):

    pool = SUBCLASS_DATA.get(selected_class, [])

    if selected_class == "002":
        keywords = DEPT_KEYWORDS.get(dept, [])

        if not keywords:
            return ["CL_FACTORY_CLASS"]

        filtered = [
            s for s in pool
            if any(k in s for k in keywords)
        ]

        return filtered if filtered else ["CL_FACTORY_CLASS"]

    return pool

# -----------------------------
# UI
# -----------------------------

st.set_page_config(page_title="Material Master Portal", layout="wide")

st.title("Material Creation Form")

col1, col2 = st.columns(2)

with col1:
    mill = st.selectbox("Mill", ["MIJM", "SGJM", "SHJM", "SSKT"])

    dept = st.selectbox(
        "Department",
        sorted(list(DEPT_DEFAULT_MAP.keys()))
    )

    req_by_dept = st.text_input(
        "Requested By (Dept)",
        placeholder="e.g. Name from department"
    )

    req_by = st.text_input(
        "Requested By (Store)",
        placeholder="e.g. Sulagna Roy, Sanat Das"
    )

    req_mail = st.text_input(
        "Requester Email",
        placeholder="e.g. store.hjm@jute-india.com"
    )

    machine = st.text_input(
        "Machine",
        placeholder="e.g. General, 030BC021"
    )

with col2:
    default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])
    class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))

    selected_class = st.selectbox("Class", class_options)

    subclass_options = get_subclass_options(mill, dept, selected_class)

    subclass = st.selectbox("Subclass", subclass_options)

    reason = st.text_area(
        "Reason",
        placeholder="Explain why new material is required"
    )

# ---------------- MATERIALS ----------------

st.subheader("Materials")

if st.button("➕ Add Material"):
    st.session_state.materials.append({"attr": "", "unit": "SET"})

units = ["SET", "Pcs", "L", "Kg"]

for i, mat in enumerate(st.session_state.materials):

    col1, col2, col3 = st.columns([4, 2, 1])

    with col1:
        st.session_state.materials[i]["attr"] = st.text_input(
            f"Material {i+1}",
            value=mat["attr"],
            key=f"attr_{i}"
        )

    with col2:
        st.session_state.materials[i]["unit"] = st.selectbox(
            f"Unit {i+1}",
            units,
            index=units.index(mat["unit"]) if mat["unit"] in units else 0,
            key=f"unit_{i}"
        )

    with col3:
        if st.button("❌", key=f"del_{i}"):
            st.session_state.materials.pop(i)
            st.rerun()

# ---------------- SUBMIT ----------------

if st.button("Submit Request"):

    if (
        not req_by or
        not req_mail or
        "@" not in req_mail or
        not machine or
        not reason or
        len(st.session_state.materials) == 0
    ):
        st.error("Fill all required fields & add at least 1 material")

    else:

        request_id = generate_request_id()

        data = {
            "Request_ID": request_id,
            "Date": datetime.now(),
            "Mill": mill,
            "Department": dept,
            "Requested_By_dept": req_by_dept,
            "Requested_By": req_by,
            "Requester_Email": req_mail,
            "Machine": machine,
            "Class": selected_class,
            "Subclass": subclass,
            "Attributes": st.session_state.materials.copy(),
            "Reason": reason,
            "Status": "Pending"
        }

        save_request(data)
        send_admin_email(data)

        st.success(f"Request {request_id} submitted")

        st.session_state.materials = []
