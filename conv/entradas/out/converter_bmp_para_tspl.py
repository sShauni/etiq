import os
import binascii
import traceback
from PIL import Image

# ==============================
# CONFIGURAÇÕES — EDITAR AQUI
# ==============================
PASTA_ENTRADA = "out"  # onde estão as .bmp
PASTA_SAIDA = "tspl_out"       # onde salvar .tspl

DPI = 203
LARGURA_MM = 101.6   # largura da etiqueta (mm)
ALTURA_MM = 76.2     # altura da etiqueta (mm)
GAP_MM = 3         # gap entre etiquetas
THRESHOLD = 128    # threshold pra converter pra 1-bit
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
    new_img = Image.new("1", (new_w, h), 1)  # branco
    new_img.paste(img, (0, 0))
    return new_img


def img_to_tspl_hex(img):
    w, h = img.size
    pixels = img.load()
    bytes_per_line = w // 8
    parts = []

    for y in range(h):
        line_bytes = bytearray()
        for bx in range(bytes_per_line):
            val = 0
            for bit in range(8):
                x = bx * 8 + bit
                pix = pixels[x, y]
                if pix == 0:  # preto
                    val |= (1 << (7 - bit))
            line_bytes.append(val)
        parts.append(binascii.hexlify(bytes(line_bytes)).decode("ascii"))

    return "".join(parts), w, h


def processar():
    print("[INÍCIO] Convertendo BMP -> TSPL")

    ensure_dir(PASTA_SAIDA)

    try:
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(".bmp")])
    except FileNotFoundError:
        print(f"[ERRO] Pasta '{PASTA_ENTRADA}' não existe.")
        return

    if not arquivos:
        print(f"[AVISO] Nenhum arquivo .bmp encontrado em '{PASTA_ENTRADA}'.")
        return

    # dimensões alvo
    target_w = mm_to_px(LARGURA_MM, DPI)
    target_h = mm_to_px(ALTURA_MM, DPI)

    total = 0

    for arq in arquivos:
        path = os.path.join(PASTA_ENTRADA, arq)
        nome = os.path.splitext(arq)[0]
        print(f"[INFO] Processando {arq}...")

        try:
            img = Image.open(path)
            img = img.resize((target_w, target_h), Image.LANCZOS)
            img = convert_to_1bit(img, THRESHOLD)
            img = pad_width(img)

            hex_data, w, h = img_to_tspl_hex(img)
            bytes_w = w // 8

            tspl = [
                f"CSL",
                f"SIZE {LARGURA_MM} mm, {ALTURA_MM} mm",
                f"GAP {GAP_MM} mm, 0 mm",
                "CLS",
                f"BITMAP 0,0,{bytes_w},{h},1,{hex_data}",
                "PRINT 1"
            ]

            out_path = os.path.join(PASTA_SAIDA, f"{nome}.tspl")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(tspl))

            print(f"[OK] Gerado: {out_path}")
            total += 1

        except Exception as e:
            print(f"[ERRO] Falha ao processar {arq}: {e}")
            traceback.print_exc()

    print(f"[FIM] {total} arquivos convertidos.")


if __name__ == "__main__":
    processar()
