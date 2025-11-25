# db_config.py
def get_db_config():
    """返回数据库连接配置"""
    return {
        "host": "192.168.22.173",
        "port": 3306,
        "user": "remote_user",
        "password": "123456".encode('utf8'),  # 按需处理编码
        "database": "qing2",
        "charset": "utf8mb4"
    }