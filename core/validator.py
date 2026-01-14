"""
Validação de combinações de altura, fio e malha.
Garante que apenas combinações válidas sejam processadas.
"""

from typing import List, Tuple, Optional
from config.settings import settings


class SelectionValidator:
    """Valida seleções de altura, fio e malha."""
    
    def __init__(self):
        """Inicializa com as configurações atuais."""
        self.alturas_exibidas = settings.alturas_exibidas
        self.combinacoes_validas = settings.combinacoes_validas
    
    def validate_altura_selection(self, altura_indices: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Valida seleção de alturas.
        
        Args:
            altura_indices: Lista de índices de alturas selecionadas
        
        Returns:
            (válido, mensagem_erro)
        """
        if not altura_indices:
            return False, "Selecione ao menos uma altura"
        
        if len(altura_indices) > 2:
            return False, "Só é possível selecionar até duas alturas"
        
        # Se selecionou 2 alturas, valida a combinação
        if len(altura_indices) == 2:
            base1 = self.alturas_exibidas[altura_indices[0]]['base']
            base2 = self.alturas_exibidas[altura_indices[1]]['base']
            
            # Verifica se a combinação está na lista de válidas
            if (base1, base2) not in self.combinacoes_validas and \
               (base2, base1) not in self.combinacoes_validas:
                return False, "Combinação de alturas inválida"
        
        return True, None
    
    def validate_complete_selection(
        self, 
        altura_indices: List[int],
        fio_index: Optional[int],
        malha_index: Optional[int]
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida uma seleção completa.
        
        Args:
            altura_indices: Índices das alturas selecionadas
            fio_index: Índice do fio selecionado
            malha_index: Índice da malha selecionada
        
        Returns:
            (válido, mensagem_erro)
        """
        # Valida alturas
        valid, error = self.validate_altura_selection(altura_indices)
        if not valid:
            return False, error
        
        # Valida fio
        if fio_index is None:
            return False, "Selecione um fio"
        
        # Valida malha
        if malha_index is None:
            return False, "Selecione uma malha"
        
        return True, None
    
    def get_altura_base(self, altura_index: int) -> int:
        """Obtém o índice base de uma altura."""
        if 0 <= altura_index < len(self.alturas_exibidas):
            return self.alturas_exibidas[altura_index]['base']
        return -1
    
    def is_valid_combination(self, base1: int, base2: int) -> bool:
        """Verifica se uma combinação de bases é válida."""
        return (base1, base2) in self.combinacoes_validas or \
               (base2, base1) in self.combinacoes_validas


if __name__ == '__main__':
    # Teste do validador
    validator = SelectionValidator()
    
    # Teste 1: Sem altura
    valid, error = validator.validate_altura_selection([])
    print(f"Teste 1 (sem altura): {valid} - {error}")
    
    # Teste 2: Uma altura
    valid, error = validator.validate_altura_selection([0])
    print(f"Teste 2 (uma altura): {valid} - {error}")
    
    # Teste 3: Duas alturas válidas
    valid, error = validator.validate_altura_selection([0, 1])
    print(f"Teste 3 (duas válidas): {valid} - {error}")
    
    # Teste 4: Três alturas (inválido)
    valid, error = validator.validate_altura_selection([0, 1, 2])
    print(f"Teste 4 (três alturas): {valid} - {error}")
    
    # Teste 5: Seleção completa
    valid, error = validator.validate_complete_selection([0], 0, 0)
    print(f"Teste 5 (seleção completa): {valid} - {error}")
    
    # Teste 6: Seleção incompleta
    valid, error = validator.validate_complete_selection([0], None, 0)
    print(f"Teste 6 (sem fio): {valid} - {error}")