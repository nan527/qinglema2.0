document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginMessage = document.getElementById('loginMessage');
    
    // 检查是否已登录（已登录直接跳转到管理员页面）
    if (localStorage.getItem('token')) {
        window.location.href = 'admin.html';
        return;
    }

    // 登录表单提交事件
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // 阻止表单默认提交
        
        // 获取表单数据
        const account = document.getElementById('userAccount').value.trim();
        const password = document.getElementById('userPassword').value.trim();
        const roleType = parseInt(document.getElementById('roleType').value);
        
        // 表单验证
        if (!account || !password || isNaN(roleType)) {
            showMessage('请填写完整且有效的登录信息', 'error');
            return;
        }
        
        // 调用登录接口
        const result = await API.login(account, password, roleType);
        
        // 处理登录结果
        if (result.success && result.data.success) {
            // 登录成功：保存用户信息和token
            localStorage.setItem('token', result.data.data.token);
            localStorage.setItem('userInfo', JSON.stringify(result.data.data));
            
            // 仅管理员可进入管理界面
            if (result.data.data.role_type === 4) {
                showMessage('登录成功，正在跳转...', 'success');
                setTimeout(() => {
                    window.location.href = 'admin.html';
                }, 1500);
            } else {
                showMessage('您没有管理员权限，无法进入管理界面', 'error');
            }
        } else {
            // 登录失败：显示错误信息
            const errorMsg = result.data?.message || '登录失败，请检查账号、密码或身份类型';
            showMessage(errorMsg, 'error');
        }
    });
    
    /**
     * 显示消息提示
     * @param {string} text - 消息内容
     * @param {string} type - 消息类型（error/success）
     */
    function showMessage(text, type = 'error') {
        loginMessage.textContent = text;
        loginMessage.className = `message ${type}-message`;
        loginMessage.style.display = 'block';
        
        // 3秒后自动隐藏
        setTimeout(() => {
            loginMessage.style.display = 'none';
        }, 3000);
    }
});