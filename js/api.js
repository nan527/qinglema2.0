/**
 * 接口封装：与后端Flask接口完全对齐
 */
const API = {
    // 登录接口
    login: async (account, password, roleType) => {
        try {
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_account: account,
                    user_password: password,
                    role_type: roleType
                })
            });
            
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            console.error('登录请求失败:', error);
            return { success: false, error: '网络错误，请检查后端服务是否启动' };
        }
    },

    // 获取所有用户
    getAllUsers: async () => {
        try {
            const response = await fetch('http://localhost:5000/api/users', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            console.error('获取用户列表失败:', error);
            return { success: false, error: '网络错误，请检查后端服务是否启动' };
        }
    },

    // 添加用户
    addUser: async (userData) => {
        try {
            const response = await fetch('http://localhost:5000/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            console.error('添加用户失败:', error);
            return { success: false, error: '网络错误，请检查后端服务是否启动' };
        }
    },

    // 更新用户
    updateUser: async (account, userData) => {
        try {
            const response = await fetch(`http://localhost:5000/api/users/${account}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            console.error('更新用户失败:', error);
            return { success: false, error: '网络错误，请检查后端服务是否启动' };
        }
    },

    // 删除用户
    deleteUser: async (account) => {
        try {
            const response = await fetch(`http://localhost:5000/api/users/${account}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            return { success: response.ok, data: await response.json() };
        } catch (error) {
            console.error('删除用户失败:', error);
            return { success: false, error: '网络错误，请检查后端服务是否启动' };
        }
    }
};