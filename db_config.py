# db_config.py
def get_db_config():
    """返回数据库连接配置"""
    return {
        "host": "192.168.5.173",
        "port": 3306,
        "user": "remote_user",
        "password": "123456",  # pymysql需要字符串，不是bytes
        "database": "qing2",
        "charset": "utf8mb4",
        "connect_timeout": 20,  # 连接超时20秒
        "read_timeout": 60,  # 读取超时60秒
        "write_timeout": 60,  # 写入超时60秒
        "autocommit": True,  # 自动提交，避免长时间事务
        "init_command": "SET SESSION wait_timeout=28800",  # 设置会话超时为8小时
        "sql_mode": "STRICT_TRANS_TABLES",  # 设置SQL模式
    }