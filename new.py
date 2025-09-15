# new.py - BudgetBee with Moonstone & Dark Denim Theme
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import tempfile
import os

# --- Moonstone & Dark Denim Color Theme ---
PRIMARY_COLOR = "#4A6572"  # Dark Denim
SECONDARY_COLOR = "#B0BEC5"  # Moonstone
BACKGROUND_COLOR = "#263238"
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#FF8A65"

# Apply custom CSS
st.markdown(f"""
<style>
    .main {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {SECONDARY_COLOR};
        color: {BACKGROUND_COLOR};
    }}
    .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {{
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
        border-radius: 6px;
    }}
    .stDataFrame {{
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
    }}
    .metric-card {{
        background-color: {PRIMARY_COLOR};
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid {ACCENT_COLOR};
    }}
    .success-message {{
        background-color: #2E7D32;
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }}
    .warning-message {{
        background-color: #FF8A65;
        color: {BACKGROUND_COLOR};
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }}
    .info-message {{
        background-color: {SECONDARY_COLOR};
        color: {BACKGROUND_COLOR};
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }}
</style>
""", unsafe_allow_html=True)

# --- Check for OCR dependencies ---
OCR_AVAILABLE = False  # Force disable for cloud deployment
OCR_ENABLED = False   # Control variable

# -------------------------------
# 2. ANALYTICS ENGINE
# -------------------------------
def categorize_expense(description):
    """Categorize expenses based on description."""
    if not description:
        return 'Other'
        
    description_lower = description.lower()
    categories = {
        'Food': ['coffee', 'mcdonald', 'kfc', 'restaurant', 'food', 'grocery', 'supermarket', 'cafe'],
        'Transport': ['shell', 'gas', 'petrol', 'metro', 'bus', 'uber', 'transport', 'fuel', 'taxi'],
        'Entertainment': ['cine', 'movie', 'netflix', 'entertain', 'concert', 'game'],
        'Utilities': ['rent', 'electric', 'water', 'internet', 'bill', 'wifi'],
        'Shopping': ['mall', 'clothes', 'amazon', 'store', 'shop']
    }
    
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    return 'Other'

def load_data():
    """Load expense data from CSV."""
    try:
        return pd.read_csv('expenses.csv', parse_dates=['Date'])
    except FileNotFoundError:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Category'])

def save_data(df):
    """Save DataFrame to CSV."""
    df.to_csv('expenses.csv', index=False)

# -------------------------------
# 3. THE HUB (Streamlit UI)
# -------------------------------
# Initialize session state
if 'df_expenses' not in st.session_state:
    st.session_state.df_expenses = load_data()

# Page Config
st.set_page_config(page_title="BudgetBee - Premium Tracker", layout="wide", page_icon="🐝")

# Sidebar Navigation
st.sidebar.markdown(f"<h1 style='color: {ACCENT_COLOR};'>BudgetBee 🐝</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='color: {SECONDARY_COLOR};'>The Complete ETHOS Stack Expense Tracker</p>", unsafe_allow_html=True)

# OCR Status in Sidebar
if not OCR_AVAILABLE:
    st.sidebar.markdown(f"""
    <div class='warning-message'>
        ⚠️ OCR Disabled<br>
        <small>Receipt scanning requires local installation</small>
    </div>
    """, unsafe_allow_html=True)

page = st.sidebar.radio("Navigate", ["📊 Dashboard", "💸 Add Expense", "📷 Receipt Scanner", "⚙️ Manage Expenses"])

# Dashboard Page
if page == "📊 Dashboard":
    st.header("📊 Financial Dashboard")
    
    if not st.session_state.df_expenses.empty:
        # Metrics Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <h3>Total Expenses</h3>
                <h2>${st.session_state.df_expenses['Amount'].sum():.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <h3>Total Transactions</h3>
                <h2>{len(st.session_state.df_expenses)}</h2>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            avg_expense = st.session_state.df_expenses['Amount'].mean()
            st.markdown(f"""
            <div class='metric-card'>
                <h3>Average Expense</h3>
                <h2>${avg_expense:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)

        # Expenses Table
        st.subheader("💰 Expense History")
        st.dataframe(st.session_state.df_expenses.style.format({'Amount': '${:.2f}'}), use_container_width=True)

        # Spending by Category Chart
        st.subheader("📈 Spending by Category")
        category_totals = st.session_state.df_expenses.groupby('Category')['Amount'].sum()
        st.bar_chart(category_totals)

    else:
        st.info("No expenses recorded yet. Add some via 'Add Expense'!")

# Add Expense Page
elif page == "💸 Add Expense":
    st.header("💸 Add New Expense")
    
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 Date", datetime.today())
            amount = st.number_input("💵 Amount ($)", min_value=0.0, step=1.0, format="%.2f")
        with col2:
            desc = st.text_input("📝 Description")
            category = st.selectbox("🏷️ Category", ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Other"])
        
        submitted = st.form_submit_button("💾 Save Expense")
        
        if submitted:
            if desc and amount > 0:
                new_row = pd.DataFrame([[date, desc, amount, category]], 
                                      columns=['Date', 'Description', 'Amount', 'Category'])
                st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_row], ignore_index=True)
                save_data(st.session_state.df_expenses)
                st.markdown(f"""
                <div class='success-message'>
                    ✅ Expense added successfully! ${amount:.2f} for {desc}
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Please fill in description and amount.")

# Receipt Scanner Page
elif page == "📷 Receipt Scanner":
    st.header("📷 Receipt Scanner")
    
    if not OCR_AVAILABLE:
        st.markdown(f"""
        <div class='info-message'>
            <h3>📋 Manual Receipt Entry</h3>
            <p>OCR feature is disabled for cloud deployment. You can manually enter receipt details below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Manual receipt entry form
        with st.form("manual_receipt_form"):
            st.subheader("📝 Enter Receipt Details Manually")
            
            col1, col2 = st.columns(2)
            with col1:
                receipt_date = st.date_input("Receipt Date", datetime.today())
                receipt_vendor = st.text_input("Store/Vendor Name")
            with col2:
                receipt_total = st.number_input("Total Amount ($)", min_value=0.0, step=1.0, format="%.2f")
                receipt_category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Other"])
            
            receipt_description = st.text_input("Description (optional)", value="Receipt purchase")
            
            if st.form_submit_button("💾 Add Receipt Expense"):
                if receipt_total > 0:
                    vendor_text = f" at {receipt_vendor}" if receipt_vendor else ""
                    desc = f"{receipt_description}{vendor_text}"
                    
                    new_row = pd.DataFrame([[receipt_date, desc, receipt_total, receipt_category]], 
                                          columns=['Date', 'Description', 'Amount', 'Category'])
                    st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_row], ignore_index=True)
                    save_data(st.session_state.df_expenses)
                    
                    st.markdown(f"""
                    <div class='success-message'>
                        ✅ Receipt added successfully! ${receipt_total:.2f} for {desc}
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("Please enter a valid total amount.")

# Manage Expenses Page (with Delete functionality)
elif page == "⚙️ Manage Expenses":
    st.header("⚙️ Manage Expenses")
    
    if not st.session_state.df_expenses.empty:
        st.subheader("Current Expenses")
        st.dataframe(st.session_state.df_expenses.style.format({'Amount': '${:.2f}'}), use_container_width=True)
        
        st.subheader("🗑️ Delete Expenses")
        
        # Option 1: Delete by selection
        expense_options = [f"{row['Date']} - {row['Description']} (${row['Amount']})" 
                          for _, row in st.session_state.df_expenses.iterrows()]
        
        selected_expense = st.selectbox("Select expense to delete:", expense_options)
        
        if st.button("🚮 Delete Selected Expense", type="secondary"):
            # Find the index of the selected expense
            selected_index = expense_options.index(selected_expense)
            
            # Get the description for confirmation
            expense_desc = st.session_state.df_expenses.iloc[selected_index]['Description']
            expense_amount = st.session_state.df_expenses.iloc[selected_index]['Amount']
            
            # Remove the expense
            st.session_state.df_expenses = st.session_state.df_expenses.drop(selected_index).reset_index(drop=True)
            save_data(st.session_state.df_expenses)
            
            st.markdown(f"""
            <div class='success-message'>
                ✅ Deleted: {expense_desc} (${expense_amount:.2f})
            </div>
            """, unsafe_allow_html=True)
            st.rerun()
        
        # Option 2: Clear all data
        st.subheader("🔄 Reset All Data")
        if st.button("🧹 Clear All Expenses", type="primary"):
            st.session_state.df_expenses = pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Category'])
            save_data(st.session_state.df_expenses)
            st.success("All expenses have been cleared!")
            st.rerun()
            
    else:
        st.info("No expenses to manage. Add some expenses first!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"<p style='color: {SECONDARY_COLOR}; font-size: 12px;'>ETHOS Stack: Extraction, Tracking, Hub, Optimization, System</p>", unsafe_allow_html=True)

# Local instructions in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div class='info-message'>
    <h4>🚀 Local Development</h4>
    <p>For full OCR features, run locally:</p>
    <code>pip install opencv-python easyocr</code>
</div>
""", unsafe_allow_html=True)
