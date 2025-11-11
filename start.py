import pymysql
config = {
    "host": "localhost",       # 主机地址
    "port": 3306,              # 端口号（整数类型）
    "user": "root",            # 用户名
    "password": "123456",     # 密码
    "database": "qing2",      # 数据库名
    "charset": "utf8mb4"       # 字符集（支持中文）
}
try:
    # 建立连接
    conn = pymysql.connect(**config)
    print("数据库连接成功！")

    # 创建游标（用于执行SQL语句）
    cursor = conn.cursor()

    # 示例：执行一条查询语句（查看数据库版本）
    cursor.execute("SELECT VERSION()")
    result = cursor.fetchone()  # 获取查询结果
    print(f"MySQL 版本：{result[0]}")

except pymysql.MySQLError as e:
    print(f"数据库连接失败：{e}")

finally:
    # 关闭连接（无论成功与否都需关闭）
    if 'conn' in locals() and conn.open:
        cursor.close()
        conn.close()
        print("数据库连接已关闭")