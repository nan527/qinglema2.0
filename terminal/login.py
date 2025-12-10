import pymysql
from db_config import get_db_config

def login():
    # 登录循环，直到成功或用户主动退出
    while True:
        # 1. 获取账号和密码，支持退出功能
        print("\n----- 用户登录 -----")
        account = input("请输入账号（输入'quit'退出登录）：").strip()
        
        # 检查是否要退出
        if account.lower() == 'quit':
            print("退出登录")
            return None
            
        password = input("请输入密码：").strip()

        # 2. 账号长度→身份表映射
        account_len = len(account)
        role_map = {
            4: {
                "table": "admin_info",
                "account_field": "admin_id",
                "pwd_field": "admin_password",
                "name_field": "admin_name",
                "role_name": "管理员"
            },
            8: {
                "table": "counselor_info",
                "account_field": "counselor_id",
                "pwd_field": "counselor_password",
                "name_field": "counselor_name",
                "role_name": "辅导员",
                "extra_field": "responsible_grade"  # 辅导员特有字段
            },
            9: {
                "table": "teacher_info",
                "account_field": "teacher_id",
                "pwd_field": "teacher_password",
                "name_field": "teacher_name",
                "role_name": "讲师"
            },
            12: {
                "table": "student_info",
                "account_field": "student_id",
                "pwd_field": "student_password",
                "name_field": "student_name",
                "role_name": "学生"
            }
        }

        # 3. 校验账号长度是否支持
        if account_len not in role_map:
            print(f"❌ 不支持的账号长度（当前{account_len}位）！支持规则：4位(管理员)/8位(辅导员)/9位(讲师)/12位(学生)")
            print("请重新输入...")
            continue

        # 4. 获取目标表信息
        target = role_map[account_len]
        config = get_db_config()
        conn = None
        cursor = None

        try:
            # 5. 查询对应表的账号、密码、姓名（辅导员需额外查询负责年级）
            conn = pymysql.connect(**config)
            cursor = conn.cursor()
            
            # 构建SQL语句（区分辅导员和其他角色）
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

            # 6. 验证逻辑
            if not user:
                print(f"❌ {target['role_name']}账号不存在")
                print("请重新输入...")
                continue
            
            # 解析查询结果
            if target["role_name"] == "辅导员":
                db_account, db_password, db_name, db_responsible_grade = user
            else:
                db_account, db_password, db_name = user

            if password != db_password:
                print("❌ 密码错误")
                print("请重新输入...")
                continue

            # 7. 登录成功，返回用户信息
            welcome_msg = f"✅ 登录成功！欢迎回来，{db_name}（{target['role_name']}·{db_account}）"
            print(welcome_msg)
            
            result = {
                "user_account": db_account,
                "user_name": db_name,
                "role_name": target['role_name'],
                "identity_table": target['table']
            }
            
            # 添加辅导员特有信息
            if target["role_name"] == "辅导员":
                result["responsible_grade"] = db_responsible_grade

            return result

        except pymysql.MySQLError as e:
            print(f"❌ 数据库错误：{e}")
            print("请重新输入...")
            continue
        finally:
            if cursor:
                cursor.close()
            if conn and conn.open:
                conn.close()