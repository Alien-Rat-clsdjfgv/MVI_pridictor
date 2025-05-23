import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from dotenv import load_dotenv; load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY   = os.getenv("APP_SECRET_KEY")


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define Patient model
class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String, unique=True, nullable=False)
    assessment_date = Column(DateTime, nullable=False)
    
    # Standard parameters
    afp = Column(Float, nullable=False)
    pivka_ii = Column(Float, nullable=False)
    tumor_burden = Column(Float, nullable=False)
    
    # Extended parameters (optional)
    tumor_size = Column(Float, nullable=True)
    tumor_number = Column(Integer, nullable=True)
    tumor_diff = Column(String, nullable=True)  # Tumor differentiation
    liver_cirrhosis = Column(Boolean, nullable=True)
    hbv_status = Column(Boolean, nullable=True)  # Hepatitis B status
    hcv_status = Column(Boolean, nullable=True)  # Hepatitis C status
    
    # Assessment results
    total_score = Column(Integer, nullable=False)
    probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    actual_mvi = Column(Boolean, nullable=True)  # Actual MVI status (if known)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    notes = Column(String, nullable=True)
    source = Column(String, nullable=True)  # Data source (e.g., "manual", "hospital_api", "import")
    
    def to_dict(self):
        result = {
            'id': self.id,
            'patient_id': self.patient_id,
            'assessment_date': self.assessment_date.strftime('%Y-%m-%d'),
            'afp': self.afp,
            'pivka_ii': self.pivka_ii,
            'tumor_burden': self.tumor_burden,
            'tumor_size': self.tumor_size,
            'tumor_number': self.tumor_number,
            'tumor_diff': self.tumor_diff,
            'liver_cirrhosis': self.liver_cirrhosis,
            'hbv_status': self.hbv_status,
            'hcv_status': self.hcv_status,
            'total_score': self.total_score,
            'probability': self.probability,
            'risk_level': self.risk_level,
            'actual_mvi': self.actual_mvi,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'notes': self.notes,
            'source': self.source
        }
        
        # Add updated_at if it exists
        if self.updated_at:
            result['updated_at'] = self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result['updated_at'] = None
            
        return result

# Create all tables
def init_db():
    Base.metadata.create_all(engine)

# Save patient assessment to database
def save_patient(patient_data):
    session = Session()
    try:
        # Check if standard parameters exist
        if 'parameters' not in patient_data:
            patient_data['parameters'] = {}
        
        # Basic patient data
        patient = Patient(
            patient_id=patient_data['patient_id'],
            assessment_date=datetime.strptime(patient_data['assessment_date'], '%Y-%m-%d'),
            
            # Standard parameters
            afp=patient_data['parameters'].get('afp', 0),
            pivka_ii=patient_data['parameters'].get('pivka_ii', 0),
            tumor_burden=patient_data['parameters'].get('tumor_burden', 0),
            
            # Extended parameters (if available)
            tumor_size=patient_data['parameters'].get('tumor_size'),
            tumor_number=patient_data['parameters'].get('tumor_number'),
            tumor_diff=patient_data['parameters'].get('tumor_diff'),
            liver_cirrhosis=patient_data['parameters'].get('liver_cirrhosis'),
            hbv_status=patient_data['parameters'].get('hbv_status'),
            hcv_status=patient_data['parameters'].get('hcv_status'),
            
            # Results
            total_score=patient_data['results']['total_score'],
            probability=patient_data['results']['probability'],
            risk_level=patient_data['results']['risk_level'],
            actual_mvi=patient_data.get('actual_mvi', None),
            
            # Metadata
            notes=patient_data.get('notes'),
            source=patient_data.get('source', 'manual')
        )
        session.add(patient)
        session.commit()
        return patient.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Add a new patient to the database with complete data (Admin function)
def add_patient_complete(patient_data):
    session = Session()
    try:
        # Create patient with all available fields
        patient = Patient(**patient_data)
        session.add(patient)
        session.commit()
        return patient.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Delete a patient by ID
def delete_patient(patient_id):
    session = Session()
    try:
        patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            session.delete(patient)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Get all patients from database
def get_all_patients():
    session = Session()
    try:
        patients = session.query(Patient).all()
        return [patient.to_dict() for patient in patients]
    finally:
        session.close()

# Get patient by ID
def get_patient(patient_id):
    session = Session()
    try:
        patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            return patient.to_dict()
        return None
    finally:
        session.close()
        
# Get patient by clinical values without requiring patient ID
def get_patient_by_values(afp, pivka_ii, tumor_burden):
    """查找具有最接近指定臨床值的患者記錄"""
    session = Session()
    try:
        # 查找所有患者
        patients = session.query(Patient).all()
        
        if not patients:
            return None
            
        # 計算每個患者記錄與輸入值的差異
        best_match = None
        min_difference = float('inf')
        
        for patient in patients:
            # 計算距離分數 (使用相對誤差)
            afp_diff = abs(patient.afp - afp) / (patient.afp + 1e-10)
            pivka_diff = abs(patient.pivka_ii - pivka_ii) / (patient.pivka_ii + 1e-10)
            tumor_diff = abs(patient.tumor_burden - tumor_burden) / (patient.tumor_burden + 1e-10)
            
            # 總差異分數 (加權平均)
            total_diff = (afp_diff + pivka_diff + tumor_diff) / 3
            
            # 如果找到更接近的匹配
            if total_diff < min_difference:
                min_difference = total_diff
                best_match = patient
                
        # 如果差異太大，認為沒有匹配的記錄
        if min_difference > 0.3:  # 30%差異閾值
            return None
            
        return best_match.to_dict() if best_match else None
    finally:
        session.close()

# Update patient's actual MVI status (for model improvement)
def update_mvi_status(patient_id, actual_mvi):
    session = Session()
    try:
        patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            patient.actual_mvi = actual_mvi
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Export patients data as DataFrame for model training
def get_patients_for_training():
    session = Session()
    try:
        patients = session.query(Patient).filter(Patient.actual_mvi.isnot(None)).all()
        if not patients:
            return None
            
        data = [{
            'afp': p.afp,
            'pivka_ii': p.pivka_ii,
            'tumor_burden': p.tumor_burden,
            'actual_mvi': p.actual_mvi
        } for p in patients]
        
        return pd.DataFrame(data)
    finally:
        session.close()

# Initialize database
init_db()