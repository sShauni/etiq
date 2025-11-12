import subprocess

# === Controle global ===
# Se True, nenhuma operação de impressão real será executada.
# O sistema apenas simula a impressão no console.
IGNORAR_IMPRESSORA = True

def ativar_impressora(nome):
    """
    Ativa a impressora no CUPS, caso esteja desativada.
    Ignora se IGNORAR_IMPRESSORA = True.
    """
    if IGNORAR_IMPRESSORA:
        print(f"[Simulação] Impressora '{nome}' ignorada (modo teste ativo).")
        return

    try:
        subprocess.run(["cupsaccept", nome], check=True)
        subprocess.run(["cupsenable", nome], check=True)
        print(f"Impressora '{nome}' ativada com sucesso.")
    except Exception as e:
        print(f"Falha ao ativar a impressora '{nome}': {e}")


def imprimir_arquivo(nome_impressora, arquivo):
    """
    Envia o arquivo para impressão, ou apenas simula se IGNORAR_IMPRESSORA = True.
    """
    if IGNORAR_IMPRESSORA:
        print(f"[Simulação] Impressão ignorada: {arquivo}")
        return

    try:
        subprocess.run(["lp", "-d", nome_impressora, arquivo], check=True)
        print(f"Impressão enviada: {arquivo}")
    except Exception as e:
        print(f"Erro na impressão: {e}")
