import os
import io
import re
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory, Response
from functools import wraps
import pymysql
from collections import Counter
from db_config import get_db_config  # 确保存在数据库配置文件
from terminal.counselor_operation import CounselorOperation

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_123456'  # 生产环境需更换为随机安全密钥
app.config['UPLOAD_FOLDER'] = 'data/signatures'  # 签字图片保存目录
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'  # 根据环境变量设置调试模式

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
            # 同步头像到 session
            sync_user_avatar()
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sync_user_avatar():
    """从数据库同步用户头像到 session"""
    if 'user_info' not in session:
        return
    
    role = session['user_info'].get('role_name')
    user_account = session['user_info'].get('user_account')
    
    table_map = {
        "管理员": ("admin_info", "admin_id"),
        "辅导员": ("counselor_info", "counselor_id"),
        "讲师": ("teacher_info", "teacher_id"),
        "学生": ("student_info", "student_id")
    }
    
    if role not in table_map:
        return
    
    table_name, id_field = table_map[role]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT avatar FROM {table_name} WHERE {id_field} = %s", (user_account,))
        row = cursor.fetchone()
        if row and row[0]:
            session['user_info']['avatar'] = row[0]
        cursor.close()
        conn.close()
    except Exception:
        pass  # 同步失败不影响正常功能

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
    return render_template('admin/index.html', user_info=session['user_info'])

@app.route('/admin/students')
@login_required(role='管理员')
def student_list_page():
    """学生信息列表页面（仅管理员可访问）"""
    return render_template('student/list.html', user_info=session['user_info'])

@app.route('/admin/teachers')
@login_required(role='管理员')
def teacher_list_page():
    """教师信息列表页面（仅管理员可访问）"""
    return render_template('teacher/list.html', user_info=session['user_info'])

@app.route('/admin/counselors')
@login_required(role='管理员')
def counselor_list_page():
    """辅导员信息列表页面（仅管理员可访问）"""
    return render_template('counselor/list.html', user_info=session['user_info'])

@app.route('/admin/admins')
@login_required(role='管理员')
def admin_list_page():
    """管理员信息列表页面（仅管理员可访问）"""
    return render_template('admin/list.html', user_info=session['user_info'])

@app.route('/student')
@login_required(role='学生')
def student_page():
    """学生页面"""
    return render_template('student/index.html', user_info=session['user_info'])

@app.route('/teacher')
@login_required(role='讲师')
def teacher_page():
    """讲师页面"""
    return render_template('teacher/index.html', user_info=session['user_info'])

@app.route('/counselor')
@login_required(role='辅导员')
def counselor_page():
    """辅导员页面（重定向到默认的全部假条页面）"""
    signature = request.args.get('signature', '')
    # 重定向到全部假条页面，并传递signature参数
    if signature:
        return redirect(url_for('counselor_all_leaves', signature=signature))
    return redirect(url_for('counselor_all_leaves'))

@app.route('/counselor/chat')
@login_required(role='辅导员')
def counselor_chat():
    """辅导员消息页面"""
    return render_template('counselor/chat.html', user_info=session['user_info'])

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

@app.route('/counselor/statistics')
@login_required(role='辅导员')
def counselor_statistics():
    """数据统计页面"""
    return render_template(
        'counselor/statistics.html',
        user_info=session['user_info'],
        title='数据统计'
    )

@app.route('/counselor/profile')
@login_required(role='辅导员')
def counselor_profile():
    """辅导员个人资料页面"""
    counselor = {}
    db_avatar = None
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT counselor_id, counselor_name, dept,
                   responsible_grade, responsible_major, contact, avatar
            FROM counselor_info
            WHERE counselor_id = %s
        """
        counselor_id = session['user_info']['user_account']
        cursor.execute(sql, (counselor_id,))
        row = cursor.fetchone()
        if row:
            counselor = {
                "counselor_id": row[0],
                "counselor_name": row[1],
                "dept": row[2],
                "responsible_grade": row[3],
                "responsible_major": row[4],
                "contact": row[5],
            }
            db_avatar = row[6]  # 从数据库读取头像
    except pymysql.MySQLError as e:
        print(f"查询辅导员信息失败: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.open:
                conn.close()
        except Exception:
            pass

    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    avatars = []
    try:
        for name in os.listdir(image_folder):
            lower = name.lower()
            if lower.endswith('.png') or lower.endswith('.jpg') or lower.endswith('.jpeg') or lower.endswith('.gif'):
                avatars.append(name)
    except FileNotFoundError:
        avatars = []

    # 优先使用数据库中的头像，其次使用 session，最后使用默认值
    current_avatar = db_avatar or session.get('user_info', {}).get('avatar')
    if not current_avatar:
        if 'boy.png' in avatars:
            current_avatar = 'boy.png'
        elif avatars:
            current_avatar = avatars[0]
        else:
            current_avatar = ''

    # 同步到 session
    if 'user_info' in session and current_avatar:
        session['user_info']['avatar'] = current_avatar

    return render_template(
        'counselor/profile.html',
        user_info=session['user_info'],
        title='个人资料',
        counselor=counselor,
        avatar=current_avatar,
        avatars=avatars
    )

@app.route('/qianzi')
@login_required(role='辅导员')
def qianzi_page():
    """签字页面（仅辅导员可访问）"""
    return render_template('counselor/qianzi.html')

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
        
        # 构建查询SQL（所有角色都查询 avatar 字段）
        if target["role_name"] == "辅导员":
            sql = f"""
                SELECT {target['account_field']}, {target['pwd_field']}, {target['name_field']}, {target['extra_field']}, avatar
                FROM {target['table']}
                WHERE {target['account_field']} = %s
            """
        else:
            sql = f"""
                SELECT {target['account_field']}, {target['pwd_field']}, {target['name_field']}, avatar
                FROM {target['table']}
                WHERE {target['account_field']} = %s
            """
            
        cursor.execute(sql, (account,))
        user = cursor.fetchone()
        print(f"[DEBUG] 登录查询结果: {user}")  # 调试打印
        
        if not user:
            return jsonify({"status": "error", "message": f"{target['role_name']}账号不存在"})
        
        # 解析查询结果
        if target["role_name"] == "辅导员":
            db_account, db_password, db_name, db_responsible_grade, db_avatar = user
        else:
            db_account, db_password, db_name, db_avatar = user
            
        if password != db_password:
            return jsonify({"status": "error", "message": "密码错误"})
        
        # 登录成功，保存用户信息到session
        print(f"[DEBUG] db_name = {db_name}")  # 调试
        session['user_info'] = {
            "user_account": db_account,
            "user_name": db_name,
            "role_name": target['role_name'],
            "avatar": db_avatar or 'boy.png'  # 默认头像
        }
        print(f"[DEBUG] session存储: {session['user_info']}")  # 调试
        
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

@app.route('/api/user_preview', methods=['POST'])
def user_preview():
    """获取用户预览信息（用于登录界面显示）"""
    data = request.json
    account = data.get('account', '').strip()
    
    if not account:
        return jsonify({"success": False, "message": "账号不能为空"})
    
    account_len = len(account)
    
    # 角色映射表
    role_map = {
        4: {
            "table": "admin_info",
            "account_field": "admin_id",
            "name_field": "admin_name",
            "role_name": "管理员",
            "dept_field": "'系统管理部'"
        },
        8: {
            "table": "counselor_info",
            "account_field": "counselor_id",
            "name_field": "counselor_name",
            "role_name": "辅导员",
            "dept_field": "dept"
        },
        9: {
            "table": "teacher_info",
            "account_field": "teacher_id",
            "name_field": "teacher_name",
            "role_name": "讲师",
            "dept_field": "dept"
        },
        12: {
            "table": "student_info",
            "account_field": "student_id",
            "name_field": "student_name",
            "role_name": "学生",
            "dept_field": "major"
        }
    }
    
    if account_len not in role_map:
        return jsonify({"success": False, "message": "账号长度不符合规则"})
    
    target = role_map[account_len]
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询SQL
        sql = f"""
            SELECT {target['account_field']} as id, {target['name_field']} as name, 
                   {target['dept_field']} as dept, avatar
            FROM {target['table']}
            WHERE {target['account_field']} = %s
        """
        
        cursor.execute(sql, (account,))
        user = cursor.fetchone()
        
        if user:
            avatar_url = None
            if user[3]:  # avatar字段
                # 检查头像文件位置
                avatar_file = user[3]
                if avatar_file.startswith('teacher_'):
                    avatar_url = f"/static/avatars/{avatar_file}"
                else:
                    avatar_url = f"/head_image/{avatar_file}"
            
            return jsonify({
                "success": True,
                "data": {
                    "id": user[0],
                    "name": user[1],
                    "dept": user[2] or "未知部门",
                    "role": target["role_name"],
                    "avatar": avatar_url
                }
            })
        else:
            return jsonify({"success": False, "message": "用户不存在"})
            
    except Exception as e:
        print(f"用户预览查询失败: {e}")
        return jsonify({"success": False, "message": "查询失败"})
    finally:
        if conn:
            conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    """退出登录接口"""
    session.pop('user_info', None)
    return jsonify({"status": "success", "message": "已成功登出"})

# 消息相关API
@app.route('/api/chat/contacts', methods=['GET'])
@login_required(role='辅导员')
def get_chat_contacts():
    """获取辅导员的学生联系人列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取当前辅导员负责的年级
        counselor_id = session['user_info']['user_account']
        cursor.execute("SELECT responsible_grade FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
        counselor = cursor.fetchone()
        
        if not counselor or not counselor['responsible_grade']:
            conn.close()
            return jsonify({"success": True, "data": []})
        
        responsible_grade = str(counselor['responsible_grade']).strip()
        
        # 获取该年级的学生列表
        sql = """
            SELECT student_id, student_name, avatar
            FROM student_info 
            WHERE LEFT(student_id, 4) = %s
            ORDER BY student_id
        """
        
        cursor.execute(sql, (responsible_grade,))
        students = cursor.fetchall()
        
        # 转换为前端需要的格式
        contacts = []
        for student in students:
            contacts.append({
                "id": student['student_id'],
                "name": student['student_name'],
                "avatar": student['avatar'] or 'boy.png',
                "unread": 0,  # 暂时设为0，后续可以添加未读消息统计
                "last_message": "点击开始聊天",
                "last_time": ""
            })
        
        conn.close()
        return jsonify({"success": True, "data": contacts})
        
    except Exception as e:
        print(f"获取联系人列表失败: {e}")
        return jsonify({"success": False, "message": "获取联系人列表失败"})

@app.route('/api/chat/unread_count', methods=['GET'])
@login_required(role='辅导员')
def get_chat_unread_count():
    """获取辅导员未读消息总数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        # 统计所有学生发给辅导员的未读消息
        cursor.execute("""
            SELECT COUNT(*) as unread_count 
            FROM chat_messages 
            WHERE receiver_id = %s AND sender_role = '学生' AND is_read = 0
        """, (counselor_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({"success": True, "data": result['unread_count'] if result else 0})
        
    except Exception as e:
        print(f"获取未读消息数失败: {e}")
        return jsonify({"success": False, "message": "获取未读消息数失败"})

@app.route('/api/chat/messages', methods=['GET'])
@login_required(role='辅导员')
def get_chat_messages():
    """获取聊天消息记录"""
    try:
        contact_id = request.args.get('contact_id')
        if not contact_id:
            return jsonify({"success": False, "message": "缺少联系人ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        # 获取辅导员和学生头像
        cursor.execute("SELECT avatar FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
        counselor_avatar_row = cursor.fetchone()
        counselor_avatar = counselor_avatar_row['avatar'] if counselor_avatar_row and counselor_avatar_row['avatar'] else 'boy.png'
        
        cursor.execute("SELECT avatar FROM student_info WHERE student_id = %s", (contact_id,))
        student_avatar_row = cursor.fetchone()
        student_avatar = student_avatar_row['avatar'] if student_avatar_row and student_avatar_row['avatar'] else 'boy.png'
        
        # 获取聊天记录
        cursor.execute("""
            SELECT message_id, sender_id, sender_name, sender_role, content, 
                   DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%s') as create_time,
                   CASE WHEN sender_id = %s THEN 1 ELSE 0 END as is_self
            FROM chat_messages 
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY create_time ASC
        """, (counselor_id, counselor_id, contact_id, contact_id, counselor_id))
        
        messages = cursor.fetchall()
        
        # 为每条消息添加头像
        for msg in messages:
            if msg['is_self']:
                msg['avatar'] = counselor_avatar
            else:
                msg['avatar'] = student_avatar
        
        # 标记消息为已读
        cursor.execute("""
            UPDATE chat_messages SET is_read = 1 
            WHERE sender_id = %s AND receiver_id = %s AND is_read = 0
        """, (contact_id, counselor_id))
        conn.commit()
        
        conn.close()
        
        return jsonify({"success": True, "data": messages})
        
    except Exception as e:
        print(f"获取消息失败: {e}")
        return jsonify({"success": False, "message": "获取消息失败"})

@app.route('/api/chat/send', methods=['POST'])
@login_required(role='辅导员')
def send_chat_message():
    """辅导员发送消息给学生"""
    try:
        data = request.json
        content = data.get('content', '').strip()
        receiver_id = data.get('receiver_id', '').strip()
        
        if not content:
            return jsonify({"success": False, "message": "消息内容不能为空"})
        if not receiver_id:
            return jsonify({"success": False, "message": "缺少接收者ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        # 获取辅导员和学生姓名
        cursor.execute("SELECT counselor_name FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
        counselor_row = cursor.fetchone()
        counselor_name = counselor_row['counselor_name'] if counselor_row else '辅导员'
        
        cursor.execute("SELECT student_name FROM student_info WHERE student_id = %s", (receiver_id,))
        student_row = cursor.fetchone()
        student_name = student_row['student_name'] if student_row else '学生'
        
        # 插入消息记录
        cursor.execute("""
            INSERT INTO chat_messages (sender_id, sender_name, sender_role, receiver_id, receiver_name, receiver_role, content, create_time)
            VALUES (%s, %s, '辅导员', %s, %s, '学生', %s, NOW())
        """, (counselor_id, counselor_name, receiver_id, student_name, content))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "发送成功"})
        
    except Exception as e:
        print(f"发送消息失败: {e}")
        return jsonify({"success": False, "message": f"发送失败: {str(e)}"})

@app.route('/api/save_signature', methods=['POST'])
@login_required(role='辅导员')
def save_signature():
    """保存辅导员签字图片接口，命名规则：counselor_id_leave_id.png"""
    try:
        data = request.json
        image_data = data.get('imageData', '').replace('data:image/png;base64,', '')
        leave_id = data.get('leave_id', '')
        
        if not image_data:
            return jsonify({"success": False, "message": "未获取到签字数据"})
        
        if not leave_id:
            return jsonify({"success": False, "message": "缺少假条ID"})
        
        # 获取辅导员ID
        counselor_id = session['user_info']['user_account']
        
        # 使用新命名规则：counselor_id_leave_id.png
        file_name = f"{counselor_id}_{leave_id}.png"
        
        # 保存到qianzi文件夹
        signature_folder = os.path.join(app.root_path, 'data', 'signatures')
        if not os.path.exists(signature_folder):
            os.makedirs(signature_folder)
        
        file_path = os.path.join(signature_folder, file_name)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return jsonify({
            "success": True,
            "message": "签字保存成功",
            "imagePath": file_name
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 管理员专用接口 - 获取所有用户
@app.route('/api/admin/users', methods=['GET'])
@login_required(role='管理员')
def get_all_users():
    """获取所有用户（仅管理员）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT 4 as role_type, admin_id as user_account, admin_name as user_name, NULL as dept, NULL as grade, NULL as major, NULL as class_num, NULL as contact FROM admin_info
            UNION ALL
            SELECT 2 as role_type, counselor_id as user_account, counselor_name as user_name, dept, NULL as grade, NULL as major, NULL as class_num, contact FROM counselor_info
            UNION ALL
            SELECT 3 as role_type, teacher_id as user_account, teacher_name as user_name, dept, NULL as grade, NULL as major, NULL as class_num, contact FROM teacher_info
            UNION ALL
            SELECT 1 as role_type, student_id as user_account, student_name as user_name, dept, grade, major, class_num, contact FROM student_info
        """)
        users = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": users})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})

# 管理员专用接口 - 新增用户
@app.route('/api/admin/users', methods=['POST'])
@login_required(role='管理员')
def add_user():
    """新增用户（仅管理员）"""
    try:
        data = request.json
        account = data.get('account', '').strip()
        user_name = data.get('user_name', '').strip()
        password = data.get('password', '').strip()
        role_type = data.get('role_type')  # 1=学生，2=辅导员，3=教师，4=管理员
        
        if not account or not user_name or not password or not role_type:
            return jsonify({"success": False, "message": "所有字段都是必填的"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 根据角色类型插入到对应的表
        if role_type == 1:  # 学生
            if len(account) != 12:
                return jsonify({"success": False, "message": "学生账号必须是12位"})
            
            dept = data.get('dept', 'SC')
            grade = data.get('grade', '2024级')
            major = data.get('major', '计算机科学与技术')
            class_num = data.get('class_num', '01')
            contact = data.get('contact', '')
            
            major_code_map = {
                '计算机科学与技术': '01', '软件工程': '02', '网络工程': '03',
                '信息安全': '04', '数据科学与大数据技术': '05', '人工智能': '06',
                '物联网工程': '07', '电子信息工程': '08', '通信工程': '09', '自动化': '10'
            }
            major_code = major_code_map.get(major, '01')
            
            cursor.execute("""
                INSERT INTO student_info (student_id, student_name, password, dept, dept_id, grade, major, major_code, class_num, contact)
                VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s, %s)
            """, (account, user_name, password, dept, grade, major, major_code, class_num, contact))
        elif role_type == 2:  # 辅导员
            if len(account) != 8:
                return jsonify({"success": False, "message": "辅导员账号必须是8位"})
            
            dept = data.get('dept', '')
            responsible_grade = data.get('responsible_grade', '')
            responsible_major = data.get('responsible_major', '')
            contact = data.get('contact', '')
            
            cursor.execute("""
                INSERT INTO counselor_info (counselor_id, counselor_name, password, dept, responsible_grade, responsible_major, contact)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (account, user_name, password, dept, responsible_grade, responsible_major, contact))
        elif role_type == 3:  # 教师
            if len(account) != 9:
                return jsonify({"success": False, "message": "教师账号必须是9位"})
            
            dept = data.get('dept', '')
            contact = data.get('contact', '')
            
            cursor.execute("""
                INSERT INTO teacher_info (teacher_id, teacher_name, password, dept, contact)
                VALUES (%s, %s, %s, %s, %s)
            """, (account, user_name, password, dept, contact))
        elif role_type == 4:  # 管理员
            if len(account) != 4:
                return jsonify({"success": False, "message": "管理员账号必须是4位"})
            
            dept = data.get('dept', '')
            
            cursor.execute("""
                INSERT INTO admin_info (admin_id, admin_name, password, dept)
                VALUES (%s, %s, %s, %s)
            """, (account, user_name, password, dept))
        else:
            return jsonify({"success": False, "message": "无效的角色类型"})
        
        conn.commit()
        conn.close()
        
        role_map = {1: 'student', 2: 'counselor', 3: 'teacher', 4: 'admin'}
        role_name_map = {1: '学生', 2: '辅导员', 3: '教师', 4: '管理员'}
        details = f"新增{role_name_map.get(role_type, '用户')}：{user_name}"
        log_admin_operation(operation_type='ADD', target_account=account, target_name=user_name,
                           target_role=role_map.get(role_type, 'unknown'), details=details, status='SUCCESS')
        
        return jsonify({"success": True, "message": "用户添加成功"})
        
    except pymysql.IntegrityError:
        role_map = {1: 'student', 2: 'counselor', 3: 'teacher', 4: 'admin'}
        log_admin_operation(operation_type='ADD', target_account=account, target_name=user_name,
                           target_role=role_map.get(role_type, 'unknown'), details=f"尝试新增用户：{user_name}",
                           status='FAILED', error_msg='该账号已存在')
        return jsonify({"success": False, "message": "该账号已存在"})
    except Exception as e:
        return jsonify({"success": False, "message": f"添加失败：{str(e)}"})

# 管理员专用接口 - 修改用户
@app.route('/api/admin/users/<account>', methods=['PUT'])
@login_required(role='管理员')
def update_user(account):
    """修改用户信息（仅管理员）"""
    try:
        if len(account) == 4:
            return jsonify({"success": False, "message": "🛡️ 系统保护：管理员账户不可编辑！"})
        
        data = request.json
        new_name = (data.get('new_name') or '').strip()
        new_password = (data.get('new_password') or '').strip()
        new_contact = (data.get('new_contact') or '').strip()
        new_role = data.get('new_role')
        new_dept = (data.get('new_dept') or '').strip()
        new_grade = (data.get('new_grade') or '').strip()
        new_major = (data.get('new_major') or '').strip()
        new_class_num = (data.get('new_class_num') or '').strip()
        
        if not new_name and not new_password and not new_contact and not new_role and not new_dept and not new_grade and not new_major and not new_class_num:
            return jsonify({"success": False, "message": "至少需要提供一个要修改的字段"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = [
            ('student_info', 'student_id', 'student_name', 1),
            ('counselor_info', 'counselor_id', 'counselor_name', 2),
            ('teacher_info', 'teacher_id', 'teacher_name', 3),
            ('admin_info', 'admin_id', 'admin_name', 4)
        ]
        
        user_found = False
        current_role = None
        
        for table, id_col, name_col, role in tables:
            cursor.execute(f"SELECT {id_col} FROM {table} WHERE {id_col} = %s", (account,))
            if cursor.fetchone():
                user_found = True
                current_role = role
                
                if new_role and new_role != current_role:
                    cursor.execute(f"SELECT {name_col}, password FROM {table} WHERE {id_col} = %s", (account,))
                    user_info = cursor.fetchone()
                    old_name = user_info[0]
                    old_password = user_info[1]
                    cursor.execute(f"DELETE FROM {table} WHERE {id_col} = %s", (account,))
                    
                    new_table_info = tables[new_role - 1]
                    new_table = new_table_info[0]
                    new_id_col = new_table_info[1]
                    new_name_col = new_table_info[2]
                    
                    final_name = new_name if new_name else old_name
                    final_password = new_password if new_password else old_password
                    
                    cursor.execute(f"""
                        INSERT INTO {new_table} ({new_id_col}, {new_name_col}, password)
                        VALUES (%s, %s, %s)
                    """, (account, final_name, final_password))
                else:
                    updates = []
                    params = []
                    
                    if new_name:
                        updates.append(f"{name_col} = %s")
                        params.append(new_name)
                    if new_password:
                        updates.append("password = %s")
                        params.append(new_password)
                    if new_contact and table != 'admin_info':
                        updates.append("contact = %s")
                        params.append(new_contact)
                    
                    if table == 'student_info':
                        if new_dept:
                            updates.append("dept = %s")
                            params.append(new_dept)
                        if new_grade:
                            updates.append("grade = %s")
                            params.append(new_grade)
                        if new_major:
                            updates.append("major = %s")
                            params.append(new_major)
                            major_code_map = {
                                '计算机科学与技术': '01', '软件工程': '02', '网络工程': '03',
                                '信息安全': '04', '数据科学与大数据技术': '05', '人工智能': '06',
                                '物联网工程': '07', '电子信息工程': '08', '通信工程': '09', '自动化': '10'
                            }
                            updates.append("major_code = %s")
                            params.append(major_code_map.get(new_major, '01'))
                        if new_class_num:
                            updates.append("class_num = %s")
                            params.append(new_class_num)
                    
                    if table == 'teacher_info':
                        if new_dept:
                            updates.append("dept = %s")
                            params.append(new_dept)
                    
                    if table == 'counselor_info':
                        if new_dept:
                            updates.append("dept = %s")
                            params.append(new_dept)
                        if new_grade:
                            updates.append("responsible_grade = %s")
                            params.append(new_grade)
                        if new_major:
                            updates.append("responsible_major = %s")
                            params.append(new_major)
                    
                    if updates:
                        params.append(account)
                        cursor.execute(f"UPDATE {table} SET {', '.join(updates)} WHERE {id_col} = %s", params)
                
                break
        
        if not user_found:
            conn.close()
            log_admin_operation(operation_type='UPDATE', target_account=account, target_name='unknown',
                               target_role='unknown', details=f"尝试修改用户：{account}", status='FAILED', error_msg='用户不存在')
            return jsonify({"success": False, "message": "用户不存在"})
        
        conn.commit()
        conn.close()
        
        role_map = {1: 'student', 2: 'counselor', 3: 'teacher', 4: 'admin'}
        role_name_map = {1: '学生', 2: '辅导员', 3: '教师', 4: '管理员'}
        update_details = []
        if new_name: update_details.append(f"姓名→{new_name}")
        if new_password: update_details.append("密码已更新")
        if new_contact: update_details.append(f"联系方式→{new_contact}")
        if new_dept: update_details.append(f"部门→{new_dept}")
        if new_grade: update_details.append(f"年级→{new_grade}")
        if new_major: update_details.append(f"专业→{new_major}")
        if new_class_num: update_details.append(f"班级→{new_class_num}")
        if new_role: update_details.append(f"角色变更→{role_name_map.get(new_role, '未知')}")
        
        details = f"修改{role_name_map.get(current_role, '用户')}信息：" + "，".join(update_details)
        log_admin_operation(operation_type='UPDATE', target_account=account, target_name=new_name if new_name else 'unknown',
                           target_role=role_map.get(current_role, 'unknown'), details=details, status='SUCCESS')
        
        return jsonify({"success": True, "message": "用户信息修改成功"})
        
    except Exception as e:
        log_admin_operation(operation_type='UPDATE', target_account=account if 'account' in locals() else 'unknown',
                           target_name='unknown', target_role='unknown', details=f"尝试修改用户失败",
                           status='FAILED', error_msg=str(e))
        return jsonify({"success": False, "message": f"修改失败：{str(e)}"})

# 管理员专用接口 - 删除用户
@app.route('/api/admin/users/<account>', methods=['DELETE'])
@login_required(role='管理员')
def delete_user(account):
    """删除用户（仅管理员）"""
    try:
        if len(account) == 4:
            log_admin_operation(operation_type='DELETE', target_account=account, target_name='unknown',
                               target_role='admin', details=f"尝试删除管理员账户：{account}",
                               status='FAILED', error_msg='管理员账户受系统保护，不可删除')
            return jsonify({"success": False, "message": "⚠️ 系统保护：管理员账户不可删除！❌"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        tables = [
            ('student_info', 'student_id', 'student_name', 1, 'student'),
            ('counselor_info', 'counselor_id', 'counselor_name', 2, 'counselor'),
            ('teacher_info', 'teacher_id', 'teacher_name', 3, 'teacher'),
            ('admin_info', 'admin_id', 'admin_name', 4, 'admin')
        ]
        
        deleted = False
        deleted_user_name = 'unknown'
        deleted_user_role = 'unknown'
        role_name_map = {1: '学生', 2: '辅导员', 3: '教师', 4: '管理员'}
        
        for table, id_col, name_col, role_type, role_str in tables:
            cursor.execute(f"SELECT {name_col} FROM {table} WHERE {id_col} = %s", (account,))
            user_info = cursor.fetchone()
            
            if user_info:
                deleted_user_name = user_info[name_col]
                deleted_user_role = role_str
                
                cursor.execute(f"DELETE FROM {table} WHERE {id_col} = %s", (account,))
                if cursor.rowcount > 0:
                    deleted = True
                    log_admin_operation(operation_type='DELETE', target_account=account, target_name=deleted_user_name,
                                       target_role=deleted_user_role, details=f"删除{role_name_map.get(role_type, '用户')}：{deleted_user_name}（账号：{account}）",
                                       status='SUCCESS')
                    break
        
        if not deleted:
            conn.close()
            log_admin_operation(operation_type='DELETE', target_account=account, target_name='unknown',
                               target_role='unknown', details=f"尝试删除用户：{account}", status='FAILED', error_msg='用户不存在')
            return jsonify({"success": False, "message": "用户不存在"})
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "用户删除成功"})
        
    except Exception as e:
        log_admin_operation(operation_type='DELETE', target_account=account if 'account' in locals() else 'unknown',
                           target_name='unknown', target_role='unknown', details=f"尝试删除用户失败",
                           status='FAILED', error_msg=str(e))
        return jsonify({"success": False, "message": f"删除失败：{str(e)}"})

# 教师获取请假记录接口
@app.route('/api/teacher/leave_requests', methods=['GET'])
@login_required(role='讲师')
def get_teacher_leave_requests():
    """获取教师相关的请假记录（基于teacher_id字段）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        # 查询teacher_id为当前教师的请假记录
        cursor.execute("""
            SELECT 
                sl.leave_id,
                sl.student_id,
                sl.student_name,
                sl.dept,
                sl.course_id,
                sl.start_time,
                sl.end_time,
                sl.leave_reason,
                sl.approval_status,
                sl.approver_id,
                sl.approver_name,
                sl.approval_time,
                sl.sort,
                sl.attachment,
                sl.times
            FROM student_leave sl
            WHERE sl.teacher_id = %s
            ORDER BY sl.start_time DESC
        """, (teacher_id,))
        leave_requests = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": leave_requests})
        
    except Exception as e:
        print(f"教师获取请假记录失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取请假记录失败: {str(e)}"})

# 教师发送通知API
@app.route('/api/teacher/send_notification', methods=['POST'])
@login_required(role='讲师')
def teacher_send_notification():
    """教师发送通知给学生"""
    try:
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        notify_type = data.get('notify_type', '课程通知')
        priority = data.get('priority', '普通')
        course_id = data.get('course_id', '')
        
        if not title or not content:
            return jsonify({"success": False, "message": "标题和内容不能为空"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        teacher_name = session['user_info']['user_name']
        
        # 插入通知记录（使用实际存在的字段）
        cursor.execute("""
            INSERT INTO teacher_notifications (teacher_id, dept, course_id, reason, start_time, end_time, priority)
            VALUES (%s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 1 DAY), %s)
        """, (teacher_id, 'CS', course_id, title, priority))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "通知发送成功"})
        
    except Exception as e:
        print(f"发送通知失败: {str(e)}")
        # 如果表不存在，创建表
        if "doesn't exist" in str(e):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS teacher_notifications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        teacher_id VARCHAR(50) NOT NULL,
                        teacher_name VARCHAR(100),
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        notify_type VARCHAR(50) DEFAULT '课程通知',
                        priority VARCHAR(20) DEFAULT '普通',
                        course_id VARCHAR(50),
                        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
                return jsonify({"success": False, "message": "通知表已创建，请重新发送"})
            except:
                pass
        return jsonify({"success": False, "message": f"发送通知失败: {str(e)}"})

# 教师获取已发送的通知
@app.route('/api/teacher/notifications', methods=['GET'])
@login_required(role='讲师')
def get_teacher_notifications():
    """获取教师已发送的通知列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        cursor.execute("""
            SELECT leave_id as id, reason as title, reason as content, '课程通知' as notify_type, priority, course_id,
                   DATE_FORMAT(start_time, '%%Y-%%m-%%d %%H:%%i') as create_time
            FROM teacher_notifications
            WHERE teacher_id = %s
            ORDER BY start_time DESC
        """, (teacher_id,))
        notifications = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": notifications})
        
    except Exception as e:
        print(f"获取通知失败: {str(e)}")
        # 如果表不存在，返回空数组
        if "doesn't exist" in str(e):
            return jsonify({"success": True, "data": []})
        return jsonify({"success": False, "message": f"获取通知失败: {str(e)}"})

# 教师删除通知API
@app.route('/api/teacher/delete_notification', methods=['POST'])
@login_required(role='讲师')
def delete_teacher_notification():
    """删除教师通知"""
    try:
        data = request.json
        notification_id = data.get('id')
        
        if not notification_id:
            return jsonify({"success": False, "message": "缺少通知ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        teacher_id = session['user_info']['user_account']
        
        # 只能删除自己的通知
        cursor.execute("""
            DELETE FROM teacher_notifications 
            WHERE leave_id = %s AND teacher_id = %s
        """, (notification_id, teacher_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "删除成功"})
        
    except Exception as e:
        print(f"删除通知失败: {str(e)}")
        return jsonify({"success": False, "message": f"删除失败: {str(e)}"})

# 学生获取通知API
@app.route('/api/student/notifications', methods=['GET'])
@login_required(role='学生')
def get_student_notifications():
    """学生获取相关通知"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        
        # 获取筛选参数
        course_filter = request.args.get('course_id', '')
        teacher_filter = request.args.get('teacher_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # 基础查询：获取学生选课相关的通知
        sql = """
            SELECT DISTINCT 
                tn.leave_id as id,
                tn.reason as title, 
                tn.reason as content, 
                '课程通知' as notify_type, 
                tn.priority,
                tn.course_id, 
                tn.teacher_id, 
                ti.teacher_name,
                DATE_FORMAT(tn.start_time, '%%Y-%%m-%%d %%H:%%i') as create_time,
                ci.course_name,
                tn.start_time
            FROM teacher_notifications tn
            JOIN student_course_selection scs ON tn.course_id = scs.course_id
            LEFT JOIN course_info ci ON tn.course_id = ci.course_id
            LEFT JOIN teacher_info ti ON tn.teacher_id = ti.teacher_id
            WHERE scs.student_id = %s
        """
        params = [student_id]
        
        # 添加筛选条件
        if course_filter:
            sql += " AND tn.course_id = %s"
            params.append(course_filter)
        
        if teacher_filter:
            sql += " AND tn.teacher_id = %s"
            params.append(teacher_filter)
        
        if start_date:
            sql += " AND DATE(tn.start_time) >= %s"
            params.append(start_date)
        
        if end_date:
            sql += " AND DATE(tn.start_time) <= %s"
            params.append(end_date)
        
        sql += " ORDER BY tn.start_time DESC"
        
        cursor.execute(sql, params)
        notifications = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": notifications})
        
    except Exception as e:
        print(f"获取学生通知失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取通知失败: {str(e)}"})

# 学生获取课程和教师列表（用于筛选）
@app.route('/api/student/filter_options', methods=['GET'])
@login_required(role='学生')
def get_student_filter_options():
    """获取学生的课程和教师列表用于筛选"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        
        # 获取学生选课的课程列表
        cursor.execute("""
            SELECT DISTINCT ci.course_id, ci.course_name
            FROM student_course_selection scs
            JOIN course_info ci ON scs.course_id = ci.course_id
            WHERE scs.student_id = %s
            ORDER BY ci.course_name
        """, (student_id,))
        courses = cursor.fetchall()
        
        # 获取相关教师列表
        cursor.execute("""
            SELECT DISTINCT ti.teacher_id, ti.teacher_name
            FROM student_course_selection scs
            JOIN teacher_course tc ON scs.course_id = tc.course_id
            JOIN teacher_info ti ON tc.teacher_id = ti.teacher_id
            WHERE scs.student_id = %s
            ORDER BY ti.teacher_name
        """, (student_id,))
        teachers = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True, 
            "data": {
                "courses": courses,
                "teachers": teachers
            }
        })
        
    except Exception as e:
        print(f"获取筛选选项失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取筛选选项失败: {str(e)}"})

# 教师获取学生列表（用于聊天）
@app.route('/api/teacher/chat/students', methods=['GET'])
@login_required(role='讲师')
def get_teacher_chat_students():
    """获取该教师课程的所有选课学生"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        # 方式1：从teacher_course表获取教师课程，再查选课学生
        cursor.execute("""
            SELECT DISTINCT si.student_id as id, si.student_name as name, si.avatar
            FROM teacher_course tc
            JOIN student_course_selection scs ON tc.course_id = scs.course_id
            JOIN student_info si ON scs.student_id = si.student_id
            WHERE tc.teacher_id = %s
            ORDER BY si.student_id
        """, (teacher_id,))
        students = cursor.fetchall()
        
        if not students:
            # 方式2：从请假记录中获取该教师的课程，再查所有选课学生
            cursor.execute("""
                SELECT DISTINCT si.student_id as id, si.student_name as name, si.avatar
                FROM student_leave sl
                JOIN student_course_selection scs ON sl.course_id = scs.course_id
                JOIN student_info si ON scs.student_id = si.student_id
                WHERE sl.teacher_id = %s
                ORDER BY si.student_id
            """, (teacher_id,))
            students = cursor.fetchall()
        
        if not students:
            # 方式3：仅从请假记录获取（最终兜底）
            cursor.execute("""
                SELECT DISTINCT sl.student_id as id, sl.student_name as name, si.avatar
                FROM student_leave sl
                LEFT JOIN student_info si ON sl.student_id = si.student_id
                WHERE sl.teacher_id = %s
                ORDER BY sl.student_id
            """, (teacher_id,))
            students = cursor.fetchall()
        
        conn.close()
        
        return jsonify({"success": True, "data": students})
        
    except Exception as e:
        print(f"获取学生列表失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# 教师获取聊天记录
@app.route('/api/teacher/chat/messages', methods=['GET'])
@login_required(role='讲师')
def get_teacher_chat_messages():
    """获取与学生的聊天记录"""
    try:
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({"success": False, "message": "缺少学生ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        cursor.execute("""
            SELECT content, sender_role,
                   DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i') as create_time
            FROM chat_messages
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY create_time ASC
        """, (teacher_id, student_id, student_id, teacher_id))
        messages = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": messages})
        
    except Exception as e:
        print(f"获取聊天记录失败: {str(e)}")
        return jsonify({"success": True, "data": []})

# 教师发送消息
@app.route('/api/teacher/chat/send', methods=['POST'])
@login_required(role='讲师')
def teacher_send_chat_message():
    """教师发送消息给学生"""
    try:
        data = request.json
        student_id = data.get('student_id')
        message = data.get('message', '').strip()
        
        if not student_id or not message:
            return jsonify({"success": False, "message": "缺少必要参数"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        teacher_name = session['user_info']['user_name']
        
        # 获取学生姓名
        cursor.execute("SELECT student_name FROM student_info WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        student_name = student['student_name'] if student else '学生'
        
        cursor.execute("""
            INSERT INTO chat_messages (sender_id, sender_name, sender_role, receiver_id, receiver_name, receiver_role, content, create_time)
            VALUES (%s, %s, '讲师', %s, %s, '学生', %s, NOW())
        """, (teacher_id, teacher_name, student_id, student_name, message))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "发送成功"})
        
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# 教师获取个人信息
@app.route('/api/teacher/profile', methods=['GET'])
@login_required(role='讲师')
def get_teacher_profile():
    """获取教师个人信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        # 获取教师基本信息
        cursor.execute("""
            SELECT teacher_id, teacher_name, dept, contact, avatar
            FROM teacher_info
            WHERE teacher_id = %s
        """, (teacher_id,))
        teacher = cursor.fetchone()
        
        # 获取教师授课课程（优先从teacher_course表，备选从teacher_notifications表）
        cursor.execute("""
            SELECT GROUP_CONCAT(DISTINCT ci.course_name SEPARATOR ', ') as courses
            FROM teacher_course tc
            JOIN course_info ci ON tc.course_id = ci.course_id
            WHERE tc.teacher_id = %s
        """, (teacher_id,))
        course_result = cursor.fetchone()
        courses = course_result.get('courses', '') if course_result else ''
        
        # 如果teacher_course表没有数据，从teacher_notifications表获取
        if not courses:
            cursor.execute("""
                SELECT GROUP_CONCAT(DISTINCT ci.course_name SEPARATOR ', ') as courses
                FROM teacher_notifications tn
                JOIN course_info ci ON tn.course_id = ci.course_id
                WHERE tn.teacher_id = %s
            """, (teacher_id,))
            course_result = cursor.fetchone()
            courses = course_result.get('courses', '') if course_result else ''
        
        conn.close()
        
        if teacher:
            return jsonify({
                "success": True,
                "data": {
                    "dept": teacher.get('dept', ''),
                    "contact": teacher.get('contact', ''),
                    "courses": courses or '',
                    "avatar": teacher.get('avatar', '')
                }
            })
        return jsonify({"success": True, "data": {}})
        
    except Exception as e:
        print(f"获取教师信息失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# 教师更新联系方式
@app.route('/api/teacher/update_contact', methods=['POST'])
@login_required(role='讲师')
def update_teacher_contact():
    """更新教师联系方式"""
    try:
        data = request.json
        contact = data.get('contact', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        teacher_id = session['user_info']['user_account']
        
        cursor.execute("""
            UPDATE teacher_info SET contact = %s WHERE teacher_id = %s
        """, (contact, teacher_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "更新成功"})
        
    except Exception as e:
        print(f"更新联系方式失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# 教师上传头像
@app.route('/api/teacher/upload_avatar', methods=['POST'])
@login_required(role='讲师')
def upload_teacher_avatar():
    """上传教师头像"""
    try:
        if 'avatar' not in request.files:
            return jsonify({"success": False, "message": "没有上传文件"})
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"success": False, "message": "没有选择文件"})
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            return jsonify({"success": False, "message": "不支持的图片格式"})
        
        teacher_id = session['user_info']['user_account']
        
        # 生成文件名
        import uuid
        filename = f"teacher_{teacher_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # 确保目录存在
        avatar_dir = os.path.join(app.root_path, 'static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(avatar_dir, filename)
        file.save(filepath)
        
        # 更新数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE teacher_info SET avatar = %s WHERE teacher_id = %s", (filename, teacher_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "avatar": filename, "message": "头像更新成功"})
        
    except Exception as e:
        print(f"上传头像失败: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# 教师获取课程学生数
@app.route('/api/teacher/course_students', methods=['GET'])
@login_required(role='讲师')
def get_teacher_course_students():
    """获取教师各课程的选课学生人数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        teacher_id = session['user_info']['user_account']
        
        # 从teacher_course表获取教师课程，再统计选课学生数
        cursor.execute("""
            SELECT tc.course_id, COUNT(DISTINCT scs.student_id) as student_count
            FROM teacher_course tc
            LEFT JOIN student_course_selection scs ON tc.course_id = scs.course_id
            WHERE tc.teacher_id = %s
            GROUP BY tc.course_id
        """, (teacher_id,))
        results = cursor.fetchall()
        
        conn.close()
        
        # 转换为 {course_id: count} 格式
        course_counts = {r['course_id']: r['student_count'] for r in results}
        
        return jsonify({"success": True, "data": course_counts})
        
    except Exception as e:
        print(f"获取课程学生数失败: {str(e)}")
        return jsonify({"success": True, "data": {}})

# 获取辅导员待审批数量
@app.route('/api/counselor/leave_count', methods=['GET'])
@login_required(role='辅导员')
def get_counselor_leave_count():
    """获取辅导员待审批/已批准/已驳回的请假数量"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        responsible_grade = session['user_info'].get('responsible_grade', '')
        responsible_grade = str(responsible_grade).strip() if responsible_grade else ''
        
        sql = """
            SELECT 
                SUM(CASE WHEN approval_status = '待审批' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN approval_status = '已批准' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN approval_status = '已驳回' THEN 1 ELSE 0 END) as rejected,
                COUNT(*) as total
            FROM student_leave
            WHERE 1=1
        """
        
        params = []
        if responsible_grade:
            sql += " AND LEFT(student_id, 4) = %s"
            params.append(responsible_grade)
        
        cursor.execute(sql, params)
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "pending": result['pending'] or 0,
                "approved": result['approved'] or 0,
                "rejected": result['rejected'] or 0,
                "total": result['total'] or 0
            }
        })
        
    except Exception as e:
        print(f"获取待审批数量失败: {e}")
        return jsonify({"success": False, "message": "获取数量失败"})

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
                sl.course_id,
                sl.start_time,
                sl.end_time,
                sl.leave_reason,
                sl.approval_status,
                sl.sort,
                sl.attachment,
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
            # 清理responsible_grade，去除空白字符
            responsible_grade = str(responsible_grade).strip()
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

# 辅导员请假统计API
@app.route('/api/counselor/leave_statistics', methods=['GET'])
@login_required(role='辅导员')
def get_leave_statistics():
    """获取请假统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        responsible_grade = session['user_info'].get('responsible_grade', '')
        
        sql = """
            SELECT sl.leave_id, sl.student_id, si.student_name, sl.sort,
                   sl.start_time, sl.end_time, sl.approval_status
            FROM student_leave sl
            LEFT JOIN student_info si ON sl.student_id = si.student_id
            WHERE 1=1
        """
        params = []
        if responsible_grade:
            sql += " AND LEFT(sl.student_id, 4) = %s"
            params.append(responsible_grade)
        
        cursor.execute(sql, params)
        records = cursor.fetchall()
        conn.close()
        
        total = len(records)
        status_count = Counter(r['approval_status'] for r in records)
        type_count = Counter(r['sort'] or '其他' for r in records)
        grade_count = Counter(r['student_id'][:4] + '级' for r in records if r['student_id'])
        
        month_count = {}
        for r in records:
            if r['start_time']:
                month_key = r['start_time'].strftime('%Y-%m') if hasattr(r['start_time'], 'strftime') else str(r['start_time'])[:7]
                month_count[month_key] = month_count.get(month_key, 0) + 1
        
        total_days = 0
        valid_count = 0
        for r in records:
            if r['start_time'] and r['end_time']:
                try:
                    start = r['start_time']
                    end = r['end_time']
                    days = (end - start).days + 1
                    if days > 0:
                        total_days += days
                        valid_count += 1
                except:
                    pass
        avg_days = round(total_days / valid_count, 1) if valid_count > 0 else 0
        
        return jsonify({
            "success": True,
            "data": {
                "total": total,
                "by_status": dict(status_count),
                "by_type": dict(type_count),
                "by_grade": dict(grade_count),
                "by_month": dict(sorted(month_count.items())[-12:] if month_count else {}),
                "avg_days": avg_days
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

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
        
        # 1. 校验请假记录 - 修改为支持逗号分隔的course_code
        sql_check = """
            SELECT sl.leave_id, sl.approval_status 
            FROM student_leave sl
            WHERE sl.leave_id = %s
            AND (
                # 使用FIND_IN_SET函数检查教师是否负责请假记录中的任一课程
                EXISTS (SELECT 1 FROM teacher_courses tc 
                        WHERE tc.teacher_id = %s 
                        AND FIND_IN_SET(tc.course_id, sl.course_code))
                OR sl.approver_id = %s
            )
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
        
        # 4.2 仅"同意"时，更新student_info的times字段
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

@app.route('/api/teacher/leave_records', methods=['GET'])
def api_teacher_leave_records():
    """
    获取学生所选课程的老师请假记录
    """
    try:
        # 获取当前登录的学生ID
        if 'user_info' not in session or session['user_info']['role_name'] != '学生':
            return jsonify({"success": False, "message": "用户未登录或不是学生"})
        student_id = session['user_info']['user_account']
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询学生所选课程的老师请假记录
        # 通过student_course_selection表关联，只返回学生选课的课程对应的老师请假信息
        cursor.execute("""
            SELECT 
                t_leave.teacher_id,
                ti.teacher_name,
                t_leave.leave_reason,
                t_leave.start_time,
                t_leave.end_time,
                t_leave.course_id,
                ci.course_name
            FROM 
                teacher_leave t_leave
            LEFT JOIN 
                teacher_info ti ON t_leave.teacher_id = ti.teacher_id
            LEFT JOIN
                course_info ci ON t_leave.course_id = ci.course_id
            INNER JOIN
                student_course_selection scs ON t_leave.course_id = scs.course_id
            WHERE
                scs.student_id = %s
            ORDER BY 
                t_leave.start_time DESC
        """, (student_id,))
        
        records = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": records
        })
    except pymysql.MySQLError as e:
        print(f"数据库错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取教师请假记录失败: {str(e)}"})
    except Exception as e:
        print(f"系统错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取教师请假记录失败: {str(e)}"})


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
        print(f"获取课程教师信息失败: {str(e)}")
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


@app.route('/api/student/leave', methods=['POST'])
@login_required(role='学生')
def api_student_leave():
    """学生提交请假"""
    data = request.json or {}
    course_teacher_pairs = data.get('course_teacher_pairs', [])
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()
    leave_reason = data.get('leave_reason', '').strip()
    leave_type = data.get('leave_type', '事假').strip()
    
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

        # 将多个课程ID合并为逗号分隔的字符串
        course_codes = ','.join([pair.get('course_id', '').strip() for pair in course_teacher_pairs])
        # 将多个教师ID合并为逗号分隔的字符串
        teacher_ids = ','.join([pair.get('teacher_id', '').strip() for pair in course_teacher_pairs])
        
        # 创建单条请假记录，包含所有课程和教师信息
        cursor.execute('''
            INSERT INTO student_leave
            (student_id, student_name, dept, course_id, teacher_id, leave_reason, start_time, end_time, approval_status, times, sort)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (student_account, student_name, dept, course_codes, teacher_ids, leave_reason, start_time, end_time, approval_status, current_times, leave_type))
        
        conn.commit()
        
        # 获取新插入的leave_id
        leave_id = cursor.lastrowid
        
        return jsonify({"success": True, "message": "请假提交成功", "leave_id": leave_id})
        
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


@app.route('/api/student/leave_records', methods=['GET'])
@login_required(role='学生')
def api_student_leave_records():
    """学生查看自己的请假记录，返回 {success, data: [leave_records], message} """
    student_id = session['user_info']['user_account']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print(f"开始查询学生{student_id}的请假记录")
        
        # 查询学生的所有请假记录
        cursor.execute("""
            SELECT 
                leave_id,
                course_id, 
                teacher_id, 
                start_time, 
                end_time, 
                leave_reason, 
                approval_status, 
                sort,
                approver_id,
                approver_name,
                approval_time
            FROM student_leave 
            WHERE student_id = %s 
            ORDER BY start_time DESC
        """, (student_id,))
        
        records = cursor.fetchall()
        
        # 获取所有课程名称的映射
        cursor.execute("SELECT course_id, course_name FROM course_info")
        course_map = {row['course_id']: row['course_name'] for row in cursor.fetchall()}
        
        # 为每条记录添加课程名称
        for record in records:
            if record.get('course_id'):
                course_ids = record['course_id'].split(',')
                course_names = [course_map.get(cid.strip(), cid.strip()) for cid in course_ids]
                record['course_names'] = ', '.join(course_names)
            else:
                record['course_names'] = ''
        
        print(f"查询成功，获取到{len(records)}条记录")
        return jsonify({"success": True, "data": records})
    except pymysql.MySQLError as e:
        print(f"MySQL错误查询学生请假记录失败: {str(e)}")
        return jsonify({"success": False, "message": f"数据库查询失败：{str(e)}"})
    except Exception as e:
        print(f"未知错误查询学生请假记录失败: {str(e)}")
        return jsonify({"success": False, "message": f"系统异常：{str(e)}"})
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

# 获取假条详情API
@app.route('/api/leave/detail/<int:leave_id>', methods=['GET'])
def get_leave_detail(leave_id):
    """获取假条详情"""
    if 'user_info' not in session:
        return jsonify({"success": False, "message": "请先登录"})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT sl.leave_id, sl.student_id, sl.course_id, sl.teacher_id,
                   sl.start_time, sl.end_time, sl.leave_reason, sl.approval_status,
                   sl.sort, sl.approver_id, sl.approver_name, sl.approval_time, sl.attachment,
                   si.student_name, si.major, si.class_num, si.dept, si.contact as student_contact
            FROM student_leave sl
            LEFT JOIN student_info si ON sl.student_id = si.student_id
            WHERE sl.leave_id = %s
        """, (leave_id,))
        
        leave = cursor.fetchone()
        if not leave:
            return jsonify({"success": False, "message": "假条不存在"})
        
        # 权限验证
        user_role = session['user_info']['role_name']
        user_account = session['user_info']['user_account']
        if user_role == '学生' and leave['student_id'] != user_account:
            return jsonify({"success": False, "message": "无权查看此假条"})
        
        # 获取课程名称
        if leave.get('course_id'):
            course_ids = leave['course_id'].split(',')
            placeholders = ','.join(['%s'] * len(course_ids))
            cursor.execute(f"SELECT course_id, course_name FROM course_info WHERE course_id IN ({placeholders})", course_ids)
            course_map = {row['course_id']: row['course_name'] for row in cursor.fetchall()}
            leave['course_names'] = ', '.join([course_map.get(cid.strip(), cid.strip()) for cid in course_ids])
        else:
            leave['course_names'] = ''
        
        # 检查签名文件
        signature_folder = os.path.join(app.root_path, 'data', 'signatures')
        student_sign = f"{leave['student_id']}_{leave_id}.png"
        counselor_sign = f"{leave.get('approver_id', '')}_{leave_id}.png" if leave.get('approver_id') else ''
        leave['student_signature'] = f"/qianzi/{student_sign}" if os.path.exists(os.path.join(signature_folder, student_sign)) else None
        leave['counselor_signature'] = f"/qianzi/{counselor_sign}" if counselor_sign and os.path.exists(os.path.join(signature_folder, counselor_sign)) else None
        
        # 检查佐证文件
        if leave.get('attachment'):
            attachment_folder = os.path.join(app.root_path, 'data', 'certificates')
            if os.path.exists(os.path.join(attachment_folder, leave['attachment'])):
                leave['attachment_url'] = f"/zhengming/{leave['attachment']}"
            else:
                leave['attachment_url'] = None
        else:
            leave['attachment_url'] = None
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": leave})
    except Exception as e:
        print(f"获取假条详情失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取失败: {str(e)}"})

# 学生获取联系人列表API
@app.route('/api/student/chat/contacts', methods=['GET'])
@login_required(role='学生')
def get_student_chat_contacts():
    """获取学生可以聊天的联系人列表（辅导员+讲师）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        grade = student_id[:4]
        
        # 获取当前学生头像
        cursor.execute("SELECT avatar FROM student_info WHERE student_id = %s", (student_id,))
        student_row = cursor.fetchone()
        student_avatar = student_row['avatar'] if student_row and student_row.get('avatar') else None
        
        # 获取本年级的辅导员（含头像）
        cursor.execute("""
            SELECT counselor_id as id, counselor_name as name, '辅导员' as role, contact, avatar
            FROM counselor_info 
            WHERE responsible_grade = %s
        """, (grade,))
        counselors = cursor.fetchall()
        
        # 获取学生选课的讲师（去重，含头像）
        cursor.execute("""
            SELECT DISTINCT ti.teacher_id as id, ti.teacher_name as name, '讲师' as role, ti.contact, ti.avatar,
                   GROUP_CONCAT(ci.course_name SEPARATOR ', ') as courses
            FROM student_course_selection scs
            JOIN teacher_course tc ON scs.course_id = tc.course_id
            JOIN teacher_info ti ON tc.teacher_id = ti.teacher_id
            JOIN course_info ci ON scs.course_id = ci.course_id
            WHERE scs.student_id = %s
            GROUP BY ti.teacher_id, ti.teacher_name, ti.contact, ti.avatar
        """, (student_id,))
        teachers = cursor.fetchall()
        
        conn.close()
        return jsonify({
            "success": True, 
            "data": {
                "counselors": counselors,
                "teachers": teachers,
                "student_avatar": student_avatar
            }
        })
    except Exception as e:
        print(f"获取联系人列表失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取联系人失败: {str(e)}"})
# 学生聊天API
@app.route('/api/student/chat/messages', methods=['GET'])
@login_required(role='学生')
def get_student_chat_messages():
    """获取学生与指定联系人的聊天记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        contact_id = request.args.get('contact_id', '').strip()
        
        if not contact_id:
            return jsonify({"success": True, "data": []})
        
        # 获取聊天记录：学生发给联系人 或 联系人发给学生
        cursor.execute("""
            SELECT content, sender_role as sender_type, create_time as created_at 
            FROM chat_messages 
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY create_time ASC
        """, (student_id, contact_id, contact_id, student_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": messages})
    except Exception as e:
        print(f"获取聊天记录失败: {str(e)}")
        return jsonify({"success": False, "message": "获取聊天记录失败"})

@app.route('/api/student/chat/send', methods=['POST'])
@login_required(role='学生')
def send_student_chat_message():
    """学生发送消息给联系人（辅导员或讲师）"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        contact_id = data.get('contact_id', '').strip()
        contact_role = data.get('contact_role', '').strip()
        
        if not message:
            return jsonify({"success": False, "message": "消息不能为空"})
        if not contact_id or not contact_role:
            return jsonify({"success": False, "message": "请选择联系人"})

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        
        # 获取学生姓名
        cursor.execute("SELECT student_name FROM student_info WHERE student_id = %s", (student_id,))
        student_row = cursor.fetchone()
        student_name = student_row['student_name'] if student_row else '学生'
        
        # 根据联系人角色获取姓名
        if contact_role == '辅导员':
            cursor.execute("SELECT counselor_name as name FROM counselor_info WHERE counselor_id = %s", (contact_id,))
        else:
            cursor.execute("SELECT teacher_name as name FROM teacher_info WHERE teacher_id = %s", (contact_id,))
        
        contact_row = cursor.fetchone()
        contact_name = contact_row['name'] if contact_row else contact_role
        
        # 插入消息记录
        cursor.execute("""
            INSERT INTO chat_messages (sender_id, sender_name, sender_role, receiver_id, receiver_name, receiver_role, content, create_time)
            VALUES (%s, %s, '学生', %s, %s, %s, %s, NOW())
        """, (student_id, student_name, contact_id, contact_name, contact_role, message))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "消息发送成功"})
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
        return jsonify({"success": False, "message": "发送消息失败"})

@app.route('/api/counselor/chat/messages', methods=['GET'])
@login_required(role='辅导员')
def get_counselor_chat_messages():
    """获取辅导员与指定学生的聊天记录"""
    try:
        student_id = request.args.get('student_id', '').strip()
        if not student_id:
            return jsonify({"success": False, "message": "缺少学生ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        cursor.execute("""
            SELECT content, sender_role as sender_type, create_time as created_at 
            FROM chat_messages 
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY create_time ASC
        """, (counselor_id, student_id, student_id, counselor_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        return jsonify({"success": True, "data": messages})
    except Exception as e:
        print(f"获取辅导员聊天记录失败: {str(e)}")
        return jsonify({"success": False, "message": "获取聊天记录失败"})

@app.route('/api/counselor/chat/send', methods=['POST'])
@login_required(role='辅导员')
def send_counselor_chat_message():
    """辅导员发送消息给学生"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        student_id = data.get('student_id', '').strip()
        
        if not message:
            return jsonify({"success": False, "message": "消息不能为空"})
        if not student_id:
            return jsonify({"success": False, "message": "缺少学生ID"})
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        # 获取辅导员和学生姓名
        cursor.execute("SELECT counselor_name FROM counselor_info WHERE counselor_id = %s", (counselor_id,))
        counselor_row = cursor.fetchone()
        counselor_name = counselor_row['counselor_name'] if counselor_row else '辅导员'
        
        cursor.execute("SELECT student_name FROM student_info WHERE student_id = %s", (student_id,))
        student_row = cursor.fetchone()
        student_name = student_row['student_name'] if student_row else '学生'
        
        # 插入消息记录
        cursor.execute("""
            INSERT INTO chat_messages (sender_id, sender_name, sender_role, receiver_id, receiver_name, receiver_role, content, create_time)
            VALUES (%s, %s, '辅导员', %s, %s, '学生', %s, NOW())
        """, (counselor_id, counselor_name, student_id, student_name, message))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "消息发送成功"})
    except Exception as e:
        print(f"辅导员发送消息失败: {str(e)}")
        return jsonify({"success": False, "message": f"发送失败: {str(e)}"})

# 头像图片访问路由（支持新旧两种URL）
@app.route('/head_image/<path:filename>')
@app.route('/data/avatars/<path:filename>')
def serve_head_image(filename):
    """提供头像图片访问"""
    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    return send_from_directory(image_folder, filename)

# 签名图片访问路由（支持新旧两种URL）
@app.route('/qianzi/<path:filename>')
@app.route('/data/signatures/<path:filename>')
def serve_signature_image(filename):
    """提供签名图片访问"""
    signature_folder = os.path.join(app.root_path, 'data', 'signatures')
    return send_from_directory(signature_folder, filename)

# 佐证文件访问路由（支持新旧两种URL）
@app.route('/zhengming/<path:filename>')
@app.route('/data/certificates/<path:filename>')
def serve_attachment_file(filename):
    """提供佐证文件访问"""
    attachment_folder = os.path.join(app.root_path, 'data', 'certificates')
    return send_from_directory(attachment_folder, filename)

# 上传佐证文件API
@app.route('/api/leave/upload_attachment', methods=['POST'])
@login_required(role='学生')
def upload_leave_attachment():
    """上传请假佐证文件（图片或PDF）"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未选择文件"})
        
        file = request.files['file']
        leave_id = request.form.get('leave_id', '')
        
        if not leave_id:
            return jsonify({"success": False, "message": "缺少假条ID"})
        
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"})
        
        student_id = session['user_info']['user_account']
        
        # 验证假条属于该学生
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM student_leave WHERE leave_id = %s", (leave_id,))
        row = cursor.fetchone()
        if not row or row[0] != student_id:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "无权操作此假条"})
        
        # 检查文件类型
        allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_ext:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "仅支持图片(png/jpg/gif)或PDF文件"})
        
        # 创建存储文件夹
        attachment_folder = os.path.join(app.root_path, 'data', 'certificates')
        if not os.path.exists(attachment_folder):
            os.makedirs(attachment_folder)
        
        # 生成文件名：student_id_leave_id.ext
        filename = f"{student_id}_{leave_id}.{ext}"
        filepath = os.path.join(attachment_folder, filename)
        
        # 保存文件
        file.save(filepath)
        
        # 更新数据库
        cursor.execute("UPDATE student_leave SET attachment = %s WHERE leave_id = %s", (filename, leave_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "佐证文件上传成功",
            "filename": filename,
            "filepath": f"/zhengming/{filename}"
        })
        
    except Exception as e:
        print(f"上传佐证文件失败: {str(e)}")
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"})

# 保存学生签名图片API
@app.route('/api/student/save_signature', methods=['POST'])
@login_required(role='学生')
def save_student_signature():
    """保存学生签名图片"""
    try:
        data = request.json or {}
        signature_data = data.get('signature', '')
        leave_id = data.get('leave_id', '')
        
        if not signature_data or not leave_id:
            return jsonify({"success": False, "message": "缺少签名数据或假条ID"})
        
        student_id = session['user_info']['user_account']
        
        # 验证该假条属于该学生
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM student_leave WHERE leave_id = %s", (leave_id,))
        row = cursor.fetchone()
        if not row or row[0] != student_id:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "无权操作此假条"})
        cursor.close()
        conn.close()
        
        # 解码base64并保存图片
        if ',' in signature_data:
            signature_data = signature_data.split(',')[1]
        
        image_data = base64.b64decode(signature_data)
        
        # 保存文件
        signature_folder = os.path.join(app.root_path, 'data', 'signatures')
        if not os.path.exists(signature_folder):
            os.makedirs(signature_folder)
        
        filename = f"{student_id}_{leave_id}.png"
        filepath = os.path.join(signature_folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return jsonify({"success": True, "message": "签名保存成功", "filename": filename})
    except Exception as e:
        print(f"保存签名失败: {str(e)}")
        return jsonify({"success": False, "message": f"保存签名失败: {str(e)}"})

# 辅导员个人信息接口
@app.route('/api/counselor/info', methods=['GET'])
@login_required(role='辅导员')
def get_counselor_info():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        counselor_id = session['user_info']['user_account']
        sql = """
            SELECT counselor_id, password, counselor_name, dept,
                   responsible_grade, responsible_major, contact
            FROM counselor_info
            WHERE counselor_id = %s
        """
        cursor.execute(sql, (counselor_id,))
        info = cursor.fetchone()

        if not info:
            return jsonify({"success": False, "message": "未找到个人信息"})

        password = info.get('password') or ''
        info['password'] = '*' * len(password) if password else ''

        return jsonify({"success": True, "data": info})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})
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

# 获取可用头像列表
@app.route('/api/avatars', methods=['GET'])
def get_avatars():
    """获取可用头像列表"""
    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    try:
        avatars = [
            name for name in os.listdir(image_folder)
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        return jsonify({"success": True, "data": avatars})
    except FileNotFoundError:
        return jsonify({"success": True, "data": []})

# 学生更新联系方式
@app.route('/api/student/contact', methods=['POST'])
@login_required(role='学生')
def update_student_contact():
    """更新学生联系方式"""
    try:
        data = request.json or {}
        contact = data.get('contact', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        student_id = session['user_info']['user_account']
        cursor.execute("UPDATE student_info SET contact = %s WHERE student_id = %s", (contact, student_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "联系方式已更新"})
    except Exception as e:
        print(f"更新联系方式失败: {e}")
        return jsonify({"success": False, "message": "更新失败"})

# 通用头像更新接口
@app.route('/api/user/avatar', methods=['POST'])
def update_user_avatar():
    """更新用户头像（通用接口，所有角色可用）"""
    if 'user_info' not in session:
        return jsonify({"success": False, "message": "请先登录"})

    data = request.json or {}
    avatar = (data.get('avatar') or '').strip()
    if not avatar:
        return jsonify({"success": False, "message": "未选择头像"})

    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    try:
        valid_files = [
            name for name in os.listdir(image_folder)
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
    except FileNotFoundError:
        return jsonify({"success": False, "message": "头像目录不存在"})

    if avatar not in valid_files:
        return jsonify({"success": False, "message": "非法的头像文件"})

    role = session['user_info']['role_name']
    user_account = session['user_info']['user_account']

    table_map = {
        "管理员": ("admin_info", "admin_id"),
        "辅导员": ("counselor_info", "counselor_id"),
        "讲师": ("teacher_info", "teacher_id"),
        "学生": ("student_info", "student_id")
    }

    if role not in table_map:
        return jsonify({"success": False, "message": "未知的用户角色"})

    table_name, id_field = table_map[role]

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = f"UPDATE {table_name} SET avatar = %s, update_time = %s WHERE {id_field} = %s"
        cursor.execute(sql, (avatar, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_account))
        conn.commit()
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"保存失败：{str(e)}"})
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.open:
                conn.close()
        except Exception:
            pass

    if 'user_info' in session:
        session['user_info']['avatar'] = avatar

    return jsonify({"success": True, "message": "头像已保存", "avatar": avatar})

# 兼容旧接口
@app.route('/api/counselor/avatar', methods=['POST'])
@login_required(role='辅导员')
def update_counselor_avatar():
    """辅导员头像更新（兼容旧接口）"""
    return update_user_avatar()

# 上传自定义头像
@app.route('/api/user/avatar/upload', methods=['POST'])
def upload_user_avatar():
    """上传自定义头像"""
    if 'user_info' not in session:
        return jsonify({"success": False, "message": "请先登录"})
    
    if 'avatar' not in request.files:
        return jsonify({"success": False, "message": "未选择文件"})
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"})
    
    # 检查文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({"success": False, "message": "只支持 png/jpg/jpeg/gif 格式"})
    
    # 生成唯一文件名
    user_id = session['user_info']['user_account']
    filename = f"avatar_{user_id}.{ext}"
    
    # 保存文件
    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    filepath = os.path.join(image_folder, filename)
    
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({"success": False, "message": f"保存失败：{str(e)}"})
    
    # 更新数据库
    role = session['user_info']['role_name']
    table_map = {
        "管理员": ("admin_info", "admin_id"),
        "辅导员": ("counselor_info", "counselor_id"),
        "讲师": ("teacher_info", "teacher_id"),
        "学生": ("student_info", "student_id")
    }
    
    if role not in table_map:
        return jsonify({"success": False, "message": "未知的用户角色"})
    
    table_name, id_field = table_map[role]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = f"UPDATE {table_name} SET avatar = %s, update_time = %s WHERE {id_field} = %s"
        cursor.execute(sql, (filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        cursor.close()
        conn.close()
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"数据库更新失败：{str(e)}"})
    
    # 更新 session
    session['user_info']['avatar'] = filename
    
    return jsonify({"success": True, "message": "头像上传成功", "avatar": filename})

# 学生个人信息页面
@app.route('/student/profile')
@login_required(role='学生')
def student_profile_page():
    """学生个人信息页面"""
    image_folder = os.path.join(app.root_path, 'data', 'avatars')
    try:
        available_avatars = [
            name for name in os.listdir(image_folder)
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
    except FileNotFoundError:
        available_avatars = []
    
    # 从数据库获取头像
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT avatar FROM student_info WHERE student_id = %s", 
                      (session['user_info']['user_account'],))
        row = cursor.fetchone()
        db_avatar = row[0] if row and row[0] else None
        cursor.close()
        conn.close()
    except:
        db_avatar = None
    
    current_avatar = db_avatar or session['user_info'].get('avatar') or 'boy.png'
    session['user_info']['avatar'] = current_avatar
    
    return render_template('student/profile.html', 
                          user_info=session['user_info'],
                          available_avatars=available_avatars,
                          current_avatar=current_avatar)

@app.route('/api/student/info', methods=['GET'])
@login_required(role='学生')
def get_student_info():
    """获取学生个人信息"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        student_id = session['user_info']['user_account']
        sql = """
            SELECT student_id, password, student_name, dept, major, class_num, contact
            FROM student_info
            WHERE student_id = %s
        """
        cursor.execute(sql, (student_id,))
        info = cursor.fetchone()
        
        if not info:
            return jsonify({"success": False, "message": "未找到个人信息"})
        
        # 隐藏密码
        password = info.get('password') or ''
        info['password'] = '*' * len(password) if password else ''
        
        return jsonify({"success": True, "data": info})
    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"查询失败：{str(e)}"})
    finally:
        if cursor: cursor.close()
        if conn and conn.open: conn.close()

# 辅导员导出请假记录
@app.route('/api/counselor/export_leaves', methods=['GET'])
@login_required(role='辅导员')
def export_leaves_excel():
    """导出请假记录为CSV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        responsible_grade = session['user_info'].get('responsible_grade', '')
        status_filter = request.args.get('status', '')
        
        sql = """
            SELECT sl.leave_id as 假条编号, sl.student_id as 学号, si.student_name as 姓名,
                   si.major as 专业, sl.sort as 请假类型,
                   sl.start_time as 开始时间, sl.end_time as 结束时间,
                   sl.leave_reason as 请假原因, sl.approval_status as 审批状态,
                   sl.approver_name as 审批人
            FROM student_leave sl
            LEFT JOIN student_info si ON sl.student_id = si.student_id
            WHERE 1=1
        """
        params = []
        if responsible_grade:
            sql += " AND LEFT(sl.student_id, 4) = %s"
            params.append(responsible_grade)
        if status_filter:
            sql += " AND sl.approval_status = %s"
            params.append(status_filter)
        sql += " ORDER BY sl.start_time DESC"
        
        cursor.execute(sql, params)
        records = cursor.fetchall()
        conn.close()
        
        output = io.StringIO()
        output.write('\ufeff')  # BOM for Excel
        if records:
            headers = list(records[0].keys())
            output.write(','.join(headers) + '\n')
            for record in records:
                row = []
                for h in headers:
                    val = record[h]
                    if val is None:
                        val = ''
                    elif hasattr(val, 'strftime'):
                        val = val.strftime('%Y-%m-%d %H:%M')
                    else:
                        val = str(val).replace(',', '，').replace('\n', ' ')
                    row.append(val)
                output.write(','.join(row) + '\n')
        
        filename = f"leave_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = Response(
            output.getvalue(),
            mimetype='text/csv'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        return response
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 辅导员审批等级API
@app.route('/api/counselor/approval_level', methods=['GET'])
@login_required(role='辅导员')
def get_counselor_approval_level():
    """获取辅导员审批等级"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        counselor_id = session['user_info']['user_account']
        
        # 获取本月审批数量
        current_month = datetime.now().strftime('%Y-%m')
        sql = """
            SELECT COUNT(*) as monthly_count
            FROM student_leave 
            WHERE approver_id = %s 
            AND DATE_FORMAT(approval_time, '%%Y-%%m') = %s
            AND approval_status IN ('已批准', '已驳回')
        """
        cursor.execute(sql, (counselor_id, current_month))
        result = cursor.fetchone()
        monthly_count = result['monthly_count'] if result else 0
        
        # 获取总审批数量
        sql_total = """
            SELECT COUNT(*) as total_count
            FROM student_leave 
            WHERE approver_id = %s 
            AND approval_status IN ('已批准', '已驳回')
        """
        cursor.execute(sql_total, (counselor_id,))
        result_total = cursor.fetchone()
        total_count = result_total['total_count'] if result_total else 0
        
        conn.close()
        
        # 计算等级
        def get_level_info(count):
            if count >= 100:
                return {"level": "王者级", "icon": "fa-crown", "color": "#8B5CF6", "next_target": None}
            elif count >= 50:
                return {"level": "黄金级", "icon": "fa-medal", "color": "#F59E0B", "next_target": 100}
            elif count >= 30:
                return {"level": "白银级", "icon": "fa-award", "color": "#6B7280", "next_target": 50}
            elif count >= 10:
                return {"level": "青铜级", "icon": "fa-trophy", "color": "#CD7C2F", "next_target": 30}
            else:
                return {"level": "新手级", "icon": "fa-star", "color": "#10B981", "next_target": 10}
        
        level_info = get_level_info(monthly_count)
        
        # 计算任职时间（工号前四位为入职年份）
        work_year = int(counselor_id[:4])
        current_year = datetime.now().year
        work_years = current_year - work_year
        
        return jsonify({
            "success": True,
            "data": {
                "monthly_count": monthly_count,
                "total_count": total_count,
                "level": level_info["level"],
                "icon": level_info["icon"],
                "color": level_info["color"],
                "next_target": level_info["next_target"],
                "work_years": work_years,
                "work_start_year": work_year
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 辅导员更新联系方式API
@app.route('/api/counselor/update_contact', methods=['POST'])
@login_required(role='辅导员')
def update_counselor_contact():
    """更新辅导员联系方式"""
    try:
        data = request.json
        new_contact = data.get('contact', '').strip()
        
        if not new_contact:
            return jsonify({"success": False, "message": "联系方式不能为空"})
        
        counselor_id = session['user_info']['user_account']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新联系方式
        sql = """
            UPDATE counselor_info 
            SET contact = %s, update_time = %s 
            WHERE counselor_id = %s
        """
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(sql, (new_contact, update_time, counselor_id))
        conn.commit()
        return jsonify({"success": True, "message": "联系方式更新成功"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"})

# 管理员专用接口 - 获取操作日志
@app.route('/api/admin/operation-logs', methods=['GET'])
@login_required(role='管理员')
def get_operation_logs():
    """获取管理员操作日志（仅管理员）"""
    try:
        # 获取筛选参数
        operation_type = request.args.get('operation_type', '')
        user_role = request.args.get('user_role', '')
        time_range = request.args.get('time_range', 'all')
        
        # 基础查询
        query = "SELECT * FROM admin_operation_logs WHERE 1=1"
        params = []
        
        # 添加操作类型筛选
        if operation_type:
            query += " AND operation_type = %s"
            params.append(operation_type)
        
        # 添加用户角色筛选
        if user_role:
            query += " AND target_user_role = %s"
            params.append(user_role)
        
        # 添加时间范围筛选
        if time_range == 'today':
            query += " AND DATE(operation_time) = CURDATE()"
        elif time_range == 'week':
            query += " AND operation_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        elif time_range == 'month':
            query += " AND operation_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        
        # 按时间倒序排列
        query += " ORDER BY operation_time DESC LIMIT 1000"
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params)
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 转换datetime为字符串
        for log in logs:
            if log.get('operation_time'):
                log['operation_time'] = log['operation_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({"success": True, "data": logs})
        
    except Exception as e:
        print(f"获取日志失败详情: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取日志失败：{str(e)}", "data": []})

# 管理员专用接口 - 记录操作日志（辅助函数）
def log_admin_operation(operation_type, target_account=None, target_name=None, target_role=None, details=None, status='SUCCESS', error_msg=None):
    """记录管理员操作日志"""
    try:
        # 获取当前登录的管理员信息
        admin_account = session.get('user_info', {}).get('user_account', 'unknown')
        admin_name = session.get('user_info', {}).get('user_name', 'unknown')
        
        print(f"[LOG] 开始记录日志 - 管理员:{admin_name}({admin_account}), 操作:{operation_type}, 目标:{target_name}({target_account}), 角色:{target_role}")
        
        # 获取客户端IP
        ip_address = request.remote_addr
        
        # 创建新的数据库连接
        print(f"[LOG] 正在连接数据库...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"[LOG] 正在执行INSERT语句...")
        cursor.execute("""
            INSERT INTO admin_operation_logs 
            (admin_account, admin_name, operation_type, target_user_account, target_user_name, 
             target_user_role, operation_details, ip_address, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (admin_account, admin_name, operation_type, target_account, target_name, 
              target_role, details, ip_address, status, error_msg))
        
        print(f"[LOG] 正在提交事务...")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[LOG] ✓ 日志记录成功！")
    except Exception as e:
        print(f"[LOG] ✗ 记录操作日志失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 日志记录失败不影响主业务

# ========== AI助手（本地Ollama） ==========
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """调用本地Ollama模型进行对话"""
    import requests
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"success": False, "message": "消息不能为空"})
        
        # 系统提示词
        system_prompt = """你是"请了吗"请假管理系统的智能助手小龙🐉。

你可以帮助学生解答请假流程、提交申请、解释请假类型、查看记录、生成模板。

重要：直接输出回复内容，不要输出任何思考过程、分析或计划。开头用"你好"或问候语。"""

        # 调用本地Ollama API（在用户消息末尾添加/no_think禁用思考模式）
        ollama_url = "http://localhost:11434/api/chat"
        payload = {
            "model": "qwen3:4b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message + " /no_think"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        response = requests.post(ollama_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result.get('message', {}).get('content', '抱歉，我暂时无法回答。')
            
            # 清理思考标签（qwen3特有）- 只保留最终回复
            import re as regex
            
            # 移除<think>标签内容
            if '<think>' in ai_reply:
                ai_reply = regex.sub(r'<think>.*?</think>', '', ai_reply, flags=regex.DOTALL).strip()
            
            # 移除未闭合的<think>标签及其后内容（思考未完成时）
            if '<think>' in ai_reply:
                ai_reply = regex.sub(r'<think>.*', '', ai_reply, flags=regex.DOTALL).strip()
            
            # 移除常见的思考过程开头（没有标签的情况）
            thinking_patterns = [
                r'^首先[，,].*?(?=\n\n|你好|我是|请|好的)',
                r'^用户.*?(?=\n\n|你好|我是|请|好的)',
                r'^我需要.*?(?=\n\n|你好|我是|请|好的)',
                r'^作为.*?(?=\n\n|你好|我是|请|好的)',
                r'^让我.*?(?=\n\n|你好|我是|请|好的)',
            ]
            for pattern in thinking_patterns:
                ai_reply = regex.sub(pattern, '', ai_reply, flags=regex.DOTALL).strip()
            
            # 如果回复以思考词开头，尝试找到真正的回复
            thinking_starts = ('首先', '用户', '我需要', '作为', '让我', '我的角色', 
                             '请假模板，', '关键点', '这个问题', '好的，', '分析')
            if ai_reply.startswith(thinking_starts) or '这可能意味着' in ai_reply[:100]:
                # 查找真正回复的开始
                match = regex.search(r'(你好[呀！~]?|亲爱的|我是小龙|请参考|以下是|✨|【请)', ai_reply)
                if match:
                    ai_reply = ai_reply[match.start():]
                else:
                    # 找不到就返回默认回复
                    ai_reply = '你好！有什么可以帮你的吗？😊'
            
            if not ai_reply.strip():
                ai_reply = '你好！有什么可以帮你的吗？😊'
            return jsonify({"success": True, "reply": ai_reply})
        else:
            return jsonify({"success": False, "message": "AI服务暂时不可用"})
            
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "请确保Ollama服务已启动（ollama serve）"})
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "AI响应超时，请稍后重试"})
    except Exception as e:
        return jsonify({"success": False, "message": f"AI服务错误: {str(e)}"})

# 启动应用
if __name__ == '__main__':
    try:
        # 获取环境变量配置
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', '8080'))
        debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"启动Flask应用: {host}:{port}, Debug: {debug}")
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()