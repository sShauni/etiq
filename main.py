#!/usr/bin/env python3
"""
Sistema de Impressão de Etiquetas - Ponto de Entrada Principal
Integra todos os módulos e gerencia o fluxo da aplicação.
"""

import sys
import os
from tkinter import messagebox

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from core.sku_mapper import SKUMapper
from core.calculator import OutputCalculator
from hardware.printer import LabelPrinter
from hardware.gpio_handler import GPIOHandler
from data.sqlite_logger import SQLiteProductionLogger as ProductionLogger
from ui.main_window import MainWindow


class EtiquetasApp:
    """Aplicação principal do sistema de etiquetas."""
    
    def __init__(self):
        """Inicializa todos os componentes da aplicação."""
        print("\n" + "="*60)
        print(f"  Sistema de Etiquetas - Máquina {settings.machine_id}")
        print("="*60 + "\n")
        
        # Inicializa componentes core
        self._init_core_components()
        
        # Inicializa hardware
        self._init_hardware()
        
        # Inicializa UI
        self._init_ui()
        
        print("\n✓ Sistema inicializado com sucesso!\n")
        
        if settings.test_mode:
            print("⚠ MODO DE TESTE ATIVO - Impressões não serão enviadas\n")
    
    def _init_core_components(self) -> None:
        """Inicializa componentes principais."""
        try:
            # SKU Mapper
            print("Carregando mapeamento de SKUs...")
            self.sku_mapper = SKUMapper(settings.sku_file_path)
            
            # Calculator
            self.calculator = OutputCalculator()
            
            # Logger
            print("Inicializando logger de produção...")
            self.logger = ProductionLogger(self.sku_mapper)
            
        except Exception as e:
            print(f"\n✗ ERRO FATAL ao inicializar componentes: {e}\n")
            sys.exit(1)
    
    def _init_hardware(self) -> None:
        """Inicializa componentes de hardware."""
        try:
            # Printer
            print("Configurando impressora...")
            self.printer = LabelPrinter()
            
            # GPIO Handler
            print("Configurando GPIO...")
            self.gpio = GPIOHandler(callback=self._on_gpio_trigger)
            
        except Exception as e:
            print(f"\n⚠ Aviso ao inicializar hardware: {e}")
            print("   Sistema continuará sem algumas funcionalidades\n")
    
    def _init_ui(self) -> None:
        """Inicializa interface gráfica."""
        try:
            print("Criando interface gráfica...")
            self.ui = MainWindow(on_print_callback=self._on_print_request)
            
        except Exception as e:
            print(f"\n✗ ERRO FATAL ao criar interface: {e}\n")
            sys.exit(1)
    
    def _on_print_request(
        self,
        altura_indices: list,
        fio_index: int,
        malha_index: int,
        automatica: bool = False
    ) -> None:
        """
        Processa requisição de impressão.
        
        Args:
            altura_indices: Índices das alturas selecionadas
            fio_index: Índice do fio selecionado
            malha_index: Índice da malha selecionada
            automatica: Se foi disparada automaticamente via GPIO
        """
        try:
            # Calcula códigos individuais para cada altura
            codigos = self.calculator.calculate_all_outputs(
                altura_indices, fio_index, malha_index
            )
            
            if not codigos:
                if not automatica:
                    messagebox.showerror("Erro", "Erro ao calcular códigos")
                return
            
            # Verifica se todas as etiquetas existem
            missing_labels = []
            for codigo in codigos:
                info = self.printer.get_label_info(codigo)
                if not info:
                    missing_labels.append(f"etiqueta_{codigo:.1f}")
            
            if missing_labels:
                if not automatica:
                    msg = "Arquivos não encontrados:\n" + "\n".join(missing_labels)
                    messagebox.showerror("Erro", msg)
                else:
                    print(f"✗ Etiquetas não encontradas: {missing_labels}")
                return
            
            # Imprime todas as etiquetas
            sucessos, falhas = self.printer.print_multiple_labels(codigos)
            
            # Registra logs apenas para as que foram impressas com sucesso
            if sucessos > 0:
                logs_ok = self.logger.log_multiple_productions(codigos, automatica)
                print(f"Logs registrados: {logs_ok}/{len(codigos)}")
            
            # Feedback ao usuário (apenas se não for automático)
            if not automatica:
                if falhas == 0:
                    modo = "selecionadas" if settings.test_mode else "impressas"
                    etiquetas = "\n".join(f"etiqueta_{c:.1f}" for c in codigos)
                    messagebox.showinfo(
                        "Sucesso",
                        f"Etiqueta(s) {modo}:\n{etiquetas}"
                    )
                else:
                    messagebox.showwarning(
                        "Parcial",
                        f"Impressas: {sucessos}\nFalhas: {falhas}"
                    )
            
        except Exception as e:
            error_msg = f"Erro ao processar impressão: {e}"
            print(f"✗ {error_msg}")
            
            if not automatica:
                messagebox.showerror("Erro", error_msg)
    
    def _on_gpio_trigger(self) -> None:
        """Callback executado quando GPIO detecta sinal."""
        # Executa no thread da UI usando after
        if self.ui and self.ui.get_root():
            self.ui.get_root().after(0, self.ui.trigger_auto_print)
    
    def run(self) -> None:
        """Inicia a aplicação."""
        try:
            # Inicia monitoramento GPIO se disponível
            if self.gpio.is_available():
                self.gpio.start_monitoring()
            
            # Inicia UI (blocking)
            self.ui.run()
            
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário")
        except Exception as e:
            print(f"\n✗ Erro durante execução: {e}\n")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Limpa recursos antes de encerrar."""
        print("\nEncerrando aplicação...")
        
        if hasattr(self, 'gpio'):
            self.gpio.cleanup()
        
        print("✓ Recursos liberados\n")


def main():
    """Função principal."""
    try:
        app = EtiquetasApp()
        app.run()
    except Exception as e:
        print(f"\n✗ ERRO FATAL: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()