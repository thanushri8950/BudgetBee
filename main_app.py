# budgetbee_app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import tempfile
import os

# --- Check for OCR dependencies ---
try:
    import cv2
    import easyocr
    import re
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    st.sidebar.warning("⚠️ Receipt scanning is disabled. Required libraries (opencv-python, easyocr) could not be installed.")

# -------------------------------
# 1. VISION & EXTRACTION CORE (OCR Function)
# -------------------------------
def process_receipt_image(uploaded_file):
    """
    Takes an uploaded Streamlit file, processes it with OpenCV & EasyOCR,
    and returns parsed data (vendor, total, items).
    """
    if not OCR_AVAILABLE:
        return None, None, []

    # Save the uploaded file to a temporary file so OpenCV can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_img_path = tmp_file.name

    try:
        # --- Image Loading and Preprocessing ---
        image = cv2.imread(tmp_img_path)
        if image is None:
            return None, None, []

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # --- Text Extraction with EasyOCR ---
        reader = easyocr.Reader(['en'])
        results = reader.readtext(thresh_image)

        # --- Data Parsing ---
        total_amount = None
        vendor_name = None
        items_list = []

        # Logic to find TOTAL
        for _, text, prob in results:
            text_clean = text.upper().replace(' ', '').replace('$', '')
            if 'TOTAL' in text_clean and prob > 0.3:
                numbers_found = re.findall(r'\d+\.\d{2}', text_clean)
                if numbers_found:
                    total_amount = float(numbers_found[0])
                    break

        # Logic to find Items and Vendor
        for i, (_, text, prob) in enumerate(results):
            # Vendor is often near the top
            if i < 3 and prob > 0.4 and vendor_name is None:
                vendor_name = text

            # Find items and prices
            if prob > 0.3:
                numbers_in_text = re.findall(r'\d+\.\d{2}', text)
                if numbers_in_text and len(text) > 3:
                    item_desc = re.sub(r'\d+\.\d{2}', '', text).strip()
                    items_list.append({'item': item_desc, 'price': float(numbers_in_text[0])})
                else:
                    try:
                        next_text = results[i+1][1]
                        if re.match(r'^\d+\.\d{2}$', next_text.strip()):
                            items_list.append({'item': text, 'price': float(next_text)})
                    except IndexError:
                        continue

        return vendor_name, total_amount, items_list

    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None, None, []
    finally:
        # Clean up the temporary file
        os.unlink(tmp_img_path)

# -------------------------------
# 2. ANALYTICS ENGINE (Pandas/NumPy)
# -------------------------------
def categorize_expense(description):
    """
    A simple rule-based categorizer.
    """
    if not description:
        return 'Other'
        
    description_lower = description.lower()
    if any(word in description_lower for word in ['coffee', 'mcdonald', 'kfc', 'restaurant', 'food', 'grocery', 'supermarket']):
        return 'Food'
    elif any(word in description_lower for word in ['shell', 'gas', 'petrol', 'metro', 'bus', 'uber', 'transport', 'fuel']):
        return 'Transport'
    elif any(word in description_lower for word in ['cine', 'movie', 'netflix', 'entertain', 'concert']):
        return 'Entertainment'
    elif any(word in description_lower for word in ['rent', 'electric', 'water', 'internet', 'bill']):
        return 'Utilities'
    else:
        return 'Other'

# -------------------------------
# 3. THE HUB (Streamlit UI)
# -------------------------------
# Page Config
st.set_page_config(page_title="BudgetBee - ETHOS Stack", layout="wide")
st.title("BudgetBee 🐝")
st.header("The Complete ETHOS Stack Expense Tracker")

# Initialize session state for our main DataFrame
if 'df_expenses' not in st.session_state:
    try:
        st.session_state.df_expenses = pd.read_csv('expenses.csv', parse_dates=['Date'])
    except FileNotFoundError:
        st.session_state.df_expenses = pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Category'])

# Sidebar for navigation
page = st.sidebar.radio("Navigate", ["Dashboard", "Add Expense", "Receipt Scanner"])

if page == "Dashboard":
    # --- DATA VISUALIZATION ---
    st.subheader("Financial Dashboard")
    
    if not st.session_state.df_expenses.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Expenses", f"${st.session_state.df_expenses['Amount'].sum():.2f}")
            st.dataframe(st.session_state.df_expenses, use_container_width=True)
        with col2:
            spending_by_category = st.session_state.df_expenses.groupby('Category')['Amount'].sum()
            st.bar_chart(spending_by_category)
    else:
        st.info("No expenses to show. Add some via 'Add Expense' or 'Receipt Scanner'!")

elif page == "Add Expense":
    # --- MANUAL DATA ENTRY UI ---
    st.subheader("Add Expense Manually")
    with st.form("manual_form"):
        date = st.date_input("Date", datetime.today())
        desc = st.text_input("Description")
        amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            if desc and amount > 0:
                category = categorize_expense(desc)
                new_row = pd.DataFrame([[date, desc, amount, category]], 
                                      columns=['Date', 'Description', 'Amount', 'Category'])
                st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_row], ignore_index=True)
                st.session_state.df_expenses.to_csv('expenses.csv', index=False)
                st.success("Expense added!")
            else:
                st.error("Please fill in description and amount.")

elif page == "Receipt Scanner":
    # --- OCR INTEGRATION UI ---
    st.subheader("Scan a Receipt")
    
    if not OCR_AVAILABLE:
        st.error("The receipt scanning feature is not available on this deployment. Required libraries could not be installed.")
        st.info("To use receipt scanning, please run this app locally with: `pip install opencv-python easyocr`")
    else:
        uploaded_file = st.file_uploader("Upload a receipt image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
            
            if st.button("Extract Data from Receipt"):
                with st.spinner("Processing image with AI... 🤖"):
                    vendor, total, items = process_receipt_image(uploaded_file)
                
                if vendor or items:
                    st.success("Data extracted!")
                    st.write(f"**Vendor:** {vendor if vendor else 'Unknown'}")
                    st.write(f"**Total Found:** ${total if total else 'Could not detect'}")
                    
                    if items:
                        st.write("**Items Found:**")
                        df_extracted = pd.DataFrame(items)
                        st.dataframe(df_extracted, use_container_width=True)
                        
                        if total and st.button(f"Add Total (${total}) to Expenses"):
                            today = datetime.today().date()
                            category = categorize_expense(vendor if vendor else "Receipt Purchase")
                            new_row = pd.DataFrame([[today, f"{vendor} (Receipt)" if vendor else 'Receipt Purchase', total, category]], 
                                                  columns=['Date', 'Description', 'Amount', 'Category'])
                            st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_row], ignore_index=True)
                            st.session_state.df_expenses.to_csv('expenses.csv', index=False)
                            st.success(f"Added ${total} to your expenses!")
                else:
                    st.error("Could not extract any data from this image. Try a clearer photo.")

# Footer
st.sidebar.divider()
st.sidebar.info("**ETHOS Stack:** Extraction (OCR), Tracking (CSV), Hub (UI), Optimization (Categorization), System")
