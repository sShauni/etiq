@echo off
title Conversor PDF -> PNG/JPEG (com ou sem rotacao)

echo ===============================
echo   CONVERSAO DE PDF EM LOTE
echo ===============================
echo.

:: Escolher formato
echo Escolha o formato de saida:
echo 1 - PNG (fundo branco)
echo 2 - JPEG
set /p fmt="Opcao: "

if "%fmt%"=="1" (
    set outfmt=png
) else (
    set outfmt=jpg
)

echo.
echo Deseja rotacionar?
echo 0 - Nao rotacionar
echo 1 - 90 graus horario
echo 2 - 90 graus anti-horario
echo 3 - 180 graus
set /p rot="Opcao: "

set rotate_arg=

if "%rot%"=="1" set rotate_arg=-rotate 90
if "%rot%"=="2" set rotate_arg=-rotate "-90"
if "%rot%"=="3" set rotate_arg=-rotate 180

echo.
echo Saida: %outfmt%
echo Rotacao: %rotate_arg%
echo.

mkdir out 2>nul

for %%f in (*.pdf) do (
    echo Convertendo %%f ...

    magick -density 300 "%%f" -quality 100 ^
        -background white -alpha off ^
        %rotate_arg% ^
        "out/%%~nf.%outfmt%"
)

echo.
echo ===============================
echo     Conversao concluida!
echo     Arquivos em /out/
echo ===============================
pause
