import os
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from functools import wraps
import pymysql
from db_config import get_db_config  # 确保存在数据库配置文件

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_123456'  # 生产环境需更换为随机安全密钥
app.config['UPLOAD_FOLDER'] = 'qianzi'  # 签字图片保存目录

# 确保签字文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库连接工具函数
def get_db_connection():
    """获取数据库连接"""
    config = get_db_config()
    return pymysql.connect(** config)

# 登录验证装饰器（带角色权限控制）
def login_required(role=None):
    """装饰器：验证登录状态和角色权限"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 未登录用户强制跳转登录页
            if 'user_info' not in session:
                return redirect(url_for('login_page'))
            # 验证角色权限（如指定角色，仅允许该角色访问）
            if role and session['user_info']['role_name'] != role:
                return "没有访问权限", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 页面路由
@app.route('/')
def index():
    """首页：根据登录状态自动跳转"""
    if 'user_info' in session:
        role = session['user_info']['role_name']
        if role == '学生':
            return redirect('/student')
        elif role == '管理员':
            return redirect('/admin')
        elif role == '辅导员':
            return redirect('/counselor')
        elif role == '讲师':
            return redirect('/teacher')
    return redirect('/login')

@app.route('/login')
def login_page():
    """登录页面"""
    if 'user_info' in session:
        return redirect(url_for('index'))  # 已登录用户直接跳转
    return render_template('login.html')

@app.route('/admin')
@login_required(role='管理员')
def admin_page():
    """管理员页面"""
    return render_template('admin.html', user_info=session['user_info'])

@app.route('/student')
@login_required(role='学生')
def student_page():
    """学生页面"""
    return render_template('student.html', user_info=session['user_info'])

@app.route('/teacher')
@login_required(role='讲师')
def teacher_page():
    """讲师页面"""
    return render_template('teacher.html', user_info=session['user_info'])

@app.route('/counselor')
@login_required(role='辅导员')
def counselor_page():
    """辅导员页面（支持接收签字图片参数）"""
    signature = request.args.get('signature', '')
    return render_template(
        'counselor.html', 
        user_info=session['user_info'],
        signature=signature
    )

@app.route('/qianzi')
@login_required(role='辅导员')
def qianzi_page():
    """签字页面（仅辅导员可访问）"""
    return render_template('qianzi.html')

# API接口
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.json
    account = data.get('account', '').strip()
    password = data.get('password', '').strip()
    
    if not account or not password:
        return jsonify({"status": "error", "message": "账号和密码不能为空"})
    
    # 账号长度→身份映射（4位管理员/8位辅导员/9位讲师/12位学生）
    account_len = len(account)
    role_map = {
        4: {
            "table": "admin_info",
            "account_field": "admin_id",
            "pwd_field": "password",
            "name_field": "admin_name",
            "role_name": "管理员"
        },
        8: {
            "table": "counselor_info",
            "account_field": "counselor_id",
            "pwd_field": "password",
            "name_field": "counselor_name",
            "role_name": "辅导员",
            "extra_field": "responsible_grade"
        },
        9: {
            "table": "teacher_info",
            "account_field": "teacher_id",
            "pwd_field": "password",
            "name_field": "teacher_name",
            "role_name": "讲师"
        },
        12: {
            "table": "student_info",
            "account_field": "student_id",
            "pwd_field": "password",
            "name_field": "student_name",
            "role_name": "学生"
        }
    }
    
    if account_len not in role_map:
        return jsonify({
            "status": "error", 
            "message": f"账号长度不符合规则（支持：4位/8位/9位/12位）"
        })
    
    target = role_map[account_len]
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询SQL
        if target["role_name"] == "辅导员":
            sql = f"""
                SELECT {target['account_field']}, {target['pwd_field']}, {target['name_field']}, {target['extra_field']}
                FROM {target['table']}
                WHERE {target['account_field']} = %s
            """
        else:
            sql = f"""
                SELECT {target['account_field']}, {target['pwd_field']}, {target['name_field']}
                FROM {target['table']}
                WHERE {target['account_field']} = %s
            """
            
        cursor.execute(sql, (account,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"status": "error", "message": f"{target['role_name']}账号不存在"})
        
        # 解析查询结果
        if target["role_name"] == "辅导员":
            db_account, db_password, db_name, db_responsible_grade = user
        else:
            db_account, db_password, db_name = user
            
        if password != db_password:
            return jsonify({"status": "error", "message": "密码错误"})
        
        # 登录成功，保存用户信息到session
        session['user_info'] = {
            "user_account": db_account,
            "user_name": db_name,
            "role_name": target['role_name']
        }
        
        if target["role_name"] == "辅导员":
            session['user_info']["responsible_grade"] = db_responsible_grade
            
        return jsonify({
            "status": "success", 
            "message": f"登录成功，欢迎回来，{db_name}",
            "role": target['role_name']
        })
        
    except pymysql.MySQLError as e:
        return jsonify({"status": "error", "message": f"数据库错误：{str(e)}"})
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()

@app.route('/api/check_login', methods=['GET'])
def check_login():
    """检查登录状态接口"""
    if 'user_info' in session:
        return jsonify({
            "logged_in": True,
            "user_info": session['user_info']
        })
    return jsonify({"logged_in": False})

@app.route('/api/logout', methods=['POST'])
def logout():
    """退出登录接口"""
    session.pop('user_info', None)
    return jsonify({"status": "success", "message": "已成功登出"})

@app.route('/api/save_signature', methods=['POST'])
@login_required(role='辅导员')
def save_signature():
    """保存签字图片接口"""
    try:
        data = request.json
        image_data = data.get('imageData', '').replace('data:image/png;base64,', '')
        file_name = data.get('fileName', f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        
        if not image_data:
            return jsonify({"success": False, "message": "未获取到签字数据"})
        
        # 解码并保存图片
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return jsonify({
            "success": True,
            "message": "签字保存成功",
            "imagePath": file_name
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 签字图片访问路由
@app.route('/qianzi/<path:filename>')
@login_required(role='辅导员')
def serve_signature(filename):
    """提供签字图片访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 管理员专用接口示例
@app.route('/api/admin/users', methods=['GET'])
@login_required(role='管理员')
def get_all_users():
    """获取所有用户（仅管理员）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT '管理员' as role, admin_id as id, admin_name as name FROM admin_info
            UNION ALL
            SELECT '辅导员' as role, counselor_id as id, counselor_name as name FROM counselor_info
            UNION ALL
            SELECT '讲师' as role, teacher_id as id, teacher_name as name FROM teacher_info
            UNION ALL
            SELECT '学生' as role, student_id as id, student_name as name FROM student_info
        """)
        users = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": users})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})


# ---------- 学生端：课程与请假相关API ----------
@app.route('/api/courses', methods=['GET'])
@login_required(role='学生')
def api_get_courses():
    """返回当前学生已选的课程列表：[{course_id, course_name}, ...]"""
    student_id = session['user_info']['user_account']  # 使用正确的session键名
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询学生已选课程
        cursor.execute("""
            SELECT ci.course_id, ci.course_name 
            FROM course_info ci
            JOIN student_course_selection scs ON ci.course_id = scs.course_id
            WHERE scs.student_id = %s
            ORDER BY ci.course_id
        """, (student_id,))
        rows = cursor.fetchall()
        
        return jsonify({"success": True, "data": rows})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.open:
                conn.close()
        except Exception:
            pass


@app.route('/api/teachers', methods=['GET'])
@login_required(role='学生')
def api_get_teachers():
    """返回所有教师列表：[{teacher_id, teacher_name}, ...]"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT teacher_id, teacher_name FROM teacher_info ORDER BY teacher_id")
        rows = cursor.fetchall()
        return jsonify({"success": True, "data": rows})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.open:
                conn.close()
        except Exception:
            pass


@app.route('/api/course_teachers', methods=['GET'])
@login_required(role='学生')
def api_course_teachers():
    """根据 course_id 返回该课程的授课教师（返回 teacher_id, teacher_name 列表）"""
    course_id = request.args.get('course_id', '').strip()  # 直接使用course_id参数
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        if course_id:
            # 直接查询teacher_course表获取该课程的所有授课教师
            cursor.execute("""
                SELECT ti.teacher_id, ti.teacher_name
                FROM teacher_course tc
                JOIN teacher_info ti ON tc.teacher_id = ti.teacher_id
                WHERE tc.course_id = %s
            """, (course_id,))
            rows = cursor.fetchall()
            
            # 过滤空结果
            rows = [r for r in rows if r and r.get('teacher_id')]
            
            # 如果没有找到，返回友好提示
            if not rows:
                return jsonify({"success": True, "data": [], "message": "该课程暂无授课教师信息"})
            
            return jsonify({"success": True, "data": rows})

        else:
            # 无 course_id 则返回所有教师
            cursor.execute("SELECT teacher_id, teacher_name FROM teacher_info ORDER BY teacher_id")
            rows = cursor.fetchall()
            return jsonify({"success": True, "data": rows})

    except Exception as e:
        # 捕获所有异常，确保返回有效的 JSON 响应
        print(f"获取课程教师信息失败: {str(e)}")
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})
    finally:
        # 确保资源被正确释放
        try:
            cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.open:
                conn.close()
        except Exception:
            pass


@app.route('/api/student/leave', methods=['POST'])
@login_required(role='学生')
def api_student_leave():
    """学生提交请假：支持多课程选择，期望 JSON {course_teacher_pairs: [{course_id, teacher_id}], start_time, end_time, leave_reason} 返回 success/message"""
    data = request.json or {}
    course_teacher_pairs = data.get('course_teacher_pairs', [])
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()
    leave_reason = data.get('leave_reason', '').strip()

    # 参数验证
    if not start_time or not end_time or not leave_reason:
        return jsonify({"success": False, "message": "请填写完整的请假信息"})
    
    # 验证课程-教师对数组
    if not isinstance(course_teacher_pairs, list) or len(course_teacher_pairs) == 0:
        return jsonify({"success": False, "message": "请至少选择一个课程和对应的老师"})
    
    # 验证每个课程-教师对
    for pair in course_teacher_pairs:
        if not isinstance(pair, dict) or not pair.get('course_id') or not pair.get('teacher_id'):
            return jsonify({"success": False, "message": "课程或教师信息不完整"})

    student_account = session['user_info']['user_account']
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取学生姓名与部门
        cursor.execute("SELECT student_name, dept FROM student_info WHERE student_id = %s", (student_account,))
        stu = cursor.fetchone()
        if not stu:
            return jsonify({"success": False, "message": "学生信息不存在"})
        student_name, dept = stu[0], stu[1]

        # 计算已批准请假次数
        cursor.execute("SELECT COUNT(*) FROM student_leave WHERE student_id = %s AND approval_status = '已批准'", (student_account,))
        approved_times = cursor.fetchone()[0]
        current_times = approved_times + 1
        approval_status = '待审批'

        # 为每个课程-教师对创建请假记录
        for pair in course_teacher_pairs:
            course_code = pair.get('course_id', '').strip()  # 获取课程代码
            teacher_id = pair.get('teacher_id', '').strip()
            
            cursor.execute('''
                INSERT INTO student_leave
                (student_id, student_name, dept, course_code, teacher_id, leave_reason, start_time, end_time, approval_status, times)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (student_account, student_name, dept, course_code, teacher_id, leave_reason, start_time, end_time, approval_status, current_times))
        
        conn.commit()
        return jsonify({"success": True, "message": "请假提交成功"})
        
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        print(f"提交请假失败: {str(e)}")
        return jsonify({"success": False, "message": f"数据库错误：{str(e)}"})
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn and hasattr(conn, 'open') and conn.open:
                conn.close()
        except Exception:
            pass

# 启动应用
if __name__ == '__main__':
    # 生产环境需设置debug=False，并配置合适的host和port
    app.run(debug=True, host='0.0.0.0', port=5000)