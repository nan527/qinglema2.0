# 学生信息管理系统主入口（整合所有角色）
from login import login
# 导入各个角色的操作类
from terminal.admin_operation import AdminOperation
from terminal.student_operation import StudentOperation
from terminal.counselor_operation import CounselorOperation

# 尝试导入老师操作类，如果失败则设置为None
TeacherOperation = None
try:
    from terminal.teacher_operation import TeacherOperation
except ImportError:
    pass

def main():
    """主程序循环：支持所有角色登录和操作"""
    while True:
        # 清空屏幕效果（通过打印多行换行符实现）
        print("\n" * 2)
        
        # 打印系统标题和分隔线，使用更美观的格式
        print("=" * 50)
        print("|" + " " * 16 + "🎓 学生信息管理系统" + " " * 16 + "|")
        print("|" + " " * 14 + "支持多角色登录与操作" + " " * 14 + "|")
        print("=" * 50)
        
        # 执行登录
        user_info = login()
        if not user_info:
            # 登录返回None时询问是否继续
            choice = input("\n" + "-" * 30 + "\n是否继续登录？(y/n): ").strip().lower()
            if choice != 'y':
                print("\n感谢使用，再见！")
                break
            print("\n" + "-" * 50)
            continue
        
        # 根据角色类型进入不同界面
        role_name = user_info["role_name"]
        
        if role_name == "管理员":
            print("\n🔑 " + "-" * 25)
            print("🔑 检测到管理员权限")
            print("🔑 欢迎，" + user_info["user_name"])
            print("🔑 " + "-" * 25)
            print("🔑 正在进入管理界面...")
            admin = AdminOperation()
            admin.show_menu()
            
        elif role_name == "学生":
            print("\n🎓 " + "-" * 25)
            print(f"🎓 检测到学生身份：{user_info['user_name']}")
            print(f"🎓 学号：{user_info['user_account']}")
            print("🎓 " + "-" * 25)
            print("🎓 正在进入学生界面...")
            student = StudentOperation(user_info["user_account"])
            student.show_menu()
            
        elif role_name == "辅导员":
            print("\n👨‍💼 " + "-" * 25)
            print(f"👨‍💼 检测到辅导员权限：{user_info['user_name']}")
            print(f"👨‍💼 负责年级：{user_info['responsible_grade']}级")
            print("👨‍💼 " + "-" * 25)
            print(f"👨‍💼 正在进入{user_info['responsible_grade']}级管理界面...")
            counselor = CounselorOperation(
                counselor_id=user_info["user_account"],
                counselor_name=user_info["user_name"],
                responsible_grade=user_info["responsible_grade"]
            )
            counselor.show_menu()
            
        elif role_name == "讲师":
            print("\n👨‍🏫 " + "-" * 25)
            print(f"👨‍🏫 检测到讲师身份：{user_info['user_name']}")
            print("👨‍🏫 " + "-" * 25)
            
            if TeacherOperation is not None:
                try:
                    print("👨‍🏫 正在进入老师工作台...")
                    teacher = TeacherOperation(user_info)
                    teacher.show_menu()
                except Exception as e:
                    print(f"\n⚠️ 讲师功能可能尚未完全开发：{str(e)}")
                    input("按回车键返回登录界面...")
            else:
                print("👨‍🏫 当前版本暂未开发讲师功能界面")
                input("按回车键返回登录界面...")

            
        else:
            print("\n❓ " + "-" * 25)
            print(f"❓ 未知角色类型：{role_name}")
            print("❓ " + "-" * 25)
            input("按回车键返回登录界面...")
        
        # 询问是否继续使用系统
        print("\n" + "=" * 50)
        choice = input("是否退出系统？(y/n): ").strip().lower()
        if choice == 'y':
            print("\n" + "=" * 50)
            print("|" + " " * 17 + "感谢使用，再见！" + " " * 17 + "|")
            print("=" * 50)
            break
        print("\n返回登录界面...")

if __name__ == "__main__":
    main()