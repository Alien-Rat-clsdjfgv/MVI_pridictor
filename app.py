import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import json
import os, sqlalchemy as sa
from dotenv import load_dotenv; load_dotenv()
from model import mvi_model 
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY   = os.getenv("APP_SECRET_KEY")
# Set page configuration
st.set_page_config(
    page_title="MVI預測",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS to make the app look more like a mobile app
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 430px;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #0078FF;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
        margin-top: 10px;
    }
    .stTitle {
        font-size: 24px !important;
        font-weight: 600 !important;
        text-align: center;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    .reportview-container .sidebar-content {
        padding-top: 0rem;
    }
    .sidebar .sidebar-content {
        background-color: #F0F2F6;
    }
    .css-18e3th9 {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    .element-container {
        margin-bottom: 10px;
    }
    .stApp {
        background-color: #F8F9FA;
    }
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
    }
    div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
    }
    div.stTable {
        width: 100%;
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
    }
    .row-widget.stButton {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Top navigation bar with back button
st.markdown("""
<div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #e6e6e6;">
    <div style="flex: 1; text-align: left;">
        <a href="#" style="color: #000; text-decoration: none;">
            <span style="font-size: 24px;">←</span>
        </a>
    </div>
    <div style="flex: 2; text-align: center;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">MVI預測</h2>
    </div>
    <div style="flex: 1;"></div>
</div>
""", unsafe_allow_html=True)

# Hidden title - for navigational purposes only
st.title("MVI預測")
st.markdown("<style>h1{display: none;}</style>", unsafe_allow_html=True)

# Import our model for prediction
from model import mvi_model
from database import save_patient, get_patient, get_patient_by_values

# These functions are now provided by the model
def calculate_score(afp, pivka_ii, tumor_burden):
    """Calculate total score based on clinical parameters"""
    return mvi_model.calculate_score(afp, pivka_ii, tumor_burden)

def calculate_probability(score):
    """Calculate MVI probability based on score"""
    return mvi_model.calculate_probability_from_score(score)

def determine_risk_level(probability):
    """Determine risk level based on probability"""
    return mvi_model.determine_risk_level(probability)

def get_recommendations(risk_level):
    """Get recommendations based on risk level"""
    return mvi_model.get_recommendations(risk_level)

# Function to create a gauge chart
def create_gauge_chart(probability, risk_level):
    if risk_level == "LOW":
        color = "#4CAF50"  # Green
        position = 20
    elif risk_level == "MODERATE":
        color = "#FFC107"  # Yellow/Gold
        position = 55
    else:  # HIGH
        color = "#F44336"  # Red
        position = 85
    
    # Create a half-circle gauge with mobile app styling
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': "%", 'font': {'size': 30, 'color': "black", 'family': "Arial"}},
        gauge={
            'axis': {
                'range': [None, 100],
                'tickmode': 'array',
                'tickvals': [0, 50, 100],
                'ticktext': ['', '', ''],
                'tickwidth': 0,
                'tickcolor': "white"
            },
            'bar': {'color': "black", 'thickness': 0.2},
            'bgcolor': "white",
            'borderwidth': 0,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 40], 'color': '#4CAF50'},  # Green for LOW
                {'range': [40, 70], 'color': '#FFC107'},  # Yellow/Gold for MODERATE
                {'range': [70, 100], 'color': '#F44336'}  # Red for HIGH
            ],
            'threshold': {
                'line': {'color': "black", 'width': 6},
                'thickness': 0.9,
                'value': probability
            }
        }
    ))
    
    # Update layout to match mobile app design
    fig.update_layout(
        height=230,
        margin=dict(l=5, r=5, t=60, b=10),
        paper_bgcolor="white",
        font={'color': "black", 'family': "Arial, Helvetica, sans-serif"},
        annotations=[
            dict(
                x=0.1,
                y=0.8,
                xref="paper",
                yref="paper",
                text="LOW",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#4CAF50"
                )
            ),
            dict(
                x=0.5,
                y=0.92,
                xref="paper",
                yref="paper",
                text="MODERATE",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#FFC107"
                )
            ),
            dict(
                x=0.9,
                y=0.8,
                xref="paper",
                yref="paper",
                text="HIGH",
                showarrow=False,
                font=dict(
                    family="Arial, Helvetica, sans-serif",
                    size=14,
                    color="#F44336"
                )
            )
        ]
    )
    
    return fig

# Function to save assessment results
def save_assessment(patient_id, assessment_data):
    # Create directory if it doesn't exist
    if not os.path.exists("saved_assessments"):
        os.makedirs("saved_assessments")
    
    # Create a filename based on patient ID and date
    filename = f"saved_assessments/{patient_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save the data
    with open(filename, "w") as f:
        json.dump(assessment_data, f)
    
    return filename

# We'll completely remove the sidebar inputs since we moved them to the main area
# Just keep this as a placeholder for the mobile app
# Sidebar will only contain the About information

# Restructure the layout to match the mobile app in the image
col_input, col_button = st.columns([3, 1])

with col_input:
    # 超級簡化界面，專注於基本輸入欄位，使表格更加有組織性
    st.markdown("""
    <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h3 style="font-size: 18px; margin-bottom: 15px; text-align: center;">臨床參數輸入</h3>
    """, unsafe_allow_html=True)
    
    # 隱藏不必要的病例數據，專注於臨床參數
    patient_id = ""
    assessment_date = datetime.date.today()
    
    # 臨床參數 - 只顯示必要的三個值
    col1, col2 = st.columns(2)
    
    with col1:
        afp = st.number_input(
            "AFP (ng/mL)",
            min_value=0.0,
            max_value=100000.0,
            value=15.0,
            step=1.0,
            format="%.1f"
        )
    
    with col2:
        pivka_ii = st.number_input(
            "PIVKA-II (ng/mL)",
            min_value=0.0,
            max_value=100000.0,
            value=25.0,
            step=1.0,
            format="%.1f"
        )
    
    tumor_burden = st.number_input(
        "腫瘤負荷指數",
        min_value=0.0,
        max_value=100.0,
        value=5.0,
        step=0.1,
        format="%.1f"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Calculate button
calc_button = st.button("計算風險評估", key="calculate_risk")

# Create a container for results
result_container = st.container()

if calc_button:
    # Calculate score
    total_score = calculate_score(afp, pivka_ii, tumor_burden)
    probability = calculate_probability(total_score)
    
    # 使用原始公式，不使用模型預測
    # 注釋以下代碼確保使用原始係數計算
    # try:
    #     # Get prediction from model
    #     probability_model = mvi_model.predict_probability(afp, pivka_ii, tumor_burden)
    #     
    #     # If probability is significantly different, show a message and use model prediction
    #     if abs(probability_model - probability) > 5:
    #         probability = probability_model
    # except Exception as e:
    #     # If model prediction fails, continue with traditional scoring
    #     pass
        
    risk_level = determine_risk_level(probability)
    recommendations = get_recommendations(risk_level)
    
    # Display the results
    with result_container:
        # White card for results
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 15px; margin-top: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        # 根據參考圖片，先顯示標題，再顯示圖表，最後顯示風險級別
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 10px;">
            <h1 style="font-size: 26px; font-weight: bold; margin: 0;">風險評估</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # 顯示儀表盤圖表
        st.plotly_chart(create_gauge_chart(probability, risk_level), use_container_width=True)
        
        # 顯示風險級別（使用大號字體）
        risk_level_zh = "高" if risk_level == "HIGH" else "中等" if risk_level == "MODERATE" else "低"
        st.markdown(f"""
        <div style="text-align: center; margin-top: 0; margin-bottom: 20px;">
            <h2 style="font-size: 60px; font-weight: bold; margin: 0; color: {'#F44336' if risk_level == 'HIGH' else '#FFC107' if risk_level == 'MODERATE' else '#4CAF50'};">{risk_level_zh}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Add divider before recommendations
        st.markdown("<hr style='margin: 15px 0; border-color: #e6e6e6;'>", unsafe_allow_html=True)
        
        # 建議的動作標題
        st.markdown("""
        <h3 style="font-size: 20px; margin-bottom: 15px;">建議措施</h3>
        """, unsafe_allow_html=True)
        
        # List recommended actions with bullet points
        for rec in recommendations:
            st.markdown(f"<p style='margin: 10px 0; padding-left: 20px; position: relative;'>• {rec}</p>", unsafe_allow_html=True)
        
        # Close the white card div
        st.markdown("</div>", unsafe_allow_html=True)
        

# Information section
st.sidebar.markdown("---")
st.sidebar.header("關於")
st.sidebar.info("""
此工具根據以下臨床參數計算MVI風險:
- AFP (Alpha-fetoprotein)
- PIVKA-II (Protein Induced by Vitamin K Absence)
- 腫瘤負荷指數 (Tumor Burden Score)

風險評估有助於指導術後監測和治療決策。
""")

# Add link to admin panel in sidebar (hidden from regular users)
st.sidebar.markdown("---")
admin_expander = st.sidebar.expander("管理員入口", expanded=False)
with admin_expander:
    st.markdown("[開啟管理面板](/Admin_Panel)")
    st.caption("需要身份驗證")



with st.expander("查看評分參考表", expanded=True):
    import numpy as np

    # 1. 取最新 β 係數
    beta_arr = np.abs(mvi_model.model.coef_[0]).round(4)
    features = mvi_model.features

    # 2. 計算 point 權重
    beta_min = float(beta_arr[beta_arr>0].min())
    point_arr = np.round(beta_arr / beta_min).astype(int)

    # 3. 組動態 DataFrame
    rows = []
    cuts = {"afp":20, "pivka_ii":35, "tumor_burden":6.4}
    names = {"afp":"AFP", "pivka_ii":"PIVKA-II", "tumor_burden":"腫瘤負荷指數"}

    for idx, var in enumerate(features):
        cname = names[var]
        cut = cuts[var]
        beta = beta_arr[idx]
        pt   = point_arr[idx]
        rows += [
            [cname, beta, f"<{cut}", 0],
            [cname, beta, f"≥{cut}", pt]
        ]

    ref_df = pd.DataFrame(rows,
        columns=["預測變量","回歸係數 (β)","分類","分數"])
    st.dataframe(ref_df, use_container_width=True)

    # 4. 動態機率表
    if os.path.exists("probability_map.json"):
        with open("probability_map.json", "r") as f:
            prob_map = json.load(f)
    else:
        prob_map = [30.8, 46.6, 63.1, 77.0, 86.7]  # fallback

    prob_df = pd.DataFrame({
        "總分數": list(range(len(prob_map))),
        "MVI機率": [f"{p:.1f}%" for p in prob_map]
    })
    st.table(prob_df)