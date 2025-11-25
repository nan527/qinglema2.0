# db_config.py
def get_db_config():
    """返回数据库连接配置"""
    return {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "123456",  # 使用字符串密码，避免编码问题
        "database": "qing2",
        "charset": "utf8mb4"
    }