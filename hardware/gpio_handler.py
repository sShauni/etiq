"""
Gerenciamento de GPIO para detecção automática de impressão.
Isolado para facilitar testes em ambientes sem GPIO.
"""

import time
import threading
from typing import Callable, Optional
from config.settings import settings


class GPIOHandler:
    """Gerencia leitura de GPIO com debounce e callback."""
    
    def __init__(self, callback: Callable[[], None]):
        """
        Inicializa o handler GPIO.
        
        Args:
            callback: Função a ser chamada quando o sinal for detectado
        """
        self.callback = callback
        self.gpio_pin = settings.gpio_pin
        self.delay = settings.printer_delay
        
        self.gpio_available = False
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self._setup_gpio()
    
    def _setup_gpio(self) -> None:
        """Configura o GPIO se disponível."""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.GPIO = GPIO
            self.gpio_available = True
            print(f"✓ GPIO configurado no pino {self.gpio_pin}")
            
        except (ImportError, RuntimeError) as e:
            self.gpio_available = False
            print(f"⚠ GPIO não disponível: {e}")
            print("   Sistema funcionará apenas com botão manual")
    
    def _monitor_loop(self) -> None:
        """Loop de monitoramento do GPIO."""
        if not self.gpio_available:
            return
        
        print(f"✓ Monitoramento GPIO iniciado (pino {self.gpio_pin})")
        
        while self.monitoring:
            try:
                # Detecta sinal LOW (botão pressionado)
                if self.GPIO.input(self.gpio_pin) == self.GPIO.LOW:
                    print("⚡ Sinal GPIO detectado!")
                    
                    # Executa callback
                    self.callback()
                    
                    # Aguarda até o botão ser solto (debounce)
                    while self.GPIO.input(self.gpio_pin) == self.GPIO.LOW:
                        time.sleep(0.05)
                    
                    # Delay extra para evitar múltiplos triggers
                    time.sleep(self.delay)
                
                else:
                    # Polling interval quando não há sinal
                    time.sleep(0.05)
                    
            except Exception as e:
                print(f"✗ Erro no loop GPIO: {e}")
                time.sleep(1)  # Espera antes de tentar novamente
    
    def start_monitoring(self) -> bool:
        """
        Inicia monitoramento GPIO em thread separada.
        
        Returns:
            True se iniciou com sucesso, False se GPIO indisponível
        """
        if not self.gpio_available:
            print("⚠ GPIO não disponível, monitoramento não iniciado")
            return False
        
        if self.monitoring:
            print("⚠ Monitoramento GPIO já está ativo")
            return True
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="GPIO-Monitor"
        )
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self) -> None:
        """Para o monitoramento GPIO."""
        if self.monitoring:
            print("Parando monitoramento GPIO...")
            self.monitoring = False
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            
            print("✓ Monitoramento GPIO parado")
    
    def cleanup(self) -> None:
        """Limpa recursos GPIO."""
        self.stop_monitoring()
        
        if self.gpio_available:
            try:
                self.GPIO.cleanup()
                print("✓ GPIO cleanup realizado")
            except Exception as e:
                print(f"⚠ Erro no GPIO cleanup: {e}")
    
    def is_available(self) -> bool:
        """Verifica se GPIO está disponível."""
        return self.gpio_available
    
    def is_monitoring(self) -> bool:
        """Verifica se está monitorando."""
        return self.monitoring
    
    def simulate_trigger(self) -> None:
        """Simula um trigger GPIO (útil para testes)."""
        print("🔧 Simulando trigger GPIO...")
        self.callback()


if __name__ == '__main__':
    # Teste do GPIO handler
    def test_callback():
        print(">>> CALLBACK EXECUTADO! <<<")
    
    handler = GPIOHandler(callback=test_callback)
    
    print(f"GPIO disponível: {handler.is_available()}")
    
    if handler.is_available():
        print("\nIniciando monitoramento por 10 segundos...")
        print("Pressione o botão conectado ao GPIO!")
        
        handler.start_monitoring()
        time.sleep(10)
        handler.stop_monitoring()
        handler.cleanup()
    else:
        print("\nTestando simulação de trigger...")
        handler.simulate_trigger()