# backend/app/main.py
from fastapi import FastAPI, HTTPException
from backend.app.models import WeldInput
from backend.app.calculators import (
    calc_b600, 
    calc_transverse_shrinkage, 
    calc_angular_beta,
    calc_clamp_pitch,
    calc_tack_pitch,
    calc_longitudinal_shrinkage
)
from backend.app.steel_db import get_steel

app = FastAPI(title="WeldGapCalculator", version="1.2")

@app.get("/")
def root():
    return {"message": "Калькулятор сварочных зазоров (Окерблом)", "version": "1.2"}

@app.post("/calculate")
def calculate(input_data: WeldInput):
    try:
        # Получаем свойства стали
        steel = get_steel(input_data.steel_mark)
        epsilon_s = steel["epsilon_s"]
        
        # Расчёт b600
        b600 = calc_b600(
            input_data.weld_type,
            input_data.thickness,
            input_data.leg,
            input_data.groove_angle
        )
        
        # Поперечная усадка
        shrinkage = calc_transverse_shrinkage(b600, input_data.B, epsilon_s)
        
        # Угловой поворот (только для стыковых швов с разделкой)
        if input_data.weld_type == "стыковой" and input_data.groove_angle is not None and input_data.groove_angle > 0:
            beta = calc_angular_beta(input_data.groove_angle)
        else:
            beta = None
        
        # Шаг прижимов
        clamp = calc_clamp_pitch(b600, input_data.B)
        
        # Шаг прихваток
        tack = calc_tack_pitch(
            input_data.weld_type,
            input_data.thickness,
            input_data.leg,
            b600
        )
        
        # Продольная усадка (НОВОЕ в V1.2)
        longitudinal = calc_longitudinal_shrinkage(
            input_data.weld_type,
            input_data.thickness,
            input_data.B,
            input_data.L,
            input_data.leg,
            input_data.groove_angle,
            input_data.gap
        )
        
        return {
            "b600_mm": round(b600, 2),
            "transverse_shrinkage_mm": shrinkage["delta_mm"],
            "b600_B_ratio": shrinkage["b600_B_ratio"],
            "condition": shrinkage["condition"],
            "efficiency": shrinkage["efficiency"],
            "color": shrinkage["color"],
            "angular_beta_deg": beta,
            "clamp_pitch_mm": clamp["clamp_pitch_mm"],
            "clamp_pitch_raw_mm": clamp["calculated_raw_mm"],
            "clamp_warning": clamp["warning"],
            "tack_pitch_mm": tack["tack_pitch_mm"],
            "tack_pitch_raw_mm": tack["calculated_raw_mm"],
            "tack_warning": tack["warning"],
            "tack_info": tack["info"],
            "longitudinal_shrinkage_mm": longitudinal["delta_L_mm"],
            "longitudinal_warning": longitudinal["warning"],
            "F_weld_mm2": longitudinal["F_weld_mm2"],
            "qn_J_per_cm": longitudinal["qn_J_per_cm"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)