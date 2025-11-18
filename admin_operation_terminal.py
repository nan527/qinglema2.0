import pymysql
from db_config import get_db_config
from datetime import datetime


class AdminOperation:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect_db()

    def _connect_db(self):
        """连接数据库"""
        try:
            config = get_db_config()
            self.conn = pymysql.connect(**config)
            self.cursor = self.conn.cursor()
        except pymysql.MySQLError as e:
            print(f"数据库连接失败：{e}")
            exit()

    def _close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.open:
            self.conn.close()

    def show_menu(self):
        """管理员操作菜单（适配多身份表）"""
        while True:
            print("\n===== 管理员操作中心 =====")
            print("1. 查看学生信息")
            print("2. 查看教师信息")
            print("3. 查看辅导员信息")
            print("4. 查看管理员信息")
            print("5. 新增用户（按身份）")
            print("6. 修改用户信息（按身份）")
            print("7. 删除用户（按身份）")
            print("8. 退出管理员界面")
            choice = input("请选择操作(1-8)：").strip()

            if choice == "1":
                self._show_all_students()
            elif choice == "2":
                self._show_all_teachers()
            elif choice == "3":
                self._show_all_counselors()
            elif choice == "4":
                self._show_all_admins()
            elif choice == "5":
                self._add_user_by_role()
            elif choice == "6":
                self._update_user_by_role()
            elif choice == "7":
                self._delete_user_by_role()
            elif choice == "8":
                print("退出管理员界面")
                self._close_db()
                break
            else:
                print("无效操作，请重新输入")

    # ---------------------------- 学生信息管理 ----------------------------
    def _show_all_students(self):
        """查看所有学生（student_info表）"""
        try:
            self.cursor.execute("""
                SELECT student_id, password, student_name, dept, dept_id, grade, class_num, major, major_code, contact, create_time, update_time, times
                FROM student_info
                ORDER BY student_id
            """)
            students = self.cursor.fetchall()
            if not students:
                print("暂无学生数据")
                return
            print("\n===== 学生信息列表 =====")
            print(f"{'学号':<15} {'密码':<12} {'姓名':<10} {'学院':<10} {'学院代码':<8} {'年级':<8} {'班级':<6} {'专业':<15} {'专业代码':<8} {'联系方式':<12} {'创建时间':<20} {'更新时间':<20} {'次数':<4}")
            print("-" * 150)
            for s in students:
                print(f"{s[0]:<15} {s[1]:<12} {s[2]:<10} {s[3]:<10} {s[4]:<8} {s[5]:<8} {s[6]:<6} {s[7]:<15} {s[8]:<8} {s[9]:<12} {str(s[10]):<20} {str(s[11]):<20} {s[12]:<4}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    def _add_student(self):
        """添加学生（student_info表）"""
        try:
            student_id = input("请输入学号：").strip()
            password = input("请输入密码（默认123456）：").strip() or "123456"
            student_name = input("请输入姓名：").strip()
            dept = input("请输入学院：").strip()
            dept_id = input("请输入学院代码：").strip()
            grade = input("请输入年级：").strip()
            class_num = input("请输入班级：").strip()
            major = input("请输入专业：").strip()
            major_code = input("请输入专业代码：").strip()
            contact = input("请输入联系方式：").strip()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_time = create_time
            times = 0

            self.cursor.execute("""
                INSERT INTO student_info 
                (student_id, password, student_name, dept, dept_id, grade, class_num, major, major_code, contact, create_time, update_time, times)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, password, student_name, dept, dept_id, grade, class_num, major, major_code, contact, create_time, update_time, times))
            self.conn.commit()
            print("学生添加成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"添加失败：{e}")

    def _update_student(self):
        """修改学生信息（student_info表）"""
        try:
            student_id = input("请输入要修改的学生学号：").strip()
            self.cursor.execute("SELECT * FROM student_info WHERE student_id = %s", (student_id,))
            if not self.cursor.fetchone():
                print("该学生不存在")
                return

            password = input("请输入新密码（不修改按回车）：").strip()
            student_name = input("请输入新姓名（不修改按回车）：").strip()
            contact = input("请输入新联系方式（不修改按回车）：").strip()
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            update_fields = []
            params = []
            if password:
                update_fields.append("password = %s")
                params.append(password)
            if student_name:
                update_fields.append("student_name = %s")
                params.append(student_name)
            if contact:
                update_fields.append("contact = %s")
                params.append(contact)
            update_fields.append("update_time = %s")
            params.append(update_time)
            params.append(student_id)

            if not update_fields:
                print("未输入任何修改内容")
                return

            sql = f"UPDATE student_info SET {', '.join(update_fields)} WHERE student_id = %s"
            self.cursor.execute(sql, params)
            self.conn.commit()
            print("学生信息修改成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"修改失败：{e}")

    def _delete_student(self):
        """删除学生（student_info表）"""
        try:
            student_id = input("请输入要删除的学生学号：").strip()
            self.cursor.execute("SELECT * FROM student_info WHERE student_id = %s", (student_id,))
            if not self.cursor.fetchone():
                print("该学生不存在")
                return

            confirm = input("确定删除吗？(y/n)：").strip().lower()
            if confirm != "y":
                return

            self.cursor.execute("DELETE FROM student_info WHERE student_id = %s", (student_id,))
            self.conn.commit()
            print("学生删除成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"删除失败：{e}")

    # ---------------------------- 教师信息管理 ----------------------------
    def _show_all_teachers(self):
        """查看所有教师（teacher_info表）"""
        try:
            self.cursor.execute("""
                SELECT teacher_id, password, teacher_name, dept, contact, create_time, update_time
                FROM teacher_info
                ORDER BY teacher_id
            """)
            teachers = self.cursor.fetchall()
            if not teachers:
                print("暂无教师数据")
                return
            print("\n===== 教师信息列表 =====")
            print(f"{'工号':<15} {'密码':<12} {'姓名':<10} {'部门':<15} {'联系方式':<12} {'创建时间':<20} {'更新时间':<20}")
            print("-" * 100)
            for t in teachers:
                print(f"{t[0]:<15} {t[1]:<12} {t[2]:<10} {t[3]:<15} {t[4]:<12} {str(t[5]):<20} {str(t[6]):<20}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    def _add_teacher(self):
        """添加教师（teacher_info表）"""
        try:
            teacher_id = input("请输入教师工号：").strip()
            password = input("请输入密码（默认123456）：").strip() or "123456"
            teacher_name = input("请输入教师姓名：").strip()
            dept = input("请输入所属部门：").strip()
            contact = input("请输入联系方式：").strip()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_time = create_time

            self.cursor.execute("""
                INSERT INTO teacher_info 
                (teacher_id, password, teacher_name, dept, contact, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (teacher_id, password, teacher_name, dept, contact, create_time, update_time))
            self.conn.commit()
            print("教师添加成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"添加失败：{e}")

    def _update_teacher(self):
        """修改教师信息（teacher_info表）"""
        try:
            teacher_id = input("请输入要修改的教师工号：").strip()
            self.cursor.execute("SELECT * FROM teacher_info WHERE teacher_id = %s", (teacher_id,))
            if not self.cursor.fetchone():
                print("该教师不存在")
                return

            password = input("请输入新密码（不修改按回车）：").strip()
            teacher_name = input("请输入新姓名（不修改按回车）：").strip()
            contact = input("请输入新联系方式（不修改按回车）：").strip()
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            update_fields = []
            params = []
            if password:
                update_fields.append("password = %s")
                params.append(password)
            if teacher_name:
                update_fields.append("teacher_name = %s")
                params.append(teacher_name)
            if contact:
                update_fields.append("contact = %s")
                params.append(contact)
            update_fields.append("update_time = %s")
            params.append(update_time)
            params.append(teacher_id)

            if not update_fields:
                print("未输入任何修改内容")
                return

            sql = f"UPDATE teacher_info SET {', '.join(update_fields)} WHERE teacher_id = %s"
            self.cursor.execute(sql, params)
            self.conn.commit()
            print("教师信息修改成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"修改失败：{e}")

    def _delete_teacher(self):
        """删除教师（teacher_info表）"""
        try:
            teacher_id = input("请输入要删除的教师工号：").strip()
            self.cursor.execute("SELECT * FROM teacher_info WHERE teacher_id = %s", (teacher_id,))
            if not self.cursor.fetchone():
                print("该教师不存在")
                return

            confirm = input("确定删除吗？(y/n)：").strip().lower()
            if confirm != "y":
                return

            self.cursor.execute("DELETE FROM teacher_info WHERE teacher_id = %s", (teacher_id,))
            self.conn.commit()
            print("教师删除成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"删除失败：{e}")

    # ---------------------------- 辅导员信息管理 ----------------------------
    def _show_all_counselors(self):
        """查看所有辅导员（counselor_info表）"""
        try:
            self.cursor.execute("""
                SELECT counselor_id, password, counselor_name, dept, responsible_grade, responsible_major, contact, create_time, update_time
                FROM counselor_info
                ORDER BY counselor_id
            """)
            counselors = self.cursor.fetchall()
            if not counselors:
                print("暂无辅导员数据")
                return
            print("\n===== 辅导员信息列表 =====")
            print(f"{'工号':<15} {'密码':<15} {'姓名':<10} {'部门':<15} {'负责年级':<10} {'负责专业':<15} {'联系方式':<12} {'创建时间':<20} {'更新时间':<20}")
            print("-" * 120)
            for c in counselors:
                print(f"{c[0]:<15} {c[1]:<15} {c[2]:<10} {c[3]:<15} {c[4]:<10} {c[5]:<15} {c[6]:<12} {str(c[7]):<20} {str(c[8]):<20}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    def _add_counselor(self):
        """添加辅导员（counselor_info表）"""
        try:
            counselor_id = input("请输入辅导员工号：").strip()
            password = input("请输入密码（默认counselor123）：").strip() or "counselor123"
            counselor_name = input("请输入辅导员姓名：").strip()
            dept = input("请输入所属部门：").strip()
            responsible_grade = input("请输入负责年级：").strip()
            responsible_major = input("请输入负责专业：").strip()
            contact = input("请输入联系方式：").strip()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_time = create_time

            self.cursor.execute("""
                INSERT INTO counselor_info 
                (counselor_id, password, counselor_name, dept, responsible_grade, responsible_major, contact, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (counselor_id, password, counselor_name, dept, responsible_grade, responsible_major, contact, create_time, update_time))
            self.conn.commit()
            print("辅导员添加成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"添加失败：{e}")

    def _update_counselor(self):
        """修改辅导员信息（counselor_info表）"""
        try:
            counselor_id = input("请输入要修改的辅导员工号：").strip()
            self.cursor.execute("SELECT * FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
            if not self.cursor.fetchone():
                print("该辅导员不存在")
                return

            password = input("请输入新密码（不修改按回车）：").strip()
            counselor_name = input("请输入新姓名（不修改按回车）：").strip()
            contact = input("请输入新联系方式（不修改按回车）：").strip()
            responsible_major = input("请输入新负责专业（不修改按回车）：").strip()
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            update_fields = []
            params = []
            if password:
                update_fields.append("password = %s")
                params.append(password)
            if counselor_name:
                update_fields.append("counselor_name = %s")
                params.append(counselor_name)
            if contact:
                update_fields.append("contact = %s")
                params.append(contact)
            if responsible_major:
                update_fields.append("responsible_major = %s")
                params.append(responsible_major)
            update_fields.append("update_time = %s")
            params.append(update_time)
            params.append(counselor_id)

            if not update_fields:
                print("未输入任何修改内容")
                return

            sql = f"UPDATE counselor_info SET {', '.join(update_fields)} WHERE counselor_id = %s"
            self.cursor.execute(sql, params)
            self.conn.commit()
            print("辅导员信息修改成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"修改失败：{e}")

    def _delete_counselor(self):
        """删除辅导员（counselor_info表）"""
        try:
            counselor_id = input("请输入要删除的辅导员工号：").strip()
            self.cursor.execute("SELECT * FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
            if not self.cursor.fetchone():
                print("该辅导员不存在")
                return

            confirm = input("确定删除吗？(y/n)：").strip().lower()
            if confirm != "y":
                return

            self.cursor.execute("DELETE FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
            self.conn.commit()
            print("辅导员删除成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"删除失败：{e}")

    # ---------------------------- 管理员信息管理 ----------------------------
    def _show_all_admins(self):
        """查看所有管理员（admin_info表）"""
        try:
            self.cursor.execute("""
                SELECT admin_id, password, dept, create_time, update_time
                FROM admin_info
                ORDER BY admin_id
            """)
            admins = self.cursor.fetchall()
            if not admins:
                print("暂无管理员数据")
                return
            print("\n===== 管理员信息列表 =====")
            print(f"{'管理员ID':<10} {'密码':<20} {'学院':<10} {'创建时间':<20} {'更新时间':<20}")
            print("-" * 80)
            for a in admins:
                print(f"{a[0]:<10} {a[1]:<20} {a[2]:<10} {str(a[3]):<20} {str(a[4]):<20}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    def _add_admin(self):
        """添加管理员（admin_info表）"""
        try:
            admin_id = input("请输入管理员ID：").strip()
            password = input("请输入密码（默认admin123）：").strip() or "admin123"
            dept = input("请输入所属学院：").strip()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_time = create_time

            self.cursor.execute("""
                INSERT INTO admin_info (admin_id, password, dept, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (admin_id, password, dept, create_time, update_time))
            self.conn.commit()
            print("管理员添加成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"添加失败：{e}")

    def _update_admin(self):
        """修改管理员信息（admin_info表）"""
        try:
            admin_id = input("请输入要修改的管理员ID：").strip()
            self.cursor.execute("SELECT * FROM admin_info WHERE admin_id = %s", (admin_id,))
            if not self.cursor.fetchone():
                print("该管理员不存在")
                return

            password = input("请输入新密码（不修改按回车）：").strip()
            dept = input("请输入新学院（不修改按回车）：").strip()
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            update_fields = []
            params = []
            if password:
                update_fields.append("password = %s")
                params.append(password)
            if dept:
                update_fields.append("dept = %s")
                params.append(dept)
            update_fields.append("update_time = %s")
            params.append(update_time)
            params.append(admin_id)

            if not update_fields:
                print("未输入任何修改内容")
                return

            sql = f"UPDATE admin_info SET {', '.join(update_fields)} WHERE admin_id = %s"
            self.cursor.execute(sql, params)
            self.conn.commit()
            print("管理员信息修改成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"修改失败：{e}")

    def _delete_admin(self):
        """删除管理员（admin_info表）"""
        try:
            admin_id = input("请输入要删除的管理员ID：").strip()
            self.cursor.execute("SELECT * FROM admin_info WHERE admin_id = %s", (admin_id,))
            if not self.cursor.fetchone():
                print("该管理员不存在")
                return

            confirm = input("确定删除吗？(y/n)：").strip().lower()
            if confirm != "y":
                return

            self.cursor.execute("DELETE FROM admin_info WHERE admin_id = %s", (admin_id,))
            self.conn.commit()
            print("管理员删除成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"删除失败：{e}")

    # ---------------------------- 按身份统一操作 ----------------------------
    def _add_user_by_role(self):
        """按身份新增用户"""
        print("\n请选择身份：1.学生 2.教师 3.辅导员 4.管理员")
        role = input("输入序号：").strip()
        if role == "1":
            self._add_student()
        elif role == "2":
            self._add_teacher()
        elif role == "3":
            self._add_counselor()
        elif role == "4":
            self._add_admin()
        else:
            print("无效身份")

    def _update_user_by_role(self):
        """按身份修改用户"""
        print("\n请选择身份：1.学生 2.教师 3.辅导员 4.管理员")
        role = input("输入序号：").strip()
        if role == "1":
            self._update_student()
        elif role == "2":
            self._update_teacher()
        elif role == "3":
            self._update_counselor()
        elif role == "4":
            self._update_admin()
        else:
            print("无效身份")

    def _delete_user_by_role(self):
        """按身份删除用户"""
        print("\n请选择身份：1.学生 2.教师 3.辅导员 4.管理员")
        role = input("输入序号：").strip()
        if role == "1":
            self._delete_student()
        elif role == "2":
            self._delete_teacher()
        elif role == "3":
            self._delete_counselor()
        elif role == "4":
            self._delete_admin()
        else:
            print("无效身份")


if __name__ == "__main__":
    admin = AdminOperation()
    admin.show_menu()