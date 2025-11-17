import os
from PIL import Image

# CONFIGURAÇÕES -----------------------------------

# Tamanho da etiqueta em pixels (ajuste se necessário)
LABEL_WIDTH = 812     # largura útil em dots
LABEL_HEIGHT = 609    # altura útil em dots

# Pasta de entrada e saída
INPUT_DIR = "."
OUTPUT_DIR = "out"

# --------------------------------------------------

def ensure_out_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def convert_image(path):
    name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(OUTPUT_DIR, f"{name}.bmp")

    img = Image.open(path).convert("L")   # converte para escala de cinza

    # redimensiona mantendo proporção
    img.thumbnail((LABEL_WIDTH, LABEL_HEIGHT))

    # converte para preto/branco 1-bit
    img = img.point(lambda x: 0 if x < 128 else 255, '1')

    # cria imagem final exatamente no tamanho certo
    final = Image.new('1', (LABEL_WIDTH, LABEL_HEIGHT), 255)
    final.paste(img, (0, 0))

    final.save(out_path, format='BMP')
    print(f"[OK] {path} -> {out_path}")

def main():
    ensure_out_dir()

    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".pdf", ".bmp")):
            # PDF não suportado por Pillow nativamente sem poppler
            if file.lower().endswith(".pdf"):
                print(f"[IGNORADO] {file} (PDF não suportado neste script)")
                continue

            convert_image(os.path.join(INPUT_DIR, file))

    print("\nPronto! BMPs compatíveis TSPL estão dentro da pasta /out")

if __name__ == "__main__":
    main()
