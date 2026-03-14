import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="War Room BAaaS | Executive P&L", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00b4d8; }
    .profit-positive { border-left: 5px solid #2ecc71 !important; }
    .profit-negative { border-left: 5px solid #e74c3c !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ War Room BAaaS")
st.subheader("Executive Profit & Loss Command Center")

# --- SIDEBAR: DATA INGESTION ---
with st.sidebar:
    st.header("⚙️ Project Controls")
    selected_project = st.selectbox("Select Project Filter", ["All Projects", "Palais Royale", "Godrej Pune"])
    st.divider()
    
    st.subheader("📂 Upload Financial & Site Data")
    st.write("Upload logs to generate the Executive Dashboard:")
    
    # The New Financial Master File
    fin_file = st.file_uploader("1. Project Billing/Budget (CSV)", type="csv")
    mat_file = st.file_uploader("2. Material Logs (CSV)", type="csv")
    mac_file = st.file_uploader("3. Machinery Logs (CSV)", type="csv")
    man_file = st.file_uploader("4. Manpower Logs (CSV)", type="csv")

# Helper function to filter data
def filter_project(df, proj):
    if proj == "All Projects":
        return df
    return df[df['project_id'] == proj]

# Helper to safely load and filter dataframes
def load_and_filter(file, proj):
    if file:
        df = pd.read_csv(file)
        return filter_project(df, proj)
    return pd.DataFrame()

# Load all data
df_fin = load_and_filter(fin_file, selected_project)
df_mat = load_and_filter(mat_file, selected_project)
df_mac = load_and_filter(mac_file, selected_project)
df_man = load_and_filter(man_file, selected_project)

# --- NAVIGATION TABS ---
if not (fin_file or mat_file or mac_file or man_file):
    st.info("👋 Welcome to the Executive War Room. Please upload your CSV logs in the sidebar to populate the P&L and operational metrics.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive P&L", "📦 Material Costs", "🚜 Machinery Costs", "👥 Manpower Costs"])

    # --- TAB 1: EXECUTIVE P&L (THE C-SUITE VIEW) ---
    with tab1:
        st.header("Corporate Profitability & Margin Analysis")
        
        # Calculate Total Costs Dynamically
        total_mat_cost = (df_mat['qty_actual'] * df_mat['unit_rate']).sum() if not df_mat.empty else 0
        
        total_mac_cost = 0
        if not df_mac.empty:
            rates = {'JCB': 437, 'Tower Crane': 1187, 'Generator': 333, 'RMC Pump': 604}
            df_mac['hourly_rate'] = df_mac['machine_type'].map(rates).fillna(500)
            total_mac_cost = (df_mac['working_hours'] + df_mac['idle_hours']).sum() * df_mac['hourly_rate'].mean() # Simplified total cost
            
        total_man_cost = df_man['actual_cost'].sum() if not df_man.empty else 0
        
        total_project_cost = total_mat_cost + total_mac_cost + total_man_cost
        
        # Calculate Revenue & Profit
        total_billed = df_fin['billed_to_date'].sum() if not df_fin.empty else 0
        gross_profit = total_billed - total_project_cost
        gross_margin_pct = (gross_profit / total_billed * 100) if total_billed > 0 else 0
        
        # High-Level Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Billed Revenue", f"₹{total_billed:,.0f}")
        c2.metric("Total Executed Cost", f"₹{total_project_cost:,.0f}")
        
        # Dynamic styling based on profit
        delta_color = "normal" if gross_profit >= 0 else "inverse"
        c3.metric("Current Gross Profit", f"₹{gross_profit:,.0f}", delta=f"Margin: {gross_margin_pct:.1f}%", delta_color=delta_color)
        
        collection_ratio = (df_fin['collected_to_date'].sum() / total_billed * 100) if not df_fin.empty and total_billed > 0 else 0
        c4.metric("Cash Collection Ratio", f"{collection_ratio:.1f}%", help="Cash actually received vs Billed")

        st.markdown("---")
        
        # THE WATERFALL CHART: Ultimate P&L Visualization
        st.subheader("Financial Waterfall: Revenue to Net Margin")
        if total_billed > 0:
            fig_waterfall = go.Figure(go.Waterfall(
                name="20", orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["Billed Revenue", "Material Cost", "Machinery Cost", "Manpower Cost", "Gross Profit"],
                textposition="outside",
                text=[f"₹{total_billed:,.0f}", f"-₹{total_mat_cost:,.0f}", f"-₹{total_mac_cost:,.0f}", f"-₹{total_man_cost:,.0f}", f"₹{gross_profit:,.0f}"],
                y=[total_billed, -total_mat_cost, -total_mac_cost, -total_man_cost, gross_profit],
                connector={"line":{"color":"rgb(63, 63, 63)"}},
                decreasing={"marker":{"color":"#e74c3c"}},
                increasing={"marker":{"color":"#2ecc71"}},
                totals={"marker":{"color":"#00b4d8"}}
            ))
            fig_waterfall.update_layout(title="Project Cost Breakdown against Revenue", waterfallgap=0.3)
            st.plotly_chart(fig_waterfall, use_container_width=True)
        else:
            st.info("Upload the 'Project Billing/Budget' CSV to generate the Financial Waterfall Chart.")

    # --- TAB 2: MATERIALS ---
    with tab2:
        if not df_mat.empty:
            df_mat['var_pct'] = ((df_mat['qty_actual'] - df_mat['qty_estimated']) / df_mat['qty_estimated']) * 100
            df_mat['leakage_rs'] = (df_mat['qty_actual'] - df_mat['qty_estimated']) * df_mat['unit_rate']
            st.metric("Total Material Leakage", f"₹{df_mat['leakage_rs'].sum():,.0f}", delta=f"{df_mat['var_pct'].mean():.1f}% Avg Var", delta_color="inverse")
            fig_mat = px.bar(df_mat, x='material_type', y='var_pct', color='var_pct', title="Variance by Material Type (%)", color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig_mat, use_container_width=True)
        else:
            st.warning("No Material data uploaded.")

    # --- TAB 3: MACHINERY ---
    with tab3:
        if not df_mac.empty:
            df_mac['idle_loss'] = df_mac['idle_hours'] * df_mac['hourly_rate']
            st.metric("Total Idle Time Loss", f"₹{df_mac['idle_loss'].sum():,.0f}", delta="Sunk Cost", delta_color="inverse")
            fig_mac = go.Figure(data=[
                go.Bar(name='Working Hours', x=df_mac['machine_type'], y=df_mac['working_hours'], marker_color='#2ecc71'),
                go.Bar(name='Idle Hours', x=df_mac['machine_type'], y=df_mac['idle_hours'], marker_color='#e74c3c')
            ])
            fig_mac.update_layout(barmode='stack', title="Working vs. Idle Hours by Machine")
            st.plotly_chart(fig_mac, use_container_width=True)
        else:
            st.warning("No Machinery data uploaded.")

    # --- TAB 4: MANPOWER ---
    with tab4:
        if not df_man.empty:
            st.metric("Total Payroll Burn", f"₹{total_man_cost:,.0f}")
            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_pie = px.pie(df_man, values='actual_cost', names='Role', hole=.4, title="Cost Distribution by Role")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_bar:
                fig_bar = px.bar(df_man, x='Role', y='count', title="Headcount Distribution", color='Role')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No Manpower data uploaded.")
