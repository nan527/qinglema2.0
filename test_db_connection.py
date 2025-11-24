# test_db_connection.py - 测试数据库连接
import pymysql
from db_config import get_db_config

def test_connection():
    """测试数据库连接"""
    config = get_db_config()
    print("=" * 50)
    print("正在测试数据库连接...")
    print(f"主机: {config['host']}")
    print(f"端口: {config['port']}")
    print(f"用户: {config['user']}")
    print(f"数据库: {config['database']}")
    print("=" * 50)
    
    try:
        print("\n尝试连接数据库...")
        conn = pymysql.connect(**config)
        print("✅ 数据库连接成功！")
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ MySQL版本: {version[0]}")
        
        cursor.close()
        conn.close()
        print("✅ 连接已关闭")
        return True
        
    except pymysql.OperationalError as e:
        error_code = e.args[0] if e.args else "未知"
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        print(f"❌ 连接错误 (代码 {error_code}): {error_msg}")
        print("\n可能的原因：")
        print("1. 数据库服务器未启动")
        print("2. IP地址不正确")
        print("3. 网络不通或防火墙阻止")
        print("4. MySQL服务未监听该IP地址")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    test_connection()

