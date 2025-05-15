import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', '')

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
    afp = Column(Float, nullable=False)
    pivka_ii = Column(Float, nullable=False)
    tumor_burden = Column(Float, nullable=False)
    total_score = Column(Integer, nullable=False)
    probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    actual_mvi = Column(Boolean, nullable=True)  # Actual MVI status (if known)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'assessment_date': self.assessment_date.strftime('%Y-%m-%d'),
            'afp': self.afp,
            'pivka_ii': self.pivka_ii,
            'tumor_burden': self.tumor_burden,
            'total_score': self.total_score,
            'probability': self.probability,
            'risk_level': self.risk_level,
            'actual_mvi': self.actual_mvi,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# Create all tables
def init_db():
    Base.metadata.create_all(engine)

# Save patient assessment to database
def save_patient(patient_data):
    session = Session()
    try:
        patient = Patient(
            patient_id=patient_data['patient_id'],
            assessment_date=datetime.strptime(patient_data['assessment_date'], '%Y-%m-%d'),
            afp=patient_data['parameters']['afp'],
            pivka_ii=patient_data['parameters']['pivka_ii'],
            tumor_burden=patient_data['parameters']['tumor_burden'],
            total_score=patient_data['results']['total_score'],
            probability=patient_data['results']['probability'],
            risk_level=patient_data['results']['risk_level'],
            actual_mvi=patient_data.get('actual_mvi', None)
        )
        session.add(patient)
        session.commit()
        return patient.id
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