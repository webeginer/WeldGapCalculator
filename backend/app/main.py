# backend/app/main.py
from fastapi import FastAPI, HTTPException
from backend.app.models import WeldInput
from backend.app.calculators import (
    calc_b600, 
    calc_transverse_shrinkage, 
    calc_angular_beta,
    calc_clamp_pitch
)

app = FastAPI(title="WeldGapCalculator", version="1.0")

@app.get("/")
def root():
    return {"message": "Калькулятор сварочных зазоров (Окерблом)", "version": "1.0"}

@app.post("/calculate")
def calculate(input_data: WeldInput):
    try:
        # Передаём groove_angle в calc_b600 для определения типа разделки
        b600 = calc_b600(
            input_data.weld_type,
            input_data.thickness,
            input_data.leg,
            input_data.groove_angle
        )
        
        shrinkage = calc_transverse_shrinkage(b600, input_data.B)
        
        # Угловой поворот только для стыковых швов с разделкой
        if input_data.weld_type == "стыковой" and input_data.groove_angle is not None and input_data.groove_angle > 0:
            beta = calc_angular_beta(input_data.groove_angle)
        else:
            beta = None
        
        clamp = calc_clamp_pitch(b600, input_data.B)
        
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
            "warning": clamp["warning"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)