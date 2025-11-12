# main.py（终端版入口，仅修改导入路径）
from login import login
from admin_operation_terminal import AdminOperation  # 改为终端版文件名

if __name__ == "__main__":
    # 先执行登录
    user_info = login()
    if not user_info:
        exit()  # 登录失败直接退出
    # 检查是否为管理员（role_type=4）
    if user_info["role_type"] == 4:
        print("\n🔑 检测到管理员权限，进入管理界面...")
        admin = AdminOperation()
        admin.show_menu()  # 显示管理员操作菜单
    else:
        print(f"\n您是{user_info['role_name']}，无管理员权限")