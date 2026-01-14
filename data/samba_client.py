"""
Cliente Samba para upload de logs ao servidor.
Inclui retry logic e verificação de conectividade.
"""

import os
import time
import subprocess
from typing import Optional, Tuple
from datetime import datetime


class SambaClient:
    """Gerencia upload de arquivos via Samba com retry."""
    
    def __init__(self, mount_point: str = "/mnt/logs"):
        """
        Inicializa o cliente Samba.
        
        Args:
            mount_point: Ponto de montagem do compartilhamento Samba
        """
        self.mount_point = mount_point
        self.max_retries = 3
        self.retry_delay = 5  # segundos
        
        # Verifica se o ponto de montagem existe
        if not os.path.exists(mount_point):
            print(f"⚠ Ponto de montagem não existe: {mount_point}")
    
    def is_mounted(self) -> bool:
        """
        Verifica se o compartilhamento Samba está montado.
        
        Returns:
            True se montado, False caso contrário
        """
        try:
            # Verifica se o diretório está acessível e não vazio
            if not os.path.exists(self.mount_point):
                return False
            
            # Tenta criar um arquivo de teste
            test_file = os.path.join(self.mount_point, '.connection_test')
            
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except (IOError, OSError):
                return False
                
        except Exception as e:
            print(f"⚠ Erro ao verificar montagem: {e}")
            return False
    
    def mount_share(self, force_remount: bool = False) -> bool:
        """
        Tenta montar o compartilhamento Samba.
        
        Args:
            force_remount: Se True, desmonta antes de montar
        
        Returns:
            True se sucesso, False se falha
        """
        try:
            # Se já está montado e não é para forçar, retorna sucesso
            if self.is_mounted() and not force_remount:
                print("✓ Compartilhamento já está montado")
                return True
            
            # Força desmontagem se solicitado
            if force_remount:
                self.unmount_share()
            
            # Executa script de montagem se existir
            mount_script = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'montar_logs.sh'
            )
            
            if os.path.exists(mount_script):
                result = subprocess.run(
                    ['bash', mount_script],
                    capture_output=True,
                    timeout=30,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✓ Compartilhamento montado via script")
                    return self.is_mounted()
                else:
                    print(f"⚠ Script de montagem falhou: {result.stderr}")
            
            return False
            
        except subprocess.TimeoutExpired:
            print("✗ Timeout ao tentar montar compartilhamento")
            return False
        except Exception as e:
            print(f"✗ Erro ao montar compartilhamento: {e}")
            return False
    
    def unmount_share(self) -> bool:
        """
        Desmonta o compartilhamento Samba.
        
        Returns:
            True se sucesso, False se falha
        """
        try:
            subprocess.run(
                ['umount', self.mount_point],
                capture_output=True,
                timeout=10
            )
            print("✓ Compartilhamento desmontado")
            return True
        except Exception as e:
            print(f"⚠ Erro ao desmontar: {e}")
            return False
    
    def upload_file(self, local_path: str, filename: Optional[str] = None) -> bool:
        """
        Faz upload de um arquivo para o servidor Samba.
        
        Args:
            local_path: Caminho do arquivo local
            filename: Nome do arquivo no servidor (padrão: mesmo nome)
        
        Returns:
            True se sucesso, False se falha
        """
        if not os.path.exists(local_path):
            print(f"✗ Arquivo local não existe: {local_path}")
            return False
        
        if filename is None:
            filename = os.path.basename(local_path)
        
        remote_path = os.path.join(self.mount_point, filename)
        
        # Tenta upload com retries
        for attempt in range(self.max_retries):
            try:
                # Verifica montagem
                if not self.is_mounted():
                    print(f"⚠ Tentativa {attempt + 1}: Compartilhamento não montado")
                    
                    if not self.mount_share():
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return False
                
                # Copia arquivo
                import shutil
                shutil.copy2(local_path, remote_path)
                
                # Verifica se foi copiado
                if os.path.exists(remote_path):
                    print(f"✓ Upload concluído: {filename}")
                    return True
                else:
                    raise IOError("Arquivo não encontrado após cópia")
                    
            except Exception as e:
                print(f"⚠ Tentativa {attempt + 1}/{self.max_retries} falhou: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"✗ Falha total no upload de {filename}")
                    return False
        
        return False
    
    def get_connection_status(self) -> dict:
        """
        Obtém status detalhado da conexão.
        
        Returns:
            Dict com informações de status
        """
        mounted = self.is_mounted()
        
        status = {
            'mounted': mounted,
            'mount_point': self.mount_point,
            'accessible': os.path.exists(self.mount_point),
            'timestamp': datetime.now().isoformat()
        }
        
        if mounted:
            try:
                # Tenta obter espaço disponível
                stat = os.statvfs(self.mount_point)
                
                total = stat.f_frsize * stat.f_blocks
                available = stat.f_frsize * stat.f_bavail
                
                status['total_space_gb'] = round(total / (1024**3), 2)
                status['available_space_gb'] = round(available / (1024**3), 2)
                status['used_percent'] = round((1 - available/total) * 100, 1)
                
            except Exception as e:
                status['error'] = str(e)
        
        return status


if __name__ == '__main__':
    # Teste do cliente Samba
    client = SambaClient()
    
    print("=== Teste do Cliente Samba ===\n")
    
    # Verifica status
    status = client.get_connection_status()
    print("Status da conexão:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print(f"\nMontado: {client.is_mounted()}")
    
    # Tenta montar se não estiver
    if not client.is_mounted():
        print("\nTentando montar compartilhamento...")
        if client.mount_share():
            print("✓ Montagem bem-sucedida")
        else:
            print("✗ Falha na montagem")
    
    # Teste de upload (comentado por segurança)
    # test_file = "test.txt"
    # with open(test_file, 'w') as f:
    #     f.write("Teste de upload")
    # 
    # if client.upload_file(test_file):
    #     print(f"✓ Upload de {test_file} concluído")
    # else:
    #     print(f"✗ Upload de {test_file} falhou")
    # 
    # os.remove(test_file)