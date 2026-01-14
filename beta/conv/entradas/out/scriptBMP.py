import os
from PIL import Image

# ========================================================
# CONFIGURAÇÃO DA ETIQUETA (75×100 mm a 203 dpi)
# ========================================================

LABEL_WIDTH = int((100 / 25.4) * 203)   # ≈ 599 px
LABEL_HEIGHT = int((75 / 25.4) * 203) # ≈ 799 px

INPUT_DIR = "."
OUTPUT_DIR = "out"

def ensure_out_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def convert_image(path):
    name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(OUTPUT_DIR, f"{name}.bmp")

    # abre imagem
    img = Image.open(path).convert("L")  # escala de cinza

    # redimensiona mantendo proporção para CABER na área útil
    img.thumbnail((LABEL_WIDTH, LABEL_HEIGHT), Image.LANCZOS)

    # convertendo para 1-bit (TSPL exige preto/branco puro)
    img = img.point(lambda x: 0 if x < 128 else 255, '1')

    # cria canvas final exato no tamanho da etiqueta
    final = Image.new('1', (LABEL_WIDTH, LABEL_HEIGHT), 255)
    final.paste(img, (0, 0))

    final.save(out_path, format="BMP")
    print(f"[OK] {path} -> {out_path}")

def main():
    ensure_out_dir()

    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            convert_image(os.path.join(INPUT_DIR, file))

    print("\nPronto — BMP TSPL gerados na pasta /out")

if __name__ == "__main__":
    main()
