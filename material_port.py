import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import pymongo

# -----------------------------
# CONFIG & DATABASE SETUP
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

MONGO_URI = "mongodb+srv://Finisher_card_sliver:Sohampanda@cluster0.mjn5qdx.mongodb.net/?retryWrites=true&w=majority"

# --- THE FIX: Caching the Database Connection ---
@st.cache_resource
def init_db():
    # This function will only run ONCE when the app starts
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info() # Test connection
    return client

try:
    # Now it grabs the saved connection instantly without waiting!
    client = init_db()
    db = client["form_to_sap"]
    request_collection = db["material_requests"]
    log_collection = db["logs"]
except Exception as e:
    st.error(f"Database Connection Error: {e}")

# -----------------------------
# LISTS & MAPPINGS
# -----------------------------
MATERIAL_TYPES = ["Select", "ZCON", "ZERS", "ZFGS", "ZNSN", "ZPKG", "ZRJU", "ZROW", "ZRSP", "ZSER", "ZSFG", "ZUBN"]
MATERIAL_GROUPS = ["Select", "RJ01-Raw Jute", "SC01-Bearing", "SC02-Beltings", "SC03-Bolts & Nuts", "SC04-Screw Wood Screws", "SC05-Rivet/Wiren Ail", "SC06-Chains & Springs", "SC07-Tools", "SC08-Pipes/Pipe Fittings", "SC09-Iron/Steel Materials", "SC10-Woods", "SC11-Lubricants", "SC12-Materials", "SC13-Electrical Goods - I", "SC14-Electrical Goods - I", "SC15-Building Materials", "SC16-Pinions", "SC17-Generals - I", "SC18-Generals - Ii", "SC20-Stationary & Printin", "SC21-Dispensary", "SC28-C.I. Materials (P/H)", "SC31-Batching", "SC32-Carding", "SC33-Drawing", "SC34-Roving", "SC35-Spining", "SC36-Winding", "SC37-Beaming/Sizing", "SC38-Weaving/Sizing", "SC39-Spares For One Mac L", "SC40-Boiler/Furnace", "SC41-Broad Loom", "SC42-Spare (Pigmy Pallet)", "SC43-Misc Machinary Parts", "SC44-Heavy Stores & Machi", "SC45-Spares Of A.C.B.", "SC46-S4A Loom", "SC48-Rapier Loom", "SC49-Computer Hardware", "SC50-Furniture", "SC51-D.G. Set", "SC52-Fork Lifter Items", "SC53-SPROCKET", "SC54-Spares", "SC55-Paint", "SC56-Workshop Items", "SC57-Accessories", "SC58-Air Compressor Parts", "SC59-C.I. Material(N/L)", "SC60-Rope/Rod/Wire", "SC61-Bush", "SC62-Dye Material", "SC63-Meta Pin", "SC64-Sack Sewing", "SC65-Press", "SC66-SQC Materials", "SC67-Reeds", "SC68-Motors", "SC71-Cash Purchase", "SC72-Misc Stores - I", "SC78-Twisting", "SC81-Precision Winding", "SC82-Dornier Looms", "SC83-Production Materials", "SC84-Gill Pin", "SC85-Card Pin", "SC86-Packaging Materials", "SC87-Stud", "SF01-Emulsifiers", "SF02-Roll", "SF03-Pile", "SF04-Spun Yarn", "SF05-Winded Yarn", "SF06-PrecisionWinded Yarn", "SF07-Beam", "SF08-Loose Hessian Cloth", "SF09-Loose Sacking Cloth", "SF10-Dornier", "SF11-Loose Unbrand HS Bag", "SF12-Loose Unbrand Sack B", "SF13-Loose Branded HS Bag", "SF14-Loose Brand Sack Bag", "SV01-Services Group", "SV02-Service Group 2"]

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
# FUNCTIONS
# -----------------------------
def generate_request_id():
    try:
        last_doc = request_collection.find_one(sort=[("Request_ID", pymongo.DESCENDING)])
        if not last_doc or "Request_ID" not in last_doc: 
            return "MAT-0001"
        last_id = last_doc["Request_ID"]
        number = int(last_id.split("-")[1]) + 1
        return f"MAT-{number:04d}"
    except:
        return "MAT-0001"

def save_request(data):
    request_collection.insert_one(data)

def write_log(user, action):
    log_entry = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": user, "Action": action}
    log_collection.insert_one(log_entry)

def send_admin_email(all_data):
    first = all_data[0]
    requester_email = first['Requester_Email']
    all_recipients = ADMIN_EMAILS + [requester_email]
    
    material_details_text = ""
    for i, d in enumerate(all_data, 1):
        material_details_text += f"""
Material {i} Details:
------------------------------------------
Material Name      : {d.get('Material_Name')}
Machine            : {d.get('Machine')}
Machine Zone       : {d.get('Machine_Zone')}
Attributes         : {d.get('Attributes')}
Unit               : {d.get('Unit')}
Material Type      : {d.get('Material_Type')}
Material Group     : {d.get('Material_Group')}
HSN Code           : {d.get('HSN_Code')}
Reference No.      : {d.get('Reference_No')}
------------------------------------------
"""

    body = f"""
NEW MATERIAL MASTER REQUEST: {first['Request_ID']}
==========================================

HEADER INFORMATION:
------------------------------------------
Mill               : {first['Mill']}
Department         : {first['Department']}
Class              : {first.get('Class')}
Subclass           : {first.get('Subclass')}
Requested By (Dept): {first.get('Requested_By_Dept')}
Requested By (Store): {first['Requested_By']}
Requester Email    : {requester_email}

REASON FOR CREATION:
------------------------------------------
{first['Reason']}

ITEMIZED LIST:
==========================================
{material_details_text}

Status: Pending
Date submitted: {first['Date'].strftime("%Y-%m-%d %H:%M:%S")}
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Request {first['Request_ID']} | {first['Mill']} | {first['Department']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(all_recipients)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, all_recipients, msg.as_string())
        server.quit()
    except Exception as e:
        st.warning(f"Recorded in DB, but Email failed: {e}")

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
menu = st.sidebar.selectbox("Navigation", ["Create Request", "Admin Panel", "Logs"])

if menu == "Create Request":
    st.title("Material Creation Form")
    c1, c2 = st.columns(2)
    with c1:
        mill = st.selectbox("Mill*", ["MIJM","SGJM","SHJM","SSKT"])
        dept = st.selectbox("Department*", sorted(list(DEPT_DEFAULT_MAP.keys())))
        req_by_dept = st.text_input("Requested By (Department)*")
        req_by = st.text_input("Requested By (Store)*")
        req_mail = st.text_input("Mail Id of Requester*")
    with c2:
        class_options = sorted(list(set(DEPT_DEFAULT_MAP.get(dept, ["002"]) + GLOBAL_CLASSES)))
        selected_class = st.selectbox("Class*", class_options)
        subclass = st.selectbox("Subclass*", get_subclass_options(dept, selected_class))

    num_materials = st.number_input("Number of Materials", 1, 10, 1)
    materials_inputs = []

    for i in range(num_materials):
        st.markdown(f"#### Material {i+1}")
        col1, col2, colZone, col3, col4 = st.columns(5)
        m_name = col1.text_input("Name*", key=f"n_{i}")
        m_mach = col2.text_input("Machine*", key=f"m_{i}")
        m_zone = colZone.text_input("Machine Zone*", key=f"z_{i}")
        m_attr = col3.text_input("Attributes*", key=f"a_{i}")
        m_unit = col4.selectbox("Unit*", ["SET", "Pcs", "Kg", "NOS"], key=f"u_{i}")
        
        col5, col6, col7, col8 = st.columns(4)
        m_type = col5.selectbox("Type*", MATERIAL_TYPES, key=f"t_{i}")
        m_group = col6.selectbox("Group*", MATERIAL_GROUPS, key=f"g_{i}")
        m_hsn = col7.text_input("HSN*", key=f"h_{i}")
        m_ref = col8.text_input("Reference No.*", key=f"r_{i}") 
        
        materials_inputs.append((m_name, m_mach, m_zone, m_attr, m_unit, m_type, m_group, m_hsn, m_ref))

    reason = st.text_area("Reason for creation*")

    if st.button("Submit Request"):
        if not all([mill, dept, req_by_dept, req_by, req_mail, reason]):
            st.error("Fill all mandatory header fields.")
        else:
            req_id = generate_request_id()
            final_list = []
            for row in materials_inputs:
                d = {
                    "Request_ID": req_id, 
                    "Date": datetime.now(), 
                    "Mill": mill, 
                    "Department": dept,
                    "Class": selected_class,
                    "Subclass": subclass,
                    "Requested_By_Dept": req_by_dept,
                    "Requested_By": req_by, 
                    "Requester_Email": req_mail, 
                    "Material_Name": row[0],
                    "Machine": row[1], 
                    "Machine_Zone": row[2], 
                    "Attributes": row[3], 
                    "Unit": row[4], 
                    "Material_Type": row[5],
                    "Material_Group": row[6], 
                    "HSN_Code": row[7], 
                    "Reference_No": row[8], 
                    "Status": "Pending", 
                    "Reason": reason
                }
                save_request(d)
                final_list.append(d)
            
            send_admin_email(final_list)
            write_log(req_by, f"Submitted {req_id}")
            st.success(f"Request {req_id} submitted successfully!")

elif menu == "Admin Panel":
    st.title("Admin Panel")
    data = list(request_collection.find({}, {"_id": 0}))
    if data: st.dataframe(pd.DataFrame(data))
    else: st.info("No requests.")

elif menu == "Logs":
    st.title("System Logs")
    logs = list(log_collection.find({}, {"_id": 0}))
    if logs: st.dataframe(pd.DataFrame(logs))
    else: st.info("No logs.")
