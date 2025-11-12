// 公共工具函数（被其他模块调用）
const common = {
  // 显示提示框
  showToast(message, isSuccess = true) {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastMessage = document.getElementById('toast-message');
    
    toastMessage.textContent = message;
    toastIcon.className = isSuccess ? 'fa fa-check-circle text-success mr-2' : 'fa fa-exclamation-circle text-danger mr-2';
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg transform transition-transform duration-300 z-50 flex items-center ${isSuccess ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`;
    toast.style.transform = 'translateX(0)';
    
    setTimeout(() => {
      toast.style.transform = 'translateX(calc(100% + 20px))';
    }, 3000);
  },

  // 角色类型映射（全局可用）
  roleMap: {
    1: '学生',
    2: '辅导员',
    3: '讲师',
    4: '管理员'
  }
};