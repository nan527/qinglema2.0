# db_config.py
def get_db_config():
    """返回数据库连接配置"""
    return {
        "host": "10.124.43.101",
        "port": 3306,
        "user": "remote_user",
        "password": "123456",
        "database": "qing2",
        "charset": "utf8mb4"
    }