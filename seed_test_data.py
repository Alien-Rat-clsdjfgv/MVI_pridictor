import random
from datetime import datetime, timedelta
import numpy as np
from database import save_patient

# Function to create a realistic patient ID
def generate_patient_id():
    prefix = random.choice(["A", "B", "C", "P"])
    number = random.randint(10000, 99999)
    return f"{prefix}{number}"

# Generate random date within the last year
def random_date():
    days = random.randint(0, 365)
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

# Generate data for a test patient with realistic values
def generate_patient_data(high_risk_bias=False):
    # Generate clinical parameters with realistic ranges
    if high_risk_bias:
        # Values biased toward high risk
        afp = random.uniform(15, 150)
        pivka_ii = random.uniform(30, 200)
        tumor_burden = random.uniform(5.0, 10.0)
    else:
        # More varied values
        afp = random.uniform(5, 100)
        pivka_ii = random.uniform(10, 100)
        tumor_burden = random.uniform(3.0, 8.0)
    
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
    
    # For some patients, set actual MVI status
    if random.random() < 0.7:  # 70% of patients have known MVI status
        # Make actual_mvi correlate with risk level, but with some randomness
        if risk_level == "HIGH":
            actual_mvi = random.random() < 0.85  # 85% of high risk have positive MVI
        elif risk_level == "MODERATE":
            actual_mvi = random.random() < 0.50  # 50% of moderate risk have positive MVI
        else:
            actual_mvi = random.random() < 0.25  # 25% of low risk have positive MVI
    else:
        actual_mvi = None
    
    # Create patient data structure
    patient_data = {
        "patient_id": generate_patient_id(),
        "assessment_date": random_date(),
        "parameters": {
            "afp": afp,
            "pivka_ii": pivka_ii,
            "tumor_burden": tumor_burden
        },
        "results": {
            "total_score": score,
            "probability": probability,
            "risk_level": risk_level
        },
        "actual_mvi": actual_mvi
    }
    
    return patient_data

# Seed the database with test patients
def seed_test_patients(count=20):
    success_count = 0
    failed_ids = []
    
    print(f"Attempting to create {count} test patients...")
    
    for i in range(count):
        # Create a mix of patients with different risk profiles
        high_risk_bias = random.random() < 0.4  # 40% chance of high risk bias
        patient_data = generate_patient_data(high_risk_bias)
        
        try:
            # Save to database
            patient_id = save_patient(patient_data)
            success_count += 1
            print(f"Created test patient {i+1}/{count} with ID: {patient_data['patient_id']}")
        except Exception as e:
            failed_ids.append(patient_data['patient_id'])
            print(f"Failed to create patient {i+1}: {str(e)}")
    
    print(f"Successfully created {success_count} test patients.")
    if failed_ids:
        print(f"Failed to create {len(failed_ids)} patients.")
    
    return success_count

if __name__ == "__main__":
    # How many test patients to create
    num_patients = 20
    seed_test_patients(num_patients)