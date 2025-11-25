// counselor.js - 辅导员页面的模块化JavaScript

class CounselorApp {
  constructor() {
    // 全局变量
    this.allLeaveRequests = [];
    this.currentFilter = 'all';
    this.currentPage = 1;
    this.pageSize = 10;
  }

  // 初始化应用
  async init() {
    // 显示用户名
    this.displayUsername();
    
    // 初始化事件监听
    this.initEventListeners();
    
    // 检查登录状态
    await this.checkLoginStatus();
    
    // 从URL获取初始筛选类型
    this.setInitialFilter();
    
    // 加载请假数据
    await this.loadLeaveRequests();
  }
  
  // 设置初始筛选类型
  setInitialFilter() {
    // 从URL路径获取当前筛选类型
    const path = window.location.pathname;
    if (path.includes('/pending')) {
      this.currentFilter = '待审批';
    } else if (path.includes('/approved')) {
      this.currentFilter = '已批准';
    } else if (path.includes('/rejected')) {
      this.currentFilter = '已驳回';
    } else {
      this.currentFilter = 'all';
    }
  }

  // 显示用户名
  displayUsername() {
    const usernameElement = document.getElementById('counselorName');
    if (usernameElement) {
      // 从localStorage获取用户名，实际应用中应从会话或cookie获取
      const username = localStorage.getItem('counselorName') || '辅导员';
      usernameElement.textContent = username;
    }
  }

  // 初始化事件监听
  initEventListeners() {
    // 筛选按钮事件 - 使用URL导航而不是AJAX加载
    if (document.getElementById('filterAll')) {
      document.getElementById('filterAll').addEventListener('click', () => {
        window.location.href = '/counselor/all';
      });
    }
    if (document.getElementById('filterPending')) {
      document.getElementById('filterPending').addEventListener('click', () => {
        window.location.href = '/counselor/pending';
      });
    }
    if (document.getElementById('filterApproved')) {
      document.getElementById('filterApproved').addEventListener('click', () => {
        window.location.href = '/counselor/approved';
      });
    }
    if (document.getElementById('filterRejected')) {
      document.getElementById('filterRejected').addEventListener('click', () => {
        window.location.href = '/counselor/rejected';
      });
    }
    
    // 搜索输入事件
    if (document.getElementById('searchInput')) {
      document.getElementById('searchInput').addEventListener('input', this.debounce(() => this.searchLeaveRequests(), 300));
    }
    
    // 年级筛选事件
    if (document.getElementById('gradeSelect')) {
      document.getElementById('gradeSelect').addEventListener('change', () => this.filterByGrade());
    }
    
    // 分页按钮事件
    if (document.getElementById('prevPage')) {
      document.getElementById('prevPage').addEventListener('click', () => this.goToPrevPage());
    }
    if (document.getElementById('nextPage')) {
      document.getElementById('nextPage').addEventListener('click', () => this.goToNextPage());
    }
    
    // 退出按钮事件
    if (document.getElementById('logoutBtn')) {
      document.getElementById('logoutBtn').addEventListener('click', () => this.logout());
    }
  }

  // 检查登录状态
  async checkLoginStatus() {
    try {
      const response = await fetch('/api/check_login');
      const result = await response.json();
      
      if (!result.logged_in) {
        // 未登录，跳转到登录页
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('检查登录状态失败:', error);
      window.location.href = '/login';
    }
  }

  // 退出登录
  async logout() {
    if (confirm('确定要退出登录吗？')) {
      try {
        // 调用后端退出API
        const response = await fetch('/api/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        
        // 无论API返回什么，都清除本地数据并跳转到登录页面
        // 清除localStorage中的数据
        localStorage.removeItem('counselorName');
        localStorage.removeItem('counselorId');
        // 直接跳转到登录页面
        window.location.href = '/login';
      } catch (error) {
        console.error('退出登录时发生错误:', error);
        // 即使发生错误，也要尝试退出
        localStorage.removeItem('counselorName');
        localStorage.removeItem('counselorId');
        window.location.href = '/login';
      }
    }
  }

  // 加载请假数据
  async loadLeaveRequests() {
    try {
      const response = await fetch('/api/counselor/leave_requests');
      if (!response.ok) {
        throw new Error('网络响应异常');
      }
      const data = await response.json();
      
      // 存储所有请假记录
      this.allLeaveRequests = data.data || [];
      
      // 更新统计数据
      this.updateStatistics();
      
      // 更新年级选择
      this.updateGradeSelect();
      
      // 渲染请假记录
      this.renderLeaveRequests();
    } catch (error) {
      console.error('加载请假数据失败:', error);
      const container = document.getElementById('leaveListContainer');
      if (container) {
        container.innerHTML = `
          <div class="text-center py-8 text-gray-500">
            <i class="fa fa-exclamation-circle text-2xl mb-2"></i>
            <p>加载数据失败，请刷新页面重试</p>
          </div>
        `;
      }
    }
  }

  // 更新统计数据
  updateStatistics() {
    const pendingCount = this.allLeaveRequests.filter(req => req.approval_status === '待审批').length;
    const approvedCount = this.allLeaveRequests.filter(req => req.approval_status === '已批准').length;
    const rejectedCount = this.allLeaveRequests.filter(req => req.approval_status === '已驳回').length;
    const totalCount = this.allLeaveRequests.length;
    
    if (document.getElementById('pendingCount')) {
      document.getElementById('pendingCount').textContent = pendingCount;
    }
    if (document.getElementById('approvedCount')) {
      document.getElementById('approvedCount').textContent = approvedCount;
    }
    if (document.getElementById('rejectedCount')) {
      document.getElementById('rejectedCount').textContent = rejectedCount;
    }
    if (document.getElementById('totalCount')) {
      document.getElementById('totalCount').textContent = totalCount;
    }
  }

  // 更新年级选择
  updateGradeSelect() {
    const gradeSelect = document.getElementById('gradeSelect');
    if (!gradeSelect) return;
    
    // 从请假记录中提取所有年级（学生ID前4位）
    const grades = [...new Set(this.allLeaveRequests.map(req => req.student_id.substring(0, 4)))];
    grades.sort();
    
    // 添加年级选项
    grades.forEach(grade => {
      const option = document.createElement('option');
      option.value = grade;
      option.textContent = grade + '级';
      gradeSelect.appendChild(option);
    });
  }

  // 筛选请假记录
  filterLeaveRequests(filterType) {
    this.currentFilter = filterType;
    this.currentPage = 1;
    
    // 更新按钮样式
    const buttons = [
      { id: 'filterAll', type: 'all', bg: 'bg-primary', text: 'text-white', hover: '' },
      { id: 'filterPending', type: '待审批', bg: 'bg-warning/10', text: 'text-warning', hover: 'hover:bg-warning/20' },
      { id: 'filterApproved', type: '已批准', bg: 'bg-success/10', text: 'text-success', hover: 'hover:bg-success/20' },
      { id: 'filterRejected', type: '已驳回', bg: 'bg-danger/10', text: 'text-danger', hover: 'hover:bg-danger/20' }
    ];
    
    buttons.forEach(btn => {
      const element = document.getElementById(btn.id);
      if (element) {
        if (filterType === btn.type) {
          element.className = `px-4 py-2 ${btn.bg} ${btn.text} rounded-lg btn-hover`;
        } else {
          element.className = `px-4 py-2 ${btn.bg} ${btn.text} rounded-lg ${btn.hover} transition-colors btn-hover`;
        }
      }
    });
    
    // 渲染筛选后的请假记录
    this.renderLeaveRequests();
  }

  // 搜索请假记录
  searchLeaveRequests() {
    this.currentPage = 1;
    this.renderLeaveRequests();
  }

  // 按年级筛选
  filterByGrade() {
    this.currentPage = 1;
    this.renderLeaveRequests();
  }

  // 渲染请假记录
  renderLeaveRequests() {
    const container = document.getElementById('leaveListContainer');
    if (!container) return;
    
    // 获取搜索关键词
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const selectedGrade = document.getElementById('gradeSelect')?.value || '';
    
    // 应用筛选条件
    let filteredRequests = [...this.allLeaveRequests];
    
    // 应用状态筛选
    if (this.currentFilter !== 'all') {
      filteredRequests = filteredRequests.filter(req => req.approval_status === this.currentFilter);
    }
    
    // 应用搜索筛选
    if (searchTerm) {
      filteredRequests = filteredRequests.filter(req => 
        req.student_name.toLowerCase().includes(searchTerm) || 
        req.student_id.includes(searchTerm)
      );
    }
    
    // 应用年级筛选
    if (selectedGrade) {
      filteredRequests = filteredRequests.filter(req => 
        req.student_id.startsWith(selectedGrade)
      );
    }
    
    // 按开始时间倒序排序
    filteredRequests.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
    
    // 计算分页
    const totalPages = Math.ceil(filteredRequests.length / this.pageSize);
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    const currentRequests = filteredRequests.slice(startIndex, endIndex);
    
    // 更新记录数量显示
    if (document.getElementById('recordCount')) {
      document.getElementById('recordCount').textContent = `${filteredRequests.length}条记录`;
    }
    
    // 更新分页按钮状态
    this.updatePagination(totalPages);
    
    // 渲染请假记录卡片
    if (currentRequests.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          <i class="fa fa-folder-open-o text-2xl mb-2"></i>
          <p>暂无符合条件的请假记录</p>
        </div>
      `;
      return;
    }
    
    container.innerHTML = '';
    currentRequests.forEach(request => {
      const card = this.createLeaveCard(request);
      container.appendChild(card);
    });
  }

  // 创建请假记录卡片
  createLeaveCard(request) {
    const card = document.createElement('div');
    card.className = 'border border-gray-200 rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300 mb-4 bg-white';
    
    // 状态样式
    let statusClass = '';
    let statusIcon = '';
    
    switch (request.approval_status) {
      case '待审批':
        statusClass = 'bg-warning/10 text-warning';
        statusIcon = 'fa-clock-o';
        break;
      case '已批准':
        statusClass = 'bg-success/10 text-success';
        statusIcon = 'fa-check-circle';
        break;
      case '已驳回':
        statusClass = 'bg-danger/10 text-danger';
        statusIcon = 'fa-times-circle';
        break;
    }
    
    // 计算请假天数
    const startDate = new Date(request.start_time);
    const endDate = new Date(request.end_time);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
    
    // 格式化日期
    const formattedStartDate = this.formatDate(request.start_time);
    const formattedEndDate = this.formatDate(request.end_time);
    const formattedSubmitTime = this.formatSubmitTime(request.start_time); // 使用开始时间作为提交时间显示
    
    // 获取年级信息（学生ID前4位）
    const grade = request.student_id.substring(0, 4);
    
    // 请假次数颜色标识
    let leaveCountClass = '';
    if (request.times > 5) {
      leaveCountClass = 'text-danger';
    } else if (request.times === 5) {
      leaveCountClass = 'text-warning';
    } else if (request.times < 5 && request.times > 0) {
      leaveCountClass = 'text-success';
    }
    
    card.innerHTML = `
      <div class="p-5">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h4 class="text-lg font-semibold flex items-center">
              <span>${request.student_name}</span>
              <span class="ml-2 text-sm text-gray-500">${request.student_id}</span>
              <span class="ml-2 text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">${grade}级</span>
            </h4>
            <p class="text-sm text-gray-500 mt-1">${request.student_class}</p>
          </div>
          <span class="px-3 py-1 rounded-full text-sm ${statusClass} flex items-center">
            <i class="fa ${statusIcon} mr-1"></i>${request.approval_status}
          </span>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p class="text-sm text-gray-500">请假类型</p>
              <p class="text-base">${request.sort || '事假'}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">请假时间</p>
              <p class="text-base">${formattedStartDate} 至 ${formattedEndDate} <span class="text-sm text-gray-500">(${days}天)</span></p>
            </div>
            <div>
              <p class="text-sm text-gray-500">请假原因</p>
              <p class="text-base">${request.leave_reason}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">本学期请假次数</p>
              <p class="text-base ${leaveCountClass}">${request.times || 0}次</p>
            </div>
        </div>
        
        <!-- 移除重复的请假事由显示 -->
        
        <div class="flex justify-between items-center mt-4">
            <div class="text-sm text-gray-500">
              提交时间: ${formattedSubmitTime}
            </div>
        </div>
        
        ${request.approval_status === '待审批' ? `
        <div class="flex justify-end space-x-3">
          <button onclick="approveLeave('${request.leave_id}', '${request.student_name}', ${request.times || 0})" class="px-4 py-2 bg-success text-white rounded-lg btn-hover flex items-center">
            <i class="fa fa-check mr-1"></i>批准
          </button>
          <button onclick="showRejectModal('${request.leave_id}')" class="px-4 py-2 bg-danger text-white rounded-lg btn-hover flex items-center">
            <i class="fa fa-times mr-1"></i>驳回
          </button>
        </div>
        ` : ''}
        
        ${(request.approval_status === '已批准' || request.approval_status === '已驳回') && request.approval_comment ? `
        <div class="mt-4 p-3 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-500">审批意见</p>
          <p class="text-base mt-1">${request.approval_comment}</p>
        </div>
        ` : ''}
        
        ${request.approval_status === '已批准' ? `
        <div class="mt-4">
          <p class="text-sm text-gray-500">审批人签名</p>
          <div class="mt-1">
            <img src="/qianzi/signature_${request.leave_id}.png" 
                 alt="审批人签名" 
                 class="max-w-[200px] max-h-[100px] object-contain border border-gray-200 rounded p-1"
                 onError="this.onerror=null;this.src='/static/images/default_signature.png';this.alt='暂无签名';" />
          </div>
        </div>
        ` : ''}
      </div>
    `;
    
    return card;
  }

  // 格式化日期
  formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // 格式化提交时间
  formatSubmitTime(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }

  // 更新分页
  updatePagination(totalPages) {
    // 更新分页显示
    if (document.getElementById('currentPageDisplay')) {
      document.getElementById('currentPageDisplay').textContent = this.currentPage;
    }
    if (document.getElementById('totalPagesDisplay')) {
      document.getElementById('totalPagesDisplay').textContent = totalPages;
    }
    
    // 更新按钮状态
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    
    if (prevPageBtn) {
      if (this.currentPage <= 1) {
        prevPageBtn.disabled = true;
        prevPageBtn.className = 'px-4 py-2 border border-gray-200 rounded-lg text-gray-400 cursor-not-allowed';
      } else {
        prevPageBtn.disabled = false;
        prevPageBtn.className = 'px-4 py-2 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors btn-hover';
      }
    }
    
    if (nextPageBtn) {
      if (this.currentPage >= totalPages) {
        nextPageBtn.disabled = true;
        nextPageBtn.className = 'px-4 py-2 border border-gray-200 rounded-lg text-gray-400 cursor-not-allowed';
      } else {
        nextPageBtn.disabled = false;
        nextPageBtn.className = 'px-4 py-2 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors btn-hover';
      }
    }
  }

  // 上一页
  goToPrevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.renderLeaveRequests();
    }
  }

  // 下一页
  goToNextPage() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const selectedGrade = document.getElementById('gradeSelect')?.value || '';
    
    // 获取当前筛选条件下的记录数
    let filteredRequests = [...this.allLeaveRequests];
    if (this.currentFilter !== 'all') {
      filteredRequests = filteredRequests.filter(req => req.approval_status === this.currentFilter);
    }
    if (searchTerm) {
      filteredRequests = filteredRequests.filter(req => 
        req.student_name.toLowerCase().includes(searchTerm) || 
        req.student_id.includes(searchTerm)
      );
    }
    if (selectedGrade) {
      filteredRequests = filteredRequests.filter(req => 
        req.student_id.startsWith(selectedGrade)
      );
    }
    
    const totalPages = Math.ceil(filteredRequests.length / this.pageSize);
    
    if (this.currentPage < totalPages) {
      this.currentPage++;
      this.renderLeaveRequests();
    }
  }

  // 防抖函数
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func.apply(this, args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

// 显示自定义模态框
function showCustomModal(title, content, onConfirm, confirmText = '确定', cancelText = '取消') {
  // 创建模态框
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn';
  // 根据是否有取消按钮生成不同的HTML
  const hasCancelButton = cancelText !== null && cancelText !== undefined && cancelText !== '';
  
  modal.innerHTML = `
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 transform transition-all duration-300 animate-scaleIn">
      <div class="p-6 border-b border-gray-200">
        <h3 class="text-lg font-semibold">${title}</h3>
      </div>
      <div class="p-6">
        ${content}
      </div>
      <div class="p-4 ${hasCancelButton ? 'flex justify-end space-x-3' : 'flex justify-center'} border-t border-gray-200">
        ${hasCancelButton ? `
        <button id="modalCancel" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
          ${cancelText}
        </button>
        ` : ''}
        <button id="modalConfirm" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors duration-200">
          ${confirmText}
        </button>
      </div>
    </div>
  `;
  
  // 添加到页面
  document.body.appendChild(modal);
  
  // 绑定事件
  if (cancelText !== null && cancelText !== undefined && cancelText !== '') {
    modal.querySelector('#modalCancel').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
  } else {
    // 如果没有取消按钮，将确认按钮居中
    const buttonContainer = modal.querySelector('.flex.justify-end');
    if (buttonContainer) {
      buttonContainer.className = 'p-4 flex justify-center border-t border-gray-200';
    }
  }
  
  modal.querySelector('#modalConfirm').addEventListener('click', () => {
    if (onConfirm) {
      onConfirm();
    }
    document.body.removeChild(modal);
  });
  
  // 点击外部关闭
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      document.body.removeChild(modal);
    }
  });
}

// 显示错误消息
function showError(message) {
  showCustomModal(
    '错误',
    `
      <div class="text-center">
        <i class="fa fa-exclamation-circle text-4xl mb-3"></i>
        <p class="text-lg">${message}</p>
      </div>
    `,
    null,
    '确定',
    '取消'
  );
}

// 批准请假入口函数，处理请假次数警告
function approveLeave(leaveId, studentName, times) {
  if (times > 5) {
    // 请假次数大于5，显示警告确认
    showCustomModal(
      '批准确认',
      `<p class="text-center mb-2">${studentName} 已请假${times}次</p><p class="text-center">超过5次限制，确认继续批准吗？</p>`,
      async () => {
        showApproveModal(leaveId);
      },
      '确认批准',
      '取消'
    );
  } else {
    // 正常确认
    showApproveModal(leaveId);
  }
}

// 显示批准模态框
function showApproveModal(requestId) {
  showCustomModal(
    '批准请假',
    `
      <div>
        <p class="mb-4">确定要批准这条请假申请吗？</p>
        <div>
          <label for="approvalComment" class="block text-sm text-gray-500 mb-2">审批意见（可选）</label>
          <textarea id="approvalComment" rows="3" class="w-full border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary/50"></textarea>
        </div>
      </div>
    `,
    async () => {
      const comment = document.getElementById('approvalComment').value;
      await approveLeaveRequest(requestId, comment);
    },
    '批准',
    '取消'
  );
}

// 显示驳回模态框
function showRejectModal(requestId) {
  showCustomModal(
    '驳回请假',
    `
      <div>
        <p class="mb-4">确定要驳回这条请假申请吗？</p>
        <div>
          <label for="rejectComment" class="block text-sm text-gray-500 mb-2">驳回原因（必填）</label>
          <textarea id="rejectComment" rows="3" class="w-full border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary/50" required></textarea>
        </div>
      </div>
    `,
    async () => {
      const comment = document.getElementById('rejectComment').value;
      if (!comment.trim()) {
        showError('请填写驳回原因');
        return;
      }
      await rejectLeaveRequest(requestId, comment);
    },
    '驳回',
    '取消'
  );
}

// 批准请假请求 - 先跳转到签字页面
async function approveLeaveRequest(requestId, comment) {
  try {
    // 保存必要信息到localStorage，以便签字完成后使用
    localStorage.setItem('pending_leave_approval', JSON.stringify({
      leave_id: requestId,
      comment: comment,
      action: 'approve'
    }));
    
    // 跳转到签字页面
    window.location.href = '/qianzi';
  } catch (error) {
    console.error('跳转到签字页面失败:', error);
    showError('操作失败，请稍后重试');
  }
}

// 驳回请假请求
async function rejectLeaveRequest(requestId, comment) {
  try {
    const response = await fetch('/api/counselor/approve_leave', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        leave_id: requestId,
        action: 'reject',
        comment: comment
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 重新加载数据
      const app = window.counselorApp;
      if (app) {
        await app.loadLeaveRequests();
        showCustomModal('成功', '<p class="text-center">请假已成功驳回</p>', null, '确定', null);
      }
    } else {
      showError(data.message || '驳回失败，请重试');
    }
  } catch (error) {
    console.error('驳回请假失败:', error);
    showError('网络错误，请稍后重试');
  }
}

// 添加必要的CSS动画样式
const style = document.createElement('style');
style.textContent = `
  .animate-fadeIn {
    animation: fadeIn 0.2s ease-out;
  }
  
  .animate-scaleIn {
    animation: scaleIn 0.2s ease-out;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  @keyframes scaleIn {
    from {
      transform: scale(0.95);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  .btn-hover {
    transition: all 0.2s ease;
  }
  
  .btn-hover:hover {
    transform: translateY(-1px);
  }
  
  .bg-primary {
    background-color: #165DFF;
  }
  
  .bg-success {
    background-color: #52C41A;
  }
  
  .bg-danger {
    background-color: #F5222D;
  }
  
  .bg-warning {
    background-color: #FAAD14;
  }
`;
document.head.appendChild(style);

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
  // 初始化应用
  window.counselorApp = new CounselorApp();
  window.counselorApp.init();
});