"""
Gerenciamento de impressão de etiquetas.
Inclui retry logic e fallback para modo de teste.
"""

import subprocess
import os
import time
from typing import List, Tuple, Optional
from config.settings import settings


class PrinterError(Exception):
    """Exceção customizada para erros de impressão."""
    pass


class LabelPrinter:
    """Gerencia impressão de etiquetas com retry e fallback."""
    
    def __init__(self):
        """Inicializa o printer com configurações."""
        self.printer_name = settings.printer_name
        self.test_mode = settings.test_mode
        self.labels_dir = settings.labels_dir
        self.extension = settings.label_extension
        
        # Configurações de retry
        self.max_retries = 3
        self.retry_delay = 2  # segundos
        
        # Tenta ativar a impressora no início
        if not self.test_mode:
            self._activate_printer()
    
    def _activate_printer(self) -> None:
        """Ativa a impressora no CUPS."""
        try:
            subprocess.run(
                ["cupsaccept", self.printer_name],
                check=True,
                capture_output=True,
                timeout=5
            )
            subprocess.run(
                ["cupsenable", self.printer_name],
                check=True,
                capture_output=True,
                timeout=5
            )
            print(f"✓ Impressora '{self.printer_name}' ativada")
        except subprocess.TimeoutExpired:
            print(f"⚠ Timeout ao ativar impressora '{self.printer_name}'")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Falha ao ativar impressora: {e}")
        except FileNotFoundError:
            print(f"⚠ Comandos CUPS não encontrados (sistema não Linux?)")
    
    def _get_label_path(self, codigo: float) -> str:
        """Obtém o caminho completo do arquivo de etiqueta."""
        filename = f"etiqueta_{codigo:.1f}{self.extension}"
        return os.path.join(self.labels_dir, filename)
    
    def _check_label_exists(self, codigo: float) -> Tuple[bool, str]:
        """
        Verifica se o arquivo de etiqueta existe.
        
        Returns:
            (existe, caminho_completo)
        """
        path = self._get_label_path(codigo)
        return os.path.exists(path), path
    
    def _print_file(self, filepath: str) -> None:
        """
        Imprime um arquivo específico.
        
        Args:
            filepath: Caminho completo do arquivo
        
        Raises:
            PrinterError: Se a impressão falhar
        """
        if self.test_mode:
            print(f"[TESTE] Imprimiria: {os.path.basename(filepath)}")
            return
        
        try:
            result = subprocess.run(
                ["lp", "-d", self.printer_name, "-o", "raw", filepath],
                check=True,
                capture_output=True,
                timeout=10,
                text=True
            )
            print(f"✓ Etiqueta impressa: {os.path.basename(filepath)}")
            
        except subprocess.TimeoutExpired:
            raise PrinterError(f"Timeout ao imprimir {filepath}")
        except subprocess.CalledProcessError as e:
            raise PrinterError(f"Erro ao imprimir: {e.stderr}")
        except FileNotFoundError:
            raise PrinterError("Comando 'lp' não encontrado")
    
    def print_label(self, codigo: float) -> bool:
        """
        Imprime uma etiqueta específica com retry.
        
        Args:
            codigo: Código numérico da etiqueta
        
        Returns:
            True se sucesso, False se falha
        """
        exists, filepath = self._check_label_exists(codigo)
        
        if not exists:
            print(f"✗ Arquivo não encontrado: {filepath}")
            return False
        
        # Tenta imprimir com retries
        for attempt in range(self.max_retries):
            try:
                self._print_file(filepath)
                return True
                
            except PrinterError as e:
                print(f"⚠ Tentativa {attempt + 1}/{self.max_retries} falhou: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"✗ Falha total ao imprimir etiqueta {codigo}")
                    return False
        
        return False
    
    def print_multiple_labels(self, codigos: List[float]) -> Tuple[int, int]:
        """
        Imprime múltiplas etiquetas.
        
        Args:
            codigos: Lista de códigos para imprimir
        
        Returns:
            (sucessos, falhas)
        """
        sucessos = 0
        falhas = 0
        
        for codigo in codigos:
            if self.print_label(codigo):
                sucessos += 1
            else:
                falhas += 1
        
        return sucessos, falhas
    
    def get_label_info(self, codigo: float) -> Optional[dict]:
        """
        Obtém informações sobre uma etiqueta.
        
        Returns:
            Dict com info ou None se não existe
        """
        exists, filepath = self._check_label_exists(codigo)
        
        if not exists:
            return None
        
        try:
            stat = os.stat(filepath)
            return {
                'codigo': codigo,
                'path': filepath,
                'size': stat.st_size,
                'exists': True
            }
        except Exception as e:
            print(f"Erro ao obter info de {filepath}: {e}")
            return None


if __name__ == '__main__':
    # Teste do printer
    printer = LabelPrinter()
    
    print(f"Modo de teste: {printer.test_mode}")
    print(f"Impressora: {printer.printer_name}")
    print(f"Diretório: {printer.labels_dir}")
    
    # Testa impressão de uma etiqueta
    test_code = 111.1
    print(f"\nTestando impressão de código {test_code}...")
    success = printer.print_label(test_code)
    print(f"Resultado: {'Sucesso' if success else 'Falha'}")
    
    # Testa info de etiqueta
    info = printer.get_label_info(test_code)
    if info:
        print(f"\nInfo da etiqueta: {info}")