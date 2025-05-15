import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="MVI預測",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS to make the app look more like a mobile app
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 430px;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #0078FF;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
        margin-top: 10px;
    }
    .stTitle {
        font-size: 24px !important;
        font-weight: 600 !important;
        text-align: center;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    .reportview-container .sidebar-content {
        padding-top: 0rem;
    }
    .sidebar .sidebar-content {
        background-color: #F0F2F6;
    }
    .css-18e3th9 {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    .element-container {
        margin-bottom: 10px;
    }
    .stApp {
        background-color: #F8F9FA;
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
    }
    div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
    }
    div.stTable {
        width: 100%;
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
    }
    .row-widget.stButton {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Top navigation bar with back button
st.markdown("""
<div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #e6e6e6;">
    <div style="flex: 1; text-align: left;">
        <a href="#" style="color: #000; text-decoration: none;">
            <span style="font-size: 24px;">←</span>
        </a>
    </div>
    <div style="flex: 2; text-align: center;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">MVI預測</h2>
    </div>
    <div style="flex: 1;"></div>
</div>
""", unsafe_allow_html=True)

# Hidden title - for navigational purposes only
st.title("MVI預測")
st.markdown("<style>h1{display: none;}</style>", unsafe_allow_html=True)

# Import our model for prediction
from model import mvi_model
from database import save_patient, get_patient, get_patient_by_values

# These functions are now provided by the model
def calculate_score(afp, pivka_ii, tumor_burden):
    """Calculate total score based on clinical parameters"""
    return mvi_model.calculate_score(afp, pivka_ii, tumor_burden)

def calculate_probability(score):
    """Calculate MVI probability based on score"""
    return mvi_model.calculate_probability_from_score(score)

def determine_risk_level(probability):
    """Determine risk level based on probability"""
    return mvi_model.determine_risk_level(probability)

def get_recommendations(risk_level):
    """Get recommendations based on risk level"""
    return mvi_model.get_recommendations(risk_level)

# Function to create a gauge chart
def create_gauge_chart(probability, risk_level):
    if risk_level == "LOW":
        color = "#4CAF50"  # Green
        position = 20
    elif risk_level == "MODERATE":
        color = "#FFC107"  # Yellow/Gold
        position = 55
    else:  # HIGH
        color = "#F44336"  # Red
        position = 85
    
    # Create a half-circle gauge with mobile app styling
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': "%", 'font': {'size': 30, 'color': "black", 'family': "Arial"}},
        gauge={
            'axis': {
                'range': [None, 100],
                'tickmode': 'array',
                'tickvals': [0, 50, 100],
                'ticktext': ['', '', ''],
                'tickwidth': 0,
                'tickcolor': "white"
            },
            'bar': {'color': "black", 'thickness': 0.2},
            'bgcolor': "white",
            'borderwidth': 0,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 40], 'color': '#4CAF50'},  # Green for LOW
                {'range': [40, 70], 'color': '#FFC107'},  # Yellow/Gold for MODERATE
                {'range': [70, 100], 'color': '#F44336'}  # Red for HIGH
            ],
            'threshold': {
                'line': {'color': "black", 'width': 6},
                'thickness': 0.9,
                'value': probability
            }
        }
    ))
    
    # Update layout to match mobile app design
    fig.update_layout(
        height=230,
        margin=dict(l=5, r=5, t=60, b=10),
        paper_bgcolor="white",
        font={'color': "black", 'family': "Arial, Helvetica, sans-serif"},
        annotations=[
            dict(
                x=0.1,
                y=0.8,
                xref="paper",
                yref="paper",
                text="LOW",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#4CAF50"
                )
            ),
            dict(
                x=0.5,
                y=0.92,
                xref="paper",
                yref="paper",
                text="MODERATE",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#FFC107"
                )
            ),
            dict(
                x=0.9,
                y=0.8,
                xref="paper",
                yref="paper",
                text="HIGH",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#F44336"
                )
            )
        ]
    )
    
    return fig

# Function to save assessment results
def save_assessment(patient_id, assessment_data):
    # Create directory if it doesn't exist
    if not os.path.exists("saved_assessments"):
        os.makedirs("saved_assessments")
    
    # Create a filename based on patient ID and date
    filename = f"saved_assessments/{patient_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save the data
    with open(filename, "w") as f:
        json.dump(assessment_data, f)
    
    return filename

# We'll completely remove the sidebar inputs since we moved them to the main area
# Just keep this as a placeholder for the mobile app
# Sidebar will only contain the About information

# Restructure the layout to match the mobile app in the image
col_input, col_button = st.columns([3, 1])

with col_input:
    # Create a card-like container for the inputs
    st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h3 style="font-size: 16px; margin-bottom: 15px;">Input Clinical Values</h3>
    """, unsafe_allow_html=True)
    
    # 新增查詢模式選擇
    lookup_mode = st.radio(
        "使用模式",
        ["輸入新資料", "查詢病例（使用臨床數值）", "查詢病例（使用病歷號）"],
        horizontal=True,
        key="lookup_mode"
    )
    
    # 根據查詢模式顯示不同選項
    if lookup_mode == "查詢病例（使用病歷號）":
        patient_id = st.text_input("病歷號", "", key="patient_id_main")
        if patient_id:
            # 查找病例
            patient_record = get_patient(patient_id)
            if patient_record:
                st.success(f"找到病歷號為 {patient_id} 的病人記錄")
                # 預填臨床數值
                afp_value = patient_record['afp']
                pivka_ii_value = patient_record['pivka_ii']
                tumor_burden_value = patient_record['tumor_burden']
            else:
                st.error(f"找不到病歷號為 {patient_id} 的病人記錄")
                afp_value = 15.0
                pivka_ii_value = 25.0
                tumor_burden_value = 5.0
        else:
            afp_value = 15.0
            pivka_ii_value = 25.0
            tumor_burden_value = 5.0
        assessment_date = st.date_input("評估日期", datetime.date.today(), key="date_main")
    elif lookup_mode == "查詢病例（使用臨床數值）":
        patient_id = ""  # 不需要病歷號
        assessment_date = st.date_input("評估日期", datetime.date.today(), key="date_main")
        # 臨床參數將在下面輸入
        afp_value = 15.0
        pivka_ii_value = 25.0
        tumor_burden_value = 5.0
    else:  # 輸入新資料
        patient_id = st.text_input("病歷號（選填）", "", key="patient_id_main")
        assessment_date = st.date_input("評估日期", datetime.date.today(), key="date_main")
        afp_value = 15.0
        pivka_ii_value = 25.0
        tumor_burden_value = 5.0
    
    # Clinical Parameters
    afp = st.number_input(
        "AFP (ng/mL)",
        min_value=0.0,
        value=afp_value,
        step=0.1,
        help="Alpha-fetoprotein level. Score 1 point if ≥ 20 ng/mL"
    )
    
    pivka_ii = st.number_input(
        "PIVKA-II (ng/mL)",
        min_value=0.0,
        value=pivka_ii_value,
        step=0.1,
        help="Protein Induced by Vitamin K Absence or Antagonist-II. Score 2 points if ≥ 35 ng/mL"
    )
    
    tumor_burden = st.number_input(
        "Tumor Burden Score",
        min_value=0.0,
        value=tumor_burden_value,
        step=0.1,
        help="Composite score based on tumor size and number. Score 1 point if ≥ 6.4"
    )
    
    # 如果是使用臨床數值查詢模式，添加查詢按鈕
    if lookup_mode == "查詢病例（使用臨床數值）":
        lookup_button = st.button("搜尋相似病例", key="lookup_button")
        if lookup_button:
            # 使用臨床值查找相似病例
            patient_record = get_patient_by_values(afp, pivka_ii, tumor_burden)
            if patient_record:
                st.success("找到匹配的病人記錄！")
                st.json(patient_record)
            else:
                st.error("無法找到匹配的病例記錄。請嘗試調整臨床參數或使用病歷號查詢。")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Calculate button
calc_button = st.button("Calculate Risk Assessment", key="calculate_risk")

# Create a container for results
result_container = st.container()

if calc_button:
    # Calculate score
    total_score = calculate_score(afp, pivka_ii, tumor_burden)
    probability = calculate_probability(total_score)
    
    # Try to use model for advanced prediction if available
    try:
        # Get prediction from model
        probability_model = mvi_model.predict_probability(afp, pivka_ii, tumor_burden)
        
        # If probability is significantly different, show a message and use model prediction
        if abs(probability_model - probability) > 5:
            probability = probability_model
    except Exception as e:
        # If model prediction fails, continue with traditional scoring
        pass
        
    risk_level = determine_risk_level(probability)
    recommendations = get_recommendations(risk_level)
    
    # Display the results
    with result_container:
        # White card for results
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 15px; margin-top: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        # Display the gauge chart
        st.plotly_chart(create_gauge_chart(probability, risk_level), use_container_width=True)
        
        # Display risk level prominently
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 28px; font-weight: bold; margin: 0;">MVI風險預測</h1>
            <h2 style="font-size: 36px; font-weight: bold; margin: 5px 0; color: {'#F44336' if risk_level == 'HIGH' else '#FFC107' if risk_level == 'MODERATE' else '#4CAF50'};">{risk_level}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Add divider before recommendations
        st.markdown("<hr style='margin: 15px 0; border-color: #e6e6e6;'>", unsafe_allow_html=True)
        
        # Recommended actions with better styling
        st.markdown("""
        <h3 style="font-size: 20px; margin-bottom: 15px;">Recommended Actions</h3>
        """, unsafe_allow_html=True)
        
        # List recommended actions with bullet points
        for rec in recommendations:
            st.markdown(f"<p style='margin: 10px 0; padding-left: 20px; position: relative;'>• {rec}</p>", unsafe_allow_html=True)
        
        # Close the white card div
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display the scoring breakdown in expandable section
        with st.expander("View Scoring Breakdown"):
            st.markdown(f"**Total Score:** {total_score}")
            st.markdown(f"**Probability of MVI:** {probability}%")
            
            details_df = pd.DataFrame({
                "Parameter": ["AFP", "PIVKA-II", "Tumor Burden Score"],
                "Value": [f"{afp:.1f} ng/mL", f"{pivka_ii:.1f} ng/mL", f"{tumor_burden:.1f}"],
                "Threshold": ["≥20", "≥35", "≥6.4"],
                "Points": [
                    "1" if afp >= 20 else "0",
                    "2" if pivka_ii >= 35 else "0",
                    "1" if tumor_burden >= 6.4 else "0"
                ]
            })
            
            st.table(details_df)
        
        # Save results option
        if patient_id:
            if st.button("Save Assessment Results", key="save_results"):
                # Prepare data to save
                assessment_data = {
                    "patient_id": patient_id,
                    "assessment_date": assessment_date.strftime("%Y-%m-%d"),
                    "parameters": {
                        "afp": afp,
                        "pivka_ii": pivka_ii,
                        "tumor_burden": tumor_burden
                    },
                    "results": {
                        "total_score": total_score,
                        "probability": probability,
                        "risk_level": risk_level,
                        "recommendations": recommendations
                    }
                }
                
                try:
                    # First try to save to database
                    patient_id = save_patient(assessment_data)
                    st.success(f"Assessment saved successfully to database (ID: {patient_id})")
                except Exception as e:
                    # Fall back to file system if database fails
                    try:
                        saved_file = save_assessment(patient_id, assessment_data)
                        st.success(f"Assessment saved successfully to {saved_file}")
                    except Exception as e2:
                        st.error(f"Failed to save assessment: {str(e2)}")
        else:
            st.warning("Enter a Patient ID to enable saving of assessment results")

# Information section
st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.info("""
This tool calculates HCC recurrence risk based on:
- AFP (Alpha-fetoprotein)
- PIVKA-II (Protein Induced by Vitamin K Absence)
- Tumor Burden Score

The risk assessment helps guide post-operative monitoring and treatment decisions.
""")

# Add link to admin panel in sidebar (hidden from regular users)
st.sidebar.markdown("---")
admin_expander = st.sidebar.expander("Admin Access", expanded=False)
with admin_expander:
    st.markdown("[Open Admin Panel](/Admin_Panel)")
    st.caption("Requires authentication")

# Display the reference table
with st.expander("View Scoring Reference Table"):
    # Get updated coefficients from model
    model_coefficients = mvi_model.get_coefficients()
    
    # Create a DataFrame for the reference table
    ref_data = {
        "Predictor variables": ["AFP", "AFP", "PIVKA-II", "PIVKA-II", "Tumor burden score", "Tumor burden score"],
        "Regression coefficients (β)": [
            model_coefficients['afp'], model_coefficients['afp'], 
            model_coefficients['pivka_ii'], model_coefficients['pivka_ii'], 
            model_coefficients['tumor_burden'], model_coefficients['tumor_burden']
        ],
        "Categories": ["<20", "≥20", "<35", "≥35", "<6.4", "≥6.4"],
        "Points": [0, 1, 0, 2, 0, 1]
    }
    
    ref_df = pd.DataFrame(ref_data)
    st.table(ref_df)
    
    # Create a DataFrame for the probability table
    prob_data = {
        "Total score": [0, 1, 2, 3, 4],
        "Probability of MVI": ["30.8%", "46.6%", "63.1%", "77.0%", "86.7%"]
    }
    
    prob_df = pd.DataFrame(prob_data)
    st.table(prob_df)
