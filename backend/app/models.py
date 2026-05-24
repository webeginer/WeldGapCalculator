# backend/app/models.py
from pydantic import BaseModel
from typing import Optional

class WeldInput(BaseModel):
    weld_type: str  # "стыковой" или "угловой"
    thickness: float  # δ, мм
    B: float  # ширина листа, мм
    leg: Optional[float] = None  # катет k для углового шва, мм
    groove_angle: Optional[float] = None  # θ для стыкового шва с разделкой, градусы
    steel_mark: str = "Ст3"  # марка стали