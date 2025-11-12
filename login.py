# login.py（兼容终端版和Web版）
import pymysql
from db_config import get_db_config

def login(account=None, password=None, role_type=None):
    # 如果未传参数（终端版调用），则通过input获取
    if not account:
        account = input("请输入账号：")
    if not password:
        password = input("请输入密码：")
    
    role_map = {1: "学生", 2: "辅导员", 3: "讲师", 4: "管理员"}
    
    # 如果未传角色类型（终端版调用），则通过input获取
    if not role_type:
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
        sql = "SELECT user_account, user_password, role_type FROM user WHERE user_account = %s"
        cursor.execute(sql, (account,))
        user = cursor.fetchone()
        
        if not user:
            print("❌ 账号不存在")
            return None
        
        db_account, db_password, db_role_type = user
        if password != db_password:
            print("❌ 密码错误")
            return None
        
        if role_type not in role_map:
            print(f"❌ 无效身份类型（请选择1-{len(role_map)}）")
            return None
        
        if role_type != db_role_type:
            actual_role = role_map[db_role_type]
            print(f"❌ 身份不匹配（实际为{actual_role}）")
            return None
        
        print(f"✅ 登录成功！欢迎回来，{db_account}（{role_map[role_type]}）")
        return {
            "user_account": db_account,
            "role_type": db_role_type,
            "role_name": role_map[role_type]
        }
    except pymysql.MySQLError as e:
        print(f"❌ 数据库错误：{e}")
        return None
    except ValueError:
        print("❌ 角色类型必须是数字")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()