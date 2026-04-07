import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# CONFIG & LISTS
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

REQUEST_FILE = "material_requests.xlsx"
LOG_FILE = "logs.xlsx"

# New Dropdown Lists
MATERIAL_TYPES = ["Select", "ZCON", "ZERS", "ZFGS", "ZNSN", "ZPKG", "ZRJU", "ZROW", "ZRSP", "ZSER", "ZSFG", "ZUBN"]
MATERIAL_GROUPS = [
    "Select", "SC01", "SC02", "SC03", "SC04", "SC05", "SC06", "SC07", "SC08", "SC09", "SC10", 
    "SC11", "SC12", "SC13", "SC14", "SC15", "SC16", "SC17", "SC18", "SC20", "SC21", "SC28", 
    "SC31", "SC32", "SC33", "SC34", "SC35", "SC36", "SC37", "SC38", "SC39", "SC40", "SC41", 
    "SC42", "SC43", "SC44", "SC45", "SC46", "SC48", "SC49", "SC50", "SC51", "SC52", "SC53", 
    "SC54", "SC55", "SC56", "SC57", "SC58", "SC59", "SC60", "SC61", "SC62", "SC63", "SC64", 
    "SC65", "SC66", "SC67", "SC68", "SC71", "SC72", "SC78", "SC81", "SC82", "SC83", "SC84", 
    "SC85", "SC86", "SC87", "SF01", "SF02", "SF03", "SF04", "SF05", "SF06", "SF07", "SF08", 
    "SF09", "SF10", "SF11", "SF12", "SF13", "SF14", "SV01", "SV02"
]

# -----------------------------
# MAPPING DATA
# -----------------------------
DEPT_DEFAULT_MAP = {
    "Batching": ["002","023"], "Carding": ["002"], "Drawing": ["002"], 
    "Spinning": ["002"], "Winding": ["002"], "Twisting": ["002"], 
    "Beaming": ["002"], "Weaving": ["002"], "Sack Sewing": ["002"], 
    "Finishing": ["002"], "Bail - Press": ["002"], "Workshop": ["002"], 
    "Boiler/Furnace": ["002"], "Civil": ["002"], "Dispensary": ["001"], 
    "EDP": ["002"], "General": ["002"], "Packaging Materials": ["002"], 
    "Power House": ["002"], "Production Material": ["002"]
}

GLOBAL_CLASSES = ["001","019","032"]
SUBCLASS_DATA = {
    "001": ["CL_FACTORY_CLASS","FG_CLASS","JUTE_CLASS","CL_MATERIAL_CLASS"],
    "019": ["WC_STIL"],
    "032": ["PO_RELEASE","PR_RELEASE"],
    "023": ["BATCH_CLASS","FG_BATCH_CLASS","SPRDER_MAT_CLASS"],
    "002":[
        "CL_CARD_MIJM","CL_CARD_SGJM","CL_CARD_SHJM","CL_CARD_ALL_MILLS",
        "CL_COP_MIJM","CL_COP_SGJM","CL_COP_SHJM","CL_DRAW_MIJM","CL_DRAW_SGJM",
        "CL_DRAW_SHJM","CL_DRAW_ALL_MILLS","CL_SOFT_MIJM","CL_SOFT_SGJM",
        "CL_SOFT_SHJM","CL_SPIN_MIJM","CL_SPIN_SGJM","CL_SPIN_SHJM",
        "CL_SPIN_ALL_MILLS","CL_SPOOL_MIJM","CL_SPOOL_SGJM","CL_SPOOL_SHJM",
        "CL_SPREAD_MIJM","CL_SPREAD_SGJM","CL_SPREAD_SHJM","CL_WINDING_ALL_MILLS",
        "CL_TWISTING_ALL_MILLS","CL_FACTORY_CLASS"
    ]
}
DEPT_KEYWORDS = {
    "Batching":["SOFT","SPREAD"], "Carding":["CARD"], "Drawing":["DRAW"],
    "Spinning":["SPIN"], "Winding":["COP","SPOOL","WINDING"], "Twisting":["TWISTING"]
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def generate_request_id():
    if not os.path.exists(REQUEST_FILE): return "MAT-0001"
    df = pd.read_excel(REQUEST_FILE)
    if df.empty: return "MAT-0001"
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
    log = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": user, "Action": action}
    df = pd.DataFrame([log])
    if os.path.exists(LOG_FILE):
        old = pd.read_excel(LOG_FILE)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(LOG_FILE, index=False)

def send_admin_email(all_data):
    first = all_data[0]
    material_rows = ""
    for i, d in enumerate(all_data, 1):
        material_rows += f"\n  Material {i}:\n    Name: {d['Material_Name']}\n    Machine: {d['Machine']}\n    Zone: {d['Machine_Zone']}\n    Type: {d['Material_Type']}\n    Group: {d['Material_Group']}\n    HSN: {d['HSN_Code']}\n"

    body = f"Material Request {first['Request_ID']}\nMill: {first['Mill']}\nDept: {first['Department']}\n{material_rows}"
    msg = MIMEText(body); msg["Subject"] = f"Request {first['Request_ID']}"; msg["From"] = SMTP_EMAIL; msg["To"] = ", ".join(ADMIN_EMAILS)
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT); server.starttls(); server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, ADMIN_EMAILS, msg.as_string()); server.quit()
    except Exception as e: st.warning(f"Email failed: {e}")

def get_subclass_options(dept, selected_class):
    pool = SUBCLASS_DATA.get(selected_class, [])
    if selected_class == "002":
        keywords = DEPT_KEYWORDS.get(dept, [])
        filtered = [s for s in pool if any(k in s for k in keywords)]
        return filtered if filtered else ["CL_FACTORY_CLASS"]
    return pool

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Material Master Portal", layout="wide")
menu = st.sidebar.selectbox("Navigation", ["Create Request","Admin Panel","Logs"])

if menu == "Create Request":
    st.title("Material Creation Form")
    c1, c2 = st.columns(2)
    with c1:
        mill = st.selectbox("Mill", ["MIJM","SGJM","SHJM","SSKT"])
        dept = st.selectbox("Department", sorted(list(DEPT_DEFAULT_MAP.keys())))
        req_by_dept = st.text_input("Requested By (Department)")
        req_by = st.text_input("Requested By (Store)")
        req_mail = st.text_input("Mail Id of Requester")
    with c2:
        default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])
        class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))
        selected_class = st.selectbox("Class", class_options)
        sub_opts = get_subclass_options(dept, selected_class)
        subclass = st.selectbox("Subclass", sub_opts)

    st.subheader("Add Material(s)")
    num_materials = st.number_input("Number of Materials", 1, 100, 1)
    materials_data = []

    for i in range(num_materials):
        st.markdown(f"#### Material {i+1}")
        # Row 1
        colA, colB, colZone, colC, colD = st.columns(5)
        m_name = colA.text_input("Material Name*", key=f"name_{i}")
        m_mach = colB.text_input("Machine*", key=f"mach_{i}")
        m_zone = colZone.text_input("Machine Zone*", key=f"zone_{i}")
        m_attr = colC.text_input("Attributes*", key=f"attr_{i}")
        m_unit = colD.selectbox("Unit", ["SET", "Pcs", "L", "Kg", "M", "NOS", "MT", "Box"], key=f"unit_{i}")
        
        # Row 2: Dropdowns for Type and Group
        colE, colF, colG, colH = st.columns(4)
        m_type = colE.selectbox("Material Type*", MATERIAL_TYPES, key=f"type_{i}")
        m_group = colF.selectbox("Material Group*", MATERIAL_GROUPS, key=f"group_{i}")
        m_hsn = colG.text_input("HSN Code*", key=f"hsn_{i}")
        m_ref = colH.text_input("Ref Material", key=f"ref_{i}")
        
        st.divider()
        materials_data.append((m_name, m_mach, m_zone, m_attr, m_unit, m_type, m_group, m_hsn, m_ref))

    reason = st.text_area("Reason for creation*")

    if st.button("Submit Request"):
        # Basic validation
        if not all([mill, dept, req_by, req_mail, reason]) or "@" not in req_mail:
            st.error("Header fields and Reason are mandatory.")
        else:
            req_id = generate_request_id()
            final_list = []
            for row in materials_data:
                # Check for "Select" or empty strings in mandatory fields
                if "Select" in [row[5], row[6]] or not all([row[0], row[1], row[2], row[3], row[7]]):
                    st.error("Please fill all mandatory fields (*) for all materials.")
                    st.stop()
                
                d = {
                    "Request_ID": req_id, "Date": datetime.now(), "Mill": mill, "Department": dept,
                    "Requested_By_dept": req_by_dept, "Requested_By": req_by, "Requester_Email": req_mail,
                    "Material_Name": row[0], "Machine": row[1], "Machine_Zone": row[2],
                    "Class": selected_class, "Subclass": subclass, "Attributes": row[3],
                    "Unit": row[4], "Material_Type": row[5], "Material_Group": row[6],
                    "HSN_Code": row[7], "Ref_Material": row[8] if row[8] else "N/A",
                    "Reason": reason, "Status": "Pending"
                }
                save_request(d)
                final_list.append(d)

            if final_list:
                send_admin_email(final_list)
                write_log(req_by, f"Submitted {req_id}")
                st.success(f"Request {req_id} submitted successfully!")

elif menu == "Logs":
    st.title("Logs")
    if os.path.exists(LOG_FILE): st.dataframe(pd.read_excel(LOG_FILE))
    else: st.info("No logs yet")
