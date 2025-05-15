import streamlit as st
import pandas as pd
import sys
import os
import json
import datetime

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our modules
from database import get_all_patients, add_patient_complete, delete_patient
from model import mvi_model
from hospital_api import test_connection, import_patients, get_config, save_config

# Set page configuration
st.set_page_config(
    page_title="HCC Risk Assessment - Data Management",
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
st.title("HCC Risk Assessment - Data Management")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Hospital Data Integration", "Manual Data Entry", "Data Import/Export"])

# Get all patients from database
try:
    patients_data = get_all_patients()
    df = pd.DataFrame(patients_data) if patients_data else pd.DataFrame()
except Exception as e:
    st.error(f"Error connecting to database: {str(e)}")
    df = pd.DataFrame()

if page == "Hospital Data Integration":
    st.header("Hospital Data Integration")
    
    st.markdown("""
    Connect to your hospital's Electronic Medical Record (EMR) system to automatically import patient data.
    """)
    
    # Get current configuration
    config = get_config()
    
    # Hospital API configuration
    st.subheader("Hospital API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        connection_type = st.selectbox(
            "Connection Type", 
            options=["REST API", "FHIR", "File Import"],
            index=0 if config.connection_type == 'rest' else (1 if config.connection_type == 'fhir' else 2)
        )
        
        api_url = st.text_input("API URL or File Path", value=config.api_url)
        hospital_id = st.text_input("Hospital ID", value=config.hospital_id)
    
    with col2:
        st.markdown("**Authentication**")
        api_key = st.text_input("API Key", value=config.api_key, type="password")
        api_username = st.text_input("Username (if needed)", value=config.api_username)
        api_password = st.text_input("Password (if needed)", value=config.api_password, type="password")
    
    # Save configuration button
    if st.button("Save Configuration"):
        # Convert connection type to internal format
        conn_type = 'rest'
        if connection_type == "FHIR":
            conn_type = 'fhir'
        elif connection_type == "File Import":
            conn_type = 'file'
        
        # Save configuration
        config_data = {
            'api_url': api_url,
            'api_key': api_key,
            'api_username': api_username,
            'api_password': api_password,
            'hospital_id': hospital_id,
            'connection_type': conn_type
        }
        
        save_config(config_data)
        st.success("Configuration saved successfully")
    
    # Test connection button
    if st.button("Test Connection"):
        # Convert connection type to internal format
        conn_type = 'rest'
        if connection_type == "FHIR":
            conn_type = 'fhir'
        elif connection_type == "File Import":
            conn_type = 'file'
        
        # Test configuration
        test_config = get_config()
        test_config.api_url = api_url
        test_config.api_key = api_key
        test_config.api_username = api_username
        test_config.api_password = api_password
        test_config.hospital_id = hospital_id
        test_config.connection_type = conn_type
        
        success, message = test_connection(test_config)
        
        if success:
            st.success(f"Connection successful: {message}")
        else:
            st.error(f"Connection failed: {message}")
    
    # Data import section
    st.subheader("Import Patient Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        import_limit = st.number_input("Maximum Records to Import", min_value=1, value=100)
    
    with col2:
        st.markdown("**Import Summary**")
        if not df.empty:
            st.info(f"Current database has {len(df)} patient records")
    
    # Import button
    if st.button("Import Data Now"):
        with st.spinner("Importing data..."):
            # Get latest configuration
            import_config = get_config()
            
            # Import data
            imported, errors, message = import_patients(import_config, limit=import_limit)
            
            if imported > 0:
                st.success(f"Successfully imported {imported} records with {errors} errors")
                st.info(message)
                
                # Offer to train model with new data
                if st.button("Train Model with New Data"):
                    with st.spinner("Training model..."):
                        try:
                            success = mvi_model.train()
                            if success:
                                st.success("Model trained successfully with the new data!")
                                st.balloons()
                            else:
                                st.warning("Model training was skipped due to insufficient data.")
                        except Exception as e:
                            st.error(f"Error during model training: {str(e)}")
            else:
                st.error(f"Import failed: {message}")

elif page == "Manual Data Entry":
    st.header("Manual Data Entry")
    
    st.markdown("""
    Manually add or edit patient data.
    """)
    
    # Form for adding a new patient
    with st.form("new_patient_form"):
        st.subheader("Add New Patient")
        
        # Basic information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_id = st.text_input("Patient ID")
        
        with col2:
            assessment_date = st.date_input("Assessment Date", datetime.datetime.now())
        
        with col3:
            source = st.selectbox("Data Source", ["Manual Entry", "Hospital Records", "Research"])
        
        # Divider
        st.markdown("---")
        st.subheader("Standard Parameters")
        
        # Standard parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            afp = st.number_input("AFP (ng/mL)", min_value=0.0, step=0.1)
        
        with col2:
            pivka_ii = st.number_input("PIVKA-II (ng/mL)", min_value=0.0, step=0.1)
        
        with col3:
            tumor_burden = st.number_input("Tumor Burden Score", min_value=0.0, step=0.1)
        
        # Extended parameters
        with st.expander("Extended Parameters", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                tumor_size = st.number_input("Tumor Size (cm)", min_value=0.0, step=0.1)
                tumor_number = st.number_input("Number of Tumors", min_value=0, step=1)
                tumor_diff = st.selectbox("Tumor Differentiation", ["", "Well", "Moderate", "Poor", "Undifferentiated"])
            
            with col2:
                liver_cirrhosis = st.checkbox("Liver Cirrhosis")
                hbv_status = st.checkbox("Hepatitis B Positive")
                hcv_status = st.checkbox("Hepatitis C Positive")
        
        # Calculate scores automatically
        if st.checkbox("Calculate Scores Automatically", value=True):
            # Calculate score
            score = 0
            if afp >= 20:
                score += 1
            if pivka_ii >= 35:
                score += 2
            if tumor_burden >= 6.4:
                score += 1
            
            # Calculate probability
            probability_map = {
                0: 30.8,
                1: 46.6,
                2: 63.1,
                3: 77.0,
                4: 86.7
            }
            probability = probability_map.get(score, 0)
            
            # Determine risk level
            if probability < 40:
                risk_level = "LOW"
            elif probability < 70:
                risk_level = "MODERATE"
            else:
                risk_level = "HIGH"
            
            st.info(f"Calculated: Score={score}, Probability={probability:.1f}%, Risk Level={risk_level}")
        else:
            # Manual score entry
            col1, col2, col3 = st.columns(3)
            
            with col1:
                score = st.number_input("Total Score", min_value=0, max_value=4)
            
            with col2:
                probability = st.number_input("Probability (%)", min_value=0.0, max_value=100.0)
            
            with col3:
                risk_level = st.selectbox("Risk Level", ["LOW", "MODERATE", "HIGH"])
        
        # Known MVI status
        actual_mvi = st.radio("Actual MVI Status (if known)", ["Unknown", "Positive", "Negative"])
        
        # Notes
        notes = st.text_area("Notes")
        
        # Submit button
        submitted = st.form_submit_button("Add Patient")
        
        if submitted:
            if not patient_id:
                st.error("Patient ID is required")
            else:
                try:
                    # Prepare patient data
                    patient_data = {
                        'patient_id': patient_id,
                        'assessment_date': assessment_date,
                        'afp': afp,
                        'pivka_ii': pivka_ii,
                        'tumor_burden': tumor_burden,
                        'tumor_size': tumor_size if tumor_size > 0 else None,
                        'tumor_number': tumor_number if tumor_number > 0 else None,
                        'tumor_diff': tumor_diff if tumor_diff else None,
                        'liver_cirrhosis': liver_cirrhosis,
                        'hbv_status': hbv_status,
                        'hcv_status': hcv_status,
                        'total_score': score,
                        'probability': probability,
                        'risk_level': risk_level,
                        'actual_mvi': True if actual_mvi == "Positive" else (False if actual_mvi == "Negative" else None),
                        'notes': notes,
                        'source': source,
                        'created_at': datetime.datetime.now()
                    }
                    
                    # Add to database
                    add_patient_complete(patient_data)
                    st.success(f"Patient {patient_id} added successfully")
                except Exception as e:
                    st.error(f"Error adding patient: {str(e)}")
    
    # Patient list for editing/deleting
    st.subheader("Manage Existing Patients")
    
    if df.empty:
        st.warning("No patients in database")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            search_id = st.text_input("Search by Patient ID")
        
        with col2:
            source_filter = st.multiselect("Filter by Source", df["source"].unique() if "source" in df.columns else [])
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_id:
            filtered_df = filtered_df[filtered_df["patient_id"].str.contains(search_id, case=False)]
        
        if source_filter:
            filtered_df = filtered_df[filtered_df["source"].isin(source_filter)]
        
        # Display table
        if not filtered_df.empty:
            # Select columns to display
            display_cols = ["patient_id", "assessment_date", "afp", "pivka_ii", 
                           "tumor_burden", "risk_level", "actual_mvi", "source"]
            
            # Display table
            st.dataframe(filtered_df[display_cols], use_container_width=True)
            
            # Delete patient
            col1, col2 = st.columns(2)
            
            with col1:
                delete_id = st.selectbox("Select Patient to Delete", filtered_df["patient_id"].unique().tolist())
            
            with col2:
                if st.button("Delete Patient"):
                    try:
                        if delete_patient(delete_id):
                            st.success(f"Patient {delete_id} deleted successfully")
                            st.rerun()
                        else:
                            st.error(f"Patient {delete_id} not found")
                    except Exception as e:
                        st.error(f"Error deleting patient: {str(e)}")
        else:
            st.info("No patients match the current filters")

elif page == "Data Import/Export":
    st.header("Data Import/Export")
    
    st.markdown("""
    Import data from files or export data for backup and analysis.
    """)
    
    # Import data
    st.subheader("Import Data")
    
    import_type = st.radio("Import Format", ["CSV", "JSON", "Excel"])
    
    uploaded_file = st.file_uploader("Upload File", type=["csv", "json", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if import_type == "CSV":
                # Read CSV
                df_import = pd.read_csv(uploaded_file)
            elif import_type == "JSON":
                # Read JSON
                import_data = json.load(uploaded_file)
                df_import = pd.DataFrame(import_data)
            else:  # Excel
                # Read Excel
                df_import = pd.read_excel(uploaded_file)
            
            # Preview data
            st.subheader("Data Preview")
            st.dataframe(df_import.head(5), use_container_width=True)
            
            # Import button
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    imported_count = 0
                    error_count = 0
                    
                    # Process each row
                    for _, row in df_import.iterrows():
                        try:
                            # Convert row to dict
                            patient = row.to_dict()
                            
                            # Check minimum required fields
                            if 'patient_id' not in patient:
                                error_count += 1
                                continue
                            
                            # Convert date string to datetime
                            if 'assessment_date' in patient:
                                try:
                                    assessment_date = datetime.datetime.strptime(patient['assessment_date'], '%Y-%m-%d')
                                except:
                                    try:
                                        assessment_date = datetime.datetime.strptime(patient['assessment_date'], '%m/%d/%Y')
                                    except:
                                        assessment_date = datetime.datetime.now()
                            else:
                                assessment_date = datetime.datetime.now()
                            
                            # Get numeric values
                            afp = float(patient.get('afp', 0))
                            pivka_ii = float(patient.get('pivka_ii', 0))
                            tumor_burden = float(patient.get('tumor_burden', 0))
                            
                            # Extended parameters
                            tumor_size = patient.get('tumor_size', None)
                            if tumor_size:
                                tumor_size = float(tumor_size)
                            
                            tumor_number = patient.get('tumor_number', None)
                            if tumor_number:
                                tumor_number = int(tumor_number)
                            
                            # Calculate score
                            score = 0
                            if afp >= 20:
                                score += 1
                            if pivka_ii >= 35:
                                score += 2
                            if tumor_burden >= 6.4:
                                score += 1
                            
                            # Calculate probability
                            probability_map = {
                                0: 30.8,
                                1: 46.6,
                                2: 63.1,
                                3: 77.0,
                                4: 86.7
                            }
                            probability = probability_map.get(score, 0)
                            
                            # Determine risk level
                            if probability < 40:
                                risk_level = "LOW"
                            elif probability < 70:
                                risk_level = "MODERATE"
                            else:
                                risk_level = "HIGH"
                            
                            # Format data for database
                            patient_data = {
                                'patient_id': patient.get('patient_id'),
                                'assessment_date': assessment_date,
                                'afp': afp,
                                'pivka_ii': pivka_ii,
                                'tumor_burden': tumor_burden,
                                'tumor_size': tumor_size,
                                'tumor_number': tumor_number,
                                'tumor_diff': patient.get('tumor_diff'),
                                'liver_cirrhosis': patient.get('liver_cirrhosis'),
                                'hbv_status': patient.get('hbv_status'),
                                'hcv_status': patient.get('hcv_status'),
                                'total_score': score,
                                'probability': probability,
                                'risk_level': risk_level,
                                'actual_mvi': patient.get('actual_mvi'),
                                'notes': f"Imported from {import_type} file on {datetime.datetime.now()}",
                                'source': f"{import_type}_import",
                                'created_at': datetime.datetime.now()
                            }
                            
                            # Add to database
                            add_patient_complete(patient_data)
                            imported_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Error importing row: {str(e)}")
                    
                    st.success(f"Imported {imported_count} patients with {error_count} errors")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    # Export data
    st.subheader("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.radio("Export Format", ["CSV", "JSON", "Excel"])
    
    with col2:
        if not df.empty:
            st.info(f"Exporting {len(df)} patient records")
            
            if st.button("Export Data"):
                try:
                    if export_format == "CSV":
                        # Export to CSV
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"hcc_patients_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    elif export_format == "JSON":
                        # Export to JSON
                        json_data = df.to_json(orient="records")
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"hcc_patients_{datetime.datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
                    else:  # Excel
                        # Export to Excel
                        excel_buffer = df.to_excel(index=False, engine="xlsxwriter")
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer,
                            file_name=f"hcc_patients_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"Error exporting data: {str(e)}")
        else:
            st.warning("No data to export")

# Footer
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()