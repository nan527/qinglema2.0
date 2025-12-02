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

  // 显示用户名（已由模板通过 user_info.user_name 渲染，无需JS覆盖）
  displayUsername() {
    // 用户名已在模板中通过 {{ user_info.user_name }} 正确显示
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
    
    // 个人信息按钮事件
    if (document.getElementById('profileBtn')) {
      document.getElementById('profileBtn').addEventListener('click', () => {
        window.location.href = '/counselor/profile';
      });
    }
    
    // 退出按钮事件
    if (document.getElementById('logoutBtn')) {
      document.getElementById('logoutBtn').addEventListener('click', () => this.logout());
    }
    
    // 统计面板展开/收起
    if (document.getElementById('toggleStats')) {
      document.getElementById('toggleStats').addEventListener('click', () => this.toggleStatistics());
    }
    
    // 导出按钮事件
    if (document.getElementById('exportBtn')) {
      document.getElementById('exportBtn').addEventListener('click', () => this.exportToExcel());
    }
    
    // 加载头部等级徽章
    this.loadHeaderLevelBadge();
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
    
    // 加载详细统计
    this.loadDetailedStatistics();
  }

  // 加载详细统计数据并渲染图表
  async loadDetailedStatistics() {
    try {
      const response = await fetch('/api/counselor/leave_statistics');
      const result = await response.json();
      
      if (result.success) {
        const data = result.data;
        
        // 渲染状态饼图
        this.renderStatusChart(data.by_status || {});
        
        // 渲染类型柱状图
        this.renderTypeChart(data.by_type || {});
        
        // 平均天数
        if (document.getElementById('avgDays')) {
          document.getElementById('avgDays').textContent = data.avg_days || 0;
        }
        
        // 本月请假数
        const currentMonth = new Date().toISOString().slice(0, 7);
        const monthCount = (data.by_month || {})[currentMonth] || 0;
        if (document.getElementById('monthCount')) {
          document.getElementById('monthCount').textContent = monthCount;
        }
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  }

  // 渲染状态饼图
  renderStatusChart(statusData) {
    const canvas = document.getElementById('statusChart');
    if (!canvas || typeof Chart === 'undefined') return;
    
    if (this.statusChart) this.statusChart.destroy();
    
    const labels = Object.keys(statusData);
    const values = Object.values(statusData);
    const colors = labels.map(l => {
      if (l === '待审批') return '#F59E0B';
      if (l === '已批准') return '#10B981';
      if (l === '已驳回') return '#EF4444';
      return '#6B7280';
    });
    
    this.statusChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '55%',
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 6, font: { size: 10 } } } }
      }
    });
  }

  // 渲染类型柱状图
  renderTypeChart(typeData) {
    const canvas = document.getElementById('typeChart');
    if (!canvas || typeof Chart === 'undefined') return;
    
    if (this.typeChart) this.typeChart.destroy();
    
    const labels = Object.keys(typeData);
    const values = Object.values(typeData);
    
    this.typeChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{ data: values, backgroundColor: ['#0EA5E9', '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B'], borderRadius: 4, barThickness: 20 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    });
  }

  // 导出为CSV
  exportToExcel() {
    const exportStatus = document.getElementById('exportStatus');
    const status = exportStatus ? exportStatus.value : '';
    window.open(`/api/counselor/export_leaves?status=${encodeURIComponent(status)}`, '_blank');
    this.showSuccess('正在导出CSV文件...');
  }

  // 显示成功提示
  showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-20 right-6 bg-green-500 text-white px-6 py-3 rounded-xl shadow-lg z-50';
    toast.innerHTML = `<i class="fa-solid fa-check-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // 加载头部等级徽章
  async loadHeaderLevelBadge() {
    try {
      const response = await fetch('/api/counselor/approval_level');
      const result = await response.json();
      
      if (result.success) {
        const data = result.data;
        const badge = document.getElementById('headerLevelBadge');
        const icon = document.getElementById('headerLevelIcon');
        const text = document.getElementById('headerLevelText');
        
        if (badge && icon && text) {
          // 只显示青铜级及以上的等级
          if (data.monthly_count >= 10) {
            badge.style.backgroundColor = data.color + '20';
            badge.style.color = data.color;
            badge.style.border = `1px solid ${data.color}`;
            badge.classList.remove('hidden');
            badge.classList.add('flex');
            
            icon.className = `fa-solid ${data.icon} mr-1 text-xs`;
            text.textContent = data.level;
          }
        }
      }
    } catch (error) {
      console.error('加载头部等级徽章失败:', error);
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

  // 创建请假记录卡片（紧凑版）
  createLeaveCard(request) {
    const card = document.createElement('div');
    card.className = 'glass-card rounded-2xl overflow-hidden hover-lift cursor-pointer transition-all duration-300 mb-3';
    
    // 状态样式
    let statusClass = '';
    let statusBg = '';
    let statusIcon = '';
    
    switch (request.approval_status) {
      case '待审批':
        statusClass = 'text-amber-600';
        statusBg = 'bg-gradient-to-r from-amber-500 to-orange-500';
        statusIcon = 'fa-solid fa-clock';
        break;
      case '已批准':
        statusClass = 'text-emerald-600';
        statusBg = 'bg-gradient-to-r from-emerald-500 to-green-500';
        statusIcon = 'fa-solid fa-circle-check';
        break;
      case '已驳回':
        statusClass = 'text-red-500';
        statusBg = 'bg-gradient-to-r from-red-500 to-pink-500';
        statusIcon = 'fa-solid fa-circle-xmark';
        break;
    }
    
    // 计算请假天数
    const startDate = new Date(request.start_time);
    const endDate = new Date(request.end_time);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
    
    // 格式化日期（简短版）
    const formatShortDate = (dateStr) => {
      const d = new Date(dateStr);
      return `${d.getMonth()+1}/${d.getDate()}`;
    };
    
    // 获取年级信息
    const grade = request.student_id.substring(0, 4);
    
    // 请假次数样式
    let timesClass = 'text-emerald-500';
    if (request.times > 5) timesClass = 'text-red-500 font-bold';
    else if (request.times === 5) timesClass = 'text-amber-500';
    
    card.innerHTML = `
      <div class="p-4 flex items-center justify-between">
        <!-- 左侧：学生信息 -->
        <div class="flex items-center space-x-4 flex-1 min-w-0">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-lg shadow-lg flex-shrink-0">
            ${request.student_name.charAt(0)}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center space-x-2 flex-wrap">
              <span class="font-bold text-gray-800">${request.student_name}</span>
              <span class="text-xs text-gray-400">${request.student_id}</span>
              <span class="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">${grade}级</span>
            </div>
            <div class="flex items-center space-x-3 mt-1 text-sm text-gray-500">
              <span class="flex items-center"><i class="fa-solid fa-tag mr-1 text-primary/60"></i>${request.sort || '事假'}</span>
              <span class="flex items-center"><i class="fa-solid fa-calendar mr-1 text-primary/60"></i>${formatShortDate(request.start_time)}-${formatShortDate(request.end_time)} <span class="ml-1 text-primary">${days}天</span></span>
            </div>
          </div>
        </div>
        
        <!-- 中间：请假次数 -->
        <div class="hidden sm:flex flex-col items-center px-4">
          <span class="text-xs text-gray-400">本学期</span>
          <span class="${timesClass} text-lg font-bold">${request.times || 0}<span class="text-xs font-normal ml-0.5">次</span></span>
        </div>
        
        <!-- 右侧：状态和操作 -->
        <div class="flex items-center space-x-3">
          <span class="px-3 py-1.5 ${statusBg} text-white text-xs font-medium rounded-full shadow-md flex items-center">
            <i class="${statusIcon} mr-1.5"></i>${request.approval_status}
          </span>
          ${request.approval_status === '待审批' ? `
          <div class="flex space-x-2">
            <button onclick="event.stopPropagation(); approveLeave('${request.leave_id}', '${request.student_name}', ${request.times || 0})" 
                    class="w-9 h-9 rounded-xl bg-gradient-to-r from-emerald-500 to-green-500 text-white flex items-center justify-center shadow-md hover:shadow-lg hover:scale-105 transition-all" title="批准">
              <i class="fa-solid fa-check"></i>
            </button>
            <button onclick="event.stopPropagation(); showRejectModal('${request.leave_id}')" 
                    class="w-9 h-9 rounded-xl bg-gradient-to-r from-red-500 to-pink-500 text-white flex items-center justify-center shadow-md hover:shadow-lg hover:scale-105 transition-all" title="驳回">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          ` : `
          <button onclick="event.stopPropagation(); showLeaveDetail(${JSON.stringify(request).replace(/"/g, '&quot;')})" 
                  class="w-9 h-9 rounded-xl bg-gray-100 text-gray-500 flex items-center justify-center hover:bg-primary/10 hover:text-primary transition-all" title="查看详情">
            <i class="fa-solid fa-chevron-right"></i>
          </button>
          `}
        </div>
      </div>
    `;
    
    // 点击卡片查看详情
    card.addEventListener('click', () => {
      showLeaveDetail(request);
    });
    
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

  async showProfile() {
    try {
      const response = await fetch('/api/counselor/info');
      const result = await response.json();

      if (!result.success) {
        showError(result.message || '获取个人信息失败');
        return;
      }

      const info = result.data || {};
      const content = `
        <div class="space-y-3 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">工号</span><span class="font-medium">${info.counselor_id || ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">姓名</span><span class="font-medium">${info.counselor_name || ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">所属部门</span><span class="font-medium">${info.dept || ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">负责年级</span><span class="font-medium">${info.responsible_grade ? info.responsible_grade + '级' : ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">负责专业</span><span class="font-medium">${info.responsible_major || ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">联系方式</span><span class="font-medium">${info.contact || ''}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">登录密码</span><span class="font-medium">${info.password || ''}</span></div>
        </div>
      `;

      showCustomModal('个人信息', content, null, '关闭', null);
    } catch (error) {
      console.error('获取个人信息失败:', error);
      showError('获取个人信息失败，请稍后重试');
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

// 显示请假详情模态框
function showLeaveDetail(request) {
  const startDate = new Date(request.start_time);
  const endDate = new Date(request.end_time);
  const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
  
  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  };
  
  let statusBg = '', statusIcon = '';
  switch (request.approval_status) {
    case '待审批': statusBg = 'from-amber-500 to-orange-500'; statusIcon = 'fa-solid fa-clock'; break;
    case '已批准': statusBg = 'from-emerald-500 to-green-500'; statusIcon = 'fa-solid fa-circle-check'; break;
    case '已驳回': statusBg = 'from-red-500 to-pink-500'; statusIcon = 'fa-solid fa-circle-xmark'; break;
  }
  
  let timesClass = 'text-emerald-500';
  if (request.times > 5) timesClass = 'text-red-500';
  else if (request.times === 5) timesClass = 'text-amber-500';
  
  const grade = request.student_id.substring(0, 4);
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn';
  
  modal.innerHTML = `
    <div class="bg-white rounded-3xl shadow-2xl max-w-lg w-full mx-4 animate-scaleIn overflow-hidden">
      <div class="relative p-6 bg-gradient-to-r from-primary to-accent">
        <button class="close-modal absolute top-4 right-4 w-8 h-8 rounded-full bg-white/20 text-white flex items-center justify-center hover:bg-white/30"><i class="fa-solid fa-xmark"></i></button>
        <div class="flex items-center space-x-4">
          <div class="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center text-white text-2xl font-bold">${request.student_name.charAt(0)}</div>
          <div class="text-white">
            <h3 class="text-xl font-bold">${request.student_name}</h3>
            <p class="text-white/80 text-sm">${request.student_id} · ${grade}级</p>
            <p class="text-white/60 text-xs mt-1">${request.student_class || ''}</p>
          </div>
        </div>
        <span class="absolute bottom-4 right-6 px-4 py-1.5 bg-gradient-to-r ${statusBg} text-white text-sm font-medium rounded-full shadow-lg flex items-center"><i class="${statusIcon} mr-1.5"></i>${request.approval_status}</span>
      </div>
      <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-1"><i class="fa-solid fa-tag mr-1"></i>请假类型</p><p class="font-semibold text-gray-800">${request.sort || '事假'}</p></div>
          <div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-1"><i class="fa-solid fa-hashtag mr-1"></i>本学期请假</p><p class="font-semibold ${timesClass}">${request.times || 0} 次</p></div>
        </div>
        <div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-1"><i class="fa-solid fa-calendar-days mr-1"></i>请假时间</p><p class="font-semibold text-gray-800">${formatDate(request.start_time)} 至 ${formatDate(request.end_time)}</p><p class="text-sm text-primary mt-1">共 ${days} 天</p></div>
        <div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-1"><i class="fa-solid fa-comment mr-1"></i>请假原因</p><p class="text-gray-800">${request.leave_reason || '无'}</p></div>
        ${request.attachment ? `<div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-2"><i class="fa-solid fa-paperclip mr-1"></i>佐证材料</p>${request.attachment.toLowerCase().endsWith('.pdf') ? `<div class="flex items-center justify-between"><div class="flex items-center space-x-2"><div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center"><i class="fa-solid fa-file-pdf text-red-500"></i></div><span class="text-gray-700 text-sm">${request.attachment}</span></div><a href="/zhengming/${request.attachment}" target="_blank" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm hover:bg-primary/80"><i class="fa-solid fa-eye mr-1"></i>预览</a></div>` : `<img src="/zhengming/${request.attachment}" class="max-w-full max-h-48 rounded-lg cursor-pointer hover:opacity-90" onclick="window.open('/zhengming/${request.attachment}', '_blank')" onerror="this.outerHTML='<span class=text-gray-400>文件加载失败</span>'" />`}</div>` : ''}
        ${request.approval_comment ? `<div class="bg-primary/5 rounded-xl p-4 border border-primary/10"><p class="text-xs text-primary/70 mb-1"><i class="fa-solid fa-pen mr-1"></i>审批意见</p><p class="text-gray-800">${request.approval_comment}</p></div>` : ''}
        ${request.approval_status === '已批准' ? `<div class="bg-gray-50 rounded-xl p-4"><p class="text-xs text-gray-400 mb-2"><i class="fa-solid fa-signature mr-1"></i>审批人签名</p><img src="/qianzi/signature_${request.leave_id}.png" alt="签名" class="max-w-[180px] max-h-[80px] object-contain" onerror="this.outerHTML='<p class=text-gray-400>暂无签名</p>'"></div>` : ''}
      </div>
      <div class="px-6 pb-6">
        ${request.approval_status === '待审批' ? `
        <div class="flex space-x-3">
          <button class="approve-btn flex-1 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all flex items-center justify-center"><i class="fa-solid fa-check mr-2"></i>批准</button>
          <button class="reject-btn flex-1 py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all flex items-center justify-center"><i class="fa-solid fa-xmark mr-2"></i>驳回</button>
        </div>` : `<button class="close-modal w-full py-3 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition-all">关闭</button>`}
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  modal.querySelectorAll('.close-modal').forEach(btn => btn.addEventListener('click', () => document.body.removeChild(modal)));
  modal.addEventListener('click', (e) => { if (e.target === modal) document.body.removeChild(modal); });
  
  const approveBtn = modal.querySelector('.approve-btn');
  const rejectBtn = modal.querySelector('.reject-btn');
  if (approveBtn) approveBtn.addEventListener('click', () => { document.body.removeChild(modal); approveLeave(request.leave_id, request.student_name, request.times || 0); });
  if (rejectBtn) rejectBtn.addEventListener('click', () => { document.body.removeChild(modal); showRejectModal(request.leave_id); });
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
        
        <!-- 快捷意见区域 -->
        <div class="mb-4">
          <label class="block text-sm text-gray-500 mb-2">快捷意见（可多选）</label>
          <div class="flex flex-wrap gap-2" id="quickApproveOptions">
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-emerald-200 text-emerald-600 rounded-full hover:bg-emerald-50 transition-all" data-text="同意请假">
              <i class="fa-solid fa-check mr-1"></i>同意请假
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-blue-200 text-blue-600 rounded-full hover:bg-blue-50 transition-all" data-text="材料齐全">
              <i class="fa-solid fa-file-check mr-1"></i>材料齐全
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-purple-200 text-purple-600 rounded-full hover:bg-purple-50 transition-all" data-text="请注意安全">
              <i class="fa-solid fa-shield mr-1"></i>请注意安全
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-amber-200 text-amber-600 rounded-full hover:bg-amber-50 transition-all" data-text="请按时返校">
              <i class="fa-solid fa-clock mr-1"></i>请按时返校
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-cyan-200 text-cyan-600 rounded-full hover:bg-cyan-50 transition-all" data-text="请保持联系">
              <i class="fa-solid fa-phone mr-1"></i>请保持联系
            </button>
          </div>
        </div>
        
        <div>
          <label for="approvalComment" class="block text-sm text-gray-500 mb-2">审批意见（可选）</label>
          <textarea id="approvalComment" rows="3" class="w-full border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary/50" placeholder="点击上方快捷意见或手动输入..."></textarea>
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
  
  // 初始化快捷意见点击事件
  initQuickOptions('quickApproveOptions', 'approvalComment');
}

// 显示驳回模态框
function showRejectModal(requestId) {
  showCustomModal(
    '驳回请假',
    `
      <div>
        <p class="mb-4">确定要驳回这条请假申请吗？</p>
        
        <!-- 快捷意见区域 -->
        <div class="mb-4">
          <label class="block text-sm text-gray-500 mb-2">快捷意见（可多选）</label>
          <div class="flex flex-wrap gap-2" id="quickRejectOptions">
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-full hover:bg-red-50 transition-all" data-text="缺少证明材料">
              <i class="fa-solid fa-file-circle-exclamation mr-1"></i>缺少证明材料
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-amber-200 text-amber-600 rounded-full hover:bg-amber-50 transition-all" data-text="请假次数过多">
              <i class="fa-solid fa-triangle-exclamation mr-1"></i>请假次数过多
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-orange-200 text-orange-600 rounded-full hover:bg-orange-50 transition-all" data-text="请假时间过长">
              <i class="fa-solid fa-clock-rotate-left mr-1"></i>请假时间过长
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-purple-200 text-purple-600 rounded-full hover:bg-purple-50 transition-all" data-text="理由不充分">
              <i class="fa-solid fa-comment-slash mr-1"></i>理由不充分
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-blue-200 text-blue-600 rounded-full hover:bg-blue-50 transition-all" data-text="请补充相关材料">
              <i class="fa-solid fa-file-circle-plus mr-1"></i>请补充相关材料
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-pink-200 text-pink-600 rounded-full hover:bg-pink-50 transition-all" data-text="需要家长确认">
              <i class="fa-solid fa-user-check mr-1"></i>需要家长确认
            </button>
            <button type="button" class="quick-option px-3 py-1.5 text-sm border border-cyan-200 text-cyan-600 rounded-full hover:bg-cyan-50 transition-all" data-text="与课程安排冲突">
              <i class="fa-solid fa-calendar-xmark mr-1"></i>与课程安排冲突
            </button>
          </div>
        </div>
        
        <div>
          <label for="rejectComment" class="block text-sm text-gray-500 mb-2">驳回原因（必填）</label>
          <textarea id="rejectComment" rows="3" class="w-full border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary/50" placeholder="点击上方快捷意见或手动输入..." required></textarea>
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
  
  // 初始化快捷意见点击事件
  initQuickOptions('quickRejectOptions', 'rejectComment');
}

// 初始化快捷意见点击事件
function initQuickOptions(containerId, textareaId) {
  setTimeout(() => {
    const container = document.getElementById(containerId);
    const textarea = document.getElementById(textareaId);
    
    if (!container || !textarea) return;
    
    const options = container.querySelectorAll('.quick-option');
    
    options.forEach(option => {
      option.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const text = this.getAttribute('data-text');
        const isSelected = this.classList.contains('selected');
        
        if (isSelected) {
          // 取消选中 - 从文本框移除
          this.classList.remove('selected', 'ring-2', 'ring-offset-1');
          this.style.backgroundColor = '';
          
          // 从文本框中移除该意见
          let currentText = textarea.value;
          currentText = currentText.replace(text + '；', '').replace(text, '');
          // 清理多余的分号和空格
          currentText = currentText.replace(/^；+|；+$/g, '').replace(/；+/g, '；').trim();
          textarea.value = currentText;
        } else {
          // 选中 - 添加到文本框
          this.classList.add('selected', 'ring-2', 'ring-offset-1');
          
          // 根据按钮颜色设置背景
          if (this.classList.contains('text-emerald-600')) {
            this.style.backgroundColor = '#D1FAE5';
            this.classList.add('ring-emerald-400');
          } else if (this.classList.contains('text-red-600')) {
            this.style.backgroundColor = '#FEE2E2';
            this.classList.add('ring-red-400');
          } else if (this.classList.contains('text-amber-600')) {
            this.style.backgroundColor = '#FEF3C7';
            this.classList.add('ring-amber-400');
          } else if (this.classList.contains('text-orange-600')) {
            this.style.backgroundColor = '#FFEDD5';
            this.classList.add('ring-orange-400');
          } else if (this.classList.contains('text-purple-600')) {
            this.style.backgroundColor = '#EDE9FE';
            this.classList.add('ring-purple-400');
          } else if (this.classList.contains('text-blue-600')) {
            this.style.backgroundColor = '#DBEAFE';
            this.classList.add('ring-blue-400');
          } else if (this.classList.contains('text-pink-600')) {
            this.style.backgroundColor = '#FCE7F3';
            this.classList.add('ring-pink-400');
          } else if (this.classList.contains('text-cyan-600')) {
            this.style.backgroundColor = '#CFFAFE';
            this.classList.add('ring-cyan-400');
          }
          
          // 追加到文本框
          if (textarea.value.trim()) {
            textarea.value = textarea.value.trim() + '；' + text;
          } else {
            textarea.value = text;
          }
        }
      });
    });
  }, 100);
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