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