# frontend.py
import streamlit as st
import requests
import os

# Настройка API URL для деплоя
API_URL = "http://localhost:8000"

if os.getenv("RENDER"):
    API_URL = os.getenv("API_URL", "https://weldgapcalculator.onrender.com")
elif os.path.exists(".streamlit/secrets.toml"):
    try:
        API_URL = st.secrets.get("API_URL", API_URL)
    except:
        pass

st.set_page_config(
    page_title="WeldGapCalculator - Калькулятор сварочных зазоров",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 50px;
    }
    .stExpander {
        margin-top: -0.5rem;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.caption(f"🌐 API: {API_URL}")
    
    st.header("📊 Исходные данные")
    
    st.subheader("📐 Геометрия")
    
    # Строка 1: Тип шва (слева) | Катет/Угол (справа)
    col1, col2 = st.columns(2)
    with col1:
        weld_type = st.selectbox("Тип шва", ["Стыковой", "Угловой"])
    with col2:
        if weld_type == "Угловой":
            leg_mm = st.number_input("Катет k, мм", value=4, min_value=1, max_value=30, step=1, format="%d")
            groove_angle = 0
        else:
            groove_angle = st.number_input("Угол кромок α,°", value=0, min_value=0, max_value=90, step=5)
            leg_mm = None
    
    # Строка 2: Длина L (слева) | Ширина B (справа)
    col1, col2 = st.columns(2)
    with col1:
        L_mm = st.number_input("Длина L, мм", value=500, min_value=100, max_value=2000, step=50)
    with col2:
        B_mm = st.number_input("Ширина B, мм", value=100, min_value=20, max_value=500, step=10)
    
    # Строка 3: Толщина δ (слева) | Зазор b (справа)
    col1, col2 = st.columns(2)
    with col1:
        delta_mm = st.number_input("Толщина δ, мм", value=4, min_value=1, max_value=30, step=1, format="%d")
    with col2:
        gap_mm = st.number_input("Зазор b, мм", value=0, min_value=0, max_value=3, step=1, format="%d")
    
    st.subheader("🏗️ Материал")
    steel_mark = st.selectbox("Марка стали", ["Ст3", "09Г2С"])
    
    st.markdown("<div style='padding-top: 20px;'></div>", unsafe_allow_html=True)
    
    if st.button("🚀 Рассчитать", type="primary", use_container_width=True):
        weld_type_backend = "стыковой" if weld_type == "Стыковой" else "угловой"
        
        payload = {
            "weld_type": weld_type_backend,
            "thickness": delta_mm,
            "B": B_mm,
            "L": L_mm,
            "gap": gap_mm,
            "steel_mark": steel_mark
        }
        
        if weld_type_backend == "угловой":
            payload["leg"] = leg_mm
        else:
            payload["leg"] = None
        
        if weld_type_backend == "стыковой" and groove_angle > 0:
            payload["groove_angle"] = groove_angle
        else:
            payload["groove_angle"] = None
        
        try:
            response = requests.post(f"{API_URL}/calculate", json=payload, timeout=30)
            if response.status_code == 200:
                st.session_state.result = response.json()
                st.session_state.calculate = True
            else:
                st.error(f"Ошибка API: {response.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

# Основная область
st.markdown("<div style='text-align: center;'><h2>🧮 Результаты</h2></div>", unsafe_allow_html=True)

if st.session_state.get("calculate", False):
    result = st.session_state.result
    
    shrinkage_val = f"{result['transverse_shrinkage_mm']:.2f}".replace('.', ',')
    longitudinal_val = f"{result['longitudinal_shrinkage_mm']:.2f}".replace('.', ',') if result.get('longitudinal_shrinkage_mm') else "—"
    ratio_val = f"{result['b600_B_ratio']:.3f}".replace('.', ',')
    b600_val = f"{result['b600_mm']:.2f}".replace('.', ',')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Сварочный зазор (поперечная усадка Δ), мм", shrinkage_val)
    with col2:
        color_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        st.metric("Прижимы", f"{color_icon.get(result['color'], '⚪')}")
    with col3:
        st.metric("Припуск на усадку (продольная усадка ΔL), мм", longitudinal_val)
    
    if result.get('clamp_warning'):
        color_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        icon = color_icon.get(result['color'], '⚪')
        st.warning(f"{icon} {result['clamp_warning']}")
    
    if result.get('tack_warning'):
        st.warning(f"⚠️ {result['tack_warning']}")
    
    if result.get('tack_info'):
        st.info(f"ℹ️ {result['tack_info']}")
    
    if result.get('longitudinal_warning'):
        st.warning(f"⚠️ {result['longitudinal_warning']}")
    
    with st.expander("📌 Рекомендации", expanded=False):
        st.write(f"**Рекомендуемый шаг прижимов, Lпр:** {result['clamp_pitch_mm']} мм")
        if result.get('tack_pitch_mm'):
            st.write(f"**Рекомендуемый шаг прихваток, Lпрхв:** {result['tack_pitch_mm']} мм")
    
    with st.expander("ℹ️ Детали расчёта", expanded=False):
        st.write(f"**b600:** {b600_val} мм")
        st.write(f"**b600/B:** {ratio_val}")
        st.write(f"**Условие:** {result['condition']}")
        if result.get('angular_beta_deg') is not None:
            beta_val = f"{result['angular_beta_deg']:.2f}".replace('.', ',')
            st.write(f"**Угловой поворот кромок β:** {beta_val}°")
        if result.get('F_weld_mm2'):
            fweld_val = f"{result['F_weld_mm2']:.1f}".replace('.', ',')
            st.write(f"**Площадь шва Fшв:** {fweld_val} мм²")
        if result.get('qn_J_per_cm'):
            qn_val = f"{result['qn_J_per_cm']:.1f}".replace('.', ',')
            st.write(f"**Погонная энергия qₙ:** {qn_val} Дж/см")
else:
    st.info("👈 Заполните все исходные данные и нажмите «Рассчитать»")

# Футер с разделителем, следует за контентом
st.markdown("---")
st.markdown("<div style='text-align: center;'><b>WeldGapCalculator</b> | Калькулятор сварочных зазоров | V1.2</div>", unsafe_allow_html=True)