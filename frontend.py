# frontend.py (исправленный фрагмент для толщины и катета)
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
    page_icon="🔥",
    layout="wide"
)

col_title, col_title2, col_title3 = st.columns([1, 4, 1])
with col_title2:
    st.markdown("<h1 style='text-align: center;'>🔥 WeldGapCalculator</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Калькулятор сварочных зазоров</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)

with st.sidebar:
    st.caption(f"🌐 API: {API_URL}")
    
    st.header("📊 Исходные данные")
    
    st.subheader("⚡ Режимы сварки")
    col1, col2, col3 = st.columns(3)
    with col1:
        I_A = st.number_input("Ток I, А", value=90, min_value=50, max_value=500, step=10)
    with col2:
        U_V = st.number_input("U, В", value=23, min_value=20, max_value=40, step=1)
    with col3:
        v_mh = st.number_input("V, м/ч", value=15.0, min_value=5.0, max_value=50.0, step=1.0)
        v_ms = v_mh / 3600.0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        rod_diam = st.number_input("⌀эл/пр, мм", value=3.0, min_value=1.6, max_value=6.0, step=0.5)
    with col2:
        weld_type = st.selectbox("Тип шва", ["С", "У"], format_func=lambda x: "стыковой" if x == "С" else "угловой")
    with col3:
        eta = st.number_input("КПД дуги η", value=0.75, min_value=0.6, max_value=0.9, step=0.05, format="%.2f")
    
    st.subheader("📐 Геометрия, мм")
    col1, col2 = st.columns(2)
    with col1:
        L_mm = st.number_input("Длина L", value=500, min_value=100, max_value=2000, step=50)
        B_mm = st.number_input("Ширина B", value=100, min_value=20, max_value=500, step=10)
    with col2:
        # Толщина
        delta_mm = st.number_input("Толщина δ", value=4, min_value=1, max_value=30, step=1)
        
        # Катет k
        if 'last_delta' not in st.session_state:
            st.session_state.last_delta = delta_mm
            st.session_state.leg_mm = float(delta_mm)
        
        # Обновляем катет только для углового шва
        if delta_mm != st.session_state.last_delta:
            if weld_type == "У":
                st.session_state.leg_mm = float(delta_mm)
            st.session_state.last_delta = delta_mm
        
        if weld_type == "С":
            leg_mm = st.number_input("Катет k, мм", value=st.session_state.leg_mm, min_value=1.0, max_value=float(delta_mm), step=1.0, disabled=True)
        else:
            leg_mm = st.number_input("Катет k, мм", value=st.session_state.leg_mm, min_value=1.0, max_value=float(delta_mm), step=1.0)
            st.session_state.leg_mm = leg_mm
    
    # Угол разделки: блокируется, если выбран "У"
    if weld_type == "У":
        groove_angle = st.number_input("Угол разделки кромок θ, градусы", value=0, min_value=0, max_value=90, step=5, disabled=True)
    else:
        groove_angle = st.number_input("Угол разделки кромок θ, градусы", value=0, min_value=0, max_value=90, step=5)
    
    st.subheader("🏗️ Материал")
    steel_mark = st.selectbox("Марка стали", ["Ст3", "09Г2С"])
    
    st.divider()
    
    if st.button("🚀 Рассчитать", type="primary", use_container_width=True):
        weld_type_full = "стыковой" if weld_type == "С" else "угловой"
        
        payload = {
            "weld_type": weld_type_full,
            "thickness": delta_mm,
            "B": B_mm,
            "steel_mark": steel_mark
        }
        
        if weld_type_full == "угловой":
            payload["leg"] = leg_mm
        else:
            payload["leg"] = None
        
        if weld_type_full == "стыковой" and groove_angle > 0:
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
st.header("📤 Результаты")

if st.session_state.get("calculate", False):
    result = st.session_state.result
    
    shrinkage_val = f"{result['transverse_shrinkage_mm']:.2f}".replace('.', ',')
    ratio_val = f"{result['b600_B_ratio']:.3f}".replace('.', ',')
    b600_val = f"{result['b600_mm']:.2f}".replace('.', ',')
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Сварочный зазор (поперечная усадка Δ), мм", shrinkage_val)
    with col2:
        color_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        st.metric("Прижимы", f"{color_icon.get(result['color'], '⚪')} {result['efficiency']}")
    
    if result['angular_beta_deg'] is not None:
        beta_val = f"{result['angular_beta_deg']:.2f}".replace('.', ',')
        st.info(f"**Угловой поворот кромок β:** {beta_val}°")
    
    st.success(f"**Рекомендуемый шаг прижимов, Lпр:** {result['clamp_pitch_mm']} мм")
    if result.get('warning'):
        st.warning(result['warning'])
    
    with st.expander("ℹ️ Детали расчёта"):
        st.write(f"**b600:** {b600_val} мм")
        st.write(f"**b600/B:** {ratio_val}")
        st.write(f"**Условие:** {result['condition']}")
else:
    st.info("👈 Настройте параметры и нажмите «Рассчитать»")

st.markdown("---")
st.markdown("**WeldGapCalculator** | Калькулятор сварочных зазоров | V1.0")