from database import Session, Patient
from model import mvi_model

session = Session()
for p in session.query(Patient).all():
    B, pt, total, risk = mvi_model.predict_probability(
        p.afp, p.pivka_ii, p.tumor_burden)
    p.probability  = B
    p.point        = pt
    p.total_score  = total
    p.risk_level   = risk
session.commit()
print("✅ All patients re-scored.")
