@echo off
chcp 65001 >nul
echo ========================================
echo   取消开机自动启动域名服务
echo ========================================
echo.

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=请了吗域名服务.lnk"

if exist "%STARTUP_FOLDER%\%SHORTCUT_NAME%" (
    del "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
    echo ✅ 已取消开机自启动
) else (
    echo ⚠️  未设置开机自启动，无需取消
)

echo.
pause
