import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import pymongo
from dotenv import load_dotenv

# -----------------------------
# CONFIG & DATABASE SETUP
# -----------------------------
# Load environment variables from .env file
load_dotenv()

# Email Config (Using .env for security)
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "prakhar.chandel@jute-india.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "") # Put your new App Password in your .env file!
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

ADMIN_EMAILS = [
    "soham.panda@jute-india.com",
    "payal.sinha@jute-india.com",
    "anushka.dutta@jute-india.com",
    "nitin.pandey@jute-india.com",
    "prakhar.chandel@jute-india.com"
]

# MongoDB Cloud Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["form_to_sap"]
    request_collection = db["material_requests"]
    log_collection = db["logs"]
except Exception as e:
    st.error(f"Database Connection Error: {e}")

# -----------------------------
# LISTS & MAPPINGS
# -----------------------------
MATERIAL_TYPES = ["Select", "ZCON", "ZERS", "ZFGS", "ZNSN", "ZPKG", "ZRJU", "ZROW", "ZRSP", "ZSER", "ZSFG", "ZUBN"]

MATERIAL_GROUPS = [
    "Select", "RJ01-Raw Jute", "SC01-Bearing", "SC02-Beltings", "SC03-Bolts & Nuts", 
    "SC04-Screw Wood Screws", "SC05-Rivet/Wiren Ail", "SC06-Chains & Springs", 
    "SC07-Tools", "SC08-Pipes/Pipe Fittings", "SC09-Iron/Steel Materials", 
    "SC10-Woods", "SC11-Lubricants", "SC12-Materials", "SC13-Electrical Goods - I", 
    "SC14-Electrical Goods - I", "SC15-Building Materials", "SC16-Pinions", 
    "SC17-Generals - I", "SC18-Generals - Ii", "SC20-Stationary & Printin", 
    "SC21-Dispensary", "SC28-C.I. Materials (P/H)", "SC31-Batching", 
    "SC32-Carding", "SC33-Drawing", "SC34-Roving", "SC35-Spining", 
    "SC36-Winding", "SC37-Beaming/Sizing", "SC38-Weaving/Sizing", 
    "SC39-Spares For One Mac L", "SC40-Boiler/Furnace", "SC41-Broad Loom", 
    "SC42-Spare (Pigmy Pallet)", "SC43-Misc Machinary Parts", 
    "SC44-Heavy Stores & Machi", "SC45-Spares Of A.C.B.", "SC46-S4A Loom", 
    "SC48-Rapier Loom", "SC49-Computer Hardware", "SC50-Furniture", 
    "SC51-D.G. Set", "SC52-Fork Lifter Items", "SC53-SPROCKET", "SC54-Spares", 
    "SC55-Paint", "SC56-Workshop Items", "SC57-Accessories", 
    "SC58-Air Compressor Parts", "SC59-C.I. Material(N/L)", "SC60-Rope/Rod/Wire", 
    "SC61-Bush", "SC62-Dye Material", "SC63-Meta Pin", "SC64-Sack Sewing", 
    "SC65-Press", "SC66-SQC Materials", "SC67-Reeds", "SC68-Motors", 
    "SC71-Cash Purchase", "SC72-Misc Stores - I", "SC78-Twisting", 
    "SC81-Precision Winding", "SC82-Dornier Looms", "SC83-Production Materials", 
    "SC84-Gill Pin", "SC85-Card Pin", "SC86-Packaging Materials", "SC87-Stud", 
    "SF01-Emulsifiers", "SF02-Roll", "SF03-Pile", "SF04-Spun Yarn", 
    "SF05-Winded Yarn", "SF06-PrecisionWinded Yarn", "SF07-Beam", 
    "SF08-Loose Hessian Cloth", "SF09-Loose Sacking Cloth", "SF10-Dornier", 
    "SF11-Loose Unbrand HS Bag", "SF12-Loose Unbrand Sack B", 
    "SF13-Loose Branded HS Bag", "SF14-Loose Brand Sack Bag", 
    "SV01-Services Group", "SV02-Service Group 2"
]

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
    # Find the latest document in MongoDB by sorting Request_ID descending
    last_doc = request_collection.find_one(sort=[("Request_ID", pymongo.DESCENDING)])
    if not last_doc or "Request_ID" not in last_doc: 
        return "MAT-0001"
    
    last_id = last_doc["Request_ID"]
    try:
        number = int(last_id.split("-")[1]) + 1
        return f"MAT-{number:04d}"
    except:
        return "MAT-0001"

def save_request(data):
    # Insert safely into MongoDB Cloud
    request_collection.insert_one(data)

def write_log(user, action):
    # Insert securely into MongoDB Cloud
    log_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "User": user, 
        "Action": action
    }
    log_collection.insert_one(log_entry)

def send_admin_email(all_data):
    if not SMTP_PASSWORD:
        st.warning("Email not sent: Please add your SMTP_PASSWORD to your .env file.")
        return

    first = all_data[0]
    requester_email = first['Requester_Email']
    all_recipients = ADMIN_EMAILS + [requester_email]
    
    material_rows = ""
    for i, d in enumerate(all_data, 1):
        material_rows += f"""
Material {i}:
------------------------------------------
Material Name      : {d['Material_Name']}
Machine            : {d['Machine']}
Machine Zone       : {d['Machine_Zone']}
Attributes         : {d['Attributes']}
Unit               : {d['Unit']}
Material Type      : {d['Material_Type']}
Material Group     : {d['Material_Group']}
HSN Code           : {d['HSN_Code']}
Reference Material : {d['Ref_Material']}
"""

    body = f"""
NEW MATERIAL MASTER REQUEST
==========================================
Request ID          : {first['Request_ID']}
Date & Time         : {first['Date'].strftime("%Y-%m-%d %H:%M:%S")}

HEADER DETAILS
==========================================
Mill                : {first['Mill']}
Department          : {first['Department']}
Class               : {first['Class']}
Subclass            : {first['Subclass']}

REQUESTER INFO
==========================================
Requested By (Dept) : {first['Requested_By_dept']}
Requested By (Store): {first['Requested_By']}
Requester Email     : {requester_email}
Reason for Creation : {first['Reason']}

MATERIAL LIST ({len(all_data)} items)
==========================================
{material_rows}
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
        st.warning(f"Submission recorded but email failed: {e}")

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
        default_classes = DEPT_DEFAULT_MAP.get(dept, ["002"])
        class_options = sorted(list(set(default_classes + GLOBAL_CLASSES)))
        selected_class = st.selectbox("Class*", class_options)
        sub_opts = get_subclass_options(dept, selected_class)
        subclass = st.selectbox("Subclass*", sub_opts)

    st.subheader("Add Material(s)")
    num_materials = st.number_input("Number of Materials", 1, 100, 1)
    materials_data = []

    for i in range(num_materials):
        st.markdown(f"#### Material {i+1}")
        colA, colB, colZone, colC, colD = st.columns(5)
        m_name = colA.text_input("Material Name*", key=f"name_{i}")
        m_mach = colB.text_input("Machine*", key=f"mach_{i}")
        m_zone = colZone.text_input("Machine Zone*", key=f"zone_{i}")
        m_attr = colC.text_input("Attributes*", key=f"attr_{i}")
        m_unit = colD.selectbox("Unit*", ["SET", "Pcs", "L", "Kg", "M", "NOS", "MT", "Box"], key=f"unit_{i}")
        
        colE, colF, colG, colH = st.columns(4)
        m_type = colE.selectbox("Material Type*", MATERIAL_TYPES, key=f"type_{i}")
        m_group = colF.selectbox("Material Group*", MATERIAL_GROUPS, key=f"group_{i}")
        m_hsn = colG.text_input("HSN Code*", key=f"hsn_{i}")
        m_ref = colH.text_input("Reference Material*", key=f"ref_{i}")
        
        st.divider()
        materials_data.append((m_name, m_mach, m_zone, m_attr, m_unit, m_type, m_group, m_hsn, m_ref))

    reason = st.text_area("Reason for creation*")

    if st.button("Submit Request"):
        # 1. Header Validation
        if not all([mill, dept, req_by_dept, req_by, req_mail, reason]):
            st.error("All Header fields and the Reason for creation are mandatory.")
        elif "@" not in req_mail:
            st.error("Please enter a valid email address.")
        else:
            req_id = generate_request_id()
            final_list = []
            
            # 2. Material Validation
            for idx, row in enumerate(materials_data):
                if "Select" in [row[5], row[6]] or not all([row[0], row[1], row[2], row[3], row[7], row[8]]):
                    st.error(f"Please fill all mandatory fields (*) for Material {idx+1}.")
                    st.stop()
                
                # Create dictionary for MongoDB
                d = {
                    "Request_ID": req_id, "Date": datetime.now(), "Mill": mill, "Department": dept,
                    "Requested_By_dept": req_by_dept, "Requested_By": req_by, "Requester_Email": req_mail,
                    "Material_Name": row[0], "Machine": row[1], "Machine_Zone": row[2],
                    "Class": selected_class, "Subclass": subclass, "Attributes": row[3],
                    "Unit": row[4], "Material_Type": row[5], "Material_Group": row[6],
                    "HSN_Code": row[7], "Ref_Material": row[8],
                    "Reason": reason, "Status": "Pending"
                }
                
                # Save to MongoDB
                save_request(d)
                final_list.append(d)

            if final_list:
                send_admin_email(final_list)
                write_log(req_by, f"Submitted {req_id}")
                st.success(f"SUCCESS: Request {req_id} submitted to Database. Check your email for a copy.")

# NEW ADMIN PANEL SECTION
elif menu == "Admin Panel":
    st.title("Admin Control Panel")
    st.subheader("Pending Material Requests")
    
    # Fetch all material requests from MongoDB, excluding the internal _id field
    requests_data = list(request_collection.find({}, {"_id": 0}))
    
    if requests_data:
        st.dataframe(pd.DataFrame(requests_data))
    else:
        st.info("No material requests have been submitted yet.")

# UPDATED LOGS SECTION
elif menu == "Logs":
    st.title("System Logs")
    
    # Fetch all logs from MongoDB, excluding the internal _id field
    logs_data = list(log_collection.find({}, {"_id": 0}))
    
    if logs_data:
        st.dataframe(pd.DataFrame(logs_data))
    else:
        st.info("No logs have been recorded yet.")
