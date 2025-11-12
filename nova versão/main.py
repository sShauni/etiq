from frontend.pygame_interface import iniciar_interface
from backend.impressao import ativar_impressora
from backend.gpio_monitor import iniciar_monitoramento

NOME_IMPRESSORA = "Thermal"

if __name__ == "__main__":
    ativar_impressora(NOME_IMPRESSORA)
    iniciar_monitoramento(lambda: print("Sinal GPIO recebido!"))
    iniciar_interface()
