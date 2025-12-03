from typing import Dict


# Dummy VIN decoder for demonstration. In a real implementation this could call an external API.
def decode_vin(vin: str) -> Dict[str, str]:
    vin = vin.strip().upper()
    if len(vin) < 5:
        return {}

    # Mocked decoding output
    return {
        "vin": vin,
        "model": "Sample Model",
        "year": "2020",
        "engine": "Sample Engine",
    }
