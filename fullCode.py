# app.py (Streamlit Version)
import streamlit as st
import pandas as pd
import joblib
from PIL import Image

# Set page config
st.set_page_config(
    page_title="BudgetBee 🐝", 
    page_icon="🐝", 
    layout="centered"
)

# Custom CSS to match your beautiful design
st.markdown("""
<style>
    .main {
        background-color: #fffbea;
    }
    .stButton>button {
        background-color: #ffcc00;
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: black;
        color: #ffcc00;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #ffcc00;
    }
    .result-card {
        background-color: white;
        border: 2px solid #ffcc00;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .category-badge {
        background-color: #ffcc00;
        color: black;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Load your ML model
@st.cache_resource
def load_model():
    try:
        pipeline = joblib.load("budgetbee_pipeline.joblib")
        return pipeline
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

pipeline = load_model()

# App header
st.markdown("<h1 style='text-align: center; color: #ffcc00; text-shadow: 1px 1px black;'>🐝 BudgetBee</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Track Your Expenses</h3>", unsafe_allow_html=True)

# Input form
with st.form("prediction_form"):
    desc = st.text_input("Description", placeholder="e.g. Pizza, Uber", help="Enter the expense description")
    amt = st.number_input("Amount (₹)", min_value=0.0, step=1.0, format="%.2f", help="Enter the amount spent")
    
    submitted = st.form_submit_button("Categorize 🐝")
    
    if submitted:
        if not desc:
            st.error("Please enter a description")
        elif amt <= 0:
            st.error("Please enter a valid amount")
        elif pipeline is None:
            st.error("Model not loaded. Please check if budgetbee_pipeline.joblib exists.")
        else:
            # Make prediction
            with st.spinner("Analyzing your expense... 🐝"):
                category = pipeline.predict([desc])[0]
            
            # Display results
            st.markdown("---")
            st.markdown("<h2 style='text-align: center; color: #ffcc00;'>🐝 Prediction Result</h2>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='result-card'>
                <p><b>Description:</b> {desc}</p>
                <p><b>Amount:</b> ₹{amt:.2f}</p>
                <p><b>Predicted Category:</b></p>
                <div class='category-badge'>{category}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Option to make another prediction
            if st.button("🔁 Analyze Another Expense"):
                st.rerun()

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; padding: 15px; background: black; color: #ffcc00; border-radius: 10px; margin-top: 30px;'>", unsafe_allow_html=True)
st.markdown("<p>Made with 🐝 love by Novus</p>", unsafe_allow_html=True)
st.markdown("<p>Buzzing your budget smartly 🐝</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
