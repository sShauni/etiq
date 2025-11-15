@echo off
title Conversor para BMP (TSPL2)

echo ================================
echo   CONVERTER IMAGENS PARA BMP
echo   (compatível com TSPL2)
echo ================================
echo.

:: Criar pasta de saída
mkdir out 2>nul

:: Pergunta se quer rotacionar
echo Deseja rotacionar a imagem?
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
echo Convertendo todos os PDFs/PNGs/JPGs da pasta...
echo.

for %%f in (*.pdf *.png *.jpg *.jpeg) do (
    echo Convertendo %%f...

    magick "%%f" ^
        -density 300 ^
        -background white -alpha remove -alpha off ^
        %rotate_arg% ^
        -colorspace Gray ^
        -type Grayscale ^
        -define bmp:format=bmp2 ^
        "out/%%~nf.bmp"
)

echo.
echo ===========
echo   PRONTO!
echo   Arquivos .BMP estao na pasta /out/
echo ===========
pause
