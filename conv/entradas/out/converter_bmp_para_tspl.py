import os
import binascii
import traceback
from PIL import Image

# ==============================
# CONFIGURAÇÕES
# ==============================
PASTA_ENTRADA = "out"          # onde estão os .bmp
PASTA_SAIDA = "tspl_out"       # onde salvar .tspl

DPI = 203
LARGURA_MM = 100   # largura etiqueta
ALTURA_MM = 75     # altura etiqueta
GAP_MM = 3
THRESHOLD = 128
# ==============================


def mm_to_px(mm, dpi):
    return int(round((mm / 25.4) * dpi))


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def convert_to_1bit(img, threshold):
    g = img.convert("L")
    bw = g.point(lambda p: 0 if p < threshold else 255, "1")
    return bw.convert("1", dither=Image.NONE)


def pad_width(img):
    w, h = img.size
    if w % 8 == 0:
        return img
    new_w = ((w + 7) // 8) * 8
    new_img = Image.new("1", (new_w, h), 1)
    new_img.paste(img, (0, 0))
    return new_img


def img_to_bytes(img):
    """
    Converte imagem 1-bit em bytes crus, invertendo o bit
    para que 1 = preto e 0 = branco (modo esperado pelo TSPL).
    """
    w, h = img.size
    pixels = img.load()
    bytes_per_line = w // 8
    
    raw = bytearray()

    for y in range(h):
        for bx in range(bytes_per_line):
            val = 0
            for bit in range(8):
                x = bx * 8 + bit
                pix = pixels[x, y]  # 0 = preto, 255 = branco no Pillow
                
                if pix == 255:      # branco → deve virar 0
                    pass
                else:               # preto → deve virar 1
                    val |= (1 << (7 - bit))

            raw.append(val)

    return raw, bytes_per_line, h



def processar():
    print("[INÍCIO] Convertendo BMP -> TSPL (com saída binária)")

    ensure_dir(PASTA_SAIDA)

    try:
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(".bmp")])
    except FileNotFoundError:
        print(f"[ERRO] Pasta '{PASTA_ENTRADA}' não existe.")
        return

    if not arquivos:
        print(f"[AVISO] Nenhum .bmp encontrado em '{PASTA_ENTRADA}'.")
        return

    target_w = mm_to_px(LARGURA_MM, DPI)
    target_h = mm_to_px(ALTURA_MM, DPI)

    total = 0

    for arq in arquivos:
        caminho = os.path.join(PASTA_ENTRADA, arq)
        nome = os.path.splitext(arq)[0]

        print(f"[INFO] Processando {arq}...")

        try:
            img = Image.open(caminho)
            img = img.resize((target_w, target_h), Image.LANCZOS)
            img = convert_to_1bit(img, THRESHOLD)
            img = pad_width(img)

            raw_bytes, bytes_w, h = img_to_bytes(img)

            out_path = os.path.join(PASTA_SAIDA, f"{nome}.tspl")

            with open(out_path, "wb") as f:

                header = (
                    f"CLS\n"
                    f"SIZE {LARGURA_MM} mm, {ALTURA_MM} mm\n"
                    f"GAP {GAP_MM} mm, 0 mm\n"
                    f"BITMAP 0,0,{bytes_w},{h},1,"
                ).encode("ascii")

                f.write(header)
                f.write(raw_bytes)
                f.write(b"\nPRINT 1\n")

            print(f"[OK] Gerado: {out_path}")
            total += 1

        except Exception as e:
            print(f"[ERRO] Falha ao processar {arq}: {e}")
            traceback.print_exc()

    print(f"[FIM] {total} arquivos convertidos.]")



if __name__ == "__main__":
    processar()
