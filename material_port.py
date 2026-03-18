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

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

REQUEST_FILE = "material_requests.xlsx"
LOG_FILE = "logs.xlsx"

# -----------------------------
# SESSION STATE INIT
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


def write_log(user, action):
    log = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": user,
        "Action": action
    }

    df = pd.DataFrame([log])

    if os.path.exists(LOG_FILE):
        old = pd.read_excel(LOG_FILE, engine="openpyxl")
        df = pd.concat([old, df], ignore_index=True)

    df.to_excel(LOG_FILE, index=False)


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


def send_approval_email(email, request_id):

    body = f"""
Hello,

Your request {request_id} has been APPROVED.

Material has been successfully created.

Regards,
IT Team
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Material Created - {request_id}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [email], msg.as_string())
        server.quit()
    except:
        pass


# -----------------------------
# UI
# -----------------------------

st.set_page_config(page_title="Material Master Portal", layout="wide")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Create Request", "Admin Panel", "Logs"]
)

# -----------------------------
# CREATE REQUEST
# -----------------------------

if menu == "Create Request":

    st.title("Material Creation Form")

    col1, col2 = st.columns(2)

    with col1:
        mill = st.selectbox("Mill", ["MIJM", "SGJM", "SHJM", "SSKT"])
        dept = st.selectbox("Department", [
            "Batching","Carding","Drawing","Spinning","Winding","Twisting"
        ])

        req_by_dept = st.text_input("Requested By (Dept)")
        req_by = st.text_input("Requested By (Store)")
        req_mail = st.text_input("Requester Email")
        machine = st.text_input("Machine")

    with col2:
        selected_class = st.selectbox("Class", ["001", "002", "019", "032"])
        subclass = st.text_input("Subclass")
        reason = st.text_area("Reason")

    # ---------------- MATERIAL SECTION ----------------

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
            write_log(req_by, f"Submitted {request_id}")

            st.success(f"Request {request_id} submitted")

            st.session_state.materials = []
