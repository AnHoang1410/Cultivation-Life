@echo off
setlocal EnableDelayedExpansion
title Tien Do Van Kiep - Tu dong cap nhat

rem ============================================================
rem  update.bat - Tu dong cap nhat game len phien ban moi nhat
rem  cua kho GitHub AnHoang1410/Cultivation-Life (nhanh main).
rem
rem  Cach dung: chep file nay vao thu muc game dang choi roi
rem  nhan doi vao no, cho chay xong la duoc.
rem
rem  Cam ket an toan:
rem  - Thu muc data (file luu game) va thu muc config (cai dat
rem    AI chua khoa truy cap) LUON duoc giu nguyen.
rem  - Truoc khi thay ma nguon, toan bo ban dang choi duoc sao
rem    luu vao thu muc backups\update-<ngay-gio> de quay lai
rem    khi can.
rem  - Neu tai that bai, game cua ban khong bi thay doi gi.
rem ============================================================

rem ---------- Tu chay lai tu thu muc tam ----------
rem  De file update.bat dang chay khong bi ghi de giua luc
rem  cap nhat (ban sao dang chay nam o thu muc tam he thong).
if /i not "%~1"=="--runner" (
    set "RUNNER=%TEMP%\TienDoVanKiep_update_runner.bat"
    copy /y "%~f0" "!RUNNER!" >nul
    call "!RUNNER!" --runner "%~dp0"
    exit /b
)

set "GAMEDIR=%~2"
cd /d "%GAMEDIR%"
set "ZIP_URL=https://github.com/AnHoang1410/Cultivation-Life/archive/refs/heads/main.zip"
set "TMPDIR=%GAMEDIR%_update_tmp"
set "ZIPFILE=%TMPDIR%\latest.zip"
set "EXTRACT=%TMPDIR%\extract"
set "SRC=%EXTRACT%\Cultivation-Life-main"

echo ==========================================================
echo    TIEN DO VAN KIEP - Tu dong cap nhat
echo ==========================================================
echo.

rem ---------- 1. Dung server neu dang chay ----------
if exist "data\server_port.txt" (
    set /p PORT=<"data\server_port.txt"
    echo [1/5] Phat hien server dang chay o cong !PORT!. Dang dung server...
    powershell -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort !PORT! -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if($c){ try{ Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop } catch {} }"
    del "data\server_port.txt" >nul 2>nul
    timeout /t 2 /nobreak >nul
    echo        Da dung server.
) else (
    echo [1/5] Server khong chay, khong can dung.
)

rem ---------- 2. Sao luu ban hien tai ----------
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%T"
set "BACKUP=%GAMEDIR%backups\update-!STAMP!"
echo [2/5] Dang sao luu ban hien tai vao:
echo        !BACKUP!
mkdir "!BACKUP!" >nul 2>nul
if exist "data" robocopy "data" "!BACKUP!\data" /E /NFL /NDL /NJH /NJS /NP >nul
if exist "config" robocopy "config" "!BACKUP!\config" /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%GAMEDIR%." "!BACKUP!\code" *.py *.txt *.bat .gitignore /NFL /NDL /NJH /NJS /NP >nul
if exist "templates" robocopy "templates" "!BACKUP!\code\templates" /E /NFL /NDL /NJH /NJS /NP >nul
if exist "static" robocopy "static" "!BACKUP!\code\static" /E /NFL /NDL /NJH /NJS /NP >nul
echo        Sao luu xong.

rem ---------- 3. Tai phien ban moi nhat ----------
where curl >nul 2>nul
if errorlevel 1 goto :tool_fail
where tar >nul 2>nul
if errorlevel 1 goto :tool_fail
echo [3/5] Dang tai phien ban moi nhat tu GitHub...
if exist "%TMPDIR%" rd /s /q "%TMPDIR%"
mkdir "%TMPDIR%" >nul 2>nul
mkdir "%EXTRACT%" >nul 2>nul
curl -L --fail -o "%ZIPFILE%" "%ZIP_URL%"
if errorlevel 1 goto :download_fail
if not exist "%ZIPFILE%" goto :download_fail
tar -xf "%ZIPFILE%" -C "%EXTRACT%"
if errorlevel 1 goto :download_fail
if not exist "%SRC%\app.py" goto :download_fail
if not exist "%SRC%\start.bat" goto :download_fail
echo        Da tai va kiem tra xong phien ban moi.

rem ---------- 4. Ghi de ma nguon moi, giu nguyen data va config ----------
echo [4/5] Dang cap nhat ma nguon (data va config duoc giu nguyen)...
robocopy "%SRC%" "%GAMEDIR%." /E /XD "%SRC%\data" "%SRC%\config" /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :copy_fail
if not exist "%GAMEDIR%app.py" goto :copy_fail
if not exist "%GAMEDIR%start.bat" goto :copy_fail
if exist ".venv\Scripts\python.exe" (
    echo        Dang cap nhat thu vien theo ban moi...
    ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if errorlevel 1 echo        [Luu y] Cap nhat thu vien chua xong, start.bat se tu thu lai khi mo game.
)
echo        Cap nhat ma nguon xong.

rem ---------- 5. Don dep va mo lai game ----------
echo [5/5] Dang don dep...
rd /s /q "%TMPDIR%" >nul 2>nul
echo.
echo ==========================================================
echo   CAP NHAT THANH CONG!
echo   - Du lieu choi va cai dat AI cua ban van nguyen ven.
echo   - Ban cu (ma nguon, du lieu, cai dat) duoc luu tai:
echo     !BACKUP!
echo   Game se tu mo ngay bay gio...
echo ==========================================================
start "" "%GAMEDIR%start.bat"
pause
exit /b 0

:tool_fail
echo.
echo [LOI] May tinh thieu cong cu tai hoac giai nen san co cua Windows.
echo Cac cong cu nay co san tren Windows 10 va Windows 11 ban moi.
echo Hay cap nhat Windows roi chay lai update.bat.
echo Tro choi cua ban CHUA bi thay doi gi.
pause
exit /b 1

:download_fail
echo.
echo [LOI] Tai hoac giai nen phien ban moi that bai.
echo Kiem tra ket noi internet roi chay lai update.bat.
echo Tro choi cua ban CHUA bi thay doi gi, ban cu van nguyen ven.
if exist "%TMPDIR%" rd /s /q "%TMPDIR%"
pause
exit /b 1

:copy_fail
echo.
echo [LOI] Ghi ma nguon moi that bai giua chung.
echo Ban sao luu day du cua ban nam tai: !BACKUP!
echo Hay chup anh man hinh loi nay va bao lai de duoc ho tro.
pause
exit /b 1
