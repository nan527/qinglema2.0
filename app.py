import os
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from functools import wraps
import pymysql
from db_config import get_db_config  # 确保存在数据库配置文件
from counselor_operation import CounselorOperation

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_123456'  # 生产环境需更换为随机安全密钥
app.config['UPLOAD_FOLDER'] = 'qianzi'  # 签字图片保存目录
app.config['DEBUG'] = True  # 启用调试模式

# 确保签字文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库连接工具函数
def get_db_connection():
    """获取数据库连接"""
    try:
        config = get_db_config()
        conn = pymysql.connect(** config)
        print("数据库连接成功")
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise

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
    """辅导员页面（重定向到默认的全部假条页面）"""
    signature = request.args.get('signature', '')
    # 重定向到全部假条页面，并传递signature参数
    if signature:
        return redirect(url_for('counselor_all_leaves', signature=signature))
    return redirect(url_for('counselor_all_leaves'))

@app.route('/counselor/all')
@login_required(role='辅导员')
def counselor_all_leaves():
    """全部假条页面"""
    signature = request.args.get('signature', '')
    return render_template(
        'counselor/all_leaves.html', 
        user_info=session['user_info'],
        signature=signature,
        filter_type='all'
    )

@app.route('/counselor/pending')
@login_required(role='辅导员')
def counselor_pending_leaves():
    """待审批假条页面"""
    signature = request.args.get('signature', '')
    return render_template(
        'counselor/pending_leaves.html', 
        user_info=session['user_info'],
        signature=signature,
        filter_type='pending'
    )

@app.route('/counselor/approved')
@login_required(role='辅导员')
def counselor_approved_leaves():
    """已批准假条页面"""
    signature = request.args.get('signature', '')
    return render_template(
        'counselor/approved_leaves.html', 
        user_info=session['user_info'],
        signature=signature,
        filter_type='approved'
    )

@app.route('/counselor/rejected')
@login_required(role='辅导员')
def counselor_rejected_leaves():
    """已驳回假条页面"""
    signature = request.args.get('signature', '')
    return render_template(
        'counselor/rejected_leaves.html', 
        user_info=session['user_info'],
        signature=signature,
        filter_type='rejected'
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

# 教师获取请假记录接口
@app.route('/api/teacher/leave_requests', methods=['GET'])
@login_required(role='讲师')
def get_teacher_leave_requests():
    """获取教师相关的请假记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取当前登录教师的ID
        teacher_id = session['user_info']['user_account']
        
        # 查询教师相关的请假记录
        # 假设student_leave表中有teacher_id或course_id与teacher_info关联
        sql = """
            SELECT 
            sl.leave_id,
            sl.student_id,
            si.student_name,
            sl.course_code,
            sl.start_time,
            sl.end_time,
            sl.leave_reason,
            sl.approval_status,
            sl.sort,
            si.times
            FROM 
                student_leave sl
            LEFT JOIN 
                student_info si ON sl.student_id = si.student_id
            WHERE 
                sl.approver_id = %s OR sl.course_code IN (
                    SELECT course_id FROM teacher_courses WHERE teacher_id = %s
                )
            ORDER BY 
                sl.start_time DESC
        """
        
        cursor.execute(sql, (teacher_id, teacher_id))
        leave_requests = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": leave_requests
        })
        
    except pymysql.MySQLError as e:
        print(f"数据库错误: {str(e)}")
        # 如果teacher_courses表不存在或者关联查询失败，尝试简单查询
        try:
            cursor.execute("""
                SELECT 
            sl.leave_id,
            sl.student_id,
            si.student_name,
            sl.course_code,
            sl.start_time,
            sl.end_time,
            sl.leave_reason,
            sl.approval_status,
            sl.sort,
            si.times
                FROM 
                    student_leave sl
                LEFT JOIN 
                    student_info si ON sl.student_id = si.student_id
                WHERE 
                    sl.approver_id = %s
                ORDER BY 
                    sl.start_time DESC
            """, (teacher_id,))
            leave_requests = cursor.fetchall()
            conn.close()
            return jsonify({
                "success": True,
                "data": leave_requests
            })
        except Exception as inner_e:
            print(f"备用查询也失败: {str(inner_e)}")
            return jsonify({
                "success": False,
                "message": f"获取请假记录失败: {str(inner_e)}"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取请假记录失败: {str(e)}"
        })

# 辅导员获取请假记录接口
@app.route('/api/counselor/leave_requests', methods=['GET'])
@login_required(role='辅导员')
def get_counselor_leave_requests():
    """获取辅导员相关的请假记录（基于负责年级）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取当前登录辅导员的ID和负责年级
        counselor_id = session['user_info']['user_account']
        responsible_grade = session['user_info'].get('responsible_grade', '')
        
        # 根据年级过滤学生请假记录
        # 从学生ID的前4位判断年级
        sql = """
            SELECT 
                sl.leave_id,
                sl.student_id,
                si.student_name,
                sl.course_code,
                sl.start_time,
                sl.end_time,
                sl.leave_reason,
                sl.approval_status,
                sl.sort,
                si.times
            FROM 
                student_leave sl
            LEFT JOIN 
                student_info si ON sl.student_id = si.student_id
            WHERE 
                1=1
        """
        
        # 如果有负责年级，添加年级过滤条件
        params = []
        if responsible_grade:
            sql += " AND LEFT(sl.student_id, 4) = %s"
            params.append(responsible_grade)
        
        # 添加排序
        sql += " ORDER BY sl.start_time DESC"
        
        cursor.execute(sql, params)
        leave_requests = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": leave_requests
        })
        
    except pymysql.MySQLError as e:
        print(f"数据库错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取请假记录失败: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取请假记录失败: {str(e)}"
        })

# 辅导员请假审批API
@app.route('/api/counselor/approve_leave', methods=['POST'])
@login_required(role='辅导员')
def counselor_approve_leave():
    """辅导员审批请假申请API"""
    try:
        # 获取请求数据
        data = request.json
        leave_id = data.get('leave_id')
        action = data.get('action')
        
        # 验证参数
        if not leave_id or action not in ['approve', 'reject']:
            return jsonify({
                "success": False,
                "message": "无效的请求参数"
            })
        
        # 获取辅导员信息
        counselor_id = session['user_info']['user_account']
        counselor_name = session['user_info']['user_name']
        responsible_grade = session['user_info'].get('responsible_grade', '')
        
        # 创建CounselorOperation实例并调用审批方法
        counselor = CounselorOperation(counselor_id, counselor_name, responsible_grade)
        result = counselor.approve_leave_api(leave_id, action)
        counselor._close_db()  # 确保关闭数据库连接
        
        return jsonify(result)
        
    except Exception as e:
        print(f"审批API异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"系统错误: {str(e)}"
        })

# 教师请假审批API
@app.route('/api/teacher/approve_leave', methods=['POST'])
@login_required(role='讲师')
def teacher_approve_leave():
    """教师审批请假申请API"""
    try:
        # 获取请求数据
        data = request.json
        leave_id = data.get('leave_id')
        action = data.get('action')
        
        # 验证参数
        if not leave_id or action not in ['approve', 'reject']:
            return jsonify({
                "success": False,
                "message": "无效的请求参数"
            })
        
        # 获取教师信息
        teacher_id = session['user_info']['user_account']
        teacher_name = session['user_info']['user_name']
        
        # 数据库操作：审批请假
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 校验请假记录
        sql_check = """
            SELECT sl.leave_id, sl.approval_status 
            FROM student_leave sl
            WHERE sl.leave_id = %s
            AND (sl.course_code IN (SELECT course_id FROM teacher_courses WHERE teacher_id = %s) 
                 OR sl.approver_id = %s)
        """
        cursor.execute(sql_check, (leave_id, teacher_id, teacher_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"success": False, "message": "未找到您负责的请假记录"})
        
        if result[1] != "待审批":
            conn.close()
            return jsonify({"success": False, "message": f"该请假记录状态为「{result[1]}」，无需重复审批"})
        
        # 2. 确定审批结果
        new_status = "已批准" if action == "approve" else "已驳回"
        approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 3. 获取学生ID（用于更新times字段）
        sql_get_student_id = """
            SELECT student_id FROM student_leave WHERE leave_id = %s
        """
        cursor.execute(sql_get_student_id, (leave_id,))
        student_id_result = cursor.fetchone()
        student_id = student_id_result[0] if student_id_result else None
        
        # 4. 事务处理：更新请假记录 + （仅同意时）更新学生times
        conn.begin()
        
        # 4.1 更新请假记录
        sql_update = """
            UPDATE student_leave
            SET approval_status = %s, 
                approver_id = %s, 
                approver_name = %s, 
                approval_time = %s
            WHERE leave_id = %s
        """
        cursor.execute(sql_update, (new_status, teacher_id, teacher_name, approval_time, leave_id))
        
        # 4.2 仅“同意”时，更新student_info的times字段
        if action == "approve" and student_id:
            sql_update_student = """
                UPDATE student_info
                SET times = times + 1, update_time = %s
                WHERE student_id = %s
            """
            cursor.execute(sql_update_student, (approval_time, student_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"审批成功！请假ID{leave_id}状态更新为「{new_status}」"
        })
        
    except pymysql.MySQLError as e:
        print(f"数据库错误: {str(e)}")
        return jsonify({"success": False, "message": f"数据库错误: {str(e)}"})
    except Exception as e:
        print(f"审批API异常: {str(e)}")
        return jsonify({"success": False, "message": f"系统错误: {str(e)}"})



# 启动应用
if __name__ == '__main__':
    try:
        # 运行应用程序 - 禁用自动重载以避免watchdog问题
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()