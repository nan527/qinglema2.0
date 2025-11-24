
import uuid
from datetime import datetime
from typing import List, Optional, Sequence

import pymysql
from pymysql.cursors import DictCursor

from db_config import get_db_config

# 统一维护相关表名，方便后续调整
STUDENT_LEAVE_TABLE = "student_leave"
TEACHER_LEAVE_TABLE = "teacher_leave"
COURSE_TABLE = "course_info"
TEACHER_TABLE = "teacher_info"

# 默认视为“已批准/同意”的状态枚举
DEFAULT_APPROVED_STATUSES = ("同意", "已批准", "通过")


class TeacherService:
    """
    为老师模块提供数据库操作封装：
    1. 查询导员已批准、待老师处理的学生请假记录
    2. 老师发起请假并同步给课程内学生（学生可通过自己的查询接口查看到课程老师的请假）
    """

    def __init__(self):
        self.config = {**get_db_config(), "cursorclass": DictCursor}

    # ------------------------------------------------------------------ #
    # 公共工具方法
    # ------------------------------------------------------------------ #
    def _connect(self):
        return pymysql.connect(**self.config)

    @staticmethod
    def _serialize_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """
        兼容常见的时间格式（ISO8601 / YYYY-MM-DD HH:MM:SS）
        """
        if not value:
            raise ValueError("时间不能为空")

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析时间：{value}")

    # ------------------------------------------------------------------ #
    # 数据查询
    # ------------------------------------------------------------------ #
    def get_approved_student_leaves(
        self,
        teacher_id: str,
        filter_date: Optional[str] = None,
    ) -> dict:
        """
        老师获取已由辅导员审核通过的学生请假记录
        支持按日期筛选：如果学生在选定日期内出现请假（请假期间包含该日期），则显示
        """
        if not teacher_id:
            return {"success": False, "message": "teacher_id 不能为空"}

        status_list = DEFAULT_APPROVED_STATUSES
        placeholders = ", ".join(["%s"] * len(status_list))
        
        # 构建SQL查询条件
        conditions = [
            "sl.teacher_id = %s",
            f"sl.approval_status IN ({placeholders})"
        ]
        params = [teacher_id, *status_list]
        
        # 添加日期筛选：如果选定日期在请假时间范围内（start_time <= 选定日期 <= end_time）
        if filter_date:
            conditions.append("DATE(sl.start_time) <= %s AND DATE(sl.end_time) >= %s")
            params.append(filter_date)
            params.append(filter_date)
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
            SELECT
                sl.leave_id,
                sl.student_id,
                sl.student_name,
                sl.dept,
                sl.course_id,
                c.course_name,
                sl.leave_reason,
                sl.start_time,
                sl.end_time,
                sl.approval_status,
                sl.approval_time,
                sl.times
            FROM {STUDENT_LEAVE_TABLE} sl
            LEFT JOIN {COURSE_TABLE} c
                ON sl.course_id = c.course_id
            WHERE {where_clause}
            ORDER BY sl.approval_time DESC, sl.start_time DESC
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, tuple(params))
                    rows = cursor.fetchall()
        except pymysql.MySQLError as exc:
            return {
                "success": False,
                "message": f"查询学生请假失败：{exc}",
            }

        for row in rows:
            row["start_time"] = self._serialize_datetime(row["start_time"])
            row["end_time"] = self._serialize_datetime(row["end_time"])
            row["approval_time"] = self._serialize_datetime(
                row.get("approval_time")
            )

        return {"success": True, "data": rows, "message": "查询成功"}

    # ------------------------------------------------------------------ #
    # 老师请假申请
    # ------------------------------------------------------------------ #
    def submit_teacher_leave(
        self,
        teacher_id: str,
        course_id: str,
        leave_reason: str,
        start_time: str,
        end_time: str,
    ) -> dict:
        """
        老师提交请假申请，并将请假信息与课程绑定。
        学生端可通过“我的课程”查询相应老师的请假记录。
        """
        if not all([teacher_id, course_id, leave_reason, start_time, end_time]):
            return {"success": False, "message": "请假参数不完整"}

        try:
            start_dt = self._parse_datetime(start_time)
            end_dt = self._parse_datetime(end_time)
        except ValueError as exc:
            return {"success": False, "message": str(exc)}

        if start_dt >= end_dt:
            return {"success": False, "message": "开始时间需早于结束时间"}

        # 查询教师信息
        teacher_sql = f"""
            SELECT teacher_id, teacher_name, dept
            FROM {TEACHER_TABLE}
            WHERE teacher_id = %s
        """
        # 查询课程信息
        course_sql = f"""
            SELECT course_id, course_name
            FROM {COURSE_TABLE}
            WHERE course_id = %s
        """

        leave_id = uuid.uuid4().hex[:12]
        insert_sql = f"""
            INSERT INTO {TEACHER_LEAVE_TABLE}
                (leave_id, teacher_id, dept, course_id,
                 leave_reason, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        try:
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(teacher_sql, (teacher_id,))
                    teacher = cursor.fetchone()
                    if not teacher:
                        return {
                            "success": False,
                            "message": "教师信息不存在",
                        }

                    cursor.execute(course_sql, (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {
                            "success": False,
                            "message": "课程不存在",
                        }

                    cursor.execute(
                        insert_sql,
                        (
                            leave_id,
                            teacher_id,
                            teacher["dept"],
                            course_id,
                            leave_reason,
                            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                conn.commit()
        except pymysql.MySQLError as exc:
            return {"success": False, "message": f"老师请假提交失败：{exc}"}

        return {
            "success": True,
            "message": "老师请假提交成功",
            "data": {
                "leave_id": leave_id,
                "teacher_id": teacher_id,
                "teacher_name": teacher["teacher_name"],
                "course_id": course_id,
                "course_name": course["course_name"],
                "leave_reason": leave_reason,
                "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }


class TeacherOperation:
    """
    终端版老师菜单，复用 TeacherService。
    """

    def __init__(self, teacher_info: dict):
        self.teacher_id = teacher_info["user_account"]
        self.teacher_name = teacher_info["user_name"]
        self.service = TeacherService()

    def show_menu(self):
        while True:
            print("\n===== 老师工作台 =====")
            print(f"👤 当前教师：{self.teacher_name}（{self.teacher_id}）")
            print("1. 查看已批准的学生请假")
            print("2. 提交老师请假申请")
            print("3. 退出老师工作台")
            choice = input("请选择操作(1-3)：").strip()

            if choice == "1":
                self._show_student_leaves()
            elif choice == "2":
                self._submit_teacher_leave()
            elif choice == "3":
                print("👋 已退出老师工作台")
                break
            else:
                print("❌ 无效操作，请重新输入")

    # ---------------- 菜单功能 ----------------
    def _show_student_leaves(self):
        result = self.service.get_approved_student_leaves(
            teacher_id=self.teacher_id,
            statuses=None,  # 使用默认的已批准状态
        )
        if not result.get("success"):
            print(f"❌ 查询失败：{result.get('message')}")
            return

        data = result.get("data") or []
        if not data:
            print("\n暂无匹配的学生请假记录")
            return

        print("\n===== 学生请假列表（辅导员已批准）=====")
        header = (
            f"{'请假单号':<10} {'学号':<12} {'姓名':<6} {'课程':<6} "
            f"{'课程名称':<15} {'开始时间':<19} {'结束时间':<19} {'状态':<8}"
        )
        print(header)
        print("-" * len(header))
        for item in data:
            print(
                f"{item.get('leave_id', '-'):<10} "
                f"{item.get('student_id', '-'):<12} "
                f"{item.get('student_name', '-'):<6} "
                f"{item.get('course_id', '-'):<6} "
                f"{(item.get('course_name') or '-')[:14]:<15} "
                f"{(item.get('start_time') or '-'):<19} "
                f"{(item.get('end_time') or '-'):<19} "
                f"{item.get('approval_status', '-'):<8}"
            )

    def _submit_teacher_leave(self):
        print("\n===== 老师请假申请 =====")
        course_id = input("请输入课程编号：").strip()
        leave_reason = input("请输入请假原因：").strip()
        start_time = input("请输入开始时间（格式：YYYY-MM-DD HH:MM:SS）：").strip()
        end_time = input("请输入结束时间（格式：YYYY-MM-DD HH:MM:SS）：").strip()

        result = self.service.submit_teacher_leave(
            teacher_id=self.teacher_id,
            course_id=course_id,
            leave_reason=leave_reason,
            start_time=start_time,
            end_time=end_time,
        )
        if result.get("success"):
            print("✅ 请假提交成功")
            data = result.get("data") or {}
            print(
                f"请假单号：{data.get('leave_id')} / 课程：{data.get('course_id')} "
                f" / 时间：{data.get('start_time')} ~ {data.get('end_time')}"
            )
        else:
            print(f"❌ 请假提交失败：{result.get('message')}")


if __name__ == "__main__":
    service = TeacherService()
    # 示例：打印老师可见的学生请假
    result = service.get_approved_student_leaves("201301101")
    print(result)
