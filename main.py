# main.py（终端版入口，按返回的role_name判断管理员权限）
from login import login
from admin_operation_terminal import AdminOperation

if __name__ == "__main__":
    # 1. 执行登录（无需选择角色，按账号长度自动匹配）
    user_info = login()
    if not user_info:
        exit()  # 登录失败直接退出

    # 2. 仅管理员（role_name="管理员"）可进入管理界面
    if user_info["role_name"] == "管理员":
        print("\n🔑 检测到管理员权限，进入管理界面...")
        admin = AdminOperation()
        admin.show_menu()
    else:
        print(f"\n您是{user_info['role_name']}，无管理员权限")