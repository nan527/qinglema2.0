import pymysql
from db_config import get_db_config
from datetime import datetime, timedelta

class StudentOperation:
    def __init__(self, student_id):
        self.student_id = student_id
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
        """学生操作菜单"""
        while True:
            print(f"\n===== 学生操作中心（学号：{self.student_id}） =====")
            print("1. 查看个人信息")
            print("2. 修改密码")
            print("3. 添加请假信息")
            print("4. 查看我的请假记录")
            print("5. 查看我的选课")
            print("6. 退出学生界面")
            choice = input("请选择操作(1-6)：").strip()

            if choice == "1":
                self._show_my_info()
            elif choice == "2":
                self._update_password()
            elif choice == "3":
                self._add_leave_request()
            elif choice == "4":
                self._show_my_leave_records()
            elif choice == "5":
                self._show_my_courses()
            elif choice == "6":
                print("退出学生界面")
                self._close_db()
                break
            else:
                print("无效操作，请重新输入")

    def _show_my_info(self):
        """查看学生个人信息"""
        try:
            self.cursor.execute("""
                SELECT student_id, student_name, dept_name, student_dept_id, student_grade, class_num, major, major_code, student_contact, student_create_time, student_update_time, times
                FROM student_info
                WHERE student_id = %s
            """, (self.student_id,))
            student = self.cursor.fetchone()
            
            if not student:
                print("❌ 学生信息不存在")
                return
            
            print("\n===== 个人信息 =====")
            print(f"学号：{student[0]}")
            print(f"姓名：{student[1]}")
            print(f"学院：{student[2]}")
            print(f"学院代码：{student[3]}")
            print(f"年级：{student[4]}")
            print(f"班级：{student[5]}")
            print(f"专业：{student[6]}")
            print(f"专业代码：{student[7]}")
            print(f"联系方式：{student[8]}")
            print(f"创建时间：{student[9]}")
            print(f"更新时间：{student[10]}")
            print(f"登录次数：{student[11]}")
            
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    def _update_password(self):
        """修改密码"""
        try:
            current_password = input("请输入当前密码：").strip()
            
            # 验证当前密码
            self.cursor.execute("SELECT student_password FROM student_info WHERE student_id = %s", (self.student_id,))
            result = self.cursor.fetchone()
            
            if not result or result[0] != current_password:
                print("❌ 当前密码错误")
                return
            
            new_password = input("请输入新密码：").strip()
            confirm_password = input("请再次输入新密码：").strip()
            
            if new_password != confirm_password:
                print("❌ 两次输入的密码不一致")
                return
            
            if len(new_password) < 6:
                print("❌ 密码长度不能少于6位")
                return
            
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.cursor.execute("""
                UPDATE student_info 
                SET student_password = %s, student_update_time = %s 
                WHERE student_id = %s
            """, (new_password, update_time, self.student_id))
            self.conn.commit()
            
            print("✅ 密码修改成功")
            
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 密码修改失败：{e}")

    def _get_leave_times(self):
        """获取学生已批准的请假次数"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM student_leave 
                WHERE leave_student_id = %s AND approval_status = '已批准'
            """, (self.student_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except pymysql.MySQLError as e:
            print(f"❌ 查询请假次数失败：{e}")
            return 0

    def _parse_datetime_input(self, input_str):
        """解析日期时间输入，将'2025 10 13 12 12 12'格式转换为'2025-10-13 12:12:12'"""
        try:
            # 分割输入字符串
            parts = input_str.strip().split()
            
            # 检查是否有足够的组成部分
            if len(parts) != 6:
                raise ValueError("输入格式不正确，需要6个数字分别表示年、月、日、时、分、秒")
            
            # 提取各部分
            year, month, day, hour, minute, second = parts
            
            # 验证并转换为整数
            year = int(year)
            month = int(month)
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            second = int(second)
            
            # 验证日期时间是否有效
            dt = datetime(year, month, day, hour, minute, second)
            
            # 转换为标准格式
            return dt.strftime("%Y-%m-%d %H:%M:%S")
            
        except ValueError as e:
            raise ValueError(f"日期时间格式错误: {e}")

    def _add_leave_request(self):
        """添加请假信息"""
        try:
            # 获取学生基本信息
            self.cursor.execute("SELECT student_name, dept_name FROM student_info WHERE student_id = %s", (self.student_id,))
            student_info = self.cursor.fetchone()
            
            if not student_info:
                print("❌ 学生信息不存在")
                return
                
            student_name, dept = student_info
            
            # 获取请假信息
            print("\n===== 添加请假信息 =====")
            course_id = input("请输入课程代码：").strip()
            
            # 如果输入了课程代码，显示可选的授课老师
            if course_id:
                teachers = self._get_teachers_by_course(course_id)
                if teachers:
                    print(f"\n该课程的授课老师列表：")
                    for idx, (teacher_id, teacher_name) in enumerate(teachers, 1):
                        print(f"{idx}. 工号: {teacher_id}, 姓名: {teacher_name}")
                    
                    # 让学生选择老师或手动输入
                    choice = input("请选择老师序号(或直接输入工号): ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(teachers):
                        teacher_id = teachers[int(choice)-1][0]
                        teacher_name = teachers[int(choice)-1][1]
                        print(f"已选择: {teacher_id} - {teacher_name}")
                    else:
                        # 如果输入不是序号，直接使用输入的值作为工号
                        teacher_id = choice
                else:
                    print("未找到该课程的授课老师信息，请手动输入")
                    teacher_id = input("请输入教师工号：").strip()
            else:
                teacher_id = input("请输入教师工号：").strip()
                
            leave_reason = input("请输入请假原因：").strip()
            
            # 时间输入循环
            while True:
                try:
                    start_input = input("请输入开始时间 (格式: 2025 10 13 12 12 12)：").strip()
                    start_time = self._parse_datetime_input(start_input)
                    break
                except ValueError as e:
                    print(f"❌ {e}")
                    print("请使用格式: 年 月 日 时 分 秒 (例如: 2025 10 13 12 12 12)")
            
            while True:
                try:
                    end_input = input("请输入结束时间 (格式: 2025 10 13 12 12 12)：").strip()
                    end_time = self._parse_datetime_input(end_input)
                    break
                except ValueError as e:
                    print(f"❌ {e}")
                    print("请使用格式: 年 月 日 时 分 秒 (例如: 2025 10 13 12 12 12)")
            
            # 验证时间顺序
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            if end_dt <= start_dt:
                print("❌ 结束时间必须晚于开始时间")
                return
            
            # 验证必填字段
            if not all([course_id, teacher_id, leave_reason]):
                print("❌ 课程代码、教师工号和请假原因必须填写")
                return
            
            # 计算请假次数
            approved_times = self._get_leave_times()
            current_times = approved_times + 1
            
            # 设置默认值
            approval_status = "待审批"  # 默认状态
            
            # 插入请假信息 - 包含 times 字段
            self.cursor.execute("""
                INSERT INTO student_leave
                (leave_student_id, leave_student_name, leave_dept, leave_course_id, leave_teacher_id, leave_reason, leave_start_time, leave_end_time, approval_status, leave_times)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.student_id, student_name, dept, course_id, teacher_id, leave_reason, start_time, end_time, approval_status, current_times))
            
            self.conn.commit()
            print("✅ 请假申请提交成功，等待审批")
            print(f"   请假时间: {start_time} 至 {end_time}")
            print(f"   本次请假次数: {current_times}")
            if approved_times > 0:
                print(f"   之前已批准请假次数: {approved_times}")
            
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 请假申请提交失败：{e}")

    def _show_my_leave_records(self):
        """查看我的请假记录"""
        try:
            # 查询字段与数据库表结构一致
            self.cursor.execute("""
                SELECT leave_id, leave_course_id, leave_teacher_id, leave_reason, leave_start_time, leave_end_time, 
                       approval_status, approver_id, approver_name, approval_time, leave_times
                FROM student_leave
                WHERE leave_student_id = %s
                ORDER BY leave_start_time DESC
            """, (self.student_id,))
            
            leave_records = self.cursor.fetchall()
            
            if not leave_records:
                print("暂无请假记录")
                return
            
            print("\n===== 我的请假记录 =====")
            print(f"{'请假ID':<8} {'课程代码':<12} {'教师工号':<12} {'请假原因':<15} {'开始时间':<20} {'结束时间':<20} {'状态':<8} {'审批人':<10} {'审批时间':<20} {'次数':<4}")
            print("-" * 150)
            
            for record in leave_records:
                leave_id, course_id, teacher_id, leave_reason, start_time, end_time, approval_status, approver_id, approver_name, approval_time, times = record
                
                # 处理可能为空的字段
                approver_display = approver_name if approver_name else (approver_id if approver_id else "未审批")
                approval_time_display = str(approval_time) if approval_time else "未审批"
                
                # 截断过长的请假原因以便显示
                short_reason = leave_reason[:12] + "..." if len(leave_reason) > 15 else leave_reason
                
                print(f"{leave_id:<8} {course_id:<12} {teacher_id:<12} {short_reason:<15} {str(start_time):<20} {str(end_time):<20} {approval_status:<8} {approver_display:<10} {approval_time_display:<20} {times:<4}")
                
        except pymysql.MySQLError as e:
            print(f"❌ 查询请假记录失败：{e}")

    def _get_teachers_by_course(self, course_id):
        """根据课程ID查询授课老师"""
        try:
            # 先尝试使用 course_id 字段连接
            try:
                self.cursor.execute("""
                    SELECT ti.teacher_id, ti.teacher_name
                    FROM course_info ci
                    LEFT JOIN teacher_info ti ON ci.teacher_id = ti.teacher_id
                    WHERE ci.course_id = %s
                """, (course_id,))
            except pymysql.MySQLError:
                # 兼容 course_id 字段
                self.cursor.execute("""
                    SELECT ti.teacher_id, ti.teacher_name
                    FROM course_info ci
                    LEFT JOIN teacher_info ti ON ci.teacher_id = ti.teacher_id
                    WHERE ci.course_id = %s
                """, (course_id,))
            
            teachers = self.cursor.fetchall()
            # 过滤空结果
            return [teacher for teacher in teachers if teacher and teacher[0]]
        except pymysql.MySQLError as e:
            print(f"❌ 查询授课老师失败：{e}")
            return []
    
    def _show_my_courses(self):
        """查看我的选课"""
        try:
            # 先尝试使用 course_code 字段连接
            try:
                self.cursor.execute("""
                    SELECT scs.course_id, ci.course_name
                    FROM student_course scs
                    JOIN course_info ci ON scs.course_id = ci.course_id
                    WHERE scs.student_id = %s
                    ORDER BY scs.course_id
                """, (self.student_id,))
            except pymysql.MySQLError:
                # 如果 course_id 字段不存在，尝试使用其他可能的字段名
                self.cursor.execute("""
                    SELECT scs.course_id, ci.course_name
                    FROM student_course scs
                    JOIN course_info ci ON scs.course_id = ci.course_id
                    WHERE scs.student_id = %s
                    ORDER BY scs.course_id
                """, (self.student_id,))
            
            courses = self.cursor.fetchall()
            
            if not courses:
                print("暂无选课记录")
                return
            
            print("\n===== 我的选课 =====")
            print(f"{'课程代码':<12} {'课程名称':<30} {'授课老师':<40}")
            print("-" * 90)
            
            for course in courses:
                course_id, course_name = course
                # 查询该课程的授课老师
                teachers = self._get_teachers_by_course(course_id)
                if teachers:
                    teacher_info = ", ".join([f"{t[0]}({t[1]})" for t in teachers])
                else:
                    teacher_info = "暂无授课老师信息"
                print(f"{course_id:<12} {course_name:<30} {teacher_info:<40}")
                
        except pymysql.MySQLError as e:
            print(f"❌ 查询选课记录失败：{e}")
            print("💡 提示：请检查数据库表结构是否正确")