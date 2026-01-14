"""
Cálculo de códigos de saída baseado nas seleções.
Implementa a lógica de negócio para gerar códigos numéricos.
"""

from typing import List, Optional
from config.settings import settings


class OutputCalculator:
    """Calcula códigos de saída baseado em altura, fio e malha."""
    
    def __init__(self):
        """Inicializa com as configurações atuais."""
        self.alturas_exibidas = settings.alturas_exibidas
        self.primario_valor = settings.primario_valor
        self.secundario_valor = settings.secundario_valor
    
    def calculate_single_output(
        self,
        altura_index: int,
        fio_index: int,
        malha_index: int,
        altura_indices_selecionadas: List[int]
    ) -> Optional[float]:
        """
        Calcula o código de saída para uma altura específica.
        
        Args:
            altura_index: Índice da altura atual
            fio_index: Índice do fio selecionado
            malha_index: Índice da malha selecionada
            altura_indices_selecionadas: Lista com todas as alturas selecionadas
        
        Returns:
            Código numérico ou None se inválido
        """
        if fio_index is None or malha_index is None:
            return None
        
        # Obtém o índice base da altura atual
        base_idx = self.alturas_exibidas[altura_index]['base']
        
        # Encontra todas as alturas com a mesma base
        alturas_mesma_base = [
            i for i in altura_indices_selecionadas 
            if self.alturas_exibidas[i]['base'] == base_idx
        ]
        
        # Decide se usa valor primário ou secundário
        if len(alturas_mesma_base) == 1 or altura_index == alturas_mesma_base[0]:
            altura_val = self.primario_valor.get(base_idx, 0)
        else:
            altura_val = self.secundario_valor.get(
                base_idx, 
                self.primario_valor.get(base_idx, 0)
            )
        
        # Fórmula: altura + 10*(fio+1) + 100*(malha+1)
        resultado = altura_val + 10 * (fio_index + 1) + 100 * (malha_index + 1)
        
        return round(resultado, 1)
    
    def calculate_output(
        self,
        altura_indices: List[int],
        fio_index: Optional[int],
        malha_index: Optional[int]
    ) -> Optional[float]:
        """
        Calcula o código de saída combinado (para display).
        
        Args:
            altura_indices: Lista de índices de alturas selecionadas
            fio_index: Índice do fio selecionado
            malha_index: Índice da malha selecionada
        
        Returns:
            Código numérico combinado ou None se inválido
        """
        if not altura_indices or fio_index is None or malha_index is None:
            return None
        
        # Calcula a soma dos valores de altura
        altura_val = 0
        for idx in altura_indices:
            individual = self.calculate_single_output(
                idx, fio_index, malha_index, altura_indices
            )
            if individual is None:
                return None
            
            # Remove a contribuição de fio e malha para somar só altura
            altura_val += individual - 10 * (fio_index + 1) - 100 * (malha_index + 1)
        
        # Adiciona de volta fio e malha uma vez
        resultado = altura_val + 10 * (fio_index + 1) + 100 * (malha_index + 1)
        
        return round(resultado, 1)
    
    def calculate_all_outputs(
        self,
        altura_indices: List[int],
        fio_index: Optional[int],
        malha_index: Optional[int]
    ) -> List[float]:
        """
        Calcula códigos individuais para cada altura selecionada.
        
        Args:
            altura_indices: Lista de índices de alturas selecionadas
            fio_index: Índice do fio selecionado
            malha_index: Índice da malha selecionada
        
        Returns:
            Lista de códigos numéricos (um para cada altura)
        """
        outputs = []
        
        for idx in altura_indices:
            output = self.calculate_single_output(
                idx, fio_index, malha_index, altura_indices
            )
            if output is not None:
                outputs.append(output)
        
        return outputs


if __name__ == '__main__':
    # Teste do calculador
    calculator = OutputCalculator()
    
    # Teste 1: Uma altura
    output = calculator.calculate_output([0], 0, 0)
    print(f"Teste 1 (uma altura): {output}")
    
    # Teste 2: Duas alturas
    output = calculator.calculate_output([0, 1], 0, 0)
    print(f"Teste 2 (duas alturas): {output}")
    
    # Teste 3: Códigos individuais
    outputs = calculator.calculate_all_outputs([0, 1], 0, 0)
    print(f"Teste 3 (individuais): {outputs}")
    
    # Teste 4: Sem fio (deve retornar None)
    output = calculator.calculate_output([0], None, 0)
    print(f"Teste 4 (sem fio): {output}")
    
    # Teste 5: Diferentes fios e malhas
    output = calculator.calculate_output([2], 2, 1)
    print(f"Teste 5 (fio 2, malha 1): {output}")