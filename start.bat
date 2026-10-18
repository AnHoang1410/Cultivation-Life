@echo off
setlocal EnableDelayedExpansion
title Tien Do Van Kiep - Khoi dong
cd /d "%~dp0"

echo ==========================================================
echo    TIEN DO VAN KIEP - Khoi dong tro choi
echo ==========================================================
echo.

rem ---------- 1. Kiem tra Python ----------
set "PYTHON_CMD="
python --version >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    echo [LOI] May tinh chua cai Python.
    echo.
    echo Huong dan cai dat cho nguoi moi:
    echo   1. Mo trinh duyet, vao https://www.python.org/downloads/
    echo   2. Tai phien ban Python 3.11 hoac moi hon roi chay file cai dat.
    echo   3. QUAN TRONG: trong man hinh cai dat, TICH vao muc
    echo      "Add python.exe to PATH" truoc khi nhan Install.
    echo   4. Cai xong, dong cua so nay va nhan doi start.bat lai.
    echo.
    pause
    exit /b 1
)
echo [1/6] Da tim thay Python.

rem ---------- 2. Tao moi truong ao ----------
if not exist ".venv\Scripts\python.exe" (
    echo [2/6] Dang tao moi truong Python rieng cho game lan dau...
    %PYTHON_CMD% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [LOI] Tao moi truong ao that bai. Hay xoa thu muc .venv roi chay lai.
        pause
        exit /b 1
    )
) else (
    echo [2/6] Moi truong Python da san sang.
)
set "PY=%~dp0.venv\Scripts\python.exe"

rem ---------- 3. Kiem tra / cai thu vien ----------
echo [3/6] Kiem tra thu vien can thiet...
"%PY%" -c "import flask, requests" >nul 2>nul
if errorlevel 1 (
    echo        Dang cai dat thu vien, lan dau chay mat vai phut...
    "%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
    "%PY%" -c "import flask, requests" >nul 2>nul
    if errorlevel 1 (
        echo [LOI] Cai dat thu vien that bai. Kiem tra ket noi internet roi chay lai.
        pause
        exit /b 1
    )
)
echo        Thu vien da du.

rem ---------- 4. Kiem tra server da chay chua (tranh khoi dong trung) ----------
for %%P in (5000 5001 5002 5003 5004) do (
    powershell -NoProfile -Command "try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 ('http://127.0.0.1:%%P/api/health'); if($r.Content -match 'tiendovankiep'){exit 0}else{exit 1}}catch{exit 1}" >nul 2>nul
    if not errorlevel 1 (
        echo [4/6] Game da dang chay o cong %%P. Mo trinh duyet...
        start "" "http://127.0.0.1:%%P/"
        goto :done
    )
)
echo [4/6] Chua co server nao dang chay.

rem ---------- 5. Tim cong trong de dung ----------
set "CHOSEN_PORT="
for %%P in (5000 5001 5002 5003 5004) do (
    if not defined CHOSEN_PORT (
        powershell -NoProfile -Command "$c=$null;try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',%%P);exit 1}catch{exit 0}finally{if($c){$c.Close()}}" >nul 2>nul
        if not errorlevel 1 set "CHOSEN_PORT=%%P"
    )
)
if not defined CHOSEN_PORT (
    echo [LOI] Cong 5000-5004 deu bi chiem. Dong cac chuong trinh dang dung cac cong nay roi thu lai.
    pause
    exit /b 1
)
echo [5/6] Se khoi dong server tai cong !CHOSEN_PORT!.

rem ---------- 6. Khoi dong server, cho san sang roi moi mo trinh duyet ----------
start "TienDoVanKiep Server" /min "%PY%" app.py !CHOSEN_PORT!
set "READY=0"
for /L %%I in (1,1,40) do (
    if !READY!==0 (
        powershell -NoProfile -Command "try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 ('http://127.0.0.1:!CHOSEN_PORT!/api/health'); if($r.Content -match 'tiendovankiep'){exit 0}else{exit 1}}catch{exit 1}" >nul 2>nul
        if not errorlevel 1 (
            set "READY=1"
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if !READY!==0 (
    echo [LOI] Server khong khoi dong duoc trong 40 giay.
    echo Mo cua so "TienDoVanKiep Server" tren thanh tac vu de xem thong bao loi.
    pause
    exit /b 1
)
echo [6/6] Server san sang. Dang mo trinh duyet...
start "" "http://127.0.0.1:!CHOSEN_PORT!/"

:done
echo.
echo ==========================================================
echo   Game da mo trong trinh duyet. Chuc nguoi choi vui ve!
echo   - Cua so nay co the dong duoc, game van chay tiep.
echo   - De tat server an toan, hay chay stop.bat
echo ==========================================================
pause
