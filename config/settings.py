"""
Gerenciamento de configurações do sistema.
Carrega automaticamente a configuração baseada no hostname da máquina.
"""

import json
import os
import socket
from typing import Dict, Any, List, Optional


class Settings:
    """Singleton para gerenciar configurações da aplicação."""
    
    _instance = None
    _config: Dict[str, Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Carrega configuração baseada no hostname ou variável de ambiente."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'machine_config.json'
        )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Arquivo de configuração não encontrado: {config_path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Erro ao parsear JSON de configuração: {e}")
        
        # Prioridade: ENV > Hostname > Default
        machine_id = os.getenv('MACHINE_ID')
        
        if not machine_id:
            try:
                machine_id = socket.gethostname()
            except Exception:
                machine_id = None
        
        # Carrega default como base e sobrescreve com o bloco da máquina
        base = all_configs.get('default', {})

        if machine_id and machine_id in all_configs:
            self._config = {**base, **all_configs[machine_id]}
            print(f"✓ Configuração carregada para máquina: {machine_id}")
        else:
            self._config = base
            print(f"⚠ Usando configuração padrão (máquina: {machine_id or 'desconhecida'})")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração."""
        return self._config.get(key, default)
    
    def get_path(self, key: str) -> str:
        """Obtém um caminho de arquivo, resolvendo relativamente ao projeto."""
        path = self.get(key)
        if not path:
            return ""
        
        # Se já for absoluto, retorna como está
        if os.path.isabs(path):
            return path
        
        # Senão, resolve relativo ao diretório do projeto
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, path)
    
    @property
    def machine_id(self) -> str:
        """ID da máquina atual."""
        return self.get('machine_id', 'UNKNOWN')
    
    @property
    def gpio_pin(self) -> int:
        """Pino GPIO para sinal de impressão."""
        return self.get('gpio_pin', 20)
    
    @property
    def printer_name(self) -> str:
        """Nome da impressora CUPS."""
        return self.get('printer_name', 'Thermal')
    
    @property
    def printer_delay(self) -> float:
        """Delay após impressão via GPIO (em segundos)."""
        return self.get('printer_delay', 1.0)
    
    @property
    def test_mode(self) -> bool:
        """Se está em modo de teste (não imprime de verdade)."""
        return self.get('test_mode', True)
    
    @property
    def log_dir(self) -> str:
        """Diretório para salvar logs Excel."""
        return self.get('log_dir', '/mnt/logs')

    @property
    def db_path(self) -> str:
        """Caminho do banco SQLite local de produção."""
        return self.get_path('db_path') or '/var/local/etiq/producao.db'

    @property
    def pg_host(self) -> str:
        return self.get('pg_host', 'localhost')

    @property
    def pg_port(self) -> int:
        return int(self.get('pg_port', 5432))

    @property
    def pg_dbname(self) -> str:
        return self.get('pg_dbname', 'producao')

    @property
    def pg_user(self) -> str:
        return self.get('pg_user', 'pi')

    @property
    def pg_password(self) -> str:
        return self.get('pg_password', '')
    
    @property
    def sku_file_path(self) -> str:
        """Caminho completo do arquivo SKU.xlsx."""
        return self.get_path('sku_file')
    
    @property
    def labels_dir(self) -> str:
        """Diretório das etiquetas."""
        return self.get_path('labels_dir')
    
    @property
    def label_extension(self) -> str:
        """Extensão dos arquivos de etiqueta."""
        return self.get('label_extension', '.tspl')
    
    @property
    def alturas_exibidas(self) -> List[Dict[str, Any]]:
        """Lista de alturas disponíveis."""
        return self.get('alturas_exibidas', [])
    
    @property
    def botoes_visiveis(self) -> List[bool]:
        """Quais botões de altura devem ser visíveis."""
        return self.get('botoes_visiveis', [])
    
    @property
    def fios(self) -> List[str]:
        """Lista de fios disponíveis."""
        return self.get('fios', [])
    
    @property
    def fios_visiveis(self) -> List[bool]:
        """Quais fios devem ser visíveis."""
        return self.get('fios_visiveis', [])
    
    @property
    def malhas(self) -> List[str]:
        """Lista de malhas disponíveis."""
        return self.get('malhas', [])
    
    @property
    def malhas_visiveis(self) -> List[bool]:
        """Quais malhas devem ser visíveis."""
        return self.get('malhas_visiveis', [])
    
    @property
    def combinacoes_validas(self) -> List[List[int]]:
        """Combinações válidas de alturas."""
        return [tuple(c) for c in self.get('combinacoes_validas', [])]
    
    @property
    def primario_valor(self) -> Dict[int, float]:
        """Mapeamento de valores primários."""
        raw = self.get('primario_valor', {})
        return {int(k): float(v) for k, v in raw.items()}
    
    @property
    def secundario_valor(self) -> Dict[int, float]:
        """Mapeamento de valores secundários."""
        raw = self.get('secundario_valor', {})
        return {int(k): float(v) for k, v in raw.items()}


# Singleton global
settings = Settings()


if __name__ == '__main__':
    # Teste de carregamento
    print(f"Machine ID: {settings.machine_id}")
    print(f"GPIO Pin: {settings.gpio_pin}")
    print(f"Printer: {settings.printer_name}")
    print(f"Test Mode: {settings.test_mode}")
    print(f"SKU File: {settings.sku_file_path}")
    print(f"Labels Dir: {settings.labels_dir}")
    print(f"Alturas: {len(settings.alturas_exibidas)} configuradas")