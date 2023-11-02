@echo off
echo === kill_task === >> out_kill.log 2>&1
echo %date% %time% >> out_kill.log 2>&1
schtasks /end /tn \fight-pilot\fight-pilot-runner >> out_kill.log 2>&1
taskkill /IM python.exe /T /F >> out_kill.log 2>&1