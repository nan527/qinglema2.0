import pymysql
from db_config import get_db_config
from datetime import datetime
import json

class CounselorOperation:
    def __init__(self, counselor_id, counselor_name, responsible_grade):
        """初始化：接收辅导员ID、姓名、负责年级"""
        self.counselor_id = counselor_id  # 辅导员工号（主键）
        self.counselor_name = counselor_name  # 辅导员姓名
        self.responsible_grade = responsible_grade  # 负责年级
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
            raise Exception(f"数据库连接失败：{e}")

    def _close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.open:
            self.conn.close()

    def show_menu(self):
        """辅导员操作菜单（新增“查看个人信息”选项）"""
        while True:
            print(f"\n===== 辅导员操作中心（欢迎 {self.counselor_name} 老师）=====")
            print("1. 查看负责年级待审批请假记录")
            print("2. 查看负责年级所有请假记录")
            print("3. 审批请假申请")
            print("4. 修改个人密码")
            print("5. 查看个人信息")  # 新增选项：查看个人信息
            print("6. 退出系统")
            choice = input("请选择操作(1-6)：").strip()

            if choice == "1":
                self._show_pending_leaves()
            elif choice == "2":
                self._show_all_leaves()
            elif choice == "3":
                self._approve_leave()
            elif choice == "4":
                self._change_password()
            elif choice == "5":
                self._show_personal_info()  # 新增方法：显示个人信息
            elif choice == "6":
                print("👋 退出辅导员系统")
                self._close_db()
                break
            else:
                print("❌ 无效操作，请重新输入1-6")

    # ---------------------------- 新增：查看个人信息 ----------------------------
    def _show_personal_info(self):
        """从counselor_info表读取并显示所有个人信息"""
        try:
            # 查询counselor_info表中当前辅导员的所有字段
            sql = """
                SELECT counselor_id, password, counselor_name, dept, 
                       responsible_grade, responsible_major, contact,
                       create_time, update_time
                FROM counselor_info
                WHERE counselor_id = %s
            """
            self.cursor.execute(sql, (self.counselor_id,))
            info = self.cursor.fetchone()

            if not info:
                print("❌ 未查询到个人信息")
                return

            # 解析查询结果（对应表中所有字段）
            counselor_id, password, counselor_name, dept, \
            responsible_grade, responsible_major, contact, \
            create_time, update_time = info

            # 格式化显示（密码显示为***保护隐私）
            print("\n===== 个人信息详情 =====")
            print(f"辅导员工号：{counselor_id}")
            print(f"登录密码：{'*' * len(password)}（已加密显示）")
            print(f"姓名：{counselor_name}")
            print(f"所属部门：{dept}")
            print(f"负责年级：{responsible_grade}级")
            print(f"负责专业：{responsible_major}")
            print(f"联系方式：{contact}")
            print(f"记录创建时间：{create_time}")
            print(f"最后更新时间：{update_time}")
            print("=======================")

        except pymysql.MySQLError as e:
            print(f"❌ 查询个人信息失败：{e}")

    # ---------------------------- 原有功能：查看待审批请假记录 ----------------------------
    def _show_pending_leaves(self):
        """查看负责年级中状态为“待审批”的请假记录"""
        try:
            sql = """
                SELECT sl.leave_id, sl.student_id, sl.student_name, sl.course_code, 
                       sl.leave_reason, sl.start_time, sl.end_time, sl.approval_status
                FROM student_leave sl
                WHERE LEFT(sl.student_id, 4) = %s
                  AND sl.approval_status = '待审批'
                ORDER BY sl.start_time DESC
            """
            self.cursor.execute(sql, (self.responsible_grade,))
            leaves = self.cursor.fetchall()

            if not leaves:
                print(f"\n📌 暂无{self.responsible_grade}级待审批请假记录")
                return

            print(f"\n===== {self.responsible_grade}级待审批请假记录 =====")
            print(f"{'请假ID':<10} {'学生ID':<15} {'学生姓名':<10} {'课程代码':<20} {'请假原因':<20} {'开始时间':<20} {'结束时间':<20} {'状态':<10}")
            print("-" * 140)
            for leave in leaves:
                # 课程代码可能包含多个，截取显示前18个字符
                course_code_display = str(leave[3])[:18] if leave[3] else ""
                print(f"{leave[0]:<10} {leave[1]:<15} {leave[2]:<10} {course_code_display:<20} {leave[4][:18]:<20} {str(leave[5]):<20} {str(leave[6]):<20} {leave[7]:<10}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    # ---------------------------- 原有功能：查看所有请假记录 ----------------------------
    def _show_all_leaves(self):
        """查看负责年级所有请假记录（含已批准/已拒绝）"""
        try:
            sql = """
                SELECT sl.leave_id, sl.student_id, sl.student_name, sl.course_code, 
                       sl.approval_status, sl.approver_id, sl.approver_name, sl.approval_time
                FROM student_leave sl
                WHERE LEFT(sl.student_id, 4) = %s
                ORDER BY sl.approval_time DESC, sl.start_time DESC
            """
            self.cursor.execute(sql, (self.responsible_grade,))
            leaves = self.cursor.fetchall()

            if not leaves:
                print(f"\n📌 暂无{self.responsible_grade}级请假记录")
                return

            print(f"\n===== {self.responsible_grade}级所有请假记录 =====")
            print(f"{'请假ID':<10} {'学生ID':<15} {'学生姓名':<10} {'课程代码':<20} {'状态':<10} {'审批人ID':<10} {'审批人姓名':<10} {'审批时间':<20}")
            print("-" * 130)
            for leave in leaves:
                approver_id = leave[5] if leave[5] else "未审批"
                approver_name = leave[6] if leave[6] else "未审批"
                approval_time = str(leave[7]) if leave[7] else "未审批"
                # 课程代码可能包含多个，截取显示前18个字符
                course_code_display = str(leave[3])[:18] if leave[3] else ""
                print(f"{leave[0]:<10} {leave[1]:<15} {leave[2]:<10} {course_code_display:<20} {leave[4]:<10} {approver_id:<10} {approver_name:<10} {approval_time:<20}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")

    # ---------------------------- 原有功能：审批请假申请 ----------------------------
    def _approve_leave(self):
        """审批请假申请：仅“同意”时增加学生times；学生times≥5时弹出警告"""
        try:
            leave_id = input("\n请输入要审批的请假ID：").strip()
            # 1. 校验请假记录归属 + 查询学生当前请假次数
            sql_check = """
                SELECT sl.leave_id, sl.student_id, sl.approval_status, si.times
                FROM student_leave sl
                LEFT JOIN student_info si ON sl.student_id = si.student_id
                WHERE sl.leave_id = %s
                  AND LEFT(sl.student_id, 4) = %s
            """
            self.cursor.execute(sql_check, (leave_id, self.responsible_grade))
            result = self.cursor.fetchone()

            if not result:
                print(f"❌ 未找到{self.responsible_grade}级ID为{leave_id}的请假记录")
                return

            leave_id_db, student_id, approval_status, student_times = result
            if approval_status != "待审批":
                print(f"❌ 该请假记录状态为「{approval_status}」，无需重复审批")
                return

            # 2. 学生请假次数≥5时弹出警告
            if student_times >= 5:
                print(f"\n⚠️ 警告：学生{student_id}当前已请假{student_times}次，请慎重审批！")
                confirm = input("是否继续审批？(y/n)：").strip().lower()
                if confirm != "y":
                    print("审批已取消")
                    return

            # 3. 选择审批结果
            print("\n请选择审批结果：")
            print("1. 同意")
            print("2. 不同意")
            approve_choice = input("输入序号（1/2）：").strip()
            if approve_choice not in ["1", "2"]:
                print("❌ 无效选择，审批取消")
                return

            new_status = "已批准" if approve_choice == "1" else "已拒绝"
            approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            approver_name = self.counselor_name  # 当前辅导员姓名

            # 4. 事务处理：更新请假记录 + （仅同意时）更新学生times
            self.conn.begin()
            # 4.1 更新student_leave表
            sql_update_leave = """
                UPDATE student_leave
                SET approval_status = %s, 
                    approver_id = %s, 
                    approver_name = %s, 
                    approval_time = %s
                WHERE leave_id = %s
            """
            self.cursor.execute(sql_update_leave, (new_status, self.counselor_id, approver_name, approval_time, leave_id))

            # 4.2 仅“同意”时，更新student_info的times字段
            update_msg = ""
            if approve_choice == "1":
                sql_update_student = """
                    UPDATE student_info
                    SET times = times + 1, update_time = %s
                    WHERE student_id = %s
                """
                self.cursor.execute(sql_update_student, (approval_time, student_id))
                update_msg = f"，学生{student_id}请假次数更新为{student_times + 1}次"

            self.conn.commit()
            print(f"✅ 审批成功！请假ID{leave_id}状态更新为「{new_status}」，审批人：{approver_name}{update_msg}")

        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 审批失败：{e}")

    # ---------------------------- 原有功能：修改个人密码 ----------------------------
    def _change_password(self):
        """修改辅导员个人密码"""
        try:
            # 1. 验证原密码
            old_pwd = input("\n请输入原密码：").strip()
            sql_check = """
                SELECT password FROM counselor_info
                WHERE counselor_id = %s
            """
            self.cursor.execute(sql_check, (self.counselor_id,))
            db_pwd = self.cursor.fetchone()[0]

            if old_pwd != db_pwd:
                print("❌ 原密码错误，修改失败")
                return

            # 2. 输入新密码
            new_pwd = input("请输入新密码（不少于6位）：").strip()
            if len(new_pwd) < 6:
                print("❌ 新密码长度不足6位，修改失败")
                return

            confirm_pwd = input("请再次输入新密码：").strip()
            if new_pwd != confirm_pwd:
                print("❌ 两次输入的密码不一致，修改失败")
                return

            # 3. 更新密码（同时更新update_time）
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql_update = """
                UPDATE counselor_info
                SET password = %s, update_time = %s
                WHERE counselor_id = %s
            """
            self.cursor.execute(sql_update, (new_pwd, update_time, self.counselor_id))
            self.conn.commit()
            print("✅ 密码修改成功！请重新登录验证")

        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 密码修改失败：{e}")
    
    # ---------------------------- API功能：审批请假申请 ----------------------------
    def approve_leave_api(self, leave_id, action):
        """审批请假申请的API方法，返回JSON格式响应"""
        try:
            # 1. 校验请假记录归属 + 查询学生当前请假次数
            sql_check = """
                SELECT sl.leave_id, sl.student_id, sl.approval_status, si.times
                FROM student_leave sl
                LEFT JOIN student_info si ON sl.student_id = si.student_id
                WHERE sl.leave_id = %s
                  AND LEFT(sl.student_id, 4) = %s
            """
            self.cursor.execute(sql_check, (leave_id, self.responsible_grade))
            result = self.cursor.fetchone()

            if not result:
                return {"success": False, "message": f"未找到{self.responsible_grade}级ID为{leave_id}的请假记录"}

            leave_id_db, student_id, approval_status, student_times = result
            if approval_status != "待审批":
                return {"success": False, "message": f"该请假记录状态为「{approval_status}」，无需重复审批"}

            # 2. 学生请假次数≥5时仍可审批，但会在日志中记录
            if student_times >= 5:
                print(f"⚠️ 警告：学生{student_id}当前已请假{student_times}次")

            # 3. 确定审批结果
            if action == "approve":
                new_status = "已批准"
            elif action == "reject":
                new_status = "已驳回"
            else:
                return {"success": False, "message": "无效的操作类型"}

            approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            approver_name = self.counselor_name  # 当前辅导员姓名

            # 4. 事务处理：更新请假记录 + （仅同意时）更新学生times
            self.conn.begin()
            # 4.1 更新student_leave表
            sql_update_leave = """
                UPDATE student_leave
                SET approval_status = %s, 
                    approver_id = %s, 
                    approver_name = %s, 
                    approval_time = %s
                WHERE leave_id = %s
            """
            self.cursor.execute(sql_update_leave, (new_status, self.counselor_id, approver_name, approval_time, leave_id))

            # 4.2 仅“同意”时，更新student_info的times字段
            if action == "approve":
                sql_update_student = """
                    UPDATE student_info
                    SET times = times + 1, update_time = %s
                    WHERE student_id = %s
                """
                self.cursor.execute(sql_update_student, (approval_time, student_id))

            self.conn.commit()
            return {"success": True, "message": f"审批成功！请假ID{leave_id}状态更新为「{new_status}」"}

        except pymysql.MySQLError as e:
            if self.conn:
                self.conn.rollback()
            print(f"❌ 审批API失败：{e}")
            return {"success": False, "message": f"数据库错误：{str(e)}"}
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"❌ 审批API异常：{e}")
            return {"success": False, "message": f"系统错误：{str(e)}"}