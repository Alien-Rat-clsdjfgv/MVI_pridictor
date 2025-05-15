import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our modules
from model import mvi_model
from database import get_all_patients, update_mvi_status

# Set page configuration
st.set_page_config(
    page_title="HCC Risk Assessment - Admin Panel",
    page_icon="🏥",
    layout="wide"
)

# Authentication (simple password protection)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Admin Login")
    password = st.text_input("Enter admin password", type="password")
    
    if st.button("Login"):
        # Simple password verification (in a real app, use proper authentication)
        if password == "admin123":  # Default password, should be changed in production
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    
    st.stop()  # Stop execution if not authenticated

# Admin Dashboard
st.title("HCC Risk Assessment - Admin Dashboard")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Patient Data", "Model Management", "System Status"])

# Get all patients from database
try:
    patients_data = get_all_patients()
    df = pd.DataFrame(patients_data) if patients_data else pd.DataFrame()
except Exception as e:
    st.error(f"Error connecting to database: {str(e)}")
    df = pd.DataFrame()

if page == "Patient Data":
    st.header("Patient Database")
    
    if df.empty:
        st.warning("No patient data available yet. Add patients through the main application.")
    else:
        # Data overview
        st.subheader("Data Overview")
        total_patients = len(df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients", total_patients)
        
        with col2:
            if "risk_level" in df.columns:
                high_risk = len(df[df["risk_level"] == "HIGH"])
                st.metric("High Risk Patients", high_risk, f"{high_risk/total_patients:.1%}")
        
        with col3:
            if "actual_mvi" in df.columns:
                known_mvi = df["actual_mvi"].notnull().sum()
                st.metric("Known MVI Status", known_mvi, f"{known_mvi/total_patients:.1%}")
        
        # Patient data table
        st.subheader("Patient Records")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            risk_options = df["risk_level"].unique().tolist() if "risk_level" in df.columns else []
            risk_filter = st.multiselect("Filter by Risk Level", risk_options)
        
        with col2:
            patient_filter = st.text_input("Search by Patient ID")
        
        # Apply filters
        filtered_df = df.copy()
        if risk_filter:
            filtered_df = filtered_df[filtered_df["risk_level"].isin(risk_filter)]
        
        if patient_filter:
            filtered_df = filtered_df[filtered_df["patient_id"].str.contains(patient_filter, case=False)]
        
        # Display table with the most important columns
        if not filtered_df.empty:
            display_cols = ["patient_id", "assessment_date", "afp", "pivka_ii", 
                           "tumor_burden", "total_score", "probability", "risk_level"]
            
            if "actual_mvi" in filtered_df.columns:
                display_cols.append("actual_mvi")
            
            st.dataframe(filtered_df[display_cols], use_container_width=True)
        else:
            st.info("No data matching the current filters")
        
        # Update MVI Status section
        st.subheader("Update MVI Status")
        st.markdown("""
        When actual MVI status becomes available (e.g., from pathology reports), 
        update the patient record to improve the model's accuracy.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_options = df["patient_id"].unique().tolist() if "patient_id" in df.columns else []
            selected_patient = st.selectbox("Select Patient ID", patient_options)
        
        with col2:
            mvi_status = st.radio("Actual MVI Status", ["Positive", "Negative", "Unknown"])
        
        if st.button("Update Status"):
            if selected_patient:
                try:
                    status = True if mvi_status == "Positive" else False if mvi_status == "Negative" else None
                    result = update_mvi_status(selected_patient, status)
                    
                    if result:
                        st.success(f"Updated MVI status for patient {selected_patient}")
                        st.rerun()
                    else:
                        st.error("Failed to update MVI status. Patient not found.")
                except Exception as e:
                    st.error(f"Error updating status: {str(e)}")
            else:
                st.error("Please select a patient")

elif page == "Model Management":
    st.header("Model Management")
    
    # Model information
    st.subheader("Current Model")
    
    # Display current coefficients from the model
    coefficients = mvi_model.get_coefficients()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Model Coefficients:**")
        coef_df = pd.DataFrame({
            "Parameter": list(coefficients.keys()),
            "Coefficient (β)": list(coefficients.values())
        })
        st.table(coef_df)
    
    with col2:
        # Create a bar chart of the coefficients
        fig = go.Figure([go.Bar(
            x=list(coefficients.keys()),
            y=list(coefficients.values()),
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
        )])
        
        fig.update_layout(
            title="Parameter Importance (β Coefficients)",
            xaxis_title="Parameter",
            yaxis_title="Coefficient Value",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Model training section
    st.subheader("Model Training")
    
    # Count patients with known MVI status
    if not df.empty and "actual_mvi" in df.columns:
        known_mvi = df[df["actual_mvi"].notnull()]
        known_count = len(known_mvi)
        
        if known_count > 0:
            st.info(f"You have {known_count} patients with known MVI status available for training.")
            
            if known_count < 10:
                st.warning(f"At least 10 patients with known MVI status are recommended for optimal training. You currently have {known_count}.")
            
            # Display stats about the training data
            if not known_mvi.empty:
                mvi_positive = known_mvi[known_mvi["actual_mvi"] == True].shape[0]
                mvi_negative = known_mvi[known_mvi["actual_mvi"] == False].shape[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("MVI Positive Patients", mvi_positive, f"{mvi_positive/known_count:.1%}")
                
                with col2:
                    st.metric("MVI Negative Patients", mvi_negative, f"{mvi_negative/known_count:.1%}")
            
            # Train model button
            if st.button("Train Model with Current Data"):
                with st.spinner("Training model..."):
                    try:
                        success = mvi_model.train()
                        if success:
                            st.success("Model trained successfully! The system will now use the updated model for predictions.")
                            st.balloons()
                        else:
                            st.warning("Model training was skipped due to insufficient data.")
                    except Exception as e:
                        st.error(f"Error during model training: {str(e)}")
        else:
            st.warning("No patients with known MVI status found in the database. Update patient records with actual MVI status to enable model training.")
    else:
        st.warning("No patient data available. Add patients and update their MVI status to train the model.")
    
    # Model explanation
    st.subheader("About the Model")
    st.markdown("""
    **How the Model Works:**
    
    1. **Initial Scoring System:**
       - AFP ≥ 20 ng/mL: 1 point
       - PIVKA-II ≥ 35 ng/mL: 2 points
       - Tumor Burden Score ≥ 6.4: 1 point
       - Total Score (0-4) maps to MVI probabilities (30.8% to 86.7%)
    
    2. **Machine Learning Enhancement:**
       - As more patient data with confirmed MVI status is collected, the system trains a logistic regression model
       - The model learns the optimal coefficients for each parameter based on actual outcomes
       - This improves prediction accuracy beyond the initial scoring system
       - The updated coefficients are displayed in the bar chart above
    
    3. **Benefits of Model Training:**
       - More accurate risk assessment for new patients
       - Personalized recommendations based on institutional data
       - Continuous improvement as more data is collected
    """)

elif page == "System Status":
    st.header("System Status")
    
    # Database status
    st.subheader("Database Status")
    
    try:
        # Check if database connection works by getting patient count
        patient_count = len(get_all_patients() or [])
        st.success("Database connection: ✓ Active")
        st.info(f"Total records in database: {patient_count}")
        
        # Create a models directory if it doesn't exist (for model persistence)
        if not os.path.exists("models"):
            os.makedirs("models")
            st.info("Created models directory for model persistence")
        else:
            # Check if model files exist
            model_files = os.listdir("models") if os.path.exists("models") else []
            if model_files:
                st.info(f"Model files in storage: {', '.join(model_files)}")
            else:
                st.info("No model files in storage yet")
    
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
    
    # System info
    st.subheader("Environment Information")
    
    # Get environment info
    env_vars = {k: v for k, v in os.environ.items() if not k.startswith("PGPASSWORD") and not k.startswith("DATABASE_URL")}
    
    # Display selected environment variables (excluding sensitive ones)
    safe_vars = ["PGUSER", "PGDATABASE", "PGHOST", "PGPORT"]
    env_info = {k: v for k, v in env_vars.items() if k in safe_vars}
    
    for k, v in env_info.items():
        st.text(f"{k}: {v}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("HCC Risk Assessment - Admin Panel v1.0")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()