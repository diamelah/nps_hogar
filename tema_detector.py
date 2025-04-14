from temas_keywords import temas
from utils import limpiar_texto

def detectar_tema(texto):
    texto = limpiar_texto(texto)
    for tema, palabras in temas.items():
        if any(p in texto for p in palabras):
            return tema
    return None