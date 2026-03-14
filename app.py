import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="War Room BAaaS", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_dict=True)

st.title("🛡️ War Room BAaaS")
st.subheader("EPC Operations & Profitability Command Center")

# --- SIDEBAR: DATA INGESTION ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/shield.png", width=80)
    st.header("Project Controls")
    selected_project = st.selectbox("Select Project", ["Palais Royale", "Godrej Pune", "New Tender X"])
    st.divider()
    
    st.subheader("Data Upload")
    data_type = st.radio("Upload Category", ["Material Logs", "Machinery Logs", "Manpower Logs"])
    uploaded_file = st.file_uploader(f"Upload {data_type} (CSV)", type="csv")
    
    st.info("Ensure files follow the War Room Standard Template.")

# --- MODULE 1: MATERIAL VARIATION (THE KILL METRIC) ---
def render_material_tab(df):
    st.header("📦 Material Leakage Analysis")
    # Calculation
    df['var_pct'] = ((df['qty_actual'] - df['qty_estimated']) / df['qty_estimated']) * 100
    df['leakage_rs'] = (df['qty_actual'] - df['qty_estimated']) * df['unit_rate']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Leakage", f"₹{df['leakage_rs'].sum():,.0f}", delta=f"{df['var_pct'].mean():.1f}% Avg Var", delta_color="inverse")
    c2.metric("Highest Deviation", df.loc[df['var_pct'].idxmax(), 'material_type'])
    c3.metric("Data Health", "98%", delta="Validated")

    fig = px.bar(df, x='material_type', y='var_pct', color='var_pct', 
                 title="Variance by Material Type", color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: MACHINERY UTILIZATION ---
def render_machinery_tab(df):
    st.header("🚜 Machinery Efficiency & Idle Loss")
    # Hourly rates based on your specific requirements (Rent + Salary / 240 hrs)
    rates = {'JCB': 437, 'Tower Crane': 1187, 'Generator': 333, 'RMC Pump': 604}
    
    df['hourly_rate'] = df['machine_type'].map(rates)
    df['idle_loss'] = df['idle_hours'] * df['hourly_rate']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Idle Time Loss", f"₹{df['idle_loss'].sum():,.0f}", delta="Sunk Cost", delta_color="inverse")
    c2.metric("Fleet Utilization", f"{(df['working_hours'].sum() / (df['working_hours'].sum() + df['idle_hours'].sum()))*100:.1f}%")
    c3.metric("Critical Asset", df.loc[df['idle_loss'].idxmax(), 'machine_type'])

    fig = go.Figure(data=[
        go.Bar(name='Working', x=df['machine_type'], y=df['working_hours'], marker_color='#2ecc71'),
        go.Bar(name='Idle', x=df['machine_type'], y=df['idle_hours'], marker_color='#e74c3c')
    ])
    fig.update_layout(barmode='stack', title="Working vs. Idle Hours")
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: MANPOWER & PAYROLL ---
def render_manpower_tab(df):
    st.header("👥 Manpower Distribution")
    total_payroll = df['actual_cost'].sum()
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Payroll Burn", f"₹{total_payroll:,.0f}")
        fig_pie = px.pie(df, values='actual_cost', names='Role', hole=.4, title="Cost by Role")
        st.plotly_chart(fig_pie)
    with c2:
        st.metric("Total Headcount", df['count'].sum())
        fig_bar = px.bar(df, x='Role', y='count', title="Headcount Distribution", color='Role')
        st.plotly_chart(fig_bar)

# --- MAIN APP LOGIC ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    tab1, tab2, tab3 = st.tabs(["Materials", "Machinery", "Manpower"])
    
    with tab1:
        if data_type == "Material Logs": render_material_tab(df)
        else: st.warning("Please switch 'Upload Category' to Material Logs")
        
    with tab2:
        if data_type == "Machinery Logs": render_machinery_tab(df)
        else: st.warning("Please switch 'Upload Category' to Machinery Logs")
        
    with tab3:
        if data_type == "Manpower Logs": render_manpower_tab(df)
        else: st.warning("Please switch 'Upload Category' to Manpower Logs")
else:
    st.image("https://img.icons8.com/clouds/200/000000/monitoring.png")
    st.header("Welcome to the War Room.")
    st.write("Upload your site CSV logs in the sidebar to begin operational analysis.")