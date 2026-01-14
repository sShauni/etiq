# config/__init__.py
"""Módulo de configuração do sistema."""

from .settings import settings

__all__ = ['settings']


# core/__init__.py
"""Módulos principais de lógica de negócio."""

from .calculator import OutputCalculator
from .validator import SelectionValidator
from .sku_mapper import SKUMapper

__all__ = ['OutputCalculator', 'SelectionValidator', 'SKUMapper']


# hardware/__init__.py
"""Módulos de interface com hardware."""

from .printer import LabelPrinter, PrinterError
from .gpio_handler import GPIOHandler

__all__ = ['LabelPrinter', 'PrinterError', 'GPIOHandler']


# data/__init__.py
"""Módulos de gerenciamento de dados."""

from .logger import ProductionLogger
from .samba_client import SambaClient

__all__ = ['ProductionLogger', 'SambaClient']


# ui/__init__.py
"""Módulos de interface gráfica."""

from .main_window import MainWindow

__all__ = ['MainWindow']