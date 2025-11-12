# admin_operation_terminal.py（原代码无修改）
import pymysql
from db_config import get_db_config

class AdminOperation:
    def __init__(self):
        self.config = get_db_config()
        self.conn = None
        self.cursor = None

    def _connect_db(self):
        """建立数据库连接"""
        self.conn = pymysql.connect(**self.config)
        self.cursor = self.conn.cursor()

    def _close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.open:
            self.conn.close()

    def show_all_users(self):
        """查询所有用户（包含user_name）"""
        try:
            self._connect_db()
            self.cursor.execute("""
                SELECT user_account, user_name, user_password, role_type 
                FROM user
            """)
            users = self.cursor.fetchall()
            if not users:
                print("📌 暂无用户数据")
                return
            print("\n===== 用户列表 =====")
            print(f"{'账号':<10} {'用户名':<10} {'密码':<10} {'角色类型(1-4)':<10}")
            print("-" * 45)
            for user in users:
                print(f"{user[0]:<10} {user[1]:<10} {user[2]:<10} {user[3]:<10}")
        except pymysql.MySQLError as e:
            print(f"❌ 查询失败：{e}")
        finally:
            self._close_db()

    def add_user(self):
        """新增用户（包含user_name字段）"""
        try:
            self._connect_db()
            account = input("请输入新用户账号：")
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if self.cursor.fetchone():
                print("❌ 该账号已存在")
                return
            user_name = input("请输入用户名：")
            password = input("请输入密码：")
            role_type = int(input("请输入角色类型(1-4)："))
            
            if role_type not in [1,2,3,4]:
                print("❌ 角色类型必须是1-4（1=学生，2=辅导员，3=讲师，4=管理员）")
                return
            sql = """
            INSERT INTO user (user_account, user_name, user_password, role_type) 
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(sql, (account, user_name, password, role_type))
            self.conn.commit()
            print("✅ 用户新增成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 新增失败：{e}")
        except ValueError:
            print("❌ 角色类型必须是数字")
        finally:
            self._close_db()

    def update_user(self):
        """修改用户信息（支持修改user_name、密码、角色）"""
        try:
            self._connect_db()
            account = input("请输入要修改的用户账号：")
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if not self.cursor.fetchone():
                print("❌ 该账号不存在")
                return
            new_name = input("请输入新用户名（不修改按回车）：")
            new_password = input("请输入新密码（不修改按回车）：")
            new_role = input("请输入新角色类型(1-4，不修改按回车)：")
            
            update_fields = []
            params = []
            if new_name:
                update_fields.append("user_name = %s")
                params.append(new_name)
            if new_password:
                update_fields.append("user_password = %s")
                params.append(new_password)
            if new_role:
                new_role = int(new_role)
                if new_role not in [1,2,3,4]:
                    print("❌ 角色类型必须是1-4")
                    return
                update_fields.append("role_type = %s")
                params.append(new_role)
            if not update_fields:
                print("📌 未输入任何修改内容")
                return
            sql = f"UPDATE user SET {', '.join(update_fields)} WHERE user_account = %s"
            params.append(account)
            self.cursor.execute(sql, params)
            self.conn.commit()
            print("✅ 用户修改成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 修改失败：{e}")
        except ValueError:
            print("❌ 角色类型必须是数字")
        finally:
            self._close_db()

    def delete_user(self):
        """删除用户"""
        try:
            self._connect_db()
            account = input("请输入要删除的用户账号：")
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if not self.cursor.fetchone():
                print("❌ 该账号不存在")
                return
            confirm = input(f"确定要删除账号 {account} 吗？(y/n)：")
            if confirm.lower() != 'y':
                print("📌 已取消删除")
                return
            self.cursor.execute("DELETE FROM user WHERE user_account = %s", (account,))
            self.conn.commit()
            print("✅ 用户删除成功")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"❌ 删除失败：{e}")
        finally:
            self._close_db()

    def show_menu(self):
        """管理员操作菜单"""
        while True:
            print("\n===== 管理员操作中心 =====")
            print("1. 查看所有用户")
            print("2. 新增用户")
            print("3. 修改用户信息")
            print("4. 删除用户")
            print("5. 退出管理员界面")
            choice = input("请选择操作(1-5)：")
            if choice == '1':
                self.show_all_users()
            elif choice == '2':
                self.add_user()
            elif choice == '3':
                self.update_user()
            elif choice == '4':
                self.delete_user()
            elif choice == '5':
                print("👋 退出管理员界面")
                break
            else:
                print("❌ 无效选择，请输入1-5")