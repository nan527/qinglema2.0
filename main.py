# 学生信息管理系统主入口（整合所有角色）
from login import login
# 导入整合后的管理员操作类（替换原来的admin_operation_terminal）
from admin_operation import AdminOperation  # 修改这里的导入路径
from student_operation import StudentOperation
from counselor_operation import CounselorOperation
from teacher.teacher import TeacherOperation  # 导入老师操作类

def main():
    """主程序循环：支持所有角色登录和操作"""
    while True:
        print("\n" + "=" * 50)
        print("            🎓 学生信息管理系统")
        print("=" * 50)
        
        # 1. 执行登录
        user_info = login()
        if not user_info:
            # 登录返回None时询问是否继续
            choice = input("\n是否继续登录？(y/n): ").strip().lower()
            if choice != 'y':
                print("感谢使用，再见！")
                break
            continue
        
        # 2. 根据角色类型进入不同界面
        role_name = user_info["role_name"]
        
        if role_name == "管理员":
            print("\n🔑 检测到管理员权限，进入管理界面...")
            admin = AdminOperation()  # 这里使用的就是整合后的类
            admin.show_menu()
            
        elif role_name == "学生":
            print(f"\n🎓 检测到学生身份，进入学生界面...")
            student = StudentOperation(user_info["user_account"])
            student.show_menu()
            
        elif role_name == "辅导员":
            print(f"\n👨‍💼 检测到辅导员权限，进入{user_info['responsible_grade']}级管理界面...")
            counselor = CounselorOperation(
                counselor_id=user_info["user_account"],
                counselor_name=user_info["user_name"],
                responsible_grade=user_info["responsible_grade"]
            )
            counselor.show_menu()
            
        elif role_name == "讲师":
            print(f"\n👨‍🏫 检测到讲师身份，进入老师工作台...")
            teacher = TeacherOperation(user_info)
            teacher.show_menu()
            
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