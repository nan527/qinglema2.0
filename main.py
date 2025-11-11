# main.py
from login import login  # 导入独立的登录功能

if __name__ == "__main__":
    # 调用登录模块
    user_info = login()

    # 登录成功后可执行其他操作（示例）
    if user_info:
        print("\n===== 登录后操作 =====")
        if user_info["role_type"] == 4:
            print("您是管理员，可执行管理操作")
        else:
            print("您是普通用户，可执行查询操作")