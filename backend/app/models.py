from pydantic import BaseModel
from typing import Optional

class WeldInput(BaseModel):
    weld_type: str  # "угловой", "стыковой V", "стыковой без разделки"
    thickness: float  # δ, мм
    B: float  # ширина листа, мм
    leg: Optional[float] = None  # катет k для углового шва, мм
    groove_angle: Optional[float] = None  # θ для V-образного шва, градусы
    steel_mark: str = "Ст3"  # марка стали