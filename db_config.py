# db_config.py
def get_db_config():
    """返回数据库连接配置"""
    return {
        "host": "192.168.22.173",
        "port": 3306,
<<<<<<< HEAD
        "user": "remote_user",
        "password": "123456".encode('utf8'),  # 按需处理编码
=======
        "user": "root",
        "password": "123456",  # 使用字符串密码，避免编码问题
>>>>>>> 80df1667cb4604a245e42130c2fabd47dc63309e
        "database": "qing2",
        "charset": "utf8mb4"
    }