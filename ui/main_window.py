"""
Interface gráfica principal do sistema de etiquetas.
Usa Tkinter para criar a UI de seleção.
"""

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Callable
from config.settings import settings
from core.calculator import OutputCalculator
from core.validator import SelectionValidator


class MainWindow:
    """Janela principal da aplicação."""
    
    def __init__(
        self,
        on_print_callback: Callable[[List[int], int, int], None]
    ):
        """
        Inicializa a janela principal.
        
        Args:
            on_print_callback: Função chamada quando usuário clica em imprimir
                              Recebe (altura_indices, fio_index, malha_index)
        """
        self.on_print = on_print_callback
        
        # Componentes core
        self.calculator = OutputCalculator()
        self.validator = SelectionValidator()
        
        # Estado da seleção
        self.selected_alturas: List[int] = []
        self.selected_fio: Optional[int] = None
        self.selected_malha: Optional[int] = None
        
        # Configurações
        self.alturas_config = settings.alturas_exibidas
        self.botoes_visiveis = settings.botoes_visiveis
        self.fios = settings.fios
        self.fios_visiveis = settings.fios_visiveis
        self.malhas = settings.malhas
        self.malhas_visiveis = settings.malhas_visiveis
        
        # Widgets
        self.root: Optional[tk.Tk] = None
        self.altura_buttons: List[tk.Button] = []
        self.fio_buttons: List[tk.Button] = []
        self.malha_buttons: List[tk.Button] = []
        self.output_var: Optional[tk.StringVar] = None
        
        self._create_window()
    
    def _create_window(self) -> None:
        """Cria a janela e todos os widgets."""
        self.root = tk.Tk()
        self.root.title(f"Selecionador de Etiquetas - {settings.machine_id}")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="white")
        self.root.bind("<Escape>", lambda e: self.close())
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(pady=10)
        
        # Cria colunas de seleção
        self._create_altura_column(main_frame)
        self._create_option_column(main_frame, "Fio", self.fios, self.fios_visiveis, "fio")
        self._create_option_column(main_frame, "Malha", self.malhas, self.malhas_visiveis, "malha")
        
        # Label de saída
        self.output_var = tk.StringVar()
        self.output_var.set("Faça suas seleções")
        
        tk.Label(
            self.root,
            textvariable=self.output_var,
            font=("Arial", 12),
            bg="white"
        ).pack(pady=5)
        
        # Botão de impressão
        tk.Button(
            self.root,
            text="Imprimir etiqueta",
            command=self._on_print_clicked,
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2
        ).pack(pady=8)
    
    def _create_altura_column(self, parent: tk.Frame) -> None:
        """Cria a coluna de seleção de alturas."""
        column = tk.Frame(parent, bg="white")
        
        # Cabeçalho
        tk.Label(
            column,
            text="Altura(s)",
            font=("Arial", 10, "bold"),
            bg="lightgreen",
            width=20
        ).grid(row=0, column=0, columnspan=2)
        
        # Botões
        self.altura_buttons = []
        altura_visual_map = []
        row, col = 1, 0
        
        for idx, altura_config in enumerate(self.alturas_config):
            if not self.botoes_visiveis[idx]:
                continue
            
            button = tk.Button(
                column,
                text=altura_config['texto'],
                width=12,
                height=2,
                font=("Arial", 10),
                bg="lightgray",
                command=lambda i=idx: self._on_altura_clicked(i)
            )
            button.grid(row=row, column=col, padx=2, pady=2)
            
            self.altura_buttons.append(button)
            altura_visual_map.append(idx)
            
            col = 0 if col >= 1 else 1
            if col == 0:
                row += 1
        
        self._altura_visual_map = altura_visual_map
        column.pack(side=tk.LEFT, padx=5)
    
    def _create_option_column(
        self,
        parent: tk.Frame,
        title: str,
        options: List[str],
        visible: List[bool],
        option_type: str
    ) -> None:
        """Cria uma coluna de opções (fio ou malha)."""
        column = tk.Frame(parent, bg="white")
        
        # Cabeçalho
        tk.Label(
            column,
            text=title,
            font=("Arial", 10, "bold"),
            bg="lightgreen",
            width=14
        ).pack()
        
        # Botões
        buttons = []
        visual_map = []
        
        for idx, option in enumerate(options):
            if not visible[idx]:
                continue
            
            button = tk.Button(
                column,
                text=option,
                width=12,
                height=2,
                font=("Arial", 10),
                bg="lightgray",
                command=lambda i=idx, t=option_type: self._on_option_clicked(i, t)
            )
            button.pack(pady=2)
            
            buttons.append(button)
            visual_map.append(idx)
        
        # Armazena referências
        if option_type == "fio":
            self.fio_buttons = buttons
            self._fio_visual_map = visual_map
        else:
            self.malha_buttons = buttons
            self._malha_visual_map = visual_map
        
        column.pack(side=tk.LEFT, padx=5)
    
    def _on_altura_clicked(self, altura_idx: int) -> None:
        """Callback quando uma altura é clicada."""
        if altura_idx in self.selected_alturas:
            # Deseleciona
            self.selected_alturas.remove(altura_idx)
        elif len(self.selected_alturas) < 2:
            # Seleciona
            self.selected_alturas.append(altura_idx)
        else:
            messagebox.showwarning(
                "Erro",
                "Só é possível selecionar até duas alturas."
            )
            return
        
        self._update_altura_buttons()
        self._update_output_display()
    
    def _on_option_clicked(self, option_idx: int, option_type: str) -> None:
        """Callback quando fio ou malha é clicado."""
        if option_type == "fio":
            self.selected_fio = option_idx
            self._update_fio_buttons()
        else:
            self.selected_malha = option_idx
            self._update_malha_buttons()
        
        self._update_output_display()
    
    def _update_altura_buttons(self) -> None:
        """Atualiza cores dos botões de altura."""
        for i, button in enumerate(self.altura_buttons):
            actual_idx = self._altura_visual_map[i]
            color = "mediumpurple1" if actual_idx in self.selected_alturas else "lightgray"
            button.config(bg=color)
    
    def _update_fio_buttons(self) -> None:
        """Atualiza cores dos botões de fio."""
        for i, button in enumerate(self.fio_buttons):
            actual_idx = self._fio_visual_map[i]
            color = "mediumpurple1" if actual_idx == self.selected_fio else "lightgray"
            button.config(bg=color)
    
    def _update_malha_buttons(self) -> None:
        """Atualiza cores dos botões de malha."""
        for i, button in enumerate(self.malha_buttons):
            actual_idx = self._malha_visual_map[i]
            color = "mediumpurple1" if actual_idx == self.selected_malha else "lightgray"
            button.config(bg=color)
    
    def _update_output_display(self) -> None:
        """Atualiza o display de saída."""
        valor = self.calculator.calculate_output(
            self.selected_alturas,
            self.selected_fio,
            self.selected_malha
        )
        
        if valor is not None:
            self.output_var.set(f"Valor de saída: {valor:.1f}")
        else:
            # Valida para mostrar mensagem apropriada
            valid, error = self.validator.validate_complete_selection(
                self.selected_alturas,
                self.selected_fio,
                self.selected_malha
            )
            
            if error:
                self.output_var.set(error)
            else:
                self.output_var.set("Faça suas seleções")
    
    def _on_print_clicked(self) -> None:
        """Callback quando botão de imprimir é clicado."""
        # Valida seleção
        valid, error = self.validator.validate_complete_selection(
            self.selected_alturas,
            self.selected_fio,
            self.selected_malha
        )
        
        if not valid:
            messagebox.showerror("Erro", error)
            return
        
        # Chama callback externo
        self.on_print(
            self.selected_alturas,
            self.selected_fio,
            self.selected_malha
        )
    
    def trigger_auto_print(self) -> None:
        """Dispara impressão automática (via GPIO)."""
        # Valida seleção silenciosamente
        valid, _ = self.validator.validate_complete_selection(
            self.selected_alturas,
            self.selected_fio,
            self.selected_malha
        )
        
        if valid:
            # Chama callback com flag de automática
            self.on_print(
                self.selected_alturas,
                self.selected_fio,
                self.selected_malha,
                automatica=True
            )
    
    def run(self) -> None:
        """Inicia o loop principal da aplicação."""
        if self.root:
            self.root.mainloop()
    
    def close(self) -> None:
        """Fecha a aplicação."""
        if self.root:
            self.root.destroy()
    
    def get_root(self) -> tk.Tk:
        """Retorna a janela root (para integração com GPIO)."""
        return self.root