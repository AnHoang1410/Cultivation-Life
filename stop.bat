@echo off
setlocal
title Tien Do Van Kiep - Dung server
cd /d "%~dp0"

if not exist "data\server_port.txt" (
    echo Khong tim thay file cong server. Co the server chua duoc khoi dong.
    pause
    exit /b 0
)
set /p PORT=<"data\server_port.txt"
echo Dang tim va dung server tai cong %PORT%...
powershell -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if($c){ try{ Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop; Write-Host 'Da dung server an toan.' } catch { Write-Host 'Khong the dung tien trinh server.' } } else { Write-Host 'Khong tim thay server dang chay o cong nay.' }"
del "data\server_port.txt" >nul 2>nul
echo.
echo Da xong. Du lieu game da duoc luu trong thu muc data.
pause
