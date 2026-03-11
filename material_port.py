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

ADMIN_EMAILS = ["soham.panda@jute-india.com"]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

REQUEST_FILE = "material_requests.xlsx"
LOG_FILE = "logs.xlsx"

# -----------------------------
# MAPPING DATA
# -----------------------------

DEPT_DEFAULT_MAP = {
    "Batching": ["002","023"],
    "Carding": ["002"],
    "Drawing": ["002"],
    "Spinning": ["002"],
    "Winding": ["002"],
    "Twisting": ["002"],
    "Beaming": ["002"],
    "Weaving": ["002"],
    "Sack Sewing": ["002"],
    "Finishing": ["002"],
    "Bail - Press": ["002"],
    "Workshop": ["002"],
    "Boiler/Furnace": ["002"],
    "Civil": ["002"],
    "Dispensary": ["001"],
    "EDP": ["002"],
    "General": ["002"],
    "Packaging Materials": ["002"],
    "Power House": ["002"],
    "Production Material": ["002"]
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
# FUNCTIONS
# -----------------------------

def generate_request_id():

    if not os.path.exists(REQUEST_FILE):
        return "MAT-0001"

    df = pd.read_excel(REQUEST_FILE)

    if df.empty:
        return "MAT-0001"

    last = df["Request_ID"].iloc[-1]
    number = int(last.split("-")[1]) + 1

    return f"MAT-{number:04d}"


def save_request(data):

    df = pd.DataFrame([data])

    if os.path.exists(REQUEST_FILE):
        old = pd.read_excel(REQUEST_FILE)
        df = pd.concat([old,df],ignore_index=True)

    df.to_excel(REQUEST_FILE,index=False)


def write_log(user,action):

    log = {
        "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User":user,
        "Action":action
    }

    df = pd.DataFrame([log])

    if os.path.exists(LOG_FILE):
        old = pd.read_excel(LOG_FILE)
        df = pd.concat([old,df],ignore_index=True)

    df.to_excel(LOG_FILE,index=False)


def send_admin_email(data):

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

Attributes: {data['Attributes']}

Reason:
{data['Reason']}
"""

    msg = MIMEText(body)

    msg["Subject"] = f"Material Request {data['Request_ID']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(ADMIN_EMAILS)

    server = smtplib.SMTP(SMTP_SERVER,SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL,SMTP_PASSWORD)
    server.sendmail(SMTP_EMAIL,ADMIN_EMAILS,msg.as_string())
    server.quit()


def send_approval_email(email,request_id):

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

    server = smtplib.SMTP(SMTP_SERVER,SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL,SMTP_PASSWORD)
    server.sendmail(SMTP_EMAIL,[email],msg.as_string())
    server.quit()


def get_subclass_options(dept,selected_class):

    pool = SUBCLASS_DATA.get(selected_class,[])

    if selected_class == "002":

        keywords = DEPT_KEYWORDS.get(dept,[])

        if not keywords:
            return ["CL_FACTORY_CLASS"]

        filtered = [s for s in pool if any(k in s for k in keywords)]

        return filtered if filtered else ["CL_FACTORY_CLASS"]

    return pool


# -----------------------------
# STREAMLIT UI
# -----------------------------

st.set_page_config(page_title="Material Master Portal",layout="wide")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Create Request","Admin Panel","Logs"]
)

# -----------------------------
# CREATE REQUEST
# -----------------------------

if menu == "Create Request":

    st.title("Material Creation Form")

    col1,col2 = st.columns(2)

    with col1:

        mill = st.selectbox("Mill",["MIJM","SGJM","SHJM","SSKT"])

        dept = st.selectbox(
            "Department",
            sorted(list(DEPT_DEFAULT_MAP.keys()))
        )

        req_by_dept = st.text_input("Requested By (Department)")
        req_by = st.text_input("Requested By (Store)")
        req_mail = st.text_input("Requester Email")
        machine = st.text_input("Machine")

    with col2:

        default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])

        class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))

        selected_class = st.selectbox("Class", class_options)

        subclass_options = get_subclass_options(dept,selected_class)

        subclass = st.selectbox("Subclass",subclass_options)

        attr = st.text_input("Material Attributes")
        reason = st.text_area("Reason")

    if st.button("Submit Request"):

        if not mill or not dept or not req_by or not req_mail or not machine or not attr or not reason:

            st.error("All fields mandatory")

        else:

            request_id = generate_request_id()

            data = {
                "Request_ID":request_id,
                "Date":datetime.now(),
                "Mill":mill,
                "Department":dept,
                "Requested_By_dept":req_by_dept,
                "Requested_By":req_by,
                "Requester_Email":req_mail,
                "Machine":machine,
                "Class":selected_class,
                "Subclass":subclass,
                "Attributes":attr,
                "Reason":reason,
                "Status":"Pending"
            }

            save_request(data)
            send_admin_email(data)
            write_log(req_by,f"Submitted {request_id}")

            st.success(f"Request {request_id} submitted")

# -----------------------------
# ADMIN PANEL
# -----------------------------

elif menu == "Admin Panel":

    st.title("Admin Panel")

    user = st.text_input("Username")
    pwd = st.text_input("Password",type="password")

    if st.button("Login"):

        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            st.session_state.admin = True

    if st.session_state.get("admin"):

        df = pd.read_excel(REQUEST_FILE)

        st.subheader("Dashboard")

        col1,col2,col3 = st.columns(3)

        col1.metric("Total Requests",len(df))
        col2.metric("Pending",len(df[df["Status"]=="Pending"]))
        col3.metric("Approved",len(df[df["Status"]=="Approved"]))

        st.dataframe(df)

        pending = df[df["Status"]=="Pending"]

        st.subheader("Pending Approvals")

        for i,row in pending.iterrows():

            st.write(f"{row['Request_ID']} | {row['Machine']} | {row['Department']}")

            if st.button(f"Approve {row['Request_ID']}"):

                full = pd.read_excel(REQUEST_FILE)

                full.loc[full["Request_ID"]==row["Request_ID"],"Status"] = "Approved"

                full.to_excel(REQUEST_FILE,index=False)

                send_approval_email(row["Requester_Email"],row["Request_ID"])

                write_log("ADMIN",f"Approved {row['Request_ID']}")

                st.success("Approved")

                st.rerun()

# -----------------------------
# LOGS
# -----------------------------

elif menu == "Logs":

    st.title("System Logs")

    if os.path.exists(LOG_FILE):

        df = pd.read_excel(LOG_FILE)

        st.dataframe(df)

    else:

        st.info("No logs yet")
