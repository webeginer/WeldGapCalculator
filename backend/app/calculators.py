# backend/app/calculators.py
import math

def calc_b600(weld_type: str, thickness_mm: float, leg_mm: float = None, groove_angle: float = None) -> float:
    """Расчёт ширины зоны пластических деформаций (b600)"""
    if weld_type == "угловой":
        if leg_mm is None:
            raise ValueError("Для углового шва требуется указать катет (leg)")
        return 4.5 * leg_mm
    elif weld_type == "стыковой":
        # Определяем тип разделки по углу
        if groove_angle is not None and groove_angle > 0:
            # С разделкой (V-образная)
            return 3.0 * thickness_mm
        else:
            # Без разделки
            return 2.25 * thickness_mm
    else:
        raise ValueError(f"Неизвестный тип шва: {weld_type}. Допустимые: 'угловой', 'стыковой'")

def calc_transverse_shrinkage(b600: float, B: float, epsilon_s: float = 0.00114) -> dict:
    """Расчёт поперечной усадки Δ и эффективности прижимов (с жёлтым цветом)
    
    Args:
        b600: ширина зоны пластических деформаций, мм
        B: ширина листа, мм
        epsilon_s: относительная деформация (для Ст3 = 0.00114, для 09Г2С = 0.00164)
    """
    ratio = b600 / B
    
    # Цветовая индикация по ТЗ
    if ratio >= 0.30:
        delta = 0.0088 * b600
        condition = "свободная усадка (b600/B ≥ 0.30)"
        efficiency = "НЕЭФФЕКТИВНЫ - ТРЕБУЕТСЯ ИЗМЕНЕНИЕ РЕЖИМА"
        color = "red"
    elif ratio >= 0.15:
        delta = 0.0088 * b600
        condition = "свободная усадка (0.15 ≤ b600/B < 0.30)"
        efficiency = "ВОЗМОЖНЫ ДЕФОРМАЦИИ"
        color = "yellow"
    else:  # ratio < 0.15
        delta = epsilon_s * 13 * b600
        condition = "жёсткая усадка (b600/B < 0.15)"
        efficiency = "ЭФФЕКТИВНЫ"
        color = "green"
    
    return {
        "delta_mm": round(delta, 2),
        "b600_B_ratio": round(ratio, 3),
        "condition": condition,
        "efficiency": efficiency,
        "color": color
    }

def calc_angular_beta(groove_angle: float) -> float:
    """Расчёт углового поворота β (только для V-образных швов)
    Формула: β = 2 * arctg(0.000012 * 580 * tg(θ/2))
    """
    if groove_angle is None or groove_angle <= 0:
        return None  # Не применимо для угловых швов и без разделки
    
    theta_rad = math.radians(groove_angle)
    beta_rad = 2 * math.atan(0.000012 * 580 * math.tan(theta_rad / 2))
    beta_deg = math.degrees(beta_rad)
    
    return round(beta_deg, 2)

def calc_clamp_pitch(b600: float, B: float) -> dict:
    """Расчёт шага прижимов L_pr"""
    # Расчётный шаг: 5 * b600
    calculated = 5 * b600
    
    # Ограничения: не менее 50 мм и не более B
    if calculated < 50:
        final = 50
        warning = f"Расчётный шаг прижимов ({round(calculated, 1)} мм) менее 50 мм. Режим критический, рекомендуется снизить тепловложение или уменьшить катет шва."
    else:
        final = min(calculated, B)
        warning = None
    
    return {
        "clamp_pitch_mm": round(final),
        "calculated_raw_mm": round(calculated, 1),
        "warning": warning
    }

# backend/app/calculators.py (добавить в конец файла)
def calc_tack_pitch(weld_type: str, thickness_mm: float, leg_mm: float = None, b600: float = None) -> dict:
    """Расчёт шага прихваток L_прхв по § 34 Окерблома"""
    
    if weld_type == "угловой":
        if leg_mm is None or leg_mm == 0:
            return {"tack_pitch_mm": None, "warning": None, "info": None}
        calculated = 100 * thickness_mm / leg_mm
    else:  # стыковой
        if b600 is None or b600 == 0:
            return {"tack_pitch_mm": None, "warning": None, "info": None}
        equiv_leg = b600 / 4.5  # эквивалентный катет
        calculated = 100 * thickness_mm / equiv_leg
    
    # Округление до 10 мм вверх
    rounded = int((calculated + 9) // 10 * 10)
    
    # Ограничения
    final = max(50, min(500, rounded))
    
    # Предупреждения
    warning = None
    info = None
    if calculated < 50:
        warning = f"Расчётный шаг прихваток ({round(calculated, 1)} мм) менее 50 мм. Требуется очень частая фиксация кромок. Возможно, тепловложение завышено."
    elif final > 300:
        info = f"Расчётный шаг прихваток большой ({final} мм). Допустима фиксация только в начале и конце шва."
    
    return {
        "tack_pitch_mm": final,
        "calculated_raw_mm": round(calculated, 1),
        "warning": warning,
        "info": info
    }


# backend/app/calculators.py (добавить новую функцию)

def calc_longitudinal_shrinkage(weld_type: str, thickness_mm: float, B_mm: float, L_mm: float,
                                 leg_mm: float = None, groove_angle: float = None, gap_mm: float = 0) -> dict:
    """Расчёт продольной усадки ΔL по Окерблому"""
    
    # Площадь сечения детали
    F_det = thickness_mm * B_mm  # мм²
    
    # Площадь шва Fшв (мм²)
    if weld_type == "угловой":
        if leg_mm is None:
            return {"delta_L_mm": None, "warning": None}
        F_weld = (leg_mm ** 2) / 2
    elif weld_type == "стыковой":
        if groove_angle is not None and groove_angle > 0:
            # V-образная разделка
            theta_rad = math.radians(groove_angle)
            F_weld = gap_mm * thickness_mm + (thickness_mm ** 2) * math.tan(theta_rad / 2)
        else:
            # Без разделки
            F_weld = gap_mm * thickness_mm
    else:
        return {"delta_L_mm": None, "warning": None}
    
    # Погонная энергия (Дж/см)
    qn = 650 * F_weld  # Дж/см
    
    # Относительное укорочение
    delta_ct = 0.83e-6 * (qn / F_det)  # безразмерная
    
    # Полная продольная усадка (мм)
    delta_L = delta_ct * L_mm
    
    # Предупреждение
    warning = None
    if delta_L > 1.0:
        warning = f"Продольная усадка значительная ({delta_L:.2f} мм), рекомендуется изменить геометрию"
    
    return {
        "delta_L_mm": round(delta_L, 2),
        "F_weld_mm2": round(F_weld, 2),
        "qn_J_per_cm": round(qn, 1),
        "warning": warning
    }