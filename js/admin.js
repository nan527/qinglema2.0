document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态：未登录则跳转到登录页
    const token = localStorage.getItem('token');
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!token || !userInfo || userInfo.role_type !== 4) {
        window.location.href = 'index.html';
        return;
    }
    
    // DOM元素获取
    const refreshUsersBtn = document.getElementById('refreshUsersBtn');
    const addUserBtn = document.getElementById('addUserBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const usersTableBody = document.getElementById('usersTableBody');
    const operationMessage = document.getElementById('operationMessage');
    const userModal = document.getElementById('userModal');
    const modalTitle = document.getElementById('modalTitle');
    const userForm = document.getElementById('userForm');
    const closeModalBtn = document.getElementById('closeModal');
    const cancelModalBtn = document.getElementById('cancelModal');
    const editAccountInput = document.getElementById('editAccount');
    const modalUserAccount = document.getElementById('modalUserAccount');
    const modalUserName = document.getElementById('modalUserName');
    const modalUserPassword = document.getElementById('modalUserPassword');
    const modalRoleType = document.getElementById('modalRoleType');
    
    // 角色类型映射（用于显示）
    const roleMap = {
        1: '学生',
        2: '辅导员',
        3: '讲师',
        4: '管理员'
    };
    
    // 事件监听绑定
    refreshUsersBtn.addEventListener('click', loadAllUsers);
    addUserBtn.addEventListener('click', openAddUserModal);
    logoutBtn.addEventListener('click', handleLogout);
    closeModalBtn.addEventListener('click', closeModal);
    cancelModalBtn.addEventListener('click', closeModal);
    userForm.addEventListener('submit', handleFormSubmit);
    
    // 页面加载完成后，默认加载用户列表
    loadAllUsers();
    
    /**
     * 加载所有用户列表
     */
    async function loadAllUsers() {
        // 显示加载状态
        usersTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">加载中...</td></tr>';
        
        // 调用接口获取用户列表
        const result = await API.getAllUsers();
        
        if (result.success && result.data.success) {
            const users = result.data.data;
            renderUsersTable(users);
        } else {
            const errorMsg = result.data?.message || '获取用户列表失败';
            usersTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px; color: #dc2626;">${errorMsg}</td></tr>`;
            showMessage(errorMsg, 'error');
        }
    }
    
    /**
     * 渲染用户表格
     * @param {Array} users - 用户列表数据
     */
    function renderUsersTable(users) {
        if (!users || users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">暂无用户数据</td></tr>';
            return;
        }
        
        // 拼接表格内容
        let tableHtml = '';
        users.forEach(user => {
            tableHtml += `
                <tr>
                    <td>${user.user_account}</td>
                    <td>${user.user_name}</td>
                    <td>${user.user_password}</td>
                    <td>${roleMap[user.role_type]}(${user.role_type})</td>
                    <td class="action-buttons">
                        <button class="action-btn edit-btn" data-account="${user.user_account}">编辑</button>
                        <button class="action-btn delete-btn" data-account="${user.user_account}">删除</button>
                    </td>
                </tr>
            `;
        });
        
        usersTableBody.innerHTML = tableHtml;
        
        // 为编辑和删除按钮绑定事件
        bindActionButtons();
    }
    
    /**
     * 绑定表格操作按钮事件
     */
    function bindActionButtons() {
        // 编辑按钮事件
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const account = btn.dataset.account;
                openEditUserModal(account);
            });
        });
        
        // 删除按钮事件
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const account = btn.dataset.account;
                confirmDeleteUser(account);
            });
        });
    }
    
    /**
     * 打开新增用户模态框
     */
    function openAddUserModal() {
        modalTitle.textContent = '新增用户';
        editAccountInput.value = ''; // 清空编辑标识
        userForm.reset(); // 重置表单
        modalUserAccount.disabled = false; // 新增时账号可编辑
        userModal.style.display = 'flex'; // 显示模态框
    }
    
    /**
     * 打开编辑用户模态框
     * @param {string} account - 要编辑的用户账号
     */
    async function openEditUserModal(account) {
        // 获取所有用户数据，找到要编辑的用户
        const result = await API.getAllUsers();
        if (result.success && result.data.success) {
            const user = result.data.data.find(u => u.user_account === account);
            if (!user) {
                showMessage('未找到该用户数据', 'error');
                return;
            }
            
            // 填充表单数据
            modalTitle.textContent = '编辑用户';
            editAccountInput.value = account; // 存储编辑标识
            modalUserAccount.value = user.user_account;
            modalUserAccount.disabled = true; // 编辑时账号不可修改
            modalUserName.value = user.user_name;
            modalUserPassword.value = user.user_password;
            modalRoleType.value = user.role_type;
            
            // 显示模态框
            userModal.style.display = 'flex';
        }
    }
    
    /**
     * 关闭模态框
     */
    function closeModal() {
        userModal.style.display = 'none';
    }
    
    /**
     * 处理表单提交（新增/编辑用户）
     * @param {Event} e - 提交事件
     */
    async function handleFormSubmit(e) {
        e.preventDefault(); // 阻止表单默认提交
        
        // 获取表单数据
        const account = modalUserAccount.value.trim();
        const userName = modalUserName.value.trim();
        const password = modalUserPassword.value.trim();
        const roleType = parseInt(modalRoleType.value);
        const editAccount = editAccountInput.value.trim();
        
        // 表单验证
        if (!account || !userName || !password || isNaN(roleType)) {
            showMessage('请填写完整且有效的用户信息', 'error');
            return;
        }
        
        // 构造用户数据
        const userData = {
            user_account: account,
            user_name: userName,
            user_password: password,
            role_type: roleType
        };
        
        let result;
        if (editAccount) {
            // 编辑用户：调用更新接口
            result = await API.updateUser(editAccount, userData);
        } else {
            // 新增用户：调用添加接口
            result = await API.addUser(userData);
        }
        
        // 处理提交结果
        if (result.success && result.data.success) {
            showMessage(result.data.message, 'success');
            closeModal(); // 关闭模态框
            loadAllUsers(); // 刷新用户列表
        } else {
            const errorMsg = result.data?.message || (editAccount ? '修改用户失败' : '新增用户失败');
            showMessage(errorMsg, 'error');
        }
    }
    
    /**
     * 确认删除用户
     * @param {string} account - 要删除的用户账号
     */
    async function confirmDeleteUser(account) {
        if (confirm(`确定要删除账号【${account}】的用户吗？此操作不可恢复！`)) {
            const result = await API.deleteUser(account);
            
            if (result.success && result.data.success) {
                showMessage(result.data.message, 'success');
                loadAllUsers(); // 刷新用户列表
            } else {
                const errorMsg = result.data?.message || '删除用户失败';
                showMessage(errorMsg, 'error');
            }
        }
    }
    
    /**
     * 处理退出登录
     */
    function handleLogout() {
        if (confirm('确定要退出登录吗？')) {
            // 清除本地存储的用户信息和token
            localStorage.removeItem('token');
            localStorage.removeItem('userInfo');
            // 跳转到登录页
            window.location.href = 'index.html';
        }
    }
    
    /**
     * 显示操作消息提示
     * @param {string} text - 消息内容
     * @param {string} type - 消息类型（error/success）
     */
    function showMessage(text, type = 'error') {
        operationMessage.textContent = text;
        operationMessage.className = `message ${type}-message`;
        operationMessage.style.display = 'block';
        
        // 3秒后自动隐藏
        setTimeout(() => {
            operationMessage.style.display = 'none';
        }, 3000);
    }
});