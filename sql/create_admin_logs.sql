-- 创建管理员操作日志表
CREATE TABLE IF NOT EXISTS admin_operation_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    admin_account VARCHAR(50) NOT NULL COMMENT '操作管理员账号',
    admin_name VARCHAR(100) COMMENT '操作管理员姓名',
    operation_type VARCHAR(20) NOT NULL COMMENT '操作类型：ADD/UPDATE/DELETE/VIEW',
    target_user_account VARCHAR(50) COMMENT '目标用户账号',
    target_user_name VARCHAR(100) COMMENT '目标用户姓名',
    target_user_role VARCHAR(20) COMMENT '目标用户角色：student/counselor/teacher/admin',
    operation_details TEXT COMMENT '操作详情JSON',
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    status VARCHAR(20) DEFAULT 'SUCCESS' COMMENT '操作状态：SUCCESS/FAILED',
    error_message TEXT COMMENT '错误信息（如果失败）',
    INDEX idx_admin_account (admin_account),
    INDEX idx_operation_time (operation_time),
    INDEX idx_operation_type (operation_type),
    INDEX idx_target_user (target_user_account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员操作日志表';
