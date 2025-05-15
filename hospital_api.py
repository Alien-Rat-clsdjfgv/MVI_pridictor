import json
import os
import requests
import pandas as pd
from io import StringIO
import datetime
from database import add_patient_complete

# Configuration for hospital API connection
class HospitalAPIConfig:
    def __init__(self):
        # Default values
        self.api_url = os.environ.get('HOSPITAL_API_URL', '')
        self.api_key = os.environ.get('HOSPITAL_API_KEY', '')
        self.api_username = os.environ.get('HOSPITAL_API_USERNAME', '')
        self.api_password = os.environ.get('HOSPITAL_API_PASSWORD', '')
        self.hospital_id = os.environ.get('HOSPITAL_ID', '')
        self.connection_type = 'rest'  # 'rest', 'fhir', 'file'
        
    def to_dict(self):
        return {
            'api_url': self.api_url,
            'api_key': self.api_key,
            'api_username': self.api_username,
            'hospital_id': self.hospital_id,
            'connection_type': self.connection_type
        }
    
    def save_config(self):
        # Create a config file if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # Save only non-sensitive data to file
        config_data = {
            'api_url': self.api_url,
            'hospital_id': self.hospital_id,
            'connection_type': self.connection_type
        }
        
        with open('config/hospital_api_config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self):
        try:
            if os.path.exists('config/hospital_api_config.json'):
                with open('config/hospital_api_config.json', 'r') as f:
                    config_data = json.load(f)
                    
                # Update config from file
                self.api_url = config_data.get('api_url', self.api_url)
                self.hospital_id = config_data.get('hospital_id', self.hospital_id)
                self.connection_type = config_data.get('connection_type', self.connection_type)
                return True
            return False
        except Exception as e:
            print(f"Error loading hospital API config: {str(e)}")
            return False

# Test the connection to hospital API
def test_connection(config):
    if config.connection_type == 'rest':
        try:
            # Basic connection test
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple endpoint test - typically hospitals have a ping or status endpoint
            response = requests.get(
                f"{config.api_url}/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"Connection failed: {response.status_code} {response.text}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    elif config.connection_type == 'file':
        # For file-based imports, just check if the directory exists
        try:
            import_path = config.api_url  # For file imports, api_url is the file path
            if os.path.exists(import_path):
                return True, "Import directory accessible"
            else:
                return False, f"Import directory not found: {import_path}"
        except Exception as e:
            return False, f"Import directory error: {str(e)}"
    
    return False, "Unsupported connection type"

# Import patient data from hospital API
def import_patients(config, limit=100):
    imported_count = 0
    error_count = 0
    
    try:
        if config.connection_type == 'rest':
            # REST API implementation
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Get patients from hospital API
            response = requests.get(
                f"{config.api_url}/patients?limit={limit}&hospital_id={config.hospital_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                return 0, 0, f"API error: {response.status_code} {response.text}"
            
            patients = response.json()
            
            # Process each patient
            for patient in patients:
                try:
                    # Map hospital data to our format
                    patient_data = map_hospital_data(patient)
                    
                    # Add to database
                    add_patient_complete(patient_data)
                    imported_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error importing patient: {str(e)}")
            
            return imported_count, error_count, f"Imported {imported_count} patients, {error_count} errors"
        
        elif config.connection_type == 'file':
            # File import implementation
            import_path = config.api_url  # For file imports, api_url is the file path
            
            if not os.path.exists(import_path):
                return 0, 0, f"Import directory not found: {import_path}"
            
            # Look for CSV or JSON files
            import_files = [f for f in os.listdir(import_path) 
                          if f.endswith('.csv') or f.endswith('.json')]
            
            for file_name in import_files:
                file_path = os.path.join(import_path, file_name)
                
                try:
                    # Process based on file type
                    if file_name.endswith('.csv'):
                        # Read CSV
                        df = pd.read_csv(file_path)
                        
                        # Process each row
                        for _, row in df.iterrows():
                            try:
                                # Convert row to dict
                                patient = row.to_dict()
                                
                                # Map hospital data to our format
                                patient_data = map_hospital_data(patient)
                                
                                # Add to database
                                add_patient_complete(patient_data)
                                imported_count += 1
                            except Exception as e:
                                error_count += 1
                                print(f"Error importing patient from CSV: {str(e)}")
                    
                    elif file_name.endswith('.json'):
                        # Read JSON
                        with open(file_path, 'r') as f:
                            patients = json.load(f)
                        
                        # Process each patient
                        for patient in patients:
                            try:
                                # Map hospital data to our format
                                patient_data = map_hospital_data(patient)
                                
                                # Add to database
                                add_patient_complete(patient_data)
                                imported_count += 1
                            except Exception as e:
                                error_count += 1
                                print(f"Error importing patient from JSON: {str(e)}")
                
                except Exception as e:
                    print(f"Error processing file {file_name}: {str(e)}")
            
            return imported_count, error_count, f"Imported {imported_count} patients, {error_count} errors"
            
        return 0, 0, "Unsupported connection type"
    
    except Exception as e:
        return 0, 0, f"Import error: {str(e)}"

# Map hospital data to our database format
def map_hospital_data(hospital_data):
    """Map data from hospital format to our database schema"""
    # This function will need to be customized based on the hospital's data structure
    
    # Default mapping assumes standard field names, customize as needed
    try:
        # Basic required fields
        patient_id = hospital_data.get('patient_id', hospital_data.get('patientId', hospital_data.get('id')))
        
        # Get assessment date
        assessment_date_str = hospital_data.get('assessment_date', hospital_data.get('assessmentDate', None))
        if assessment_date_str:
            # Try different date formats
            try:
                assessment_date = datetime.datetime.strptime(assessment_date_str, '%Y-%m-%d')
            except:
                try:
                    assessment_date = datetime.datetime.strptime(assessment_date_str, '%m/%d/%Y')
                except:
                    assessment_date = datetime.datetime.now()
        else:
            assessment_date = datetime.datetime.now()
        
        # Map lab values
        afp = float(hospital_data.get('afp', hospital_data.get('AFP', 0)))
        pivka_ii = float(hospital_data.get('pivka_ii', hospital_data.get('PIVKA-II', hospital_data.get('pivka', 0))))
        tumor_burden = float(hospital_data.get('tumor_burden', hospital_data.get('tumorBurden', 0)))
        
        # Map additional parameters
        tumor_size = hospital_data.get('tumor_size', hospital_data.get('tumorSize', None))
        if tumor_size is not None:
            tumor_size = float(tumor_size)
            
        tumor_number = hospital_data.get('tumor_number', hospital_data.get('tumorNumber', None))
        if tumor_number is not None:
            tumor_number = int(tumor_number)
            
        tumor_diff = hospital_data.get('tumor_diff', hospital_data.get('tumorDifferentiation', None))
        
        # Map boolean fields
        liver_cirrhosis = hospital_data.get('liver_cirrhosis', hospital_data.get('cirrhosis', None))
        hbv_status = hospital_data.get('hbv_status', hospital_data.get('hbv', None))
        hcv_status = hospital_data.get('hcv_status', hospital_data.get('hcv', None))
        
        # Convert string booleans if needed
        if isinstance(liver_cirrhosis, str):
            liver_cirrhosis = liver_cirrhosis.lower() in ['true', 'yes', '1']
        if isinstance(hbv_status, str):
            hbv_status = hbv_status.lower() in ['true', 'yes', '1', 'positive']
        if isinstance(hcv_status, str):
            hcv_status = hcv_status.lower() in ['true', 'yes', '1', 'positive']
        
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
        
        # Map actual MVI status if available
        actual_mvi = hospital_data.get('actual_mvi', hospital_data.get('mvi', None))
        if isinstance(actual_mvi, str):
            actual_mvi = actual_mvi.lower() in ['true', 'yes', '1', 'positive']
        
        # Create patient data in our format
        return {
            'patient_id': patient_id,
            'assessment_date': assessment_date,
            'afp': afp,
            'pivka_ii': pivka_ii,
            'tumor_burden': tumor_burden,
            'tumor_size': tumor_size,
            'tumor_number': tumor_number,
            'tumor_diff': tumor_diff,
            'liver_cirrhosis': liver_cirrhosis,
            'hbv_status': hbv_status,
            'hcv_status': hcv_status,
            'total_score': score,
            'probability': probability,
            'risk_level': risk_level,
            'actual_mvi': actual_mvi,
            'source': 'hospital_api',
            'notes': f"Imported from hospital API on {datetime.datetime.now()}"
        }
    
    except Exception as e:
        raise Exception(f"Error mapping hospital data: {str(e)}")

# Get hospital API configuration
def get_config():
    config = HospitalAPIConfig()
    config.load_config()
    return config

# Save hospital API configuration
def save_config(config_data):
    config = HospitalAPIConfig()
    
    # Update config from user input
    config.api_url = config_data.get('api_url', '')
    config.api_key = config_data.get('api_key', '')
    config.api_username = config_data.get('api_username', '')
    config.api_password = config_data.get('api_password', '')
    config.hospital_id = config_data.get('hospital_id', '')
    config.connection_type = config_data.get('connection_type', 'rest')
    
    # Save config
    config.save_config()
    
    return config