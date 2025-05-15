import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database import get_all_patients, update_mvi_status
from model import mvi_model
import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="HCC Risk Assessment - Admin Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("HCC Risk Assessment - Admin Dashboard")
st.markdown("""
This admin dashboard provides insights into patient data and allows for model retraining.
""")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Patient Data", "Model Training", "Model Performance"])

# Get all patients from database
patients_data = get_all_patients()
df = pd.DataFrame(patients_data) if patients_data else pd.DataFrame()

if page == "Patient Data":
    st.header("Patient Database")
    
    if df.empty:
        st.warning("No patient data available. Add patients through the main application.")
    else:
        # Add filter options
        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_filter = st.multiselect("Risk Level", df["risk_level"].unique())
        
        with col2:
            if "actual_mvi" in df.columns:
                mvi_filter = st.multiselect("Actual MVI Status", ["Positive", "Negative", "Unknown"])
            else:
                mvi_filter = []
                
        with col3:
            date_range = st.date_input(
                "Date Range",
                [
                    datetime.datetime.now() - datetime.timedelta(days=30),
                    datetime.datetime.now()
                ]
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if risk_filter:
            filtered_df = filtered_df[filtered_df["risk_level"].isin(risk_filter)]
        
        if mvi_filter:
            if "Positive" in mvi_filter:
                filtered_df = filtered_df[filtered_df["actual_mvi"] == True]
            if "Negative" in mvi_filter:
                filtered_df = filtered_df[filtered_df["actual_mvi"] == False]
            if "Unknown" in mvi_filter:
                filtered_df = filtered_df[filtered_df["actual_mvi"].isna()]
        
        # Display table
        st.subheader("Patient Records")
        st.dataframe(filtered_df)
        
        # Update MVI status
        st.subheader("Update MVI Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_patient = st.selectbox("Select Patient ID", df["patient_id"].unique())
        
        with col2:
            mvi_status = st.radio("Actual MVI Status", ["Positive", "Negative"])
        
        if st.button("Update Status"):
            status = True if mvi_status == "Positive" else False
            if update_mvi_status(selected_patient, status):
                st.success(f"Updated MVI status for patient {selected_patient} to {mvi_status}")
                st.rerun()
            else:
                st.error("Failed to update MVI status")

elif page == "Model Training":
    st.header("Model Training")
    
    # Count patients with known MVI status
    if not df.empty and "actual_mvi" in df.columns:
        known_mvi = df[df["actual_mvi"].notnull()]
        known_count = len(known_mvi)
        
        st.info(f"You have {known_count} patients with known MVI status in the database.")
        
        if known_count < 10:
            st.warning(f"At least 10 patients with known MVI status are recommended for training. You have {known_count}.")
        
        # Display training data preview
        if not known_mvi.empty:
            st.subheader("Training Data Preview")
            training_preview = known_mvi[["patient_id", "afp", "pivka_ii", "tumor_burden", "actual_mvi"]]
            st.dataframe(training_preview)
            
            # Train model button
            if st.button("Train Model"):
                with st.spinner("Training model..."):
                    success = mvi_model.train()
                    if success:
                        st.success("Model trained successfully!")
                    else:
                        st.error("Model training failed. Not enough data or an error occurred.")
    else:
        st.warning("No patients with known MVI status found. Update patient records with actual MVI status to enable model training.")
    
    # Current model coefficients
    st.subheader("Current Model Coefficients")
    coefficients = mvi_model.get_coefficients()
    
    coef_df = pd.DataFrame({
        "Parameter": list(coefficients.keys()),
        "Coefficient": list(coefficients.values())
    })
    
    st.table(coef_df)
    
    # Explanation of coefficients
    st.markdown("""
    **About Model Coefficients**
    
    The coefficients represent the importance of each parameter in predicting MVI:
    - Higher coefficient values indicate stronger influence on the prediction
    - The model uses these coefficients to calculate probability
    - Training on more patient data improves coefficient accuracy
    """)

elif page == "Model Performance":
    st.header("Model Performance")
    
    if not df.empty and "actual_mvi" in df.columns:
        known_mvi = df[df["actual_mvi"].notna()]
        
        if not known_mvi.empty:
            # Calculate metrics
            true_positives = len(known_mvi[(known_mvi["risk_level"] == "HIGH") & (known_mvi["actual_mvi"] == True)])
            false_positives = len(known_mvi[(known_mvi["risk_level"] == "HIGH") & (known_mvi["actual_mvi"] == False)])
            true_negatives = len(known_mvi[(known_mvi["risk_level"] != "HIGH") & (known_mvi["actual_mvi"] == False)])
            false_negatives = len(known_mvi[(known_mvi["risk_level"] != "HIGH") & (known_mvi["actual_mvi"] == True)])
            
            total = len(known_mvi)
            
            # Calculate performance metrics
            accuracy = (true_positives + true_negatives) / total if total > 0 else 0
            sensitivity = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            specificity = true_negatives / (true_negatives + false_positives) if (true_negatives + false_positives) > 0 else 0
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Accuracy", f"{accuracy:.2%}")
            
            with col2:
                st.metric("Sensitivity", f"{sensitivity:.2%}")
            
            with col3:
                st.metric("Specificity", f"{specificity:.2%}")
            
            # Confusion matrix
            confusion_matrix = [
                [true_positives, false_positives],
                [false_negatives, true_negatives]
            ]
            
            fig = px.imshow(
                confusion_matrix,
                labels=dict(x="Predicted", y="Actual"),
                x=["High Risk", "Low/Moderate Risk"],
                y=["MVI Present", "MVI Absent"],
                text_auto=True,
                color_continuous_scale="Blues"
            )
            
            fig.update_layout(
                title="Confusion Matrix",
                width=500,
                height=500
            )
            
            st.plotly_chart(fig)
            
            # Risk distribution
            risk_dist = known_mvi["risk_level"].value_counts().reset_index()
            risk_dist.columns = ["Risk Level", "Count"]
            
            fig = px.bar(
                risk_dist,
                x="Risk Level",
                y="Count",
                color="Risk Level",
                color_discrete_map={
                    "LOW": "green",
                    "MODERATE": "gold",
                    "HIGH": "red"
                }
            )
            
            fig.update_layout(
                title="Risk Level Distribution",
                xaxis_title="Risk Level",
                yaxis_title="Number of Patients"
            )
            
            st.plotly_chart(fig)
            
            # Parameter distribution
            st.subheader("Parameter Distribution by Actual MVI Status")
            
            param_option = st.selectbox(
                "Select Parameter",
                ["afp", "pivka_ii", "tumor_burden", "probability"]
            )
            
            fig = px.box(
                known_mvi,
                x="actual_mvi",
                y=param_option,
                color="actual_mvi",
                points="all",
                labels={"actual_mvi": "MVI Status"}
            )
            
            fig.update_layout(
                xaxis_title="Actual MVI Status",
                yaxis_title=param_option.upper()
            )
            
            st.plotly_chart(fig)
            
        else:
            st.warning("No patients with known MVI status found. Update patient records with actual MVI status to view performance metrics.")
    else:
        st.warning("No patient data available or missing MVI status information.")