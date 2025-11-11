import pymysql
from db_config import get_db_config

def login():
    print("\n===== 用户登录 =====")
    user_account = input("请输入账号：")
    user_password = input("请输入密码：")
    
    # 本地维护 role_type 与角色名称的映射关系
    role_map = {
        1: "学生",
        2: "辅导员",
        3: "讲师",
        4: "管理员"
    }
    
    # 展示可选角色
    print("可选身份类型：")
    for key, value in role_map.items():
        print(f"{key}. {value}")
    role_type = int(input("请选择身份类型序号："))

    config = get_db_config()
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        # 仅查询 user 表的核心字段
        sql = """
        SELECT user_account, user_password, role_type 
        FROM user 
        WHERE user_account = %s
        """
        cursor.execute(sql, (user_account,))
        user = cursor.fetchone()

        if not user:
            print("❌ 登录失败：账号不存在")
            return None
        
        db_account, db_password, db_role_type = user
        
        # 密码验证（实际项目需加密比对，此处简化为明文）
        if user_password != db_password:
            print("❌ 登录失败：密码错误")
            return None
        
        # 角色合法性校验
        if role_type not in role_map:
            print(f"❌ 登录失败：无效的身份类型（请选择1-{len(role_map)}）")
            return None
        
        # 角色匹配校验
        if role_type != db_role_type:
            actual_role = role_map.get(db_role_type, "未知角色")
            print(f"❌ 登录失败：身份类型不匹配（实际为{actual_role}）")
            return None
        
        # 登录成功，返回用户信息
        login_role = role_map[role_type]
        print(f"✅ 登录成功！欢迎回来，{db_account}（身份：{login_role}）")
        return {
            "user_account": db_account,
            "role_type": db_role_type,
            "role_name": login_role
        }

    except pymysql.MySQLError as e:
        print(f"❌ 数据库错误：{e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()