"""
Sistema de logging de produção em CSV.
Registra SKUs produzidos por máquina e data.
"""

import os
import csv
from datetime import datetime
from typing import Optional, Dict
from config.settings import settings
from core.sku_mapper import SKUMapper


class ProductionLogger:
    """Gerencia logs de produção em arquivos CSV."""
    
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
            Caminho completo do arquivo CSV
        """
        if date is None:
            date = datetime.now()
        
        # Formato: S06250114.csv (máquina + AAMMDD)
        date_str = date.strftime("%y%m%d")
        filename = f"{self.machine_id}{date_str}.csv"
        
        return os.path.join(self.log_dir, filename)
    
    def _read_csv_data(self, filepath: str) -> Dict[str, int]:
        """
        Lê dados do CSV e retorna um dicionário SKU -> Quantidade.
        
        Args:
            filepath: Caminho do arquivo CSV
        
        Returns:
            Dict com SKUs e quantidades
        """
        data = {}
        
        if not os.path.exists(filepath):
            return data
        
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sku = row.get('SKU', '').strip()
                    quantidade = row.get('Quantidade', '0').strip()
                    
                    if sku:
                        try:
                            data[sku] = int(quantidade)
                        except ValueError:
                            data[sku] = 0
        except Exception as e:
            print(f"⚠ Erro ao ler CSV: {e}")
        
        return data
    
    def _write_csv_data(self, filepath: str, data: Dict[str, int]) -> bool:
        """
        Escreve dados no CSV.
        
        Args:
            filepath: Caminho do arquivo CSV
            data: Dict com SKUs e quantidades
        
        Returns:
            True se sucesso, False se falha
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Escreve cabeçalho
                writer.writerow(['SKU', 'Quantidade'])
                
                # Escreve dados ordenados por SKU
                for sku in sorted(data.keys()):
                    writer.writerow([sku, data[sku]])
            
            return True
            
        except Exception as e:
            print(f"✗ Erro ao escrever CSV: {e}")
            return False
    
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
            # Lê dados existentes
            data = self._read_csv_data(filepath)
            
            # Incrementa ou adiciona SKU
            if sku in data:
                data[sku] += 1
            else:
                data[sku] = 1
            
            # Salva de volta
            if self._write_csv_data(filepath, data):
                modo = "automática" if automatica else "manual"
                print(f"✓ Log registrado ({modo}): SKU {sku} -> {os.path.basename(filepath)}")
                return True
            else:
                return False
            
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
    
    def get_today_summary(self) -> Dict[str, int]:
        """
        Obtém resumo da produção de hoje.
        
        Returns:
            Dict com SKUs e quantidades
        """
        filepath = self._get_log_filepath()
        return self._read_csv_data(filepath)
    
    def get_total_today(self) -> int:
        """Obtém total de peças produzidas hoje."""
        summary = self.get_today_summary()
        return sum(summary.values())
    
    def export_to_excel(self, date: Optional[datetime] = None) -> Optional[str]:
        """
        Exporta CSV para Excel (opcional, requer openpyxl).
        
        Args:
            date: Data do log (padrão: hoje)
        
        Returns:
            Caminho do arquivo Excel criado ou None se falhar
        """
        try:
            from openpyxl import Workbook
            
            csv_path = self._get_log_filepath(date)
            data = self._read_csv_data(csv_path)
            
            if not data:
                print("Nenhum dado para exportar")
                return None
            
            # Cria arquivo Excel
            excel_path = csv_path.replace('.csv', '.xlsx')
            wb = Workbook()
            ws = wb.active
            ws.title = "Produção"
            
            # Cabeçalhos
            ws.append(['SKU', 'Quantidade'])
            
            # Dados
            for sku in sorted(data.keys()):
                ws.append([sku, data[sku]])
            
            # Formata cabeçalhos
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
            
            wb.save(excel_path)
            print(f"✓ Exportado para Excel: {os.path.basename(excel_path)}")
            
            return excel_path
            
        except ImportError:
            print("⚠ openpyxl não instalado, não é possível exportar para Excel")
            return None
        except Exception as e:
            print(f"✗ Erro ao exportar para Excel: {e}")
            return None


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
        
        # Testa exportação para Excel (opcional)
        print("\nTestando exportação para Excel...")
        excel_path = logger.export_to_excel()
        if excel_path:
            print(f"Excel criado: {excel_path}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")