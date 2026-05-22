# frontend.py (исправленный блок результатов)
import streamlit as st
import requests

st.set_page_config(page_title="Калькулятор сварочных зазоров", layout="wide")

col_title, col_title2, col_title3 = st.columns([1, 4, 1])
with col_title2:
    st.markdown("<h1 style='text-align: center;'>🔥 WeldFOAM</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Калькулятор сварочных зазоров</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)

API_URL = "http://localhost:8000"

with st.sidebar:
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
    col1, col2, col3 = st.columns(3)
    with col1:
        L_mm = st.number_input("Длина L", value=500, min_value=100, max_value=2000, step=50)
    with col2:
        B_mm = st.number_input("Ширина B", value=100, min_value=20, max_value=500, step=10)
    with col3:
        delta_mm = st.number_input("Толщина δ", value=4.0, min_value=1.0, max_value=20.0, step=1.0)
    
    # Угол разделки: блокируется, если выбран "У" (угловой)
    if weld_type == "У":
        groove_angle = st.number_input("Угол разделки кромок θ, градусы", value=0, min_value=0, max_value=90, step=5, disabled=True)
    else:
        groove_angle = st.number_input("Угол разделки кромок θ, градусы", value=0, min_value=0, max_value=90, step=5)
    
    st.subheader("🏗️ Материал")
    steel_mark = st.selectbox("Марка стали", ["Ст3", "09Г2С"])
    
    st.divider()
    
    if st.button("🚀 Рассчитать", type="primary", use_container_width=True):
        # Преобразование типа шва
        weld_type_full = "стыковой" if weld_type == "С" else "угловой"
        
        # Формируем payload без костылей
        payload = {
            "weld_type": weld_type_full,
            "thickness": delta_mm,
            "B": B_mm,
            "steel_mark": steel_mark
        }
        
        # Добавляем leg только для углового шва
        if weld_type_full == "угловой":
            payload["leg"] = rod_diam
        else:
            payload["leg"] = None
        
        # Добавляем groove_angle только для стыкового шва с разделкой
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Сварочный зазор (поперечная усадка Δ)", f"{result['transverse_shrinkage_mm']} мм")
    with col2:
        color_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        st.metric("Эффективность прижимов", f"{color_icon.get(result['color'], '⚪')} {result['efficiency']}")
    
    # Показываем угловой поворот только если он есть
    if result['angular_beta_deg'] is not None:
        st.info(f"**Угловой поворот кромок β:** {result['angular_beta_deg']}°")
    
    st.success(f"**Рекомендуемый шаг прижимов L_pr:** {result['clamp_pitch_mm']} мм")
    if result.get('warning'):
        st.warning(result['warning'])
    
    with st.expander("ℹ️ Детали расчёта"):
        st.write(f"**b600 (ширина зоны пластических деформаций):** {result['b600_mm']} мм")
        st.write(f"**Отношение b600/B:** {result['b600_B_ratio']}")
        st.write(f"**Условие:** {result['condition']}")
    
    st.caption("Примечание: расчёт выполнен для конструкционных сталей (Ст3, 09Г2С и аналоги). Теория Окерблома (1948).")
else:
    st.info("👈 Настройте параметры в боковой панели и нажмите «Рассчитать»")

st.markdown("---")
st.markdown("**WeldFOAM** | Калькулятор сварочных зазоров | Версия 1.0")