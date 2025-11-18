# main.py（终端版入口，支持循环登录）
from login import login
from admin_operation_terminal import AdminOperation
from student_operation_terminal import StudentOperation

def main():
    """主程序循环"""
    while True:
        print("\n" + "=" * 50)
        print("            🎓 学生信息管理系统")
        print("=" * 50)
        
        # 1. 执行登录
        user_info = login()
        if not user_info:
            # 如果登录返回None，询问是否继续
            choice = input("\n是否继续登录？(y/n): ").strip().lower()
            if choice != 'y':
                print("感谢使用，再见！")
                break
            continue
        
        # 2. 根据角色类型进入不同界面
        role_name = user_info["role_name"]
        
        if role_name == "管理员":
            print("\n🔑 检测到管理员权限，进入管理界面...")
            admin = AdminOperation()
            admin.show_menu()
            # 管理员界面退出后会自动回到登录界面
            
        elif role_name == "学生":
            print(f"\n🎓 检测到学生身份，进入学生界面...")
            student = StudentOperation(user_info["user_account"])
            student.show_menu()
            # 学生界面退出后会自动回到登录界面
            
        elif role_name == "讲师":
            print(f"\n👨‍🏫 您是{role_name}，当前版本暂未开发讲师功能界面")
            input("按回车键返回登录界面...")
            
        elif role_name == "辅导员":
            print(f"\n👨‍💼 您是{role_name}，当前版本暂未开发辅导员功能界面")
            input("按回车键返回登录界面...")
            
        else:
            print(f"\n❓ 未知角色类型：{role_name}")
            input("按回车键返回登录界面...")
        
        # 3. 询问是否继续使用系统
        print("\n" + "-" * 50)
        choice = input("是否退出系统？(y/n): ").strip().lower()
        if choice == 'y':
            print("感谢使用，再见！")
            break

if __name__ == "__main__":
    main()