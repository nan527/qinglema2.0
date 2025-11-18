import pymysql
from db_config import get_db_config

def login():
    # 1. 获取账号、密码、身份选择
    account = input("请输入账号：").strip()
    password = input("请输入密码：").strip()
    
    print("可选身份类型：")
    print("1. 学生")
    print("2. 辅导员")
    print("3. 讲师")
    print("4. 管理员")
    role_choice = input("请选择身份类型序号：").strip()

    # 2. 身份与表的映射（新增管理员姓名字段 admin_name）
    role_map = {
        "1": {
            "table": "student_info",
            "account_field": "student_id",
            "pwd_field": "password",
            "name_field": "student_name",  # 学生姓名字段
            "role_name": "学生"
        },
        "2": {
            "table": "counselor_info",
            "account_field": "counselor_id",
            "pwd_field": "password",
            "name_field": "counselor_name",  # 辅导员姓名字段
            "role_name": "辅导员"
        },
        "3": {
            "table": "teacher_info",
            "account_field": "teacher_id",
            "pwd_field": "password",
            "name_field": "teacher_name",  # 教师姓名字段
            "role_name": "讲师"
        },
        "4": {
            "table": "admin_info",
            "account_field": "admin_id",
            "pwd_field": "password",
            "name_field": "admin_name",  # 管理员姓名字段（关键）
            "role_name": "管理员"
        }
    }

    # 3. 校验身份选择是否有效
    if role_choice not in role_map:
        print("❌ 无效的身份类型序号")
        return None

    # 4. 获取目标表信息
    target = role_map[role_choice]
    config = get_db_config()
    conn = None
    cursor = None

    try:
        # 5. 连接数据库，查询账号、密码、姓名（新增姓名字段查询）
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        sql = f"""
            SELECT {target['account_field']}, {target['pwd_field']}, {target['name_field']}
            FROM {target['table']}
            WHERE {target['account_field']} = %s
        """
        cursor.execute(sql, (account,))
        user = cursor.fetchone()

        # 6. 验证逻辑
        if not user:
            print(f"❌ {target['role_name']}账号不存在")
            return None
        
        db_account, db_password, db_name = user  # 新增姓名变量
        if password != db_password:
            print("❌ 密码错误")
            return None

        # 7. 登录成功，显示个性化欢迎词（关键修改）
        welcome_msg = f"✅ 登录成功！欢迎回来，{db_name}（{target['role_name']}·{db_account}）"
        print(welcome_msg)
        
        return {
            "user_account": db_account,
            "user_name": db_name,  # 返回姓名，供后续使用
            "role_name": target['role_name'],
            "identity_table": target['table']
        }

    except pymysql.MySQLError as e:
        print(f"❌ 数据库错误：{e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()