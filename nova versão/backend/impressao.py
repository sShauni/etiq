import subprocess

def ativar_impressora(nome):
    try:
        subprocess.run(["cupsaccept", nome], check=True)
        subprocess.run(["cupsenable", nome], check=True)
        print(f"Impressora '{nome}' ativada com sucesso.")
    except Exception as e:
        print(f"Falha ao ativar a impressora '{nome}': {e}")

def imprimir_arquivo(nome_impressora, arquivo):
    try:
        subprocess.run(["lp", "-d", nome_impressora, arquivo], check=True)
        print(f"Impressão enviada: {arquivo}")
    except Exception as e:
        print(f"Erro na impressão: {e}")
