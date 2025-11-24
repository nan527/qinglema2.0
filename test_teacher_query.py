# test_teacher_query.py - 测试老师查询功能
from teacher.teacher_operation import TeacherService

service = TeacherService()
result = service.get_approved_student_leaves(
    teacher_id="201301101",
    filter_date="2025-11-14"
)

print("=" * 50)
print("测试结果：")
print(result)
print("=" * 50)

