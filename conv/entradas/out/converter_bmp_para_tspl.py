import os
import traceback
from PIL import Image

# ==============================
# CONFIGURAÇÕES — EDITAR AQUI
# ==============================
PASTA_ENTRADA = "out"
PASTA_SAIDA = "tspl_out"

DPI = 203
LARGURA_MM = 100
ALTURA_MM = 75
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


def invert_binary(raw_bytes):
    # Inverte 0 ↔ 1 em cada bit
    return bytes([~b & 0xFF for b in raw_bytes])


def processar():
    print("[INÍCIO] Convertendo BMP -> TSPL BINÁRIO")

    ensure_dir(PASTA_SAIDA)

    try:
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(".bmp")])
    except FileNotFoundError:
        print(f"[ERRO] Pasta '{PASTA_ENTRADA}' não existe.")
        return

    if not arquivos:
        print(f"[AVISO] Nenhum arquivo .bmp encontrado.")
        return

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

            w, h = img.size
            bpl = w // 8

            # RAW binário original
            raw = img.tobytes()

            # **AQUI ESTÁ A INVERSÃO CORRETA**
            #raw_invertido = invert_binary(raw)

            tspl_bytes = bytearray()
            tspl_bytes.extend(b"CLS\n")
            tspl_bytes.extend(f"SIZE {LARGURA_MM} mm, {ALTURA_MM} mm\n".encode())
            tspl_bytes.extend(f"GAP {GAP_MM} mm, 0 mm\n".encode())
            tspl_bytes.extend(b"CLS\n")
            tspl_bytes.extend(f"BITMAP 0,0,{bpl},{h},1,".encode())
            tspl_bytes.extend(raw)
            tspl_bytes.extend(b"\nPRINT 1\n")

            out_path = os.path.join(PASTA_SAIDA, f"{nome}.tspl")
            with open(out_path, "wb") as f:
                f.write(tspl_bytes)

            print(f"[OK] {out_path}")
            total += 1

        except Exception as e:
            print(f"[ERRO] Falha ao processar {arq}: {e}")
            traceback.print_exc()

    print(f"[FIM] {total} arquivos convertidos.")


if __name__ == "__main__":
    processar()
