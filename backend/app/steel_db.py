# Справочник марок стали
STEELS = {
    "Ст3": {
        "alpha": 12e-6,      # 1/°C
        "sigma_s": 240,      # МПа
        "E": 2.1e5,          # МПа
        "epsilon_s": 0.00114
    },
    "09Г2С": {
        "alpha": 12e-6,
        "sigma_s": 345,
        "E": 2.1e5,
        "epsilon_s": 0.00164
    }
}

def get_steel(mark: str):
    """Вернуть свойства стали по марке"""
    if mark not in STEELS:
        raise ValueError(f"Марка стали '{mark}' не найдена. Доступны: {list(STEELS.keys())}")
    return STEELS[mark]

def list_steels():
    """Вернуть список доступных марок"""
    return list(STEELS.keys())