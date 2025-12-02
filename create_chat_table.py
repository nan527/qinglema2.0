import pymysql
from db_config import get_db_config

try:
    conn = pymysql.connect(**get_db_config())
    cursor = conn.cursor()
    
    # 创建聊天消息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id VARCHAR(20) NOT NULL,
            receiver_id VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            sender_type ENUM('student', 'counselor') NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sender_receiver (sender_id, receiver_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    conn.commit()
    print("聊天消息表创建成功")
    
    # 插入一些测试数据
    cursor.execute("""
        INSERT INTO chat_messages (sender_id, receiver_id, content, sender_type, created_at)
        VALUES 
        ('20130101', '202301010101', '你好，有什么问题可以随时联系我。', 'counselor', NOW() - INTERVAL 1 DAY),
        ('202301010101', '20130101', '老师您好，我想咨询一下请假的相关事宜。', 'student', NOW() - INTERVAL 23 HOUR),
        ('20130101', '202301010101', '好的，请假需要提前申请，并说明原因。', 'counselor', NOW() - INTERVAL 22 HOUR)
    """)
    
    conn.commit()
    print("测试数据插入成功")
    
    conn.close()
    
except Exception as e:
    print(f"创建表失败: {e}")
