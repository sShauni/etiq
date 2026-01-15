#!/bin/bash
# Script de diagnóstico para problemas de startup

echo "======================================================"
echo "  DIAGNÓSTICO - Sistema de Etiquetas"
echo "======================================================"
echo ""

# 1. Verifica estrutura de arquivos
echo "1. VERIFICANDO ESTRUTURA DE ARQUIVOS..."
echo "------------------------------------------------------"

required_dirs=("config" "core" "hardware" "data" "ui" "etiquetas")
missing_dirs=()

for dir in "${required_dirs[@]}"; do
    if [ -d "/home/pi/etiq/$dir" ]; then
        echo "✓ Diretório existe: $dir"
    else
        echo "✗ FALTA diretório: $dir"
        missing_dirs+=("$dir")
    fi
done

required_files=(
    "main.py"
    "SKU.xlsx"
    "config/__init__.py"
    "config/settings.py"
    "config/machine_config.json"
    "core/__init__.py"
    "core/calculator.py"
    "core/validator.py"
    "core/sku_mapper.py"
    "hardware/__init__.py"
    "hardware/printer.py"
    "hardware/gpio_handler.py"
    "data/__init__.py"
    "data/logger.py"
    "data/samba_client.py"
    "ui/__init__.py"
    "ui/main_window.py"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "/home/pi/etiq/$file" ]; then
        echo "✓ Arquivo existe: $file"
    else
        echo "✗ FALTA arquivo: $file"
        missing_files+=("$file")
    fi
done

echo ""

# 2. Verifica permissões
echo "2. VERIFICANDO PERMISSÕES..."
echo "------------------------------------------------------"
ls -la /home/pi/etiq/main.py
echo ""

# 3. Verifica dependências Python
echo "3. VERIFICANDO DEPENDÊNCIAS PYTHON..."
echo "------------------------------------------------------"
python3 -c "import tkinter; print('✓ tkinter disponível')" 2>/dev/null || echo "✗ tkinter NÃO disponível"
python3 -c "import openpyxl; print('✓ openpyxl disponível')" 2>/dev/null || echo "⚠ openpyxl NÃO disponível (opcional)"
python3 -c "import csv; print('✓ csv disponível')" 2>/dev/null || echo "✗ csv NÃO disponível"
echo ""

# 4. Testa importação dos módulos
echo "4. TESTANDO IMPORTAÇÃO DOS MÓDULOS..."
echo "------------------------------------------------------"
cd /home/pi/etiq

python3 << 'EOF'
import sys
sys.path.insert(0, '/home/pi/etiq')

modules = [
    'config.settings',
    'core.sku_mapper',
    'core.calculator',
    'core.validator',
    'hardware.printer',
    'hardware.gpio_handler',
    'data.logger',
    'data.samba_client',
    'ui.main_window'
]

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except Exception as e:
        print(f"✗ {module}: {e}")
EOF

echo ""

# 5. Verifica configuração
echo "5. VERIFICANDO CONFIGURAÇÃO..."
echo "------------------------------------------------------"
if [ -f "/home/pi/etiq/config/machine_config.json" ]; then
    echo "Hostname atual: $(hostname)"
    python3 -c "from config.settings import settings; print(f'Machine ID detectado: {settings.machine_id}')" 2>&1
else
    echo "✗ Arquivo machine_config.json não encontrado!"
fi
echo ""

# 6. Verifica logs do systemd
echo "6. ÚLTIMOS LOGS DO SYSTEMD..."
echo "------------------------------------------------------"
if systemctl is-active --quiet startup.service; then
    echo "✓ Serviço está ATIVO"
else
    echo "✗ Serviço está INATIVO"
fi

echo ""
echo "Status do serviço:"
systemctl status startup.service --no-pager -l | tail -20

echo ""
echo "Últimas 30 linhas do journalctl:"
journalctl -u startup.service --no-pager -n 30

echo ""

# 7. Verifica log do aplicativo
echo "7. VERIFICANDO LOG DO APLICATIVO..."
echo "------------------------------------------------------"
if [ -f "/home/pi/etiq/log.txt" ]; then
    echo "Últimas 30 linhas de log.txt:"
    tail -30 /home/pi/etiq/log.txt
else
    echo "⚠ Arquivo log.txt não existe ainda"
fi

echo ""
echo "======================================================"
echo "  FIM DO DIAGNÓSTICO"
echo "======================================================"
echo ""

# 8. Resumo
echo "RESUMO:"
if [ ${#missing_dirs[@]} -gt 0 ]; then
    echo "✗ Faltam ${#missing_dirs[@]} diretórios"
fi

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "✗ Faltam ${#missing_files[@]} arquivos"
fi

if [ ${#missing_dirs[@]} -eq 0 ] && [ ${#missing_files[@]} -eq 0 ]; then
    echo "✓ Todos os arquivos e diretórios estão presentes"
    echo ""
    echo "PRÓXIMOS PASSOS:"
    echo "1. Verifique os logs acima para identificar o erro"
    echo "2. Teste manualmente: cd /home/pi/etiq && python3 main.py"
    echo "3. Se funcionar manualmente, o problema é no systemd"
fi

echo ""