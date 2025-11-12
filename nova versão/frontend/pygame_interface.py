import os, pygame, time
from backend.logica import calcular_saida, calcular_saida_personalizado

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')

def iniciar_interface():
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    font = pygame.font.Font(None, 28)

    botoes = [
        {"label": "Altura 1", "rect": pygame.Rect(10, 10, 120, 40), "grupo": "altura", "idx": 0},
        {"label": "Altura 2", "rect": pygame.Rect(10, 60, 120, 40), "grupo": "altura", "idx": 1},
        {"label": "Imprimir", "rect": pygame.Rect(350, 250, 120, 50), "grupo": "acao", "idx": 0},
    ]

    selecionados = {"altura": [], "fio": 0, "malha": 0}
    valor_saida = None

    rodando = True
    while rodando:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                rodando = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for b in botoes:
                    if b["rect"].collidepoint(e.pos):
                        if b["grupo"] == "altura":
                            selecionados["altura"] = [b["idx"]]
                        elif b["grupo"] == "acao":
                            valor_saida, _ = calcular_saida(selecionados, [("1,00m", 0), ("1,20m", 1)])

        screen.fill((255, 255, 255))
        for b in botoes:
            pygame.draw.rect(screen, (0, 128, 255), b["rect"])
            txt = font.render(b["label"], True, (255, 255, 255))
            screen.blit(txt, (b["rect"].x + 10, b["rect"].y + 10))

        if valor_saida:
            texto = font.render(f"Saída: {valor_saida:.1f}", True, (0, 0, 0))
            screen.blit(texto, (10, 280))

        pygame.display.flip()
        time.sleep(0.05)

    pygame.quit()
