"""
请了吗2.0 - 一键启动域名服务
自动启动Flask应用和Cloudflare Tunnel，通过域名访问本地服务
域名: https://qinglema.dpdns.org
"""

import subprocess
import sys
import os
import time
import signal
import webbrowser
from threading import Thread

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 配置
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "qinglema.dpdns.org"
FLASK_PORT = 8080
TUNNEL_NAME = "qinglema"

# 进程管理
flask_process = None
tunnel_process = None

def print_banner():
    """打印启动横幅"""
    print("\n" + "=" * 50)
    print("   [*] 请了吗2.0 - 域名服务启动器")
    print("=" * 50)
    print(f"   [L] 本地地址: http://localhost:{FLASK_PORT}")
    print(f"   [W] 域名地址: https://{DOMAIN}")
    print("=" * 50 + "\n")

def start_flask():
    """启动Flask应用"""
    global flask_process
    print("[1/2] 启动Flask应用...")
    
    python_exe = sys.executable
    flask_process = subprocess.Popen(
        [python_exe, "app.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    
    # 等待Flask启动
    time.sleep(2)
    if flask_process.poll() is None:
        print(f"   [OK] Flask应用已启动 (PID: {flask_process.pid})")
        return True
    else:
        print("   [X] Flask应用启动失败")
        return False

def start_tunnel():
    """启动Cloudflare Tunnel"""
    global tunnel_process
    print("[2/2] 启动Cloudflare隧道...")
    
    cloudflared_path = os.path.join(PROJECT_DIR, "domain", "cloudflared.exe")
    if not os.path.exists(cloudflared_path):
        print(f"   [X] 找不到 cloudflared.exe: {cloudflared_path}")
        return False
    
    tunnel_process = subprocess.Popen(
        [cloudflared_path, "tunnel", "run", TUNNEL_NAME],
        cwd=os.path.join(PROJECT_DIR, "domain"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    
    # 等待隧道连接
    time.sleep(3)
    if tunnel_process.poll() is None:
        print(f"   [OK] Cloudflare隧道已连接 (PID: {tunnel_process.pid})")
        return True
    else:
        print("   [X] Cloudflare隧道启动失败")
        return False

def stop_services():
    """停止所有服务"""
    global flask_process, tunnel_process
    print("\n[!] 正在停止服务...")
    
    if tunnel_process and tunnel_process.poll() is None:
        if os.name == 'nt':
            tunnel_process.terminate()
        else:
            os.kill(tunnel_process.pid, signal.SIGTERM)
        print("   [OK] Cloudflare隧道已停止")
    
    if flask_process and flask_process.poll() is None:
        if os.name == 'nt':
            flask_process.terminate()
        else:
            os.kill(flask_process.pid, signal.SIGTERM)
        print("   [OK] Flask应用已停止")
    
    print("\n[*] 服务已全部停止，再见！\n")

def monitor_services():
    """监控服务状态"""
    while True:
        time.sleep(5)
        # 检查Flask
        if flask_process and flask_process.poll() is not None:
            print("\n[!] Flask应用已停止，正在重启...")
            start_flask()
        # 检查Tunnel
        if tunnel_process and tunnel_process.poll() is not None:
            print("\n[!] Cloudflare隧道已断开，正在重连...")
            start_tunnel()

def main():
    """主函数"""
    print_banner()
    
    # 启动服务
    if not start_flask():
        print("\n[X] 启动失败，请检查Flask应用")
        return
    
    if not start_tunnel():
        print("\n[X] 启动失败，请检查Cloudflare配置")
        stop_services()
        return
    
    print("\n" + "=" * 50)
    print("   [OK] 所有服务已启动！")
    print(f"   [W] 访问地址: https://{DOMAIN}")
    print("=" * 50)
    print("\n[i] 按 Ctrl+C 停止服务\n")
    
    # 询问是否打开浏览器
    try:
        choice = input("是否打开浏览器访问？(y/n): ").strip().lower()
        if choice == 'y':
            webbrowser.open(f"https://{DOMAIN}")
    except:
        pass
    
    # 启动监控线程
    monitor_thread = Thread(target=monitor_services, daemon=True)
    monitor_thread.start()
    
    # 等待退出
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_services()

if __name__ == "__main__":
    main()
