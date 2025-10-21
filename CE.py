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
    """Connect to Google Sheets using Streamlit secrets"""
    try:
        # Get service account info from Streamlit secrets
        service_account_info = {
            "type": st.secrets["gcp"]["type"],
            "project_id": st.secrets["gcp"]["project_id"],
            "private_key_id": st.secrets["gcp"]["private_key_id"],
            "private_key": st.secrets["gcp"]["private_key"],
            "client_email": st.secrets["gcp"]["client_email"],
            "client_id": st.secrets["gcp"]["client_id"],
            "auth_uri": st.secrets["gcp"]["auth_uri"],
            "token_uri": st.secrets["gcp"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp"]["client_x509_cert_url"]
        }
        
        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# Load data
@st.cache_data(ttl=3600)
def load_data():
    """Load data from Google Sheets"""
    try:
        client = connect_to_google_sheets()
        if not client:
            return None
        
        sheet_id = st.secrets["sheets"]["sheet_id"]
        sheet = client.open_by_key(sheet_id)
        #sheet = client.open_by_key("1wM7DTHizhg_A3h0qV3EhX4os4hk46uolW-ESQSJkgZs")
        
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


# Mobile CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Compact metrics */
        .stMetric {
            padding: 0.5rem !important;
        }
        
        /* Better touch targets */
        .stButton button {
            min-height: 44px;
            font-size: 16px; /* Prevents zoom on iOS */
        }
        
        /* Compact cards */
        .mobile-card {
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    }
    
    /* Always show these styles */
    .compact-metric {
        text-align: center;
        padding: 0.8rem;
    }
    
    .nav-button {
        width: 100%;
        margin: 0.2rem 0;
        border-radius: 12px;
    }
    
    .performance-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Mobile header with quick stats
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏦 Loan Performance")
    with col2:
        st.metric("Loans", "156", "+12%")
    
    # Navigation pills
    st.markdown("---")
    
    # Navigation state
    if 'view' not in st.session_state:
        st.session_state.view = 'overview'
    
    # Navigation buttons
    nav_cols = st.columns(4)
    with nav_cols[0]:
        if st.button("📊", help="Overview", use_container_width=True, key="nav_overview"):
            st.session_state.view = 'overview'
    with nav_cols[1]:
        if st.button("🏢", help="Branches", use_container_width=True, key="nav_branches"):
            st.session_state.view = 'branches'
    with nav_cols[2]:
        if st.button("👤", help="RMs", use_container_width=True, key="nav_rms"):
            st.session_state.view = 'rms'
    with nav_cols[3]:
        if st.button("⚙️", help="Settings", use_container_width=True, key="nav_settings"):
            st.session_state.view = 'settings'
    
    st.markdown("---")
    
    # View routing
    if st.session_state.view == 'overview':
        show_mobile_overview()
    elif st.session_state.view == 'branches':
        show_mobile_branches()
    elif st.session_state.view == 'rms':
        show_mobile_rms()
    elif st.session_state.view == 'settings':
        show_mobile_settings()

def show_mobile_overview():
    """Mobile-optimized overview"""
    
    # Quick KPI cards
    st.subheader("📈 Quick Stats")
    
    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        with st.container():
            st.metric("Total Amount", "$4.2M", "+8%")
            st.metric("Active Loans", "156", "+12")
    
    with kpi_cols[1]:
        with st.container():
            st.metric("Avg. Loan Size", "$26.9K", "+3%")
            st.metric("Completion", "84%", "+5%")
    
    # Performance chart
    st.subheader("📊 Monthly Performance")
    
    # Sample data - replace with your actual data
    monthly_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        'Amount': [3.8, 4.1, 3.9, 4.2, 4.5],
        'Loans': [142, 148, 145, 152, 156]
    })
    
    fig = px.bar(monthly_data, x='Month', y='Amount', 
                 title="Loan Amount by Month")
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("🔔 Recent Activity")
    
    activities = [
        {"icon": "✅", "text": "Loan #2456 approved", "time": "2h ago"},
        {"icon": "👤", "text": "New RM onboarded", "time": "1d ago"},
        {"icon": "🏢", "text": "Branch BTK exceeded target", "time": "1d ago"},
        {"icon": "📈", "text": "Monthly growth +8%", "time": "2d ago"}
    ]
    
    for activity in activities:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(activity["icon"])
        with col2:
            st.write(f"**{activity['text']}**")
            st.caption(activity["time"])
        st.divider()

def show_mobile_branches():
    """Mobile-optimized branch view"""
    
    st.subheader("🏢 Branch Performance")
    
    # Branch ranking
    branches_data = [
        {"name": "SRB", "amount": "$1.2M", "growth": "+15%", "loans": "45"},
        {"name": "BTK", "amount": "$980K", "growth": "+22%", "loans": "38"},
        {"name": "NRD", "amount": "$850K", "growth": "+8%", "loans": "32"},
        {"name": "TLK", "amount": "$720K", "growth": "+5%", "loans": "28"},
        {"name": "Other", "amount": "$450K", "growth": "+3%", "loans": "13"}
    ]
    
    for i, branch in enumerate(branches_data):
        with st.expander(f"🏢 {branch['name']} - {branch['amount']} ({branch['growth']})", expanded=i==0):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Amount", branch["amount"])
            with col2:
                st.metric("Growth", branch["growth"])
            with col3:
                st.metric("Loans", branch["loans"])
            
            if st.button(f"View RMs in {branch['name']}", key=f"branch_{i}", use_container_width=True):
                st.session_state.selected_branch = branch['name']
                st.session_state.view = 'rms'
                st.rerun()

def show_mobile_rms():
    """Mobile-optimized RM view"""
    
    st.subheader("👤 Relationship Managers")
    
    # Search and filter
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search = st.text_input("Search RMs", placeholder="Type name...")
    with filter_col:
        filter_opt = st.selectbox("Filter", ["All", "Top", "Active"])
    
    # RM cards
    rms_data = [
        {"name": "HENG Leangmey", "branch": "SRB", "amount": "$450K", "loans": "18", "growth": "+25%"},
        {"name": "PEN Samnang", "branch": "NRD", "amount": "$380K", "loans": "15", "growth": "+18%"},
        {"name": "BUN Ammatak", "branch": "BTK", "amount": "$320K", "loans": "12", "growth": "+12%"},
        {"name": "NHIM Heang", "branch": "TLK", "amount": "$290K", "loans": "11", "growth": "+8%"},
        {"name": "LUN Phally", "branch": "SRB", "amount": "$270K", "loans": "10", "growth": "+15%"}
    ]
    
    for rm in rms_data:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{rm['name']}**")
                st.caption(f"🏢 {rm['branch']} | 📊 {rm['loans']} loans")
            with col2:
                st.metric("Amount", rm["amount"], rm["growth"])
            
            # Progress bar for performance
            progress_val = min(100, int(rm['amount'].replace('$', '').replace('K', '')) / 5)
            st.progress(progress_val / 100, text=f"Performance: {progress_val}%")
            
            st.divider()

def show_mobile_settings():
    """Mobile-optimized settings"""
    
    st.subheader("⚙️ Settings")
    
    # Date range
    st.write("**📅 Date Range**")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", datetime(2024, 1, 1))
    with col2:
        end_date = st.date_input("To", datetime.today())
    
    # Notifications
    st.write("**🔔 Notifications**")
    notif_col1, notif_col2 = st.columns(2)
    with notif_col1:
        st.checkbox("Performance alerts", True)
        st.checkbox("New loans", True)
    with notif_col2:
        st.checkbox("Target updates", False)
        st.checkbox("Weekly reports", True)
    
    # Actions
    st.write("**🛠️ Actions**")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.success("Data refreshed!")
    
    if st.button("📧 Export Report", use_container_width=True):
        st.info("Report generation started...")
    
    if st.button("🎯 Set Targets", use_container_width=True):
        st.session_state.view = 'overview'
        st.rerun()

# Sample data generator (replace with your actual data loading)
def load_sample_data():
    return pd.DataFrame({
        'Month': ['January', 'February', 'March', 'April', 'May'],
        'Amount': [3800000, 4100000, 3900000, 4200000, 4500000],
        'Loans': [142, 148, 145, 152, 156]
    })

if __name__ == "__main__":
    main()
