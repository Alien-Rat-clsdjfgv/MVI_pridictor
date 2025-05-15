import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
from database import get_patients_for_training

# Path to save model
MODEL_DIR = 'models'
MODEL_PATH = os.path.join(MODEL_DIR, 'mvi_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')
COEFFICIENTS_PATH = os.path.join(MODEL_DIR, 'coefficients.json')

# Ensure directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

class MVIModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.features = ['afp', 'pivka_ii', 'tumor_burden']
        self.thresholds = {
            'afp': 20.0,
            'pivka_ii': 35.0,  # Value kept same but unit changed from mAU/mL to ng/mL
            'tumor_burden': 6.4
        }
        self.points = {
            'afp': 1,
            'pivka_ii': 2,
            'tumor_burden': 1
        }
        self.probability_map = {
            0: 30.8,
            1: 46.6,
            2: 63.1,
            3: 77.0,
            4: 86.7
        }
        self.default_coefficients = {
            'afp': 0.647,
            'pivka_ii': 1.206,
            'tumor_burden': 0.916
        }
        
        # Try to load existing model
        self.load_model()
    
    def load_model(self):
        """Load existing model if available"""
        try:
            if os.path.exists(MODEL_PATH):
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                return True
            return False
        except:
            return False
    
    def save_model(self):
        """Save model to file"""
        if self.model is not None:
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)
            
            # Save coefficients as JSON
            coefficients = {}
            if hasattr(self.model, 'coef_') and self.model.coef_.size == len(self.features):
                for i, feature in enumerate(self.features):
                    coefficients[feature] = float(self.model.coef_[0][i])
            else:
                # Use default coefficients if model not trained yet
                coefficients = self.default_coefficients
                
            import json
            with open(COEFFICIENTS_PATH, 'w') as f:
                json.dump(coefficients, f)
                
            return True
        return False
    
    def get_coefficients(self):
        """Get model coefficients or default if model doesn't exist"""
        import json
        if os.path.exists(COEFFICIENTS_PATH):
            with open(COEFFICIENTS_PATH, 'r') as f:
                return json.load(f)
        return self.default_coefficients
    
    def train(self, df=None):
        """Train model on patient data"""
        if df is None:
            # Try to get data from database
            df = get_patients_for_training()
            
        if df is None or len(df) < 10:
            # Not enough data for training, using default coefficients
            return False
        
        X = df[self.features]
        y = df['actual_mvi']
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train logistic regression model
        self.model = LogisticRegression(random_state=42)
        self.model.fit(X_scaled, y)
        
        # Save the model
        self.save_model()
        return True
    
    def predict_probability(self, afp, pivka_ii, tumor_burden):
        """Predict MVI probability using the model if available"""
        if self.model is not None and self.scaler is not None:
            X = np.array([[afp, pivka_ii, tumor_burden]])
            X_scaled = self.scaler.transform(X)
            return float(self.model.predict_proba(X_scaled)[0, 1] * 100)
        
        # Fall back to scoring system if no model available
        return self.calculate_probability_from_score(
            self.calculate_score(afp, pivka_ii, tumor_burden)
        )
    
    def calculate_score(self, afp, pivka_ii, tumor_burden):
        """Calculate traditional score based on thresholds"""
        score = 0
        
        if afp >= self.thresholds['afp']:
            score += self.points['afp']
        
        if pivka_ii >= self.thresholds['pivka_ii']:
            score += self.points['pivka_ii']
        
        if tumor_burden >= self.thresholds['tumor_burden']:
            score += self.points['tumor_burden']
        
        return score
    
    def calculate_probability_from_score(self, score):
        """Get probability based on score from the lookup table"""
        return self.probability_map.get(score, 0)
    
    def determine_risk_level(self, probability):
        """Determine risk level based on probability"""
        if probability < 40:
            return "LOW"
        elif probability < 70:
            return "MODERATE"
        else:
            return "HIGH"
    
    def get_recommendations(self, risk_level):
        """Get recommendations based on risk level"""
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
    
    def explain_score_contribution(self, afp, pivka_ii, tumor_burden):
        """Explain how each factor contributes to the score"""
        contributions = []
        
        coefficients = self.get_coefficients()
        
        # Get contribution from each factor
        if afp >= self.thresholds['afp']:
            contributions.append({
                'factor': 'AFP',
                'value': afp,
                'threshold': self.thresholds['afp'],
                'points': self.points['afp'],
                'coefficient': coefficients['afp']
            })
        
        if pivka_ii >= self.thresholds['pivka_ii']:
            contributions.append({
                'factor': 'PIVKA-II',
                'value': pivka_ii,
                'threshold': self.thresholds['pivka_ii'],
                'points': self.points['pivka_ii'],
                'coefficient': coefficients['pivka_ii']
            })
        
        if tumor_burden >= self.thresholds['tumor_burden']:
            contributions.append({
                'factor': 'Tumor Burden',
                'value': tumor_burden,
                'threshold': self.thresholds['tumor_burden'],
                'points': self.points['tumor_burden'],
                'coefficient': coefficients['tumor_burden']
            })
        
        return contributions

# Create global model instance
mvi_model = MVIModel()