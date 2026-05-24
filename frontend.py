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
    
    st.subheader("📐 Геометрия")
    
    weld_type = st.selectbox("Тип шва", ["Стыковой", "Угловой"])
    
    col1, col2 = st.columns(2)
    with col1:
        B_mm = st.number_input("Ширина B, мм", value=100, min_value=20, max_value=500, step=10)
    with col2:
        delta_mm = st.number_input("Толщина δ, мм", value=4, min_value=1, max_value=30, step=1, format="%d")
    
    # Катет k
    if 'last_delta' not in st.session_state:
        st.session_state.last_delta = None
        st.session_state.leg_mm = None
        st.session_state.prev_weld_type = weld_type
    
    # При смене типа шва с "Стыковой" на "Угловой" устанавливаем катет = толщина
    if weld_type != st.session_state.get('prev_weld_type', weld_type):
        if weld_type == "Угловой" and delta_mm is not None:
            st.session_state.leg_mm = delta_mm
        st.session_state.prev_weld_type = weld_type
    
    if delta_mm is not None and delta_mm != st.session_state.last_delta:
        if weld_type == "Угловой":
            st.session_state.leg_mm = delta_mm
        st.session_state.last_delta = delta_mm
    
    if weld_type == "Стыковой":
        leg_mm = st.number_input("Катет k, мм", value=st.session_state.leg_mm, min_value=1, max_value=delta_mm if delta_mm else 50, step=1, disabled=True, format="%d")
    else:
        leg_mm = st.number_input("Катет k, мм", value=st.session_state.leg_mm, min_value=1, max_value=delta_mm if delta_mm else 50, step=1, format="%d")
        st.session_state.leg_mm = leg_mm
    
    # Угол разделки (только для стыкового шва)
    if weld_type == "Стыковой":
        groove_angle = st.number_input("Угол разделки кромок θ, градусы", value=0, min_value=0, max_value=90, step=5)
    else:
        groove_angle = 0
    
    st.subheader("🏗️ Материал")
    steel_mark = st.selectbox("Марка стали", ["Ст3", "09Г2С"])
    
    st.divider()
    
    if st.button("🚀 Рассчитать", type="primary", use_container_width=True):
        # Преобразование типа шва для бэкенда
        weld_type_backend = "стыковой" if weld_type == "Стыковой" else "угловой"
        
        payload = {
            "weld_type": weld_type_backend,
            "thickness": delta_mm,
            "B": B_mm,
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
    if result.get('clamp_warning'):
        st.warning(result['clamp_warning'])
    
    # НОВОЕ: Шаг прихваток
    if result.get('tack_pitch_mm'):
        st.info(f"**Рекомендуемый шаг прихваток, Lпрхв:** {result['tack_pitch_mm']} мм")
        if result.get('tack_warning'):
            st.warning(result['tack_warning'])
        if result.get('tack_info'):
            st.info(result['tack_info'])
    
    with st.expander("ℹ️ Детали расчёта"):
        st.write(f"**b600 (ширина зоны пластических деформаций):** {b600_val} мм")
        st.write(f"**Отношение b600/B:** {ratio_val}")
        st.write(f"**Условие:** {result['condition']}")
else:
    st.info("👈 Заполните все исходные данные и нажмите «Рассчитать»")

st.markdown("---")
st.markdown("**WeldGapCalculator** | Калькулятор сварочных зазоров | V1.1")