import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="War Room BAaaS v1.2", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS FOR MASSIVE FONTS ---
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #0e1117; }
    
    /* Make the KPI Label (Title) Larger and Bolder */
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; font-weight: 700 !important; color: #a6aeb8; }
    
    /* Make the KPI Value Massive */
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 900 !important; }
    
    /* Make the Delta (Up/Down arrow text) Larger */
    [data-testid="stMetricDelta"] { font-size: 1.2rem !important; }
    
    /* Container styling for the KPI Cards */
    .stMetric { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 6px solid #00b4d8; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ War Room BAaaS (v1.2)")
st.subheader("Executive Profit & Loss Command Center")

# --- SIDEBAR: DATA INGESTION ---
with st.sidebar:
    st.header("⚙️ Project Controls")
    selected_project = st.selectbox("Select Project Filter", ["All Projects", "Palais Royale", "Godrej Pune"])
    st.divider()
    
    st.subheader("📂 Upload Financial & Site Data")
    st.write("Upload logs to generate the Executive Dashboard:")
    
    fin_file = st.file_uploader("1. Project Billing/Budget (CSV)", type="csv")
    mat_file = st.file_uploader("2. Material Logs (CSV)", type="csv")
    mac_file = st.file_uploader("3. Machinery Logs (CSV)", type="csv")
    man_file = st.file_uploader("4. Manpower Logs (CSV)", type="csv")

# --- HELPER FUNCTIONS ---
def filter_project(df, proj):
    if proj == "All Projects": return df
    return df[df['project_id'] == proj]

def load_and_filter(file, proj):
    if file:
        return filter_project(pd.read_csv(file), proj)
    return pd.DataFrame()

# Helper function to apply massive fonts to any Plotly chart
def apply_executive_fonts(fig):
    fig.update_layout(
        font=dict(size=15), # Base font size for whole chart
        title=dict(font=dict(size=22, family="Arial Black")), # Massive Title
        xaxis=dict(tickfont=dict(size=14, weight="bold"), title_font=dict(size=16)),
        yaxis=dict(tickfont=dict(size=14, weight="bold"), title_font=dict(size=16)),
        legend=dict(font=dict(size=14)),
        height=500, # Taller charts for better visibility
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- LOAD DATA ---
df_fin = load_and_filter(fin_file, selected_project)
df_mat = load_and_filter(mat_file, selected_project)
df_mac = load_and_filter(mac_file, selected_project)
df_man = load_and_filter(man_file, selected_project)

# --- NAVIGATION TABS ---
if not (fin_file or mat_file or mac_file or man_file):
    st.info("👋 Welcome to the Executive War Room (Version 1.2). Please upload your CSV logs in the sidebar to populate the P&L and operational metrics.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive P&L", "📦 Material Costs", "🚜 Machinery Costs", "👥 Manpower Costs"])

    # --- TAB 1: EXECUTIVE P&L ---
    with tab1:
        st.header("Corporate Profitability & Margin Analysis")
        
        # Calculations
        total_mat_cost = (df_mat['qty_actual'] * df_mat['unit_rate']).sum() if not df_mat.empty else 0
        total_mac_cost = 0
        if not df_mac.empty:
            rates = {'JCB': 437, 'Tower Crane': 1187, 'Generator': 333, 'RMC Pump': 604}
            df_mac['hourly_rate'] = df_mac['machine_type'].map(rates).fillna(500)
            total_mac_cost = (df_mac['working_hours'] + df_mac['idle_hours']).sum() * df_mac['hourly_rate'].mean()
        total_man_cost = df_man['actual_cost'].sum() if not df_man.empty else 0
        total_project_cost = total_mat_cost + total_mac_cost + total_man_cost
        
        total_billed = df_fin['billed_to_date'].sum() if not df_fin.empty else 0
        gross_profit = total_billed - total_project_cost
        gross_margin_pct = (gross_profit / total_billed * 100) if total_billed > 0 else 0
        
        # KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Billed Revenue", f"₹{total_billed:,.0f}")
        c2.metric("Total Executed Cost", f"₹{total_project_cost:,.0f}")
        
        delta_color = "normal" if gross_profit >= 0 else "inverse"
        c3.metric("Current Gross Profit", f"₹{gross_profit:,.0f}", delta=f"Margin: {gross_margin_pct:.1f}%", delta_color=delta_color)
        
        collection_ratio = (df_fin['collected_to_date'].sum() / total_billed * 100) if not df_fin.empty and total_billed > 0 else 0
        c4.metric("Cash Collection Ratio", f"{collection_ratio:.1f}%", help="Cash actually received vs Billed")

        st.markdown("---")
        
        # Waterfall Chart
        st.subheader("Financial Waterfall: Revenue to Net Margin")
        if total_billed > 0:
            is_profit = gross_profit >= 0
            total_color = "#2ecc71" if is_profit else "#e74c3c"
            final_label = "Gross Profit" if is_profit else "Net Loss"
            
            fig_waterfall = go.Figure(go.Waterfall(
                name="P&L", orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["Billed Revenue", "Material Cost", "Machinery Cost", "Manpower Cost", final_label],
                textposition="outside",
                text=[f"<b>₹{total_billed:,.0f}</b>", f"<b>-₹{total_mat_cost:,.0f}</b>", f"<b>-₹{total_mac_cost:,.0f}</b>", f"<b>-₹{total_man_cost:,.0f}</b>", f"<b>₹{gross_profit:,.0f}</b>"],
                y=[total_billed, -total_mat_cost, -total_mac_cost, -total_man_cost, gross_profit],
                connector={"line":{"color":"rgba(255, 255, 255, 0.5)", "width": 2}},
                decreasing={"marker":{"color":"#e74c3c"}}, increasing={"marker":{"color":"#2ecc71"}}, totals={"marker":{"color": total_color}}
            ))
            fig_waterfall.update_traces(textfont_size=16)
            fig_waterfall = apply_executive_fonts(fig_waterfall)
            fig_waterfall.update_layout(height=650, yaxis=dict(zeroline=True, zerolinewidth=3, zerolinecolor='rgba(255,255,255,0.7)'))
            st.plotly_chart(fig_waterfall, use_container_width=True)

    # --- TAB 2: MATERIALS ---
    with tab2:
        if not df_mat.empty:
            df_mat['var_pct'] = ((df_mat['qty_actual'] - df_mat['qty_estimated']) / df_mat['qty_estimated']) * 100
            df_mat['leakage_rs'] = (df_mat['qty_actual'] - df_mat['qty_estimated']) * df_mat['unit_rate']
            st.metric("Total Material Leakage", f"₹{df_mat['leakage_rs'].sum():,.0f}", delta=f"{df_mat['var_pct'].mean():.1f}% Avg Var", delta_color="inverse")
            
            fig_mat = px.bar(df_mat, x='material_type', y='var_pct', color='var_pct', title="Variance by Material Type (%)", color_continuous_scale='RdYlGn_r', text_auto='.1f')
            fig_mat.update_traces(textfont_size=14, textposition="outside")
            st.plotly_chart(apply_executive_fonts(fig_mat), use_container_width=True)

    # --- TAB 3: MACHINERY ---
    with tab3:
        if not df_mac.empty:
            df_mac['idle_loss'] = df_mac['idle_hours'] * df_mac['hourly_rate']
            st.metric("Total Idle Time Loss", f"₹{df_mac['idle_loss'].sum():,.0f}", delta="Sunk Cost", delta_color="inverse")
            
            fig_mac = go.Figure(data=[
                go.Bar(name='Working Hours', x=df_mac['machine_type'], y=df_mac['working_hours'], marker_color='#2ecc71', text=df_mac['working_hours'], textposition='auto'),
                go.Bar(name='Idle Hours', x=df_mac['machine_type'], y=df_mac['idle_hours'], marker_color='#e74c3c', text=df_mac['idle_hours'], textposition='auto')
            ])
            fig_mac.update_layout(barmode='stack', title="Working vs. Idle Hours by Machine")
            fig_mac.update_traces(textfont_size=14)
            st.plotly_chart(apply_executive_fonts(fig_mac), use_container_width=True)

    # --- TAB 4: MANPOWER ---
    with tab4:
        if not df_man.empty:
            st.metric("Total Payroll Burn", f"₹{total_man_cost:,.0f}")
            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_pie = px.pie(df_man, values='actual_cost', names='Role', hole=.4, title="Cost Distribution by Role")
                fig_pie.update_traces(textfont_size=16)
                st.plotly_chart(apply_executive_fonts(fig_pie), use_container_width=True)
            with col_bar:
                fig_bar = px.bar(df_man, x='Role', y='count', title="Headcount Distribution", color='Role', text_auto=True)
                fig_bar.update_traces(textfont_size=14, textposition="outside")
                st.plotly_chart(apply_executive_fonts(fig_bar), use_container_width=True)
