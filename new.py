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
</style>
""", unsafe_allow_html=True)

# --- Check for OCR dependencies ---
try:
    import cv2
    import easyocr
    import re
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# -------------------------------
# 1. VISION & EXTRACTION CORE (OCR Function)
# -------------------------------
def process_receipt_image(uploaded_file):
    """Process receipt image with OCR and return parsed data."""
    if not OCR_AVAILABLE:
        return None, None, []

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_img_path = tmp_file.name

    try:
        image = cv2.imread(tmp_img_path)
        if image is None:
            return None, None, []

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        reader = easyocr.Reader(['en'])
        results = reader.readtext(thresh_image)

        total_amount = None
        vendor_name = None
        items_list = []

        # Parse receipt data
        for _, text, prob in results:
            text_clean = text.upper().replace(' ', '').replace('$', '')
            if 'TOTAL' in text_clean and prob > 0.3:
                numbers_found = re.findall(r'\d+\.\d{2}', text_clean)
                if numbers_found:
                    total_amount = float(numbers_found[0])
                    break

        for i, (_, text, prob) in enumerate(results):
            if i < 3 and prob > 0.4 and vendor_name is None:
                vendor_name = text
            if prob > 0.3:
                numbers_in_text = re.findall(r'\d+\.\d{2}', text)
                if numbers_in_text and len(text) > 3:
                    item_desc = re.sub(r'\d+\.\d{2}', '', text).strip()
                    items_list.append({'item': item_desc, 'price': float(numbers_in_text[0])})

        return vendor_name, total_amount, items_list

    except Exception as e:
        return None, None, []
    finally:
        os.unlink(tmp_img_path)

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
        st.info("No expenses recorded yet. Add some via 'Add Expense' or 'Receipt Scanner'!")

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
            else:
                st.error("Please fill in description and amount.")

# Receipt Scanner Page
elif page == "📷 Receipt Scanner":
    st.header("📷 Receipt Scanner")
    
    if not OCR_AVAILABLE:
        st.markdown(f"""
        <div class='warning-message'>
            ⚠️ Receipt scanning is disabled. Required libraries could not be installed.
        </div>
        """, unsafe_allow_html=True)
    else:
        uploaded_file = st.file_uploader("Upload receipt image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
            
            if st.button("🔍 Extract Data from Receipt"):
                with st.spinner("Processing image with AI... 🤖"):
                    vendor, total, items = process_receipt_image(uploaded_file)
                
                if vendor or items:
                    st.success("Data extracted successfully!")
                    st.write(f"**🏪 Vendor:** {vendor if vendor else 'Unknown'}")
                    st.write(f"**💰 Total:** ${total if total else 'Not detected'}")
                    
                    if items:
                        st.write("**🛒 Items Found:**")
                        df_extracted = pd.DataFrame(items)
                        st.dataframe(df_extracted.style.format({'price': '${:.2f}'}), use_container_width=True)
                        
                        if total and st.button(f"💾 Add Total (${total}) to Expenses"):
                            today = datetime.today().date()
                            category = categorize_expense(vendor if vendor else "Receipt Purchase")
                            new_row = pd.DataFrame([[today, f"{vendor} (Receipt)" if vendor else 'Receipt Purchase', total, category]], 
                                                  columns=['Date', 'Description', 'Amount', 'Category'])
                            st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_row], ignore_index=True)
                            save_data(st.session_state.df_expenses)
                            st.success(f"Added ${total} to your expenses!")

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
