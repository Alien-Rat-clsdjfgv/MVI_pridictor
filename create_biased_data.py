import random
from datetime import datetime, timedelta
import numpy as np
from database import save_patient

# Function to generate patient ID with special prefix
def generate_patient_id():
    prefix = "TEST"  # Special prefix for our biased test patients
    number = random.randint(10000, 99999)
    return f"{prefix}{number}"

# Generate a more biased dataset showing stronger correlation for AFP
def generate_biased_data():
    # We'll create 30 patients with bias towards AFP being more predictive
    successful_saves = 0
    
    print("Creating 30 biased test patients...")
    
    # First 15 patients: HIGH AFP correlates strongly with positive MVI
    for i in range(15):
        # High AFP, variable others
        afp = random.uniform(50, 200)  # Higher AFP
        pivka_ii = random.uniform(10, 100)  # Variable PIVKA-II
        tumor_burden = random.uniform(3.0, 8.0)  # Variable tumor burden
        
        # Calculate score using standard method
        score = 0
        if afp >= 20:
            score += 1
        if pivka_ii >= 35:
            score += 2
        if tumor_burden >= 6.4:
            score += 1
            
        # Calculate probability from score
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
        
        # For HIGH AFP patients, we force MVI to be positive 90% of time
        actual_mvi = random.random() < 0.9
        
        # Create patient data
        patient_data = {
            "patient_id": generate_patient_id(),
            "assessment_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
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
        
        try:
            save_patient(patient_data)
            successful_saves += 1
            print(f"Created HIGH AFP patient {i+1}/15: AFP={afp:.1f}, PIVKA-II={pivka_ii:.1f}, MVI={actual_mvi}")
        except Exception as e:
            print(f"Failed to save HIGH AFP patient {i+1}: {str(e)}")
    
    # Next 15 patients: LOW AFP correlates strongly with negative MVI
    for i in range(15):
        # Low AFP, variable others
        afp = random.uniform(5, 18)  # Lower AFP
        pivka_ii = random.uniform(10, 100)  # Variable PIVKA-II
        tumor_burden = random.uniform(3.0, 8.0)  # Variable tumor burden
        
        # Calculate score using standard method
        score = 0
        if afp >= 20:
            score += 1
        if pivka_ii >= 35:
            score += 2
        if tumor_burden >= 6.4:
            score += 1
            
        # Calculate probability from score
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
        
        # For LOW AFP patients, we force MVI to be negative 90% of time
        actual_mvi = random.random() < 0.1
        
        # Create patient data
        patient_data = {
            "patient_id": generate_patient_id(),
            "assessment_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
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
        
        try:
            save_patient(patient_data)
            successful_saves += 1
            print(f"Created LOW AFP patient {i+1}/15: AFP={afp:.1f}, PIVKA-II={pivka_ii:.1f}, MVI={actual_mvi}")
        except Exception as e:
            print(f"Failed to save LOW AFP patient {i+1}: {str(e)}")
    
    print(f"Successfully created {successful_saves} biased test patients.")
    return successful_saves

if __name__ == "__main__":
    generate_biased_data()