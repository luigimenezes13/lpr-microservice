#!/usr/bin/env python3
import argparse
import re
import sys

import cv2

try:
    from paddleocr import PaddleOCR
except ImportError as error:
    raise SystemExit(
        "PaddleOCR nao esta instalado. Ative o ambiente virtual e rode: pip install -r requirements.txt"
    ) from error

PADRAO_PLACA_ANTIGO = re.compile(r"^[A-Z]{3}[0-9]{4}$")
PADRAO_PLACA_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")


def limpar_texto(texto: str) -> str:
    return "".join(caractere for caractere in texto.upper() if caractere.isalnum())


def parece_placa_brasileira(texto_limpo: str) -> bool:
    return bool(
        PADRAO_PLACA_ANTIGO.match(texto_limpo)
        or PADRAO_PLACA_MERCOSUL.match(texto_limpo)
    )


def criar_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roda PaddleOCR em uma imagem e mostra candidatos de placa."
    )
    parser.add_argument(
        "--imagem",
        default="agora.jpg",
        help="Caminho da imagem a ser analisada (default: agora.jpg).",
    )
    parser.add_argument(
        "--lado-maximo",
        type=int,
        default=1600,
        help="Reduz a imagem para este lado maximo antes do OCR (default: 1600).",
    )
    return parser.parse_args()


def reduzir_imagem(imagem, lado_maximo: int):
    altura, largura = imagem.shape[:2]
    maior_lado = max(altura, largura)
    if maior_lado <= lado_maximo:
        return imagem

    escala = lado_maximo / float(maior_lado)
    nova_largura = int(largura * escala)
    nova_altura = int(altura * escala)
    return cv2.resize(imagem, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)


def extrair_textos(ocr, imagem):
    if hasattr(ocr, "predict"):
        try:
            resultado = ocr.predict(imagem)
            if resultado and isinstance(resultado[0], dict):
                textos = resultado[0].get("rec_texts", [])
                confiancas = resultado[0].get("rec_scores", [])
                return list(zip(textos, confiancas))
        except Exception:
            pass

    try:
        resultado_legado = ocr.ocr(imagem, cls=True)
    except TypeError:
        resultado_legado = ocr.ocr(imagem)

    if not resultado_legado or not resultado_legado[0]:
        return []

    linhas = []
    for linha in resultado_legado[0]:
        texto_original = linha[1][0]
        confianca = float(linha[1][1])
        linhas.append((texto_original, confianca))
    return linhas


def main() -> int:
    argumentos = criar_argumentos()
    imagem = cv2.imread(argumentos.imagem)

    if imagem is None:
        print(f"Nao foi possivel abrir a imagem: {argumentos.imagem}")
        return 1

    imagem = reduzir_imagem(imagem, argumentos.lado_maximo)
    ocr = PaddleOCR(use_textline_orientation=True, lang="en")
    try:
        linhas_detectadas = extrair_textos(ocr, imagem)
    except Exception as erro:
        print("Falha ao executar o PaddleOCR neste ambiente.")
        print(f"Erro original: {erro}")
        print(
            "Dica: em alguns ambientes, o PaddleOCR funciona melhor com Python 3.10/3.11 e versoes compativeis de paddlepaddle."
        )
        return 2

    if not linhas_detectadas:
        print("Nenhum texto detectado na imagem.")
        return 0

    print(f"\nTexto detectado em: {argumentos.imagem}")
    candidatos_placa = []

    for indice, (texto_original, confianca) in enumerate(linhas_detectadas, start=1):
        texto_limpo = limpar_texto(texto_original)
        eh_placa = parece_placa_brasileira(texto_limpo)

        marcador = " <-- candidato de placa" if eh_placa else ""
        print(
            f"[{indice:02d}] texto='{texto_original}' | limpo='{texto_limpo}' | conf={confianca:.3f}{marcador}"
        )

        if eh_placa:
            candidatos_placa.append((texto_limpo, confianca))

    if not candidatos_placa:
        print("\nNenhum padrao de placa brasileira foi encontrado.")
        return 0

    melhor_texto, melhor_confianca = max(candidatos_placa, key=lambda item: item[1])
    print("\nMelhor candidato de placa:")
    print(f"placa={melhor_texto} | confianca={melhor_confianca:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
