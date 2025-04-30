from temas_keywords import temas
from utils import limpiar_texto
from unidecode import unidecode
import re

def _normalizar(texto: str) -> str:
    """Minúsculas + sin tildes + sin espacios extras."""
    return unidecode(texto).lower().strip()

def detectar_tema(texto: str):
    """
    Devuelve el tema detectado o None.
    · Tokens simples → coincidencia por palabra exacta.
    · Tokens con '+' → exige todas las sub-palabras presentes.
    """
    # Texto limpio y normalizado
    texto_limpio = limpiar_texto(texto)
    texto_norm   = _normalizar(texto_limpio)

    # Conjunto de palabras aisladas — evita falsos positivos
    palabras_texto = set(re.sub(r"[^\w\s]", " ", texto_norm).split())

    for tema, tokens in temas.items():
        for token in tokens:
            token_norm = _normalizar(token)

            # ---- tokens compuestos  (palabra1+palabra2)
            if "+" in token_norm:
                subpals = set(token_norm.split("+"))
                if subpals.issubset(palabras_texto):
                    return tema
            # ---- tokens simples  (match exacto en palabras_texto)
            else:
                if token_norm in palabras_texto:
                    return tema
    return None
