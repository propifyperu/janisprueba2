import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
from django.conf import settings

class DatosRequerimiento(BaseModel):
    operacion: Optional[str] # "Venta" o "Alquiler"
    tipo_inmueble: Optional[str] # "Casa", "Departamento", "Terreno", "Local Comercial"
    distritos: List[str] = [] # Ej: ["Cerro Colorado", "Cayma", "Yanahuara"]
    presupuesto_min: Optional[int]
    presupuesto_max: Optional[int]
    area_terreno_min: Optional[int]
    area_terreno_max: Optional[int]
    area_construida_min: Optional[int]
    area_construida_max: Optional[int]
    habitaciones_min: Optional[int]
    habitaciones_max: Optional[int]
    banos_min: Optional[int]
    banos_max: Optional[int]
    cocheras_min: Optional[int]
    cocheras_max: Optional[int]
    antiguedad_min: Optional[int]
    antiguedad_max: Optional[int]
    pisos_min: Optional[int]
    pisos_max: Optional[int]
    tiene_ascensor: Optional[bool]
    acepta_mascotas: Optional[bool]
    observaciones: Optional[str]

def extraer_datos_requerimiento(texto_usuario: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ValueError("La API Key de OpenAI no está configurada en el entorno.")
    client = OpenAI(api_key=api_key)

    try:
        respuesta = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Eres un asistente experto en bienes raíces. Extrae requerimientos de clientes a partir del texto. "
                        "Si mencionan un valor único (ej: 3 habitaciones, 150k dólares, 2 pisos), colócalo tanto en su campo "
                        "mínimo (_min) como en el máximo (_max) para asegurar precisión en el rango. "
                        "Si mencionan un límite ('máximo 150k'), ponlo solo en el máximo. "
                        "Si no encuentras un dato, déjalo como nulo o vacío. Los distritos devuélvelos como una lista de nombres exactos."
                    )
                },
                {"role": "user", "content": texto_usuario}
            ],
            response_format=DatosRequerimiento,
        )

        datos = respuesta.choices[0].message.parsed
        return datos.model_dump() # Devuelve un diccionario de Python
    except Exception as e:
        print(f"Error en OpenAI: {e}")
        return None
