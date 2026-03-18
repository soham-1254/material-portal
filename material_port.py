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
SMTP_PASSWORD = "your_app_password_here"
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
# MAPPING DATA (UNCHANGED)
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
        "CL_CARD_MIJM","CL_CARD_SGJM","CL_CARD_SHJM",
        "CL_DRAW_MIJM","CL_DRAW_SGJM","CL_DRAW_SHJM",
        "CL_SPIN_MIJM","CL_SPIN_SGJM","CL_SPIN_SHJM",
        "CL_SPOOL_MIJM","CL_SPOOL_SGJM","CL_SPOOL_SHJM",
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
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(REQUEST_FILE, index=False)

def write_log(user, action):
    log = {
        "Timestamp": datetime.now(),
        "User": user,
        "Action": action
    }
    df = pd.DataFrame([log])
    if os.path.exists(LOG_FILE):
        old = pd.read_excel(LOG_FILE)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(LOG_FILE, index=False)

def get_subclass_options(dept, selected_class):
    pool = SUBCLASS_DATA.get(selected_class, [])

    if selected_class == "002":
        keywords = DEPT_KEYWORDS.get(dept, [])
        if not keywords:
            return ["CL_FACTORY_CLASS"]

        filtered = [s for s in pool if any(k in s for k in keywords)]
        return filtered if filtered else ["CL_FACTORY_CLASS"]

    return pool

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Material Portal", layout="wide")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Create Request", "Admin Panel", "Logs"]
)

# -----------------------------
# CREATE REQUEST
# -----------------------------
if menu == "Create Request":
    st.title("📦 Material Creation Form")

    col1, col2 = st.columns(2)

    with col1:
        mill = st.selectbox("Mill", ["MIJM","SGJM","SHJM","SSKT"])
        dept = st.selectbox("Department", sorted(DEPT_DEFAULT_MAP.keys()))

        req_by = st.text_input("Requested By (Store)")
        req_mail = st.text_input("Requester Email")

    with col2:
        default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])
        class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))

        selected_class = st.selectbox("Class", class_options)

        subclass_options = get_subclass_options(dept, selected_class)
        subclass = st.selectbox("Subclass", subclass_options)

    # MULTIPLE MATERIALS 🔥
    st.subheader("Add Materials")
    num_materials = st.number_input("Number of Materials", min_value=1, max_value=10, value=1)

    materials = []
    for i in range(num_materials):
        st.markdown(f"### Material {i+1}")
        colA, colB = st.columns(2)

        with colA:
            machine = st.text_input(f"Machine {i}", key=f"machine{i}")
        with colB:
            attr = st.text_input(f"Attributes {i}", key=f"attr{i}")

        materials.append((machine, attr))

    reason = st.text_area("Reason")

    if st.button("Submit"):
        if not req_by or not req_mail or "@" not in req_mail:
            st.error("Fill all required fields")
        else:
            request_id = generate_request_id()

            for machine, attr in materials:
                data = {
                    "Request_ID": request_id,
                    "Date": datetime.now(),
                    "Mill": mill,
                    "Department": dept,
                    "Requested_By": req_by,
                    "Requester_Email": req_mail,
                    "Machine": machine,
                    "Class": selected_class,
                    "Subclass": subclass,
                    "Attributes": attr,
                    "Reason": reason,
                    "Status": "Pending"
                }
                save_request(data)

            write_log(req_by, f"Submitted {request_id}")
            st.success(f"{request_id} submitted successfully")

# -----------------------------
# ADMIN PANEL
# -----------------------------
elif menu == "Admin Panel":
    st.title("🔑 Admin Panel")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            st.session_state.admin = True

    if st.session_state.get("admin"):
        if os.path.exists(REQUEST_FILE):
            df = pd.read_excel(REQUEST_FILE)
            st.dataframe(df)

            pending = df[df["Status"] == "Pending"]

            for i, row in pending.iterrows():
                if st.button(f"Approve {row['Request_ID']} {i}"):
                    df.loc[i, "Status"] = "Approved"
                    df.to_excel(REQUEST_FILE, index=False)

                    write_log("ADMIN", f"Approved {row['Request_ID']}")
                    st.success("Approved")
                    st.rerun()

# -----------------------------
# LOGS
# -----------------------------
elif menu == "Logs":
    st.title("📜 Logs")

    if os.path.exists(LOG_FILE):
        df = pd.read_excel(LOG_FILE)
        st.dataframe(df)
    else:
        st.info("No logs yet")
