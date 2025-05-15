import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="HCC Recurrence Risk Calculator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("HCC Recurrence Risk Assessment")
st.markdown("""
This application calculates the postoperative HCC recurrence risk based on clinical parameters.
Enter the patient's values below to generate a risk assessment.
""")

# Create a function to calculate the score based on the parameters
def calculate_score(afp, pivka_ii, tumor_burden):
    score = 0
    
    # AFP scoring
    if afp >= 20:
        score += 1
    
    # PIVKA-II scoring
    if pivka_ii >= 35:
        score += 2
    
    # Tumor burden scoring
    if tumor_burden >= 6.4:
        score += 1
    
    return score

# Function to calculate probability of MVI based on total score
def calculate_probability(score):
    probability_map = {
        0: 30.8,
        1: 46.6,
        2: 63.1,
        3: 77.0,
        4: 86.7
    }
    return probability_map.get(score, 0)

# Function to determine risk level based on probability
def determine_risk_level(probability):
    if probability < 40:
        return "LOW"
    elif probability < 70:
        return "MODERATE"
    else:
        return "HIGH"

# Function to get recommendations based on risk level
def get_recommendations(risk_level):
    if risk_level == "LOW":
        return [
            "Regular follow-up every 6 months.",
            "Monitor AFP levels annually.",
            "Consider ultrasound examination yearly.",
            "Maintain healthy lifestyle."
        ]
    elif risk_level == "MODERATE":
        return [
            "Regular follow-up every 4 months.",
            "Monitor AFP and PIVKA-II levels bi-annually.",
            "Consider CT/MRI examination yearly.",
            "Evaluate potential adjuvant therapy options."
        ]
    else:  # HIGH
        return [
            "Proceed with adjuvant therapy.",
            "Perform close monitoring every 3 months.",
            "Order MRI or CT for 3-year surveillance.",
            "Review AFP and PIVKA-II levels regularly."
        ]

# Function to create a gauge chart
def create_gauge_chart(probability, risk_level):
    if risk_level == "LOW":
        color = "green"
    elif risk_level == "MODERATE":
        color = "gold"
    else:  # HIGH
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Postoperative<br>HCC Recurrence<br>{risk_level}", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'green'},
                {'range': [40, 70], 'color': 'gold'},
                {'range': [70, 100], 'color': 'red'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': probability
            }
        }
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={'color': "black", 'family': "Arial"}
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

# Sidebar for input parameters
st.sidebar.header("Patient Information")
patient_id = st.sidebar.text_input("Patient ID", "")
assessment_date = st.sidebar.date_input("Assessment Date", datetime.date.today())

st.sidebar.header("Clinical Parameters")

# AFP input
afp = st.sidebar.number_input(
    "AFP (ng/mL)",
    min_value=0.0,
    value=15.0,
    step=0.1,
    help="Alpha-fetoprotein level. Score 1 point if ≥ 20 ng/mL"
)

# PIVKA-II input
pivka_ii = st.sidebar.number_input(
    "PIVKA-II (mAU/mL)",
    min_value=0.0,
    value=25.0,
    step=0.1,
    help="Protein Induced by Vitamin K Absence or Antagonist-II. Score 2 points if ≥ 35 mAU/mL"
)

# Tumor burden score input
tumor_burden = st.sidebar.number_input(
    "Tumor Burden Score",
    min_value=0.0,
    value=5.0,
    step=0.1,
    help="Composite score based on tumor size and number. Score 1 point if ≥ 6.4"
)

# Calculate button
if st.sidebar.button("Calculate Risk"):
    # Calculate score
    total_score = calculate_score(afp, pivka_ii, tumor_burden)
    probability = calculate_probability(total_score)
    risk_level = determine_risk_level(probability)
    recommendations = get_recommendations(risk_level)
    
    # Display the results
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("Risk Assessment")
        # Display the gauge chart
        st.plotly_chart(create_gauge_chart(probability, risk_level), use_container_width=True)
    
    with col2:
        st.header("Assessment Details")
        st.markdown(f"**Total Score:** {total_score}")
        st.markdown(f"**Probability of MVI:** {probability}%")
        
        # Display scoring details
        st.subheader("Scoring Details")
        
        details_df = pd.DataFrame({
            "Parameter": ["AFP", "PIVKA-II", "Tumor Burden Score"],
            "Value": [f"{afp:.1f} ng/mL", f"{pivka_ii:.1f} mAU/mL", f"{tumor_burden:.1f}"],
            "Threshold": ["≥20", "≥35", "≥6.4"],
            "Points": [
                "1" if afp >= 20 else "0",
                "2" if pivka_ii >= 35 else "0",
                "1" if tumor_burden >= 6.4 else "0"
            ]
        })
        
        st.table(details_df)
    
    # Recommended actions
    st.header("Recommended Actions")
    for rec in recommendations:
        st.markdown(f"• {rec}")
    
    # Save results option
    if patient_id:
        if st.button("Save Assessment Results"):
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
            
            saved_file = save_assessment(patient_id, assessment_data)
            st.success(f"Assessment saved successfully to {saved_file}")
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

# Display the reference table
with st.expander("View Scoring Reference Table"):
    # Create a DataFrame for the reference table
    ref_data = {
        "Predictor variables": ["AFP", "AFP", "PIVKA-II", "PIVKA-II", "Tumor burden score", "Tumor burden score"],
        "Regression coefficients (β)": [0.647, 0.647, 1.206, 1.206, 0.916, 0.916],
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
