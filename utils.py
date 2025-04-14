import string
from unidecode import unidecode

def limpiar_texto(texto):
    texto = unidecode(str(texto).lower())
    return texto.translate(str.maketrans('', '', string.punctuation))