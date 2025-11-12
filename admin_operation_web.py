# admin_operation_web.py（Web接口专用版）
import pymysql
from db_config import get_db_config

class AdminOperationWeb:
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
        """查询所有用户（返回字典列表，适配前端）"""
        try:
            self._connect_db()
            self.cursor.execute("""
                SELECT user_account, user_name, user_password, role_type 
                FROM user
            """)
            users = self.cursor.fetchall()
            # 转换为字典列表，前端可直接通过键名访问
            user_list = [
                {
                    "user_account": user[0],
                    "user_name": user[1],
                    "user_password": user[2],
                    "role_type": user[3]
                }
                for user in users
            ]
            return {"success": True, "data": user_list, "message": "查询成功"}
        except pymysql.MySQLError as e:
            error_msg = f"查询失败：{str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
        finally:
            self._close_db()

    def add_user(self, account, user_name, password, role_type):
        """新增用户（接收前端参数，返回结果字典）"""
        try:
            self._connect_db()
            # 检查账号是否已存在
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if self.cursor.fetchone():
                return {"success": False, "message": "该账号已存在"}
            
            # 角色类型校验
            if role_type not in [1, 2, 3, 4]:
                return {"success": False, "message": "角色类型必须是1-4（1=学生，2=辅导员，3=讲师，4=管理员）"}
            
            # 插入数据
            sql = """
            INSERT INTO user (user_account, user_name, user_password, role_type) 
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(sql, (account, user_name, password, role_type))
            self.conn.commit()
            return {"success": True, "message": "用户新增成功"}
        except pymysql.MySQLError as e:
            self.conn.rollback()
            error_msg = f"新增失败：{str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
        finally:
            self._close_db()

    def update_user(self, account, new_name=None, new_password=None, new_role=None):
        """修改用户信息（支持部分字段修改）"""
        try:
            self._connect_db()
            # 检查账号是否存在
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if not self.cursor.fetchone():
                return {"success": False, "message": "该账号不存在"}
            
            # 构建更新字段
            update_fields = []
            params = []
            if new_name:
                update_fields.append("user_name = %s")
                params.append(new_name)
            if new_password:
                update_fields.append("user_password = %s")
                params.append(new_password)
            if new_role is not None:
                if new_role not in [1, 2, 3, 4]:
                    return {"success": False, "message": "角色类型必须是1-4"}
                update_fields.append("role_type = %s")
                params.append(new_role)
            
            if not update_fields:
                return {"success": False, "message": "未输入任何修改内容"}
            
            # 执行更新
            sql = f"UPDATE user SET {', '.join(update_fields)} WHERE user_account = %s"
            params.append(account)
            self.cursor.execute(sql, params)
            self.conn.commit()
            return {"success": True, "message": "用户修改成功"}
        except pymysql.MySQLError as e:
            self.conn.rollback()
            error_msg = f"修改失败：{str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
        finally:
            self._close_db()

    def delete_user(self, account):
        """删除用户（接收账号参数）"""
        try:
            self._connect_db()
            # 检查账号是否存在
            self.cursor.execute("SELECT * FROM user WHERE user_account = %s", (account,))
            if not self.cursor.fetchone():
                return {"success": False, "message": "该账号不存在"}
            
            # 执行删除
            self.cursor.execute("DELETE FROM user WHERE user_account = %s", (account,))
            self.conn.commit()
            return {"success": True, "message": "用户删除成功"}
        except pymysql.MySQLError as e:
            self.conn.rollback()
            error_msg = f"删除失败：{str(e)}"
            print(error_msg)
            return {"success": False, "message": error_msg}
        finally:
            self._close_db()