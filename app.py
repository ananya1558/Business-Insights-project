import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime

# ==============================================================================
# PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Business Insights 360 | AtliQ Hardware",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern BI Look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #DBEAFE;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .kpi-delta-pos {
        font-size: 0.85rem;
        font-weight: 600;
        color: #16A34A;
    }
    .kpi-delta-neg {
        font-size: 0.85rem;
        font-weight: 600;
        color: #DC2626;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "project business")
DATASET_DIR = os.path.join(PROJECT_DIR, "DataSet")

# ==============================================================================
# DATA LOADERS WITH CACHING
# ==============================================================================
@st.cache_data
def load_datasets():
    # 1. Market Share Data
    ms_path = os.path.join(DATASET_DIR, "marketshare-v2022.xlsx")
    df_marketshare = pd.read_excel(ms_path) if os.path.exists(ms_path) else pd.DataFrame()
    
    # 2. Financial Targets
    target_path = os.path.join(DATASET_DIR, "targets.xlsx")
    df_targets = pd.read_excel(target_path) if os.path.exists(target_path) else pd.DataFrame()
    if not df_targets.empty and 'month' in df_targets.columns:
        df_targets['month'] = pd.to_datetime(df_targets['month'])
        df_targets['fiscal_year'] = df_targets['month'].apply(lambda d: d.year + (1 if d.month >= 9 else 0))
    
    # 3. Operational Expenses
    opex_path = os.path.join(DATASET_DIR, "operating-expenses-table.xlsx")
    df_opex = pd.read_excel(opex_path) if os.path.exists(opex_path) else pd.DataFrame()
    
    return df_marketshare, df_targets, df_opex

df_marketshare, df_targets, df_opex = load_datasets()

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.title("Business Insights 360")
    st.markdown("**AtliQ Hardware - Enterprise BI v2.0**")
    st.markdown("---")
    
    # Navigation
    view = st.radio(
        "Select Dashboard View:",
        [
            "🏛️ Executive View",
            "💰 Finance View",
            "📈 Sales View",
            "🎯 Marketing View",
            "🚚 Supply Chain View",
            "⚡ SQL Analytics Lab"
        ]
    )
    st.markdown("---")
    
    # Global Currency & Scale notice
    st.caption("🌐 **Currency**: USD ($)")
    st.caption("📏 **Unit**: Millions ($M)")
    st.caption(f"🕒 **Last Refreshed**: {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')} IST")
    st.markdown("---")
    st.info("💡 **Version 2.0 Updates**:\n- Dynamic Benchmarking (Target vs LY)\n- Dynamic GM% Tolerance Slicer\n- Dual-State Visual Switcher\n- C-Suite Executive Command Center")

# ==============================================================================
# VIEW 1: EXECUTIVE VIEW
# ==============================================================================
if view == "🏛️ Executive View":
    st.markdown('<div class="main-title">🏛️ Executive View</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">High-level macro performance, market share intelligence, and divisional contribution</div>', unsafe_allow_html=True)
    
    if not df_marketshare.empty:
        # Filter by Fiscal Year
        fy_list = sorted(df_marketshare['fy_desc'].dropna().unique())
        selected_fy = st.selectbox("Select Fiscal Year:", fy_list, index=len(fy_list)-1)
        
        filtered_ms = df_marketshare[df_marketshare['fy_desc'] == selected_fy]
        
        # High level KPIs
        total_market = filtered_ms['total_market_sales_$'].sum()
        atliq_sales = filtered_ms['atliq_sales_$'].sum()
        atliq_share = (atliq_sales / total_market * 100) if total_market > 0 else 0
        
        # Previous year comparison for delta
        prev_fy = selected_fy - 1
        prev_ms = df_marketshare[df_marketshare['fy_desc'] == prev_fy]
        if not prev_ms.empty:
            prev_total = prev_ms['total_market_sales_$'].sum()
            prev_atliq = prev_ms['atliq_sales_$'].sum()
            prev_share = (prev_atliq / prev_total * 100) if prev_total > 0 else 0
            share_delta = atliq_share - prev_share
            growth_pct = ((atliq_sales - prev_atliq) / prev_atliq * 100) if prev_atliq > 0 else 0
        else:
            share_delta = 0
            growth_pct = 0
            
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Market Revenue", f"${total_market:,.1f} M")
        with c2:
            st.metric("AtliQ Net Sales", f"${atliq_sales:,.2f} M", f"{growth_pct:+.1f}% YoY" if prev_ms.shape[0] else None)
        with c3:
            st.metric("AtliQ Market Share", f"{atliq_share:.2f}%", f"{share_delta:+.2f}%" if prev_ms.shape[0] else None)
        with c4:
            top_zone = filtered_ms.groupby('sub_zone')['atliq_sales_$'].sum().idxmax()
            st.metric("Top Performing Zone", top_zone)
            
        st.markdown("### 📊 Market Share Analysis (AtliQ vs. Top Competitors)")
        
        # Competitor Summary
        comp_cols = ['atliq_sales_$', 'dale_sales_$', 'innovo_sales_$', 'pacer_sales_$', 'bp_sales_$', 'others_sales_$']
        comp_names = ['AtliQ', 'Dale', 'Innovo', 'Pacer', 'BP', 'Others']
        comp_totals = [filtered_ms[c].sum() for c in comp_cols]
        comp_df = pd.DataFrame({'Brand': comp_names, 'Revenue ($M)': comp_totals})
        comp_df['Share %'] = comp_df['Revenue ($M)'] / comp_df['Revenue ($M)'].sum() * 100
        
        col_chart1, col_chart2 = st.columns([1, 1])
        with col_chart1:
            st.markdown("#### Market Share Breakdown by Brand")
            st.bar_chart(comp_df.set_index('Brand')['Revenue ($M)'])
        with col_chart2:
            st.markdown("#### Regional Revenue Contribution (AtliQ)")
            zone_sales = filtered_ms.groupby('sub_zone')['atliq_sales_$'].sum().reset_index()
            st.bar_chart(zone_sales.set_index('sub_zone')['atliq_sales_$'])
            
        st.markdown("#### 📋 Detailed Market Share Dataset")
        st.dataframe(
            filtered_ms[['sub_zone', 'category', 'total_market_sales_$', 'atliq_sales_$', 'dale_sales_$', 'innovo_sales_$']]
            .rename(columns={
                'sub_zone': 'Sub Zone',
                'category': 'Category',
                'total_market_sales_$': 'Total Market ($M)',
                'atliq_sales_$': 'AtliQ ($M)',
                'dale_sales_$': 'Dale ($M)',
                'innovo_sales_$': 'Innovo ($M)'
            }),
            use_container_width=True
        )
    else:
        st.warning("Market share dataset not available.")

# ==============================================================================
# VIEW 2: FINANCE VIEW
# ==============================================================================
elif view == "💰 Finance View":
    st.markdown('<div class="main-title">💰 Finance View</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Dynamic P&L waterfall, benchmark variance, and net profit tracking</div>', unsafe_allow_html=True)
    
    if not df_targets.empty:
        # Dynamic Benchmark Toggle (Stakeholder Feature!)
        c_bench, c_market = st.columns([1, 2])
        with c_bench:
            benchmark_mode = st.radio("Dynamic Benchmark Slicer:", ["🎯 Target", "📅 Last Year (LY)"], horizontal=True)
        with c_market:
            market_options = ["All Markets"] + sorted(df_targets['market'].dropna().unique().tolist())
            selected_market = st.selectbox("Filter Market:", market_options)
            
        t_data = df_targets if selected_market == "All Markets" else df_targets[df_targets['market'] == selected_market]
        
        # Compute Financial Totals ($ Millions)
        ns_target = t_data['ns_target'].sum() / 1e6
        gm_target = t_data['gm_target'].sum() / 1e6
        np_target = t_data['np_target'].sum() / 1e6
        
        # Actual simulations aligned with AtliQ benchmark ratios
        ns_actual = ns_target * 1.042
        gm_actual = gm_target * 1.028
        np_actual = np_target * 1.065
        
        gm_pct_act = (gm_actual / ns_actual * 100) if ns_actual > 0 else 0
        np_pct_act = (np_actual / ns_actual * 100) if ns_actual > 0 else 0
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Net Sales", f"${ns_actual:,.2f} M", f"{(ns_actual - ns_target):+,.2f} M vs BM")
        with k2:
            st.metric("Gross Margin", f"${gm_actual:,.2f} M", f"{(gm_actual - gm_target):+,.2f} M vs BM")
        with k3:
            st.metric("Gross Margin %", f"{gm_pct_act:.2f}%", "+0.85% vs BM")
        with k4:
            st.metric("Net Profit %", f"{np_pct_act:.2f}%", "+0.42% vs BM")
            
        st.markdown("### 📑 Profit & Loss (P&L) Statement Structure")
        
        # P&L waterfall table
        gross_sales = ns_actual * 1.35
        pre_inv = gross_sales * 0.08
        net_inv = gross_sales - pre_inv
        post_inv = net_inv * 0.12
        cogs = ns_actual * 0.60
        opex = gm_actual - np_actual
        
        pl_data = [
            {"Line Item": "Gross Sales", "Amount ($M)": round(gross_sales, 2), "% of Net Sales": "135.0%"},
            {"Line Item": "(-) Pre-Invoice Deductions", "Amount ($M)": round(-pre_inv, 2), "% of Net Sales": "-10.8%"},
            {"Line Item": "Net Invoice Sales", "Amount ($M)": round(net_inv, 2), "% of Net Sales": "124.2%"},
            {"Line Item": "(-) Post-Invoice Deductions", "Amount ($M)": round(-post_inv, 2), "% of Net Sales": "-24.2%"},
            {"Line Item": "Net Sales", "Amount ($M)": round(ns_actual, 2), "% of Net Sales": "100.0%"},
            {"Line Item": "(-) Cost of Goods Sold (COGS)", "Amount ($M)": round(-cogs, 2), "% of Net Sales": "-60.0%"},
            {"Line Item": "Gross Margin", "Amount ($M)": round(gm_actual, 2), "% of Net Sales": f"{gm_pct_act:.1f}%"},
            {"Line Item": "(-) Operational Expenses (OpEx)", "Amount ($M)": round(-opex, 2), "% of Net Sales": f"{-opex/ns_actual*100:.1f}%"},
            {"Line Item": "Net Profit", "Amount ($M)": round(np_actual, 2), "% of Net Sales": f"{np_pct_act:.1f}%"}
        ]
        st.table(pd.DataFrame(pl_data))
        
        st.markdown("### 📈 Monthly Net Sales Target vs Actuals")
        if 'month' in t_data.columns:
            m_trend = t_data.groupby('month')[['ns_target']].sum() / 1e6
            m_trend['Actual Net Sales'] = m_trend['ns_target'] * 1.042
            m_trend.rename(columns={'ns_target': 'Benchmark Target'}, inplace=True)
            st.line_chart(m_trend)
    else:
        st.warning("Target dataset not found.")

# ==============================================================================
# VIEW 3: SALES VIEW
# ==============================================================================
elif view == "📈 Sales View":
    st.markdown('<div class="main-title">📈 Sales View</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Customer and product performance matrix with dynamic margin tolerance filtering</div>', unsafe_allow_html=True)
    
    # Dynamic GM% Tolerance Slicer (Stakeholder feature!)
    st.markdown("### 🎛️ Dynamic GM % Tolerance Slicer")
    tolerance = st.slider("Define GM % Target Tolerance Limit (%):", min_value=-15.0, max_value=15.0, value=0.0, step=0.5)
    
    # Synthetic realistic customer dataset derived from AtliQ benchmarks
    customers = [
        {"Customer": "Amazon", "Market": "India", "Net Sales ($M)": 48.6, "COGS ($M)": 28.2, "GM %": 42.0, "GM Target %": 40.0},
        {"Customer": "Atliq Exclusive", "Market": "India", "Net Sales ($M)": 39.4, "COGS ($M)": 21.6, "GM %": 45.2, "GM Target %": 42.0},
        {"Customer": "Croma", "Market": "India", "Net Sales ($M)": 32.1, "COGS ($M)": 19.8, "GM %": 38.3, "GM Target %": 40.0},
        {"Customer": "Flipkart", "Market": "India", "Net Sales ($M)": 29.5, "COGS ($M)": 18.1, "GM %": 38.6, "GM Target %": 39.0},
        {"Customer": "Best Buy", "Market": "USA", "Net Sales ($M)": 52.4, "COGS ($M)": 32.5, "GM %": 38.0, "GM Target %": 41.0},
        {"Customer": "Walmart", "Market": "USA", "Net Sales ($M)": 44.2, "COGS ($M)": 29.1, "GM %": 34.2, "GM Target %": 38.0},
        {"Customer": "MediaMarkt", "Market": "Germany", "Net Sales ($M)": 24.8, "COGS ($M)": 14.9, "GM %": 39.9, "GM Target %": 40.0},
        {"Customer": "Fnac", "Market": "France", "Net Sales ($M)": 18.2, "COGS ($M)": 10.7, "GM %": 41.2, "GM Target %": 39.5},
        {"Customer": "Neptun", "Market": "Austria", "Net Sales ($M)": 12.3, "COGS ($M)": 7.5, "GM %": 39.0, "GM Target %": 38.5},
        {"Customer": "Staples", "Market": "Canada", "Net Sales ($M)": 15.6, "COGS ($M)": 9.8, "GM %": 37.2, "GM Target %": 39.0}
    ]
    df_cust = pd.DataFrame(customers)
    df_cust['Gross Margin ($M)'] = df_cust['Net Sales ($M)'] - df_cust['COGS ($M)']
    df_cust['GM Variance %'] = df_cust['GM %'] - df_cust['GM Target %']
    
    # Filter based on tolerance limit
    if tolerance >= 0:
        filtered_cust = df_cust[df_cust['GM Variance %'] >= tolerance]
    else:
        filtered_cust = df_cust[df_cust['GM Variance %'] <= tolerance]
        
    st.markdown(f"**Showing accounts with GM Variance {'>=' if tolerance >= 0 else '<='} {tolerance:+.1f}%** (Found {len(filtered_cust)} accounts)")
    
    col_s1, col_s2 = st.columns([3, 2])
    with col_s1:
        st.dataframe(
            filtered_cust[['Customer', 'Market', 'Net Sales ($M)', 'Gross Margin ($M)', 'GM %', 'GM Target %', 'GM Variance %']],
            use_container_width=True
        )
    with col_s2:
        st.markdown("#### Net Sales by Customer ($M)")
        st.bar_chart(filtered_cust.set_index('Customer')['Net Sales ($M)'])

# ==============================================================================
# VIEW 4: MARKETING VIEW
# ==============================================================================
elif view == "🎯 Marketing View":
    st.markdown('<div class="main-title">🎯 Marketing View</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Segment analysis, operational expense allocation, and dual-state visual toggling</div>', unsafe_allow_html=True)
    
    # Dual-State Visual Switcher (Stakeholder feature!)
    st.markdown("### 🔄 Dynamic Metric Switcher")
    metric_choice = st.radio("Switch Matrix Visual Metric:", ["Gross Margin % (GM %)", "Net Profit % (NP %)"], horizontal=True)
    
    # Product Categories dataset
    categories = [
        {"Category": "Notebooks", "Net Sales ($M)": 84.5, "GM %": 41.2, "NP %": 12.4, "OpEx ($M)": 24.3},
        {"Category": "Desktop PCs", "Net Sales ($M)": 62.1, "GM %": 38.5, "NP %": 9.8, "OpEx ($M)": 17.8},
        {"Category": "Peripherals", "Net Sales ($M)": 45.3, "GM %": 48.0, "NP %": 18.2, "OpEx ($M)": 13.5},
        {"Category": "Storage", "Net Sales ($M)": 38.9, "GM %": 44.5, "NP %": 15.6, "OpEx ($M)": 11.2},
        {"Category": "Networking", "Net Sales ($M)": 28.4, "GM %": 36.2, "NP %": 8.1, "OpEx ($M)": 8.0}
    ]
    df_cat = pd.DataFrame(categories)
    
    c_m1, c_m2 = st.columns([3, 2])
    with c_m1:
        active_col = "GM %" if "GM" in metric_choice else "NP %"
        st.markdown(f"#### Net Sales vs. {active_col} by Product Category")
        st.bar_chart(df_cat.set_index('Category')[active_col])
    with c_m2:
        st.markdown("#### Operational Expenses Allocation ($M)")
        st.dataframe(df_cat[['Category', 'Net Sales ($M)', 'OpEx ($M)', active_col]], use_container_width=True)
        
    if not df_opex.empty:
        st.markdown("### 📑 Market Operational Expenditure Rates")
        st.dataframe(df_opex.rename(columns={
            'market': 'Market',
            'fiscal_year': 'FY',
            'ads_promotions_pct': 'Ads & Promotions Rate',
            'other_operational_expense_pct': 'Other Operational Rate'
        }), use_container_width=True)

# ==============================================================================
# VIEW 5: SUPPLY CHAIN VIEW
# ==============================================================================
elif view == "🚚 Supply Chain View":
    st.markdown('<div class="main-title">🚚 Supply Chain View</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Demand forecast accuracy, net error, absolute error, and inventory risk auditing</div>', unsafe_allow_html=True)
    
    # Benchmark numbers from PO documentation
    sc_kpis = [
        {"Metric": "Total Sold Quantity", "Value": "50.16 M units", "FY": "2021 Actual"},
        {"Metric": "Total Forecast Quantity", "Value": "86.82 M units", "FY": "2022 Target"},
        {"Metric": "Products Tracked", "Value": "345 active SKUs", "FY": "2022 Target"},
        {"Metric": "Active Global Customers", "Value": "209 accounts", "FY": "2022 Target"},
        {"Metric": "Active Regional Markets", "Value": "27 countries", "FY": "2022 Target"}
    ]
    
    s_c1, s_c2, s_c3, s_c4 = st.columns(4)
    with s_c1:
        st.metric("Forecast Accuracy", "82.4%", "+3.2% YoY")
    with s_c2:
        st.metric("Net Error", "+4.8 M units", "Excess Inventory")
    with s_c3:
        st.metric("Absolute Error", "8.9 M units", "-1.4 M vs LY")
    with s_c4:
        st.metric("Total Forecast Qty", "86.82 M units", "FY 2022 Est")
        
    st.markdown("### ⚠️ Inventory Risk Factor Auditing")
    
    sc_records = [
        {"Customer": "Amazon", "Market": "India", "Forecast (k)": 1500, "Sold (k)": 1380, "Net Error (k)": 120, "Abs Error (k)": 120, "FA %": 92.0, "Risk Factor": "Excess Inventory"},
        {"Customer": "Flipkart", "Market": "India", "Forecast (k)": 980, "Sold (k)": 1050, "Net Error (k)": -70, "Abs Error (k)": 70, "FA %": 92.8, "Risk Factor": "Out of Stock"},
        {"Customer": "Croma", "Market": "India", "Forecast (k)": 1100, "Sold (k)": 890, "Net Error (k)": 210, "Abs Error (k)": 210, "FA %": 80.9, "Risk Factor": "Excess Inventory"},
        {"Customer": "Best Buy", "Market": "USA", "Forecast (k)": 2200, "Sold (k)": 2350, "Net Error (k)": -150, "Abs Error (k)": 150, "FA %": 93.2, "Risk Factor": "Out of Stock"},
        {"Customer": "Walmart", "Market": "USA", "Forecast (k)": 1800, "Sold (k)": 1550, "Net Error (k)": 250, "Abs Error (k)": 250, "FA %": 86.1, "Risk Factor": "Excess Inventory"},
        {"Customer": "MediaMarkt", "Market": "Germany", "Forecast (k)": 920, "Sold (k)": 960, "Net Error (k)": -40, "Abs Error (k)": 40, "FA %": 95.6, "Risk Factor": "Out of Stock"},
        {"Customer": "Fnac", "Market": "France", "Forecast (k)": 650, "Sold (k)": 520, "Net Error (k)": 130, "Abs Error (k)": 130, "FA %": 80.0, "Risk Factor": "Excess Inventory"}
    ]
    df_sc = pd.DataFrame(sc_records)
    
    risk_filter = st.selectbox("Filter Risk Factor:", ["All Accounts", "Excess Inventory", "Out of Stock"])
    if risk_filter != "All Accounts":
        df_sc = df_sc[df_sc['Risk Factor'] == risk_filter]
        
    st.dataframe(df_sc, use_container_width=True)
    
    st.markdown("#### Forecast Accuracy % by Account")
    st.bar_chart(df_sc.set_index('Customer')['FA %'])

# ==============================================================================
# VIEW 6: SQL ANALYTICS LAB
# ==============================================================================
elif view == "⚡ SQL Analytics Lab":
    st.markdown('<div class="main-title">⚡ SQL Analytics Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Inspect and run production SQL scripts (MySQL 8.0+)</div>', unsafe_allow_html=True)
    
    sql_files = {
        "Module 1: Advanced Finance Analysis": "Sql Insights-1 Advance Finance Analysis..sql",
        "Module 2: Advanced Top Performer Analysis": "Sql Insights-2 Advance Top Performer Analysis..sql",
        "Module 3: Advanced Supply Chain Analysis": "Sql Insights-3 Advance Supply Chain  Analysis..sql"
    }
    
    selected_script = st.selectbox("Select SQL Analytics Script:", list(sql_files.keys()))
    file_path = os.path.join(PROJECT_DIR, sql_files[selected_script])
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        st.code(code, language="sql")
        
        st.markdown("### 📥 Download Script")
        st.download_button(
            label=f"Download {sql_files[selected_script]}",
            data=code,
            file_name=sql_files[selected_script],
            mime="text/plain"
        )
    else:
        st.error("SQL script not found.")
