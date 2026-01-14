"""
Sistema de logging de produção em Excel.
Registra SKUs produzidos por máquina e data.
"""

import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from typing import Optional
from config.settings import settings
from core.sku_mapper import SKUMapper


class ProductionLogger:
    """Gerencia logs de produção em arquivos Excel."""
    
    def __init__(self, sku_mapper: SKUMapper):
        """
        Inicializa o logger.
        
        Args:
            sku_mapper: Instância do SKUMapper para conversão de códigos
        """
        self.sku_mapper = sku_mapper
        self.machine_id = settings.machine_id
        self.log_dir = settings.log_dir
        
        # Cria diretório de logs se não existir
        os.makedirs(self.log_dir, exist_ok=True)
        print(f"✓ Logger inicializado para máquina {self.machine_id}")
    
    def _get_log_filepath(self, date: Optional[datetime] = None) -> str:
        """
        Obtém o caminho do arquivo de log para uma data.
        
        Args:
            date: Data para o log (padrão: hoje)
        
        Returns:
            Caminho completo do arquivo Excel
        """
        if date is None:
            date = datetime.now()
        
        # Formato: S06250114.xlsx (máquina + AAMMDD)
        date_str = date.strftime("%y%m%d")
        filename = f"{self.machine_id}{date_str}.xlsx"
        
        return os.path.join(self.log_dir, filename)
    
    def _ensure_log_file(self, filepath: str) -> Workbook:
        """
        Garante que o arquivo de log existe e tem estrutura correta.
        
        Args:
            filepath: Caminho do arquivo Excel
        
        Returns:
            Workbook carregado ou criado
        """
        if os.path.exists(filepath):
            try:
                wb = load_workbook(filepath)
                return wb
            except Exception as e:
                print(f"⚠ Erro ao carregar log existente: {e}")
                print(f"   Criando novo arquivo...")
        
        # Cria novo arquivo
        wb = Workbook()
        ws = wb.active
        ws.title = "Produção"
        
        # Cabeçalhos
        ws.append(["SKU", "Quantidade"])
        
        # Formata cabeçalhos
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        
        wb.save(filepath)
        print(f"✓ Novo arquivo de log criado: {os.path.basename(filepath)}")
        
        return wb
    
    def log_production(self, codigo: float, automatica: bool = False) -> bool:
        """
        Registra uma produção no log.
        
        Args:
            codigo: Código numérico do produto
            automatica: Se foi impressão automática (via GPIO)
        
        Returns:
            True se sucesso, False se falha
        """
        # Converte código para SKU
        sku = self.sku_mapper.get_sku(codigo)
        
        if not sku:
            print(f"⚠ Código {codigo} não encontrado na tabela de SKUs")
            return False
        
        # Obtém arquivo de log
        filepath = self._get_log_filepath()
        
        try:
            wb = self._ensure_log_file(filepath)
            ws = wb.active
            
            # Procura SKU existente
            sku_encontrado = False
            
            for row in range(2, ws.max_row + 1):
                cell_sku = ws.cell(row=row, column=1)
                
                if cell_sku.value == sku:
                    # Incrementa quantidade
                    cell_qtd = ws.cell(row=row, column=2)
                    current_qty = cell_qtd.value or 0
                    cell_qtd.value = current_qty + 1
                    sku_encontrado = True
                    break
            
            # Se não encontrou, adiciona nova linha
            if not sku_encontrado:
                ws.append([sku, 1])
            
            # Salva arquivo
            wb.save(filepath)
            
            modo = "automática" if automatica else "manual"
            print(f"✓ Log registrado ({modo}): SKU {sku} -> {os.path.basename(filepath)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Erro ao registrar log: {e}")
            return False
    
    def log_multiple_productions(self, codigos: list, automatica: bool = False) -> int:
        """
        Registra múltiplas produções.
        
        Args:
            codigos: Lista de códigos numéricos
            automatica: Se foi impressão automática
        
        Returns:
            Número de logs registrados com sucesso
        """
        sucessos = 0
        
        for codigo in codigos:
            if self.log_production(codigo, automatica):
                sucessos += 1
        
        return sucessos
    
    def get_today_summary(self) -> dict:
        """
        Obtém resumo da produção de hoje.
        
        Returns:
            Dict com SKUs e quantidades
        """
        filepath = self._get_log_filepath()
        
        if not os.path.exists(filepath):
            return {}
        
        try:
            wb = load_workbook(filepath, read_only=True)
            ws = wb.active
            
            summary = {}
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                sku, quantidade = row
                if sku and quantidade:
                    summary[sku] = quantidade
            
            wb.close()
            return summary
            
        except Exception as e:
            print(f"Erro ao ler resumo: {e}")
            return {}
    
    def get_total_today(self) -> int:
        """Obtém total de peças produzidas hoje."""
        summary = self.get_today_summary()
        return sum(summary.values())


if __name__ == '__main__':
    # Teste do logger
    from core.sku_mapper import SKUMapper
    
    try:
        mapper = SKUMapper(settings.sku_file_path)
        logger = ProductionLogger(mapper)
        
        print("\nTestando log de produção...")
        
        # Testa log de um código
        test_code = 111.1
        success = logger.log_production(test_code, automatica=False)
        print(f"Log de {test_code}: {'Sucesso' if success else 'Falha'}")
        
        # Testa múltiplos logs
        test_codes = [111.1, 112.1, 111.1]
        count = logger.log_multiple_productions(test_codes, automatica=True)
        print(f"\nLogs múltiplos: {count}/{len(test_codes)} registrados")
        
        # Mostra resumo
        summary = logger.get_today_summary()
        total = logger.get_total_today()
        
        print(f"\nResumo de hoje:")
        for sku, qty in summary.items():
            print(f"  {sku}: {qty} unidades")
        print(f"Total: {total} peças")
        
    except Exception as e:
        print(f"Erro no teste: {e}")