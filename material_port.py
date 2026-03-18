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
    "nitin.pandey@jute-india.com",
    "prakhar.chandel@jute-india.com"
]

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
        old = pd.read_excel(LOG_FILE)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(LOG_FILE, index=False)

def send_admin_email(all_data):
    first = all_data[0]

    # Build material rows
    material_rows = ""
    for i, d in enumerate(all_data, 1):
        material_rows += f"""
  Material {i}:
    Material Name   : {d['Material_Name']}
    Machine         : {d['Machine']}
    Attributes      : {d['Attributes']}
    Unit            : {d['Unit']}
"""

    body = f"""
Material Creation Request
=========================

Request ID              : {first['Request_ID']}
Date & Time             : {first['Date'].strftime("%Y-%m-%d %H:%M:%S")}
Mill                    : {first['Mill']}
Department              : {first['Department']}
Requested By (Dept)     : {first['Requested_By_dept']}
Requested By (Store)    : {first['Requested_By']}
Requester Email         : {first['Requester_Email']}
Class                   : {first['Class']}
Subclass                : {first['Subclass']}
Reason                  : {first['Reason']}
Status                  : {first['Status']}

Materials ({len(all_data)} total):
{material_rows}
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Material Request {first['Request_ID']} | {first['Mill']} | {first['Department']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(ADMIN_EMAILS)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.sendmail(SMTP_EMAIL, ADMIN_EMAILS, msg.as_string())
    server.quit()

def get_subclass_options(mill, dept, selected_class):
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
st.set_page_config(page_title="Material Master Portal", layout="wide")

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

        req_by_dept = st.text_input(
            " Requested By (Depertment)",
            placeholder="e.g. Requester name from department"
        )

        req_by = st.text_input(
            " Requested By (Store)",
            placeholder="e.g. Sulagna Roy, Sanat Das"
        )

        req_mail = st.text_input(
            " Mail Id of requester",
            placeholder="e.g. store.hjm@jute-india.com"
        )

    with col2:
        default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])
        class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))

        selected_class = st.selectbox("Class", class_options)

        subclass_options = get_subclass_options(mill,dept,selected_class)

        subclass = st.selectbox(
            "Subclass",
            subclass_options,
            key=f"{dept}_{selected_class}"
        )

    # -----------------------------
    # MATERIALS WITH UNIT
    # -----------------------------
    st.subheader("Add Material(s)")

    num_materials = st.number_input(
        "Number of Materials",
        min_value=1,
        max_value=100,
        value=1
    )

    materials = []

    for i in range(num_materials):
        st.markdown(f"### Material {i+1}")

        colA, colB, colC, colD = st.columns(4)  # added one more column

        with colA:
            material_name = st.text_input(
                "Material Name",
                placeholder="e.g. Bearing, Belt, Oil Filter",
                key=f"material_name_{i}"
            )

        with colB:
            machine = st.text_input(
                " Machine",
                placeholder="e.g. General, 030BC021, 040D2005",
                key=f"machine_{i}"
            )

        with colC:
            attr = st.text_input(
                "Material Attributes",
                placeholder="e.g. Length, Width , Diameter",
                key=f"attr_{i}"
            )

        with colD:
            unit = st.selectbox(
                "Unit",
                ["SET", "Pcs", "L", "Kg"],
                key=f"unit_{i}"
            )

        materials.append((material_name, machine, attr, unit))

    reason = st.text_area("Reason for new material creation")

    if st.button("Submit Request"):
        if not mill or not dept or not req_by or not req_mail or "@" not in req_mail or not reason:
            st.error("All fields mandatory")
        else:
            request_id = generate_request_id()

            all_data = []  # collect all material rows

            for material_name, machine, attr, unit in materials:
                if not material_name or not machine or not attr:
                    continue

                data = {
                    "Request_ID": request_id,
                    "Date": datetime.now(),
                    "Mill": mill,
                    "Department": dept,
                    "Requested_By_dept": req_by_dept,
                    "Requested_By": req_by,
                    "Requester_Email": req_mail,
                    "Material_Name": material_name,
                    "Machine": machine,
                    "Class": selected_class,
                    "Subclass": subclass,
                    "Attributes": attr,
                    "Unit": unit,
                    "Reason": reason,
                    "Status": "Pending"
                }

                save_request(data)
                all_data.append(data)

            if all_data:
                send_admin_email(all_data)
                write_log(req_by, f"Submitted {request_id}")
                st.success(f"Request {request_id} submitted")
            else:
                st.error("Please fill in Material Name, Machine and Attributes for at least one material.")

# -----------------------------
# ADMIN PANEL
# -----------------------------
elif menu == "Admin Panel":
    st.title("Admin Panel")
    st.info("No changes here")

# -----------------------------
# LOGS
# -----------------------------
elif menu == "Logs":
    st.title("Logs")
    if os.path.exists(LOG_FILE):
        df = pd.read_excel(LOG_FILE)
        st.dataframe(df)
    else:
        st.info("No logs yet")
