@echo off
chcp 65001 >nul
echo ========================================
echo   设置开机自动启动域名服务
echo ========================================
echo.

:: 获取启动文件夹路径
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=请了吗域名服务.lnk"
set "TARGET_PATH=%~dp0启动域名服务.bat"

:: 使用PowerShell创建快捷方式
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%'); $s.TargetPath = '%TARGET_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Save()"

if exist "%STARTUP_FOLDER%\%SHORTCUT_NAME%" (
    echo ✅ 开机自启动已设置成功！
    echo.
    echo 快捷方式位置: %STARTUP_FOLDER%\%SHORTCUT_NAME%
    echo.
    echo 下次开机将自动启动域名服务
) else (
    echo ❌ 设置失败，请手动设置
)

echo.
echo ========================================
pause
