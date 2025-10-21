import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Page configuration
st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize connection
#@st.cache_resource
def connect_to_google_sheets():
    """Connect to Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(
            "/Users/thekhemfee/Downloads/service_account.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# Load data
#@st.cache_data(ttl=300)
def load_data():
    """Load data from Google Sheets"""
    try:
        client = connect_to_google_sheets()
        if not client:
            return None
        
        sheet = client.open_by_key("1wM7DTHizhg_A3h0qV3EhX4os4hk46uolW-ESQSJkgZs")
        
        # Load main data
        worksheet = sheet.worksheet("Sheet2")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Data cleaning and preprocessing
        if not df.empty:
            # Convert amount columns to numeric
            
            # Convert date columns
            date_columns = ['VALUE DATE', 'Date', 'MATUR_DATE']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Initialize session state for navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'monthly'
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = None
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = None

def clean_numeric_column(series):
    """Clean and convert numeric columns with mixed data types"""
    if series.dtype == 'object':
        # Remove currency symbols, commas, and other non-numeric characters
        cleaned = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
        # Convert to numeric, setting errors to NaN
        return pd.to_numeric(cleaned, errors='coerce')
    return series
# Main dashboard
def main():
    st.title("🏦 Performance Dashboard")
    st.markdown("---")
    
    # Load data
    df = load_data()
    
    if df is None or df.empty:
        st.error("No data loaded. Please check your connection.")
        return
# Clean numeric columns
    numeric_columns = ['AMOUNT IN USD', 'OUTSTANDING', 'INTEREST RATE']
    for col in numeric_columns:
      if col in df.columns:
        st.sidebar.info(f"🔄 Cleaning column: {col}")
        before_sample = df[col].iloc[0] if len(df) > 0 else "N/A"
        df[col] = clean_numeric_column(df[col])
        after_sample = df[col].iloc[0] if len(df) > 0 else "N/A"
        st.sidebar.write(f"   Before: {before_sample} → After: {after_sample}")
            
    # Data preprocessing
    df['MONTH'] = pd.to_datetime(df['Date']).dt.strftime('%B %Y')
    df['Quarter'] = df['Quarter'].fillna('Unknown')
    df['Branch/Outlet'] = df['Branch/Outlet'].fillna('Unknown')
    df['RM Name'] = df['RM Name'].fillna('Unknown')
    
    # Sidebar filters
    st.sidebar.title("Filters")
    
    # Quarter filter
    quarters = sorted(df['Quarter'].unique())
    selected_quarter = st.sidebar.selectbox("Select Quarter", quarters)
    
    # Product type filter
    product_types = ['All'] + sorted(df['PRODUCT_TYPE'].dropna().unique().tolist())
    selected_product = st.sidebar.selectbox("Select Product Type", product_types)
    
    # Apply filters
    filtered_df = df[df['Quarter'] == selected_quarter]
    if selected_product != 'All':
        filtered_df = filtered_df[filtered_df['PRODUCT_TYPE'] == selected_product]
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 Monthly Overview", use_container_width=True):
            st.session_state.current_view = 'monthly'
            st.session_state.selected_month = None
            st.session_state.selected_branch = None
    with col2:
        if st.button("🏢 Branch Performance", use_container_width=True):
            if st.session_state.selected_month:
                st.session_state.current_view = 'branch'
    with col3:
        if st.button("👤 RM Performance", use_container_width=True):
            if st.session_state.selected_branch:
                st.session_state.current_view = 'rm'
    
    st.markdown("---")
    
    # View routing
    if st.session_state.current_view == 'monthly':
        show_monthly_overview(filtered_df)
    elif st.session_state.current_view == 'branch':
        show_branch_performance(filtered_df, st.session_state.selected_month)
    elif st.session_state.current_view == 'rm':
        show_rm_performance(filtered_df, st.session_state.selected_branch)

def show_monthly_overview(df):
    st.header("📅 Monthly Performance Overview")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_loans = len(df)
    total_amount = df['AMOUNT IN USD'].sum()
    avg_loan_size = df['AMOUNT IN USD'].mean()
    unique_branches = df['Branch/Outlet'].nunique()
    
    with col1:
        st.metric("Total Loans", f"{total_loans:,}")
    with col2:
        st.metric("Total Amount", f"${total_amount:,.2f}")
    with col3:
        st.metric("Avg Loan Size", f"${avg_loan_size:,.2f}")
    with col4:
        st.metric("Active Branches", unique_branches)
    
    # Monthly trends
    monthly_data = df.groupby('MONTH').agg({
        'AMOUNT IN USD': ['sum', 'count'],
        'OUTSTANDING': 'sum',
        'RM Name': 'nunique'
    }).round(2)
    
    monthly_data.columns = ['Total Amount', 'Loan Count', 'Total Outstanding', 'Unique RMs']
    monthly_data = monthly_data.reset_index()
    
    # Create tabs for different charts
    tab1, tab2, tab3 = st.tabs(["Amount Trends", "Loan Count", "Product Analysis"])
    
    with tab1:
        # Amount by month
        fig_amount = px.bar(
            monthly_data, 
            x='MONTH', 
            y='Total Amount',
            title="Total Loan Amount by Month",
            color='Total Amount',
            color_continuous_scale='viridis'
        )
        fig_amount.update_layout(xaxis_title="Month", yaxis_title="Total Amount (USD)")
        st.plotly_chart(fig_amount, use_container_width=True)
        
        # Make bars clickable
        if st.button("📊 Click on bars to view branch performance"):
            st.info("Click on any bar in the chart above to drill down into branch performance for that month")
    
    with tab2:
        # Loan count by month
        fig_count = px.line(
            monthly_data,
            x='MONTH',
            y='Loan Count',
            title="Loan Count by Month",
            markers=True
        )
        fig_count.update_traces(line=dict(width=4))
        st.plotly_chart(fig_count, use_container_width=True)
    
    with tab3:
        # Product type distribution
        product_data = df.groupby('PRODUCT_TYPE')['AMOUNT IN USD'].sum().reset_index()
        fig_product = px.pie(
            product_data,
            values='AMOUNT IN USD',
            names='PRODUCT_TYPE',
            title="Loan Amount by Product Type"
        )
        st.plotly_chart(fig_product, use_container_width=True)
    
    # Interactive monthly table
    st.subheader("Monthly Summary Table")
    display_monthly = monthly_data.copy()
    display_monthly['Total Amount'] = display_monthly['Total Amount'].apply(lambda x: f"${x:,.2f}")
    display_monthly['Total Outstanding'] = display_monthly['Total Outstanding'].apply(lambda x: f"${x:,.2f}")
    
    # Add clickable functionality
    for idx, row in display_monthly.iterrows():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
        with col1:
            st.write(f"**{row['MONTH']}**")
        with col2:
            st.write(f"Amount: {row['Total Amount']}")
        with col3:
            st.write(f"Loans: {row['Loan Count']}")
        with col4:
            st.write(f"Outstanding: {row['Total Outstanding']}")
        with col5:
            if st.button("View Branches", key=f"month_{idx}"):
                st.session_state.current_view = 'branch'
                st.session_state.selected_month = row['MONTH']
                st.rerun()

def show_branch_performance(df, selected_month):
    st.header(f"🏢 Branch Performance - {selected_month}")
    
    # Filter data for selected month
    month_df = df[df['MONTH'] == selected_month]
    
    # Back button
    if st.button("← Back to Monthly Overview"):
        st.session_state.current_view = 'monthly'
        st.session_state.selected_month = None
        st.rerun()
    
    # Branch KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    branch_loans = len(month_df)
    branch_amount = month_df['AMOUNT IN USD'].sum()
    branch_outstanding = month_df['OUTSTANDING'].sum()
    unique_rms = month_df['RM Name'].nunique()
    
    with col1:
        st.metric("Branch Loans", branch_loans)
    with col2:
        st.metric("Total Amount", f"${branch_amount:,.2f}")
    with col3:
        st.metric("Total Outstanding", f"${branch_outstanding:,.2f}")
    with col4:
        st.metric("Active RMs", unique_rms)
    
    # Branch performance
    branch_data = month_df.groupby('Branch/Outlet').agg({
        'AMOUNT IN USD': ['sum', 'count'],
        'OUTSTANDING': 'sum',
        'RM Name': 'nunique',
        'INTEREST RATE': 'mean'
    }).round(2)
    
    branch_data.columns = ['Total Amount', 'Loan Count', 'Total Outstanding', 'RM Count', 'Avg Interest Rate']
    branch_data = branch_data.reset_index()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_branch_amount = px.bar(
            branch_data,
            x='Branch/Outlet',
            y='Total Amount',
            title=f"Loan Amount by Branch - {selected_month}",
            color='Total Amount'
        )
        st.plotly_chart(fig_branch_amount, use_container_width=True)
    
    with col2:
        fig_branch_count = px.pie(
            branch_data,
            values='Loan Count',
            names='Branch/Outlet',
            title=f"Loan Distribution by Branch - {selected_month}"
        )
        st.plotly_chart(fig_branch_count, use_container_width=True)
    
    # Interactive branch table
    st.subheader("Branch Performance Details")
    
    for idx, row in branch_data.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 2])
        with col1:
            st.write(f"**{row['Branch/Outlet']}**")
        with col2:
            st.write(f"Amount: ${row['Total Amount']:,.2f}")
        with col3:
            st.write(f"Loans: {row['Loan Count']}")
        with col4:
            st.write(f"Outstanding: ${row['Total Outstanding']:,.2f}")
        with col5:
            st.write(f"RMs: {row['RM Count']}")
        with col6:
            if st.button("View RMs", key=f"branch_{idx}"):
                st.session_state.current_view = 'rm'
                st.session_state.selected_branch = row['Branch/Outlet']
                st.rerun()

def show_rm_performance(df, selected_branch):
    st.header(f"👤 RM Performance - {selected_branch}")
    
    # Filter data for selected branch
    branch_df = df[df['Branch/Outlet'] == selected_branch]
    
    # Back button
    if st.button("← Back to Branch Performance"):
        st.session_state.current_view = 'branch'
        st.session_state.selected_branch = None
        st.rerun()
    
    # RM performance data
    rm_data = branch_df.groupby('RM Name').agg({
        'AMOUNT IN USD': ['sum', 'count', 'mean'],
        'OUTSTANDING': 'sum',
        'INTEREST RATE': 'mean',
        'PRODUCT_TYPE': lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A'
    }).round(2)
    
    rm_data.columns = ['Total Amount', 'Loan Count', 'Avg Loan Size', 'Total Outstanding', 'Avg Interest Rate', 'Top Product']
    rm_data = rm_data.reset_index()
    
    # RM KPIs
    top_rm = rm_data.loc[rm_data['Total Amount'].idxmax()]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Top RM", top_rm['RM Name'])
    with col2:
        st.metric("Top RM Amount", f"${top_rm['Total Amount']:,.2f}")
    with col3:
        st.metric("Total RMs", len(rm_data))
    with col4:
        st.metric("Branch Total", f"${rm_data['Total Amount'].sum():,.2f}")
    
    # RM performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_rm_amount = px.bar(
            rm_data,
            x='RM Name',
            y='Total Amount',
            title=f"Loan Amount by RM - {selected_branch}",
            color='Total Amount',
            color_continuous_scale='thermal'
        )
        st.plotly_chart(fig_rm_amount, use_container_width=True)
    
    with col2:
        fig_rm_loans = px.scatter(
            rm_data,
            x='Loan Count',
            y='Avg Loan Size',
            size='Total Amount',
            color='RM Name',
            title="RM Performance: Volume vs Size",
            hover_data=['Top Product']
        )
        st.plotly_chart(fig_rm_loans, use_container_width=True)
    
    # Detailed RM table
    st.subheader("RM Performance Details")
    
    # Format the data for display
    display_rm = rm_data.copy()
    display_rm['Total Amount'] = display_rm['Total Amount'].apply(lambda x: f"${x:,.2f}")
    display_rm['Avg Loan Size'] = display_rm['Avg Loan Size'].apply(lambda x: f"${x:,.2f}")
    display_rm['Total Outstanding'] = display_rm['Total Outstanding'].apply(lambda x: f"${x:,.2f}")
    display_rm['Avg Interest Rate'] = display_rm['Avg Interest Rate'].apply(lambda x: f"{x}%")
    
    st.dataframe(
        display_rm,
        column_config={
            "RM Name": "Relationship Manager",
            "Total Amount": "Total Amount",
            "Loan Count": "Loan Count",
            "Avg Loan Size": "Avg Loan Size",
            "Total Outstanding": "Outstanding",
            "Avg Interest Rate": "Avg Rate",
            "Top Product": "Top Product"
        },
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()