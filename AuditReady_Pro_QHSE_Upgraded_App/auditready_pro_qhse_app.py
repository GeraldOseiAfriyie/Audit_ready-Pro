import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import hashlib
import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
    from reportlab.lib.units import inch
except Exception:
    SimpleDocTemplate = None

st.set_page_config(page_title="AuditReady Pro QHSE", layout="wide", initial_sidebar_state="collapsed")

APP_TITLE = "AuditReady Pro QHSE Audit"
DB_PATH = Path("auditready_pro_qhse.db")
PHOTO_DIR = Path("audit_photos")
REPORT_DIR = Path("reports")
BRAND_DIR = Path("branding")
for p in [PHOTO_DIR, REPORT_DIR, BRAND_DIR]:
    p.mkdir(exist_ok=True)

COMPANY_NAME = "Starbites Enterprise Limited"
DOC_NUMBER = "IMS-SOP-16-FM-02"
ISSUE_DATE = "2026-05-13"
VERSION = "4.0"

SCORING = {"No NC": 10, "Minor NC": -5, "Major NC": -10, "Observation": 6}
RESPONSES = list(SCORING.keys())
NC_TYPES = ["Minor NC", "Major NC", "Observation"]
CAPA_STATUS = ["Open", "In Progress", "Awaiting Verification", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
DEFAULT_BRANCHES = ["East legon", "Tema branch", "Westlands", "Asokwa", "Agbogba", "X", "Dansoman", "Botwe", "Stadium", "N1", "Adum", "Kent", "Osu", "Central", "Tesano", "Warehouse Acc", "Warehouse Ksi", "Production unit"]

CHECKLISTS = {
    "Food Safety": [
        ("Permits", "Permits available and valid"), ("Medical Records", "Medical records available/current"), ("Cross-Contamination", "No risk of cross-contamination"),
        ("Pest Control", "Pest control report available/current"), ("Fried Oil Quality", "Compliance of quality of fried oil"), ("Stock Control", "No expired product sighted"),
        ("Equipment", "Status of equipment satisfactory"), ("Grease Trap", "Availability of grease trap"), ("Policies", "Policies available at the branch"),
        ("Training", "Training records available/current"), ("Status of washroom/Dispensers", "Is the washroom clean and the dispenser stocked"),
        ("Respect of the rules of personal hygiene", "Are staff in short finger nails, no rubber bands, no watch on their wrist, and wearing hair net?"),
        ("Evidence of staff washing their hands", "Did you observe any staff washing or not washing their hand?"), ("Expired products", "No expired product in stored and/or in use"),
        ("Application of the FIFO rule", "Is FIFO ensured"), ("Room temperature of the dry storage area", "Correct ambient temperature of the dry storage area"),
        ("Temperature of freezers and Fridges", "Are cold storages working within target temperature"), ("Calibration of equipment report", "Are all equipment calibrated"),
        ("Cleanliness of fridges/freezers", "Are fridges clean")
    ],
    "HACCP Verification": [
        ("HACCP Team", "HACCP team established"), ("IMS Meeting", "IMS meeting conducted"), ("Internal Audit", "Internal audit completed"),
        ("Receiving Records", "Receiving records completed"), ("Cooking Records", "Cooking records completed"), ("Cleaning Records", "Cleaning records completed"),
        ("Thawing Records", "Thawing records completed"), ("Cold Storage Records", "Cold storage records completed"), ("Hygiene Checklist", "Hygiene checklist completed"),
        ("Behavioural Hygiene", "Respect of rule of behavioural hygiene"), ("General Cleanliness", "General cleanliness satisfactory"), ("Labelling", "Labelling compliant"),
        ("Waste Collection", "Waste collection report available"), ("Trap Doors", "Status of trap doors satisfactory"), ("HACCP Record", "HACCP record available/current"),
        ("NCA/Rejection records", "Are NC records in place"), ("Proper washing and disinfection of vegetables", "Are there evidence of proper washing of fruits and veggies"),
        ("Proper disinfection of eggs", "Are there evidence of proper washing of eggs"), ("Absence of foreign bodies and unused equipment", "Unwanted items kept at the branch"),
        ("Respect of the preparation diagrams", "Process flow displayed at the branch"), ("Micro-analysis", "Evidence of food and water analysis")
    ],
    "Occupational Health & Safety": [
        ("Emergency Response", "Emergency response plan available"), ("Injury Report", "Injury report available/current"), ("Incident Report", "Incident report available/current"),
        ("Smoke Detectors", "Smoke detectors in place"), ("First Aid", "Status of first aid box satisfactory"), ("Gas Safety", "Gas station locked and free from items"),
        ("Chemical Safety", "SDS available for each chemical"), ("Hazard Control", "No hazard sighted"), ("Fire Extinguishers", "Status of fire extinguishers satisfactory"),
        ("Lighting", "Adequate lighting available"), ("Status of cooking equipment", "All cooking equipment are in good state"), ("Status of knives, bain marie", "No broken knife sighted"),
        ("Toolbox meeting", "Evidence of toolbox meeting"), ("Fire training", "Staff have been provided with fire training"), ("Temperature in the kitchen", "Is the temperature ok?"),
        ("Chemical station", "Locked under key"), ("Drills", "Evidence of drills performed and recorded")
    ],
    "Environmental": [
        ("Bin Condition", "Status of bin satisfactory"), ("Bin Labelling", "All bins labelled"), ("Waste Segregation", "Waste segregation ensured"),
        ("Air Quality", "Air quality test done"), ("Effluent", "Effluent test done"), ("Noise / Sound", "Sound test done"),
        ("General cleanliness of compound", "Compound is clean"), ("General cleanliness of kitchen", "Kitchen and corners of the kitchen are cleaned"),
        ("General cleanliness of sinks", "Sinks are clean"), ("General cleanliness of extractor hood", "Extractor filters and hood are free from dirt"),
        ("General cleanliness of fire extinguishers", "Extinguishers are free from dirt"), ("Grease trap and records", "Grease trap installed, in good state, and records in place"),
        ("Waste records", "Checklist in place for waste pick-up"), ("Trap doors", "All trap doors are working"), ("Insect catchers", "All insect catchers are working"),
        ("Wet floor", "Wet floor signs available and used where required")
    ]
}

st.markdown("""
<style>
:root{
    --navy:#061A33;
    --navy-2:#0A2545;
    --navy-3:#0E355F;
    --card:#0B2442;
    --card-2:#102F55;
    --line:#2F5D8C;
    --text:#FFFFFF;
    --muted:#D8E8FF;
    --gold:#F6C76A;
}
.stApp{
    background:
        radial-gradient(circle at top left, rgba(38,95,155,.45), transparent 34%),
        radial-gradient(circle at bottom right, rgba(8,36,75,.85), transparent 38%),
        linear-gradient(135deg,var(--navy),#020B16 72%);
    color:var(--text);
}
.block-container{padding-top:.8rem;max-width:1100px;color:var(--text)}
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#031123,#08213F)!important;
    border-right:1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] *{color:#FFFFFF!important;}
h1,h2,h3,h4,h5,h6,p,label,span,div{color:inherit;}
.stMarkdown, .stCaption, .stText, .stMetric, .stDataFrame{color:var(--text)!important;}
.login-wrapper{
    position:relative;
    overflow:hidden;
    background:linear-gradient(135deg,rgba(4,18,38,.96),rgba(9,47,88,.96));
    color:white;
    padding:42px 28px;
    border-radius:42px;
    text-align:center;
    box-shadow:0 18px 45px rgba(0,0,0,.45);
    margin:26px auto 18px auto;
    max-width:560px;
    border:2px solid rgba(246,199,106,.75);
}
.login-wrapper:before,
.login-wrapper:after{
    content:"";
    position:absolute;
    width:220px;
    height:220px;
    border-radius:50%;
    background:radial-gradient(circle,rgba(246,199,106,.38),rgba(66,153,225,.16),transparent 70%);
    animation:floatGlow 7s ease-in-out infinite alternate;
    z-index:0;
}
.login-wrapper:before{top:-80px;left:-60px;}
.login-wrapper:after{bottom:-95px;right:-65px;animation-delay:1.8s;}
.login-title,.login-subtitle{position:relative;z-index:1;}
.login-title{font-size:32px;font-weight:900;letter-spacing:.5px;color:#FFFFFF;}
.login-subtitle{font-size:15px;opacity:.95;color:#D8E8FF;}
@keyframes floatGlow{
    0%{transform:translate(0,0) scale(1);opacity:.55;}
    50%{transform:translate(28px,18px) scale(1.12);opacity:.9;}
    100%{transform:translate(-18px,22px) scale(.96);opacity:.65;}
}
.brand-card{
    background:linear-gradient(135deg,rgba(11,36,66,.98),rgba(12,52,94,.96));
    color:#FFFFFF;
    border-radius:22px;
    padding:16px;
    border:1px solid rgba(246,199,106,.45);
    box-shadow:0 8px 28px rgba(0,0,0,.28);
}
.brand-card h2,.brand-card b,.brand-card br{color:#FFFFFF!important;}
.doc-badge{
    float:right;
    background:#F6C76A;
    color:#061A33!important;
    padding:8px 12px;
    border-radius:18px;
    font-size:12px;
    font-weight:800;
}
.audit-card{
    background:linear-gradient(135deg,rgba(11,36,66,.98),rgba(13,45,80,.96));
    border:1px solid rgba(216,232,255,.18);
    border-radius:20px;
    padding:16px;
    margin-bottom:16px;
    box-shadow:0 7px 18px rgba(0,0,0,.24);
}
.question-title{font-size:16px;font-weight:800;color:#FFFFFF!important;}
.category-text{font-size:13px;color:#D8E8FF!important;margin-bottom:8px;}
div.stButton>button, div.stDownloadButton>button{
    width:100%;
    border-radius:30px;
    height:3rem;
    font-weight:800;
    background:linear-gradient(135deg,#F6C76A,#D79B30);
    color:#061A33;
    border:0;
}
div.stButton>button:hover, div.stDownloadButton>button:hover{
    border:0;
    color:#061A33;
    filter:brightness(1.05);
}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"],.stDateInput input{
    background-color:#FFFFFF!important;
    color:#061A33!important;
    border-radius:12px!important;
}
.stRadio label,.stCheckbox label{color:#FFFFFF!important;}
[data-testid="stMetric"]{
    background:rgba(11,36,66,.78);
    border:1px solid rgba(216,232,255,.15);
    padding:12px;
    border-radius:18px;
}
[data-testid="stMetric"] *{color:#FFFFFF!important;}
[data-testid="stDataFrame"]{background:#FFFFFF;border-radius:12px;}
.stAlert{border-radius:14px;}
</style>
""", unsafe_allow_html=True)

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def connect(): return sqlite3.connect(DB_PATH, check_same_thread=False)
def query_df(q, params=()):
    con=connect(); df=pd.read_sql_query(q,con,params=params); con.close(); return df
def execute(q, params=()):
    con=connect(); cur=con.cursor(); cur.execute(q,params); con.commit(); lid=cur.lastrowid; con.close(); return lid
def update(q, params=()):
    con=connect(); cur=con.cursor(); cur.execute(q,params); con.commit(); con.close()

def init_db():
    con=connect(); cur=con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password_hash TEXT,role TEXT,full_name TEXT,branch TEXT,active INTEGER DEFAULT 1,failed_attempts INTEGER DEFAULT 0,locked INTEGER DEFAULT 0,created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS audits(id INTEGER PRIMARY KEY AUTOINCREMENT,audit_ref TEXT,branch TEXT,auditor TEXT,auditee TEXT,audit_date TEXT,criterion TEXT,category TEXT,question TEXT,response TEXT,nc_type TEXT,score REAL,comment TEXT,image_path TEXT,annotation_note TEXT,auditor_signature TEXT,auditee_signature TEXT,submitted_by TEXT,submitted_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS capas(id INTEGER PRIMARY KEY AUTOINCREMENT,audit_ref TEXT,branch TEXT,criterion TEXT,category TEXT,finding TEXT,nc_type TEXT,priority TEXT,corrective_action TEXT,responsible_person TEXT,due_date TEXT,status TEXT,evidence_path TEXT,verification_comment TEXT,created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS schedules(id INTEGER PRIMARY KEY AUTOINCREMENT,branch TEXT,auditor TEXT,planned_date TEXT,criterion TEXT,status TEXT DEFAULT 'Planned',created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)""")
    for u,p,r,f,b in [("QHSE1","@D012","QHSE","QHSE Officer 1","All"),("QHSE2","_2H14","QHSE","QHSE Officer 2","All"),("Admin","@1984","Admin","System Admin","All")]:
        cur.execute("SELECT COUNT(*) FROM users WHERE username=?",(u,))
        if cur.fetchone()[0]==0: cur.execute("INSERT INTO users(username,password_hash,role,full_name,branch,active,created_at) VALUES(?,?,?,?,?,1,?)",(u,hash_password(p),r,f,b,datetime.now().isoformat()))
    for k,v in {"company_name":COMPANY_NAME,"doc_number":DOC_NUMBER,"issue_date":ISSUE_DATE,"version":VERSION,"email_recipients":"","whatsapp_number":""}.items(): cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    con.commit(); con.close()
init_db()

def get_setting(k, fallback=""):
    df=query_df("SELECT value FROM settings WHERE key=?",(k,)); return fallback if df.empty else df.iloc[0]["value"]
def set_setting(k,v): update("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,v))

# Keep the displayed audit document number/version updated for existing databases.
if get_setting('doc_number', DOC_NUMBER) in ['QHSE-AUD-FM-001', '']:
    set_setting('doc_number', DOC_NUMBER)
if get_setting('version', VERSION) in ['1.0', '']:
    set_setting('version', VERSION)

def pct(total,count):
    if count<=0: return 0
    return round(max(0,min(((total-(count*-10))/((count*10)-(count*-10)))*100,100)),2)
def rate(x): return "Excellent" if x>=90 else "Good" if x>=75 else "Needs Improvement" if x>=60 else "Critical"
def save_file(uploaded, folder, prefix):
    if not uploaded: return ""
    path=folder/f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{Path(uploaded.name).suffix}"
    with open(path,"wb") as f: f.write(uploaded.getbuffer())
    return str(path)
def audit_ref(branch): return f"AUD-{''.join(c for c in branch.upper() if c.isalnum())[:6] or 'GEN'}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
def current_user(): return st.session_state.get("user",{})
def role(): return current_user().get("role","")
def branch_options():
    vals=set(DEFAULT_BRANCHES)
    for table in ["users", "audits", "schedules", "capas"]:
        try:
            df=query_df(f"SELECT DISTINCT branch FROM {table} WHERE branch IS NOT NULL AND branch!=''")
            vals.update([x for x in df["branch"].tolist() if x and x != "All"])
        except Exception:
            pass
    return sorted(vals)

def branch_picker(label="Branch Name", key_prefix="branch"):
    options = branch_options() + ["➕ Add New Branch"]
    selected_branch = st.selectbox(label, options, key=f"{key_prefix}_select")
    if selected_branch == "➕ Add New Branch":
        new_branch = st.text_input("Enter New Branch Name", key=f"{key_prefix}_new").strip()
        return new_branch
    return selected_branch

def generate_pdf(audit_ref_value, df, capas):
    if SimpleDocTemplate is None: return None,"Install reportlab: pip install reportlab"
    path=REPORT_DIR/f"{audit_ref_value}_audit_report.pdf"
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=25,leftMargin=25,topMargin=25,bottomMargin=25); styles=getSampleStyleSheet(); story=[]
    story += [Paragraph(f"<b>{get_setting('company_name',COMPANY_NAME)}</b>",styles['Title']),Paragraph("<b>QHSE Audit Report</b>",styles['Heading2']),Paragraph(f"Document No: {get_setting('doc_number',DOC_NUMBER)} | Issue Date: {get_setting('issue_date',ISSUE_DATE)} | Version: {get_setting('version',VERSION)}",styles['Normal']),Paragraph(f"Audit Ref: {audit_ref_value}",styles['Normal']),Spacer(1,12)]
    if not df.empty:
        first=df.iloc[0]; meta=[["Branch",first['branch']],["Auditor",first['auditor']],["Auditee",first['auditee']],["Audit Date",first['audit_date']],["Submitted By",first['submitted_by']]]
        t=Table(meta,colWidths=[1.5*inch,4.8*inch]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(0,-1),colors.lightgrey)])); story += [t,Spacer(1,12)]
    rows=[["Criterion","Score %","Rating"]]
    for c,cdf in df.groupby('criterion'):
        x=pct(cdf['score'].sum(),len(cdf)); rows.append([c,f"{x}%",rate(x)])
    t=Table(rows,colWidths=[2.8*inch,1.4*inch,1.8*inch]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#3b1f0f')),('TEXTCOLOR',(0,0),(-1,0),colors.white)])); story += [Paragraph("<b>Score Summary</b>",styles['Heading3']),t,Spacer(1,12)]
    for c,cdf in df.groupby('criterion'):
        story.append(Paragraph(f"<b>{c}</b>",styles['Heading3']))
        rows=[["Category","Question","Outcome","Score","Comment"]]+[[str(r['category']),str(r['question']),str(r['response']),str(r['score']),str(r['comment'] or '')[:110]] for _,r in cdf.iterrows()]
        tab=Table(rows,colWidths=[1.2*inch,2.2*inch,.9*inch,.55*inch,1.8*inch]); tab.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.35,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('FONTSIZE',(0,0),(-1,-1),7)])); story += [tab,Spacer(1,10)]
    photo_rows=df[df['image_path'].fillna('')!='']
    if not photo_rows.empty:
        story += [PageBreak(),Paragraph("<b>Photo Evidence</b>",styles['Heading2'])]
        for _,r in photo_rows.iterrows():
            story.append(Paragraph(f"{r['criterion']} - {r['category']}: {r['question']}",styles['Normal']))
            if r.get('annotation_note'): story.append(Paragraph(f"Annotation note: {r['annotation_note']}",styles['Normal']))
            try:
                if Path(r['image_path']).exists(): story.append(RLImage(r['image_path'],width=3.8*inch,height=2.6*inch))
            except Exception: pass
            story.append(Spacer(1,8))
    if not capas.empty:
        story += [PageBreak(),Paragraph("<b>CAPA Register</b>",styles['Heading2'])]
        rows=[["Finding","NC Type","Priority","Responsible","Due","Status"]]+[[str(r['finding'])[:90],r['nc_type'],r['priority'],r['responsible_person'],r['due_date'],r['status']] for _,r in capas.iterrows()]
        tab=Table(rows,colWidths=[2.3*inch,.8*inch,.8*inch,1.1*inch,.8*inch,.9*inch]); tab.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.35,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('FONTSIZE',(0,0),(-1,-1),7)])); story.append(tab)
    story += [Spacer(1,18),Paragraph("<b>Digital Signatures</b>",styles['Heading3'])]
    story.append(Paragraph(f"Auditor Signature: {df['auditor_signature'].dropna().iloc[0] if not df.empty else ''}",styles['Normal']))
    story.append(Paragraph(f"Auditee/Branch Manager Signature: {df['auditee_signature'].dropna().iloc[0] if not df.empty else ''}",styles['Normal']))
    doc.build(story); return path,None

def excel_bytes(df,capas,schedules):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        df.to_excel(w,index=False,sheet_name='Audit Records'); capas.to_excel(w,index=False,sheet_name='CAPA Register'); schedules.to_excel(w,index=False,sheet_name='Audit Schedule')
        if not df.empty:
            sm=[]
            for c,cdf in df.groupby('criterion'):
                x=pct(cdf['score'].sum(),len(cdf)); sm.append({'Criterion':c,'Percentage':x,'Rating':rate(x)})
            pd.DataFrame(sm).to_excel(w,index=False,sheet_name='Summary')
    out.seek(0); return out.getvalue()

if 'logged_in' not in st.session_state: st.session_state.logged_in=False
if 'user' not in st.session_state: st.session_state.user={}
if 'audit_header_data' not in st.session_state:
    st.session_state['audit_header_data'] = None

if not st.session_state.logged_in:
    st.markdown("""<div class="login-wrapper"><div class="login-title">AuditReady Pro</div><div class="login-subtitle">Starbites QHSE Audit System</div></div>""",unsafe_allow_html=True)
    users=query_df("SELECT username FROM users WHERE active=1 ORDER BY username")
    username=st.selectbox("Username",users['username'].tolist() if not users.empty else ['Admin'])
    password=st.text_input("Password",type="password")
    if st.button("Login"):
        df=query_df("SELECT * FROM users WHERE username=?",(username,))
        if df.empty: st.error("Invalid login.")
        else:
            u=df.iloc[0].to_dict()
            if u['locked']==1: st.error("Account locked. Admin must reset it.")
            elif u['password_hash']==hash_password(password):
                update("UPDATE users SET failed_attempts=0 WHERE username=?",(username,)); st.session_state.logged_in=True; st.session_state.user=u; st.rerun()
            else:
                attempts=int(u['failed_attempts'] or 0)+1; locked=1 if attempts>=3 else 0
                update("UPDATE users SET failed_attempts=?,locked=? WHERE username=?",(attempts,locked,username)); st.error("3 failed attempts. Account locked." if locked else f"Invalid password. {3-attempts} attempt(s) remaining.")
    st.stop()

st.markdown(f"""<div class="brand-card"><span class="doc-badge">{get_setting('doc_number',DOC_NUMBER)} | Ver {get_setting('version',VERSION)}</span><h2>{get_setting('company_name',COMPANY_NAME)}</h2><b>{APP_TITLE}</b><br>Issue Date: {get_setting('issue_date',ISSUE_DATE)}</div>""",unsafe_allow_html=True)
st.caption(f"Logged in as: {current_user().get('username')} | Role: {role()} | Branch: {current_user().get('branch')}")
menu=["New Audit","CAPA Tracker","Criterion Dashboard","Audit Schedule","Reports"]
if role()=="Admin": menu += ["Branch Trend Dashboard","User Management","Branding Settings"]
selected=st.sidebar.radio("Menu",menu)
if st.sidebar.button("Logout"): st.session_state.logged_in=False; st.session_state.user={}; st.rerun()

if selected=="New Audit":
    if role() not in ["QHSE","Admin"]: st.error("Only QHSE users and Admin can submit audits."); st.stop()
    st.header("New Audit")
    with st.form("audit_header_form"):
        branch=branch_picker("Branch Name", "audit_branch"); auditor=st.text_input("Auditor Name",value=current_user().get('full_name','')); auditee=st.text_input("Auditee / Branch Manager Name"); audit_date=st.date_input("Date of Audit",value=date.today()); criterion=st.selectbox("Audit Criterion",list(CHECKLISTS.keys())); auditor_sig=st.text_input("Auditor Digital Signature"); auditee_sig=st.text_input("Auditee / Branch Manager Digital Signature"); load=st.form_submit_button("Load Checklist")
    if load:
        if not branch:
            st.error("Please enter a branch name before loading the checklist.")
            st.stop()
        st.session_state["audit_header_data"] = {
            "audit_ref": audit_ref(branch),
            "branch": branch,
            "auditor": auditor,
            "auditee": auditee,
            "audit_date": audit_date.isoformat(),
            "criterion": criterion,
            "auditor_signature": auditor_sig,
            "auditee_signature": auditee_sig
        }
    if st.session_state["audit_header_data"]:
        h=st.session_state['audit_header_data']; checklist=CHECKLISTS[h['criterion']]; st.subheader(f"{h['criterion']} Checklist"); st.info("Scoring: No NC = 10 | Minor NC = -5 | Major NC = -10 | Observation = 6")
        rows=[]
        with st.form("audit_form"):
            for i,(category,question) in enumerate(checklist,1):
                st.markdown('<div class="audit-card">',unsafe_allow_html=True); st.markdown(f'<div class="question-title">{i}. {question}</div>',unsafe_allow_html=True); st.markdown(f'<div class="category-text">Category: {category}</div>',unsafe_allow_html=True)
                response=st.radio("Outcome",RESPONSES,key=f"resp_{h['audit_ref']}_{i}",horizontal=True); comment=st.text_area("Comment / Finding",key=f"comment_{h['audit_ref']}_{i}"); photo=st.file_uploader("Upload Audit Picture",type=['jpg','jpeg','png'],key=f"photo_{h['audit_ref']}_{i}"); note=st.text_area("Photo Annotation Note",key=f"annot_{h['audit_ref']}_{i}",placeholder="Describe what to circle/mark in the photo."); priority=st.selectbox("CAPA Priority if NC/Observation",PRIORITIES,key=f"prio_{i}"); resp_person=st.text_input("Responsible Person if CAPA required",key=f"resp_person_{i}"); due=st.date_input("CAPA Due Date",value=date.today()+timedelta(days=7),key=f"due_{i}")
                rows.append(dict(category=category,question=question,response=response,nc_type=response if response in NC_TYPES else '',score=SCORING[response],comment=comment,photo=photo,note=note,priority=priority,resp_person=resp_person,due=due.isoformat()))
                st.markdown('</div>',unsafe_allow_html=True)
            submitted=st.form_submit_button("Submit Audit")
        if submitted:
            total=0
            for i,r in enumerate(rows,1):
                total+=r['score']; img=save_file(r['photo'],PHOTO_DIR,f"{h['audit_ref']}_{i}")
                execute("""INSERT INTO audits(audit_ref,branch,auditor,auditee,audit_date,criterion,category,question,response,nc_type,score,comment,image_path,annotation_note,auditor_signature,auditee_signature,submitted_by,submitted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(h['audit_ref'],h['branch'],h['auditor'],h['auditee'],h['audit_date'],h['criterion'],r['category'],r['question'],r['response'],r['nc_type'],r['score'],r['comment'],img,r['note'],h['auditor_signature'],h['auditee_signature'],current_user().get('username'),datetime.now().isoformat()))
                if r['response'] in NC_TYPES: execute("""INSERT INTO capas(audit_ref,branch,criterion,category,finding,nc_type,priority,corrective_action,responsible_person,due_date,status,evidence_path,verification_comment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(h['audit_ref'],h['branch'],h['criterion'],r['category'],r['question'],r['response'],r['priority'],'',r['resp_person'],r['due'],'Open','','',datetime.now().isoformat()))
            x=pct(total,len(rows)); st.success(f"Audit submitted. Ref: {h['audit_ref']}"); st.metric("Criterion Score",f"{x}%"); st.metric("Rating",rate(x)); st.session_state["audit_header_data"] = None

elif selected=="CAPA Tracker":
    st.header("CAPA Tracker"); capas=query_df("SELECT * FROM capas ORDER BY id DESC")
    if role()=="Branch Manager": capas=capas[capas['branch']==current_user().get('branch')]
    if capas.empty: st.info("No CAPAs available.")
    else:
        status=st.selectbox("Status filter",["All"]+CAPA_STATUS); overdue=st.selectbox("Overdue filter",["All","Overdue only"]); view=capas.copy()
        if status!="All": view=view[view['status']==status]
        if overdue=="Overdue only": view=view[(view['status']!='Closed') & (pd.to_datetime(view['due_date'])<pd.Timestamp(date.today()))]
        st.dataframe(view,use_container_width=True)
        if not view.empty:
            cid=st.selectbox("Select CAPA to update",view['id'].tolist()); sel=capas[capas['id']==cid].iloc[0]
            with st.form("capa_update"):
                st.write(f"Finding: **{sel['finding']}**"); action=st.text_area("Corrective Action",value=sel['corrective_action'] or ''); resp=st.text_input("Responsible Person",value=sel['responsible_person'] or ''); due=st.date_input("Due Date",value=pd.to_datetime(sel['due_date']).date() if sel['due_date'] else date.today()); stat=st.selectbox("Status",CAPA_STATUS,index=CAPA_STATUS.index(sel['status']) if sel['status'] in CAPA_STATUS else 0); ev=st.file_uploader("CAPA Evidence Photo",type=['jpg','jpeg','png']); ver=st.text_area("Verification Comment",value=sel['verification_comment'] or ''); save=st.form_submit_button("Save CAPA Update")
            if save:
                ev_path=sel['evidence_path'] or ''
                if ev: ev_path=save_file(ev,PHOTO_DIR,f"CAPA_{cid}")
                update("UPDATE capas SET corrective_action=?,responsible_person=?,due_date=?,status=?,evidence_path=?,verification_comment=? WHERE id=?",(action,resp,due.isoformat(),stat,ev_path,ver,int(cid))); st.success("CAPA updated.")

elif selected=="Criterion Dashboard":
    st.header("Criterion Dashboard"); df=query_df("SELECT * FROM audits ORDER BY id DESC")
    if role()=="Branch Manager": df=df[df['branch']==current_user().get('branch')]
    if df.empty: st.warning("No audit data found.")
    else:
        b=st.selectbox("Filter by branch",["All"]+sorted(df['branch'].dropna().unique().tolist())); a=st.selectbox("Filter by auditor",["All"]+sorted(df['auditor'].dropna().unique().tolist())); d=st.selectbox("Filter by date",["All"]+sorted(df['audit_date'].dropna().unique().tolist(),reverse=True)); c=st.selectbox("Filter by criterion",["All"]+sorted(df['criterion'].dropna().unique().tolist())); n=st.selectbox("Filter by NC type",["All","No NC","Minor NC","Major NC","Observation"])
        view=df.copy()
        if b!="All": view=view[view['branch']==b]
        if a!="All": view=view[view['auditor']==a]
        if d!="All": view=view[view['audit_date']==d]
        if c!="All": view=view[view['criterion']==c]
        if n!="All": view=view[view['response']==n]
        summary=[]
        for crit,cdf in view.groupby('criterion'):
            x=pct(cdf['score'].sum(),len(cdf)); summary.append({'Criterion':crit,'Percentage':x,'Rating':rate(x),'Records':len(cdf)})
        sm=pd.DataFrame(summary)
        if sm.empty: st.warning("No records match filters.")
        else:
            for _,r in sm.iterrows(): st.metric(r['Criterion'],f"{r['Percentage']}%",r['Rating'])
            st.dataframe(sm,use_container_width=True); st.bar_chart(sm.set_index('Criterion')['Percentage'])

elif selected=="Audit Schedule":
    st.header("Audit Scheduling")
    if role() in ["Admin","QHSE"]:
        with st.form("schedule"):
            b=branch_picker("Branch", "schedule_branch"); aud=st.text_input("Auditor"); pl=st.date_input("Planned Audit Date",value=date.today()+timedelta(days=7)); crit=st.selectbox("Criterion",list(CHECKLISTS.keys())); add=st.form_submit_button("Add Schedule")
        if add:
            if not b:
                st.error("Please enter a branch name before adding the schedule.")
            else:
                execute("INSERT INTO schedules(branch,auditor,planned_date,criterion,status,created_at) VALUES(?,?,?,?,?,?)",(b,aud,pl.isoformat(),crit,'Planned',datetime.now().isoformat())); st.success("Schedule added.")
    sch=query_df("SELECT * FROM schedules ORDER BY planned_date DESC")
    if role()=="Branch Manager": sch=sch[sch['branch']==current_user().get('branch')]
    if sch.empty: st.info("No schedules available.")
    else:
        sch['missed']=sch.apply(lambda r:'Missed' if r['status']=='Planned' and r['planned_date']<date.today().isoformat() else '',axis=1); st.dataframe(sch,use_container_width=True)

elif selected=="Reports":
    st.header("Reports, PDF, Excel and Sharing"); df=query_df("SELECT * FROM audits ORDER BY id DESC"); capas=query_df("SELECT * FROM capas ORDER BY id DESC"); sch=query_df("SELECT * FROM schedules ORDER BY id DESC")
    if role()=="Branch Manager": df=df[df['branch']==current_user().get('branch')]; capas=capas[capas['branch']==current_user().get('branch')]; sch=sch[sch['branch']==current_user().get('branch')]
    if df.empty: st.warning("No audit records available.")
    else:
        ref=st.selectbox("Select Audit Report",sorted(df['audit_ref'].dropna().unique().tolist(),reverse=True)); rdf=df[df['audit_ref']==ref]; cdf=capas[capas['audit_ref']==ref] if not capas.empty else pd.DataFrame()
        if st.button("Generate PDF Report"):
            pdf,err=generate_pdf(ref,rdf,cdf)
            if err: st.error(err)
            else:
                st.success("PDF generated.")
                with open(pdf,'rb') as f: st.download_button("Download PDF Report",f.read(),file_name=Path(pdf).name,mime='application/pdf')
                rec=get_setting('email_recipients',''); wa=get_setting('whatsapp_number',''); st.markdown(f"[Open Email App](mailto:{rec}?subject=QHSE%20Audit%20Report&body=Please%20find%20the%20completed%20QHSE%20audit%20report%20attached.)")
                if wa: st.markdown(f"[Open WhatsApp Share](https://wa.me/{wa}?text=QHSE%20audit%20report%20completed.%20Please%20review%20the%20PDF.)")
        st.download_button("Download Excel Workbook",excel_bytes(df,capas,sch),"auditready_qhse_export.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.dataframe(rdf,use_container_width=True)

elif selected=="Branch Trend Dashboard":
    st.header("Branch Trend Dashboard"); df=query_df("SELECT * FROM audits ORDER BY audit_date")
    if df.empty: st.warning("No audit records yet.")
    else:
        b=st.selectbox("Select Branch",sorted(df['branch'].dropna().unique().tolist())); bdf=df[df['branch']==b]; trend=[]
        for (dt,crit),cdf in bdf.groupby(['audit_date','criterion']): trend.append({'Audit Date':dt,'Criterion':crit,'Percentage':pct(cdf['score'].sum(),len(cdf))})
        tdf=pd.DataFrame(trend); st.dataframe(tdf,use_container_width=True)
        if not tdf.empty: st.line_chart(tdf.pivot_table(index='Audit Date',columns='Criterion',values='Percentage',aggfunc='mean'))
        st.subheader("Repeated Non-Conformities"); ncs=bdf[bdf['response'].isin(['Minor NC','Major NC'])]
        if ncs.empty: st.success("No repeated non-conformities found.")
        else: st.dataframe(ncs.groupby(['category','question','response']).size().reset_index(name='Count').sort_values('Count',ascending=False),use_container_width=True)

elif selected=="User Management":
    st.header("Admin User Management")
    with st.form("add_user"):
        u=st.text_input("Username"); f=st.text_input("Full Name"); p=st.text_input("Password",type='password'); r=st.selectbox("Role",['QHSE','Branch Manager','Admin']); b=st.selectbox("Assigned Branch",['All']+branch_options()); add=st.form_submit_button("Add User")
    if add:
        try: execute("INSERT INTO users(username,password_hash,role,full_name,branch,active,created_at) VALUES(?,?,?,?,?,1,?)",(u,hash_password(p),r,f,b,datetime.now().isoformat())); st.success("User added.")
        except Exception as e: st.error(f"Could not add user: {e}")
    users=query_df("SELECT id,username,role,full_name,branch,active,failed_attempts,locked FROM users ORDER BY username"); st.dataframe(users,use_container_width=True)
    edit=st.selectbox("Select user to manage",users['username'].tolist()); row=users[users['username']==edit].iloc[0]
    c1,c2,c3=st.columns(3)
    if c1.button("Deactivate / Activate"): update("UPDATE users SET active=? WHERE username=?",(0 if row['active']==1 else 1,edit)); st.success("User status updated."); st.rerun()
    if c2.button("Reset Lock"): update("UPDATE users SET failed_attempts=0,locked=0 WHERE username=?",(edit,)); st.success("Lock reset."); st.rerun()
    np=st.text_input("New Password",type='password')
    if c3.button("Reset Password"):
        if np: update("UPDATE users SET password_hash=?,failed_attempts=0,locked=0 WHERE username=?",(hash_password(np),edit)); st.success("Password reset."); st.rerun()
        else: st.warning("Enter a new password.")

elif selected=="Branding Settings":
    st.header("Logo and Company Branding")
    with st.form("brand"):
        cn=st.text_input("Company Name",value=get_setting('company_name',COMPANY_NAME)); dn=st.text_input("Document Number",value=get_setting('doc_number',DOC_NUMBER)); idt=st.text_input("Issue Date",value=get_setting('issue_date',ISSUE_DATE)); ver=st.text_input("Version Number",value=get_setting('version',VERSION)); rec=st.text_input("Default Email Recipients",value=get_setting('email_recipients','')); wa=st.text_input("WhatsApp Number with Country Code",value=get_setting('whatsapp_number','')); logo=st.file_uploader("Upload Company Logo",type=['png','jpg','jpeg']); save=st.form_submit_button("Save Branding")
    if save:
        for k,v in [('company_name',cn),('doc_number',dn),('issue_date',idt),('version',ver),('email_recipients',rec),('whatsapp_number',wa)]: set_setting(k,v)
        if logo: save_file(logo,BRAND_DIR,'company_logo')
        st.success("Branding saved.")
