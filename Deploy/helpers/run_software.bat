@echo OFF
echo === run_software.bat ===
echo %date% %time%

set CONDAPATH=C:\ProgramData\anaconda3
set ENVNAME=FIGHT

if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)

call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
cd ../software
pip install -r requirements.txt
python -u main.py > logs/out.log 2>&1
call conda deactivate