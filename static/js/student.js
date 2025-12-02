// ========== 全局变量 ==========
let allCourses = [];
let leaveRecords = [];
let attachmentFile = null;
let currentLeaveFilter = 'all'; // 当前请假记录筛选状态

// ========== 佐证文件预览 ==========
function previewAttachment(input) {
  if (!input.files || !input.files[0]) return;
  
  attachmentFile = input.files[0];
  const fileName = attachmentFile.name;
  const isPdf = fileName.toLowerCase().endsWith('.pdf');
  
  document.getElementById('previewFileName').textContent = fileName;
  document.getElementById('attachmentPreview').classList.remove('hidden');
  
  const iconEl = document.getElementById('previewIcon');
  if (isPdf) {
    iconEl.innerHTML = '<i class="fa-solid fa-file-pdf text-red-500"></i>';
    iconEl.className = 'w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center';
    document.getElementById('previewImage').classList.add('hidden');
  } else {
    iconEl.innerHTML = '<i class="fa-solid fa-image text-blue-500"></i>';
    iconEl.className = 'w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center';
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = document.getElementById('previewImage');
      img.src = e.target.result;
      img.classList.remove('hidden');
    };
    reader.readAsDataURL(attachmentFile);
  }
}

function clearAttachment() {
  attachmentFile = null;
  document.getElementById('attachmentFile').value = '';
  document.getElementById('attachmentPreview').classList.add('hidden');
  document.getElementById('previewImage').classList.add('hidden');
}

async function uploadAttachment(leaveId) {
  if (!attachmentFile || !leaveId) return;
  
  const formData = new FormData();
  formData.append('file', attachmentFile);
  formData.append('leave_id', leaveId);
  
  try {
    const res = await fetch('/api/leave/upload_attachment', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!data.success) {
      console.error('上传佐证文件失败:', data.message);
    }
  } catch (err) {
    console.error('上传佐证文件异常:', err);
  }
}

// ========== 页面切换 ==========
function switchPage(pageName) {
  document.querySelectorAll('.page-content').forEach(page => page.classList.remove('active'));
  const targetPage = document.getElementById(`page-${pageName}`);
  if (targetPage) targetPage.classList.add('active');
  
  // 更新导航菜单样式
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('text-primary', 'bg-white', 'shadow-md');
    item.classList.add('text-gray-600');
  });
  const activeNav = document.querySelector(`.nav-item[data-page="${pageName}"]`);
  if (activeNav) {
    activeNav.classList.add('text-primary', 'bg-white', 'shadow-md');
    activeNav.classList.remove('text-gray-600');
  }
  
  if (pageName === 'records') loadLeaveRecords();
  else if (pageName === 'chat') loadChatContacts();
  else if (pageName === 'profile') loadProfileInfo();
  else if (pageName === 'notifications') loadNotifications();
}

// ========== Toast 提示 ==========
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `fixed top-20 left-1/2 -translate-x-1/2 px-6 py-3 rounded-xl shadow-lg z-50 transition-opacity ${type === 'success' ? 'bg-primary text-white' : 'bg-red-500 text-white'}`;
  toast.style.opacity = '1';
  setTimeout(() => { toast.style.opacity = '0'; }, 3000);
}

// ========== 退出登录 ==========
function handleLogout() {
  if (confirm('确定要退出登录吗？')) {
    fetch('/api/logout', { method: 'POST' })
      .then(() => window.location.href = '/login')
      .catch(() => window.location.href = '/login');
  }
}

// ========== 加载课程 ==========
async function loadCourses() {
  try {
    const res = await fetch('/api/courses');
    const data = await res.json();
    if (data.success) {
      allCourses = data.data || [];
      updateCourseSelects();
    }
  } catch (err) {
    console.error('加载课程失败:', err);
  }
}

function updateCourseSelects() {
  const options = allCourses.length > 0
    ? '<option value="">请选择课程</option>' + allCourses.map(c => `<option value="${c.course_id}">${c.course_id} - ${c.course_name || ''}</option>`).join('')
    : '<option value="">暂无可选课程</option>';
  document.querySelectorAll('.course-select').forEach(select => { select.innerHTML = options; });
}

// ========== 加载教师 ==========
async function loadTeachersForSelect(courseId, teacherSelect) {
  try {
    const url = courseId ? `/api/course_teachers?course_id=${encodeURIComponent(courseId)}` : '/api/teachers';
    const res = await fetch(url);
    const data = await res.json();
    if (data.success && data.data && data.data.length > 0) {
      teacherSelect.innerHTML = '<option value="">请选择教师</option>' + data.data.map(t => `<option value="${t.teacher_id}">${t.teacher_id} - ${t.teacher_name || ''}</option>`).join('');
    } else {
      teacherSelect.innerHTML = '<option value="">暂无可选教师</option>';
    }
  } catch (err) {
    teacherSelect.innerHTML = '<option value="">加载失败</option>';
  }
}

// ========== 课程行管理 ==========
function addCourseRow() {
  const container = document.getElementById('courseTeacherContainer');
  const newRow = document.createElement('div');
  newRow.className = 'course-teacher-row flex items-center gap-2';
  newRow.innerHTML = `
    <select class="course-select flex-1 px-4 py-2.5 rounded-xl border border-gray-200 input-focus text-sm">
      ${allCourses.length > 0 ? '<option value="">请选择课程</option>' + allCourses.map(c => `<option value="${c.course_id}">${c.course_id} - ${c.course_name || ''}</option>`).join('') : '<option value="">暂无可选课程</option>'}
    </select>
    <select class="teacher-select flex-1 px-4 py-2.5 rounded-xl border border-gray-200 input-focus text-sm"><option value="">请先选择课程</option></select>
    <button type="button" class="add-course-btn w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center"><i class="fas fa-plus"></i></button>
    <button type="button" class="remove-course-btn w-10 h-10 rounded-xl bg-red-100 text-red-500 flex items-center justify-center"><i class="fas fa-minus"></i></button>
  `;
  container.appendChild(newRow);
  bindRowEvents(newRow);
  updateButtonVisibility();
}

function removeCourseRow(row) {
  if (document.querySelectorAll('.course-teacher-row').length > 1) {
    row.remove();
    updateButtonVisibility();
  }
}

function updateButtonVisibility() {
  const rows = document.querySelectorAll('.course-teacher-row');
  document.querySelectorAll('.add-course-btn').forEach((btn, i) => { btn.style.display = i === rows.length - 1 ? 'flex' : 'none'; });
  document.querySelectorAll('.remove-course-btn').forEach(btn => { btn.style.display = rows.length > 1 ? 'flex' : 'none'; });
}

function bindRowEvents(row) {
  const courseSelect = row.querySelector('.course-select');
  const teacherSelect = row.querySelector('.teacher-select');
  courseSelect.addEventListener('change', () => loadTeachersForSelect(courseSelect.value, teacherSelect));
  row.querySelector('.add-course-btn').addEventListener('click', addCourseRow);
  row.querySelector('.remove-course-btn').addEventListener('click', () => removeCourseRow(row));
}

// ========== 提交请假 ==========
async function submitLeave(e) {
  e.preventDefault();
  const startTime = document.getElementById('startTime').value;
  const endTime = document.getElementById('endTime').value;
  const leaveReason = document.getElementById('leaveReason').value.trim();
  const leaveType = document.getElementById('leaveType').value;
  
  const pairs = [];
  document.querySelectorAll('.course-teacher-row').forEach(row => {
    const courseId = row.querySelector('.course-select').value;
    const teacherId = row.querySelector('.teacher-select').value;
    if (courseId && teacherId) pairs.push({ course_id: courseId, teacher_id: teacherId });
  });
  
  if (pairs.length === 0 || !startTime || !endTime || !leaveReason) {
    showToast('请填写完整的请假信息', 'error');
    return;
  }
  
  const submitBtn = document.getElementById('submitBtn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>提交中...';
  
  try {
    const res = await fetch('/api/student/leave', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        course_teacher_pairs: pairs,
        start_time: startTime.replace('T', ' ') + ':00',
        end_time: endTime.replace('T', ' ') + ':00',
        leave_reason: leaveReason,
        leave_type: leaveType
      })
    });
    const data = await res.json();
    if (data.success) {
      // 如果有附件，上传附件
      if (attachmentFile && data.leave_id) {
        await uploadAttachment(data.leave_id);
      }
      showToast('请假提交成功！');
      document.getElementById('leaveForm').reset();
      clearAttachment();
      loadLeaveRecords();
    } else {
      showToast(data.message || '提交失败', 'error');
    }
  } catch (err) {
    showToast('提交异常，请重试', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>提交请假申请';
  }
}

// ========== 加载请假记录 ==========
async function loadLeaveRecords() {
  const container = document.getElementById('leaveRecordsContainer');
  container.innerHTML = '<div class="text-center py-10 text-gray-400"><i class="fas fa-spinner fa-spin"></i> 加载中...</div>';
  
  try {
    const res = await fetch('/api/student/leave_records');
    const data = await res.json();
    if (data.success && data.data && data.data.length > 0) {
      leaveRecords = data.data;
      // 应用当前筛选
      filterLeaveRecords(currentLeaveFilter);
      renderRecentLeaves(data.data.slice(0, 3));
      updateStats();
    } else {
      leaveRecords = [];
      container.innerHTML = '<div class="text-center py-10 text-gray-400"><i class="fas fa-inbox"></i> 暂无请假记录</div>';
      document.getElementById('recent-leaves').innerHTML = '<div class="text-center py-6 text-gray-400">暂无记录</div>';
      updateStats();
    }
  } catch (err) {
    container.innerHTML = '<div class="text-center py-10 text-red-400"><i class="fas fa-exclamation-circle"></i> 加载失败</div>';
  }
}

function renderRecords(records, container) {
  document.getElementById('records-count').textContent = records.length;
  container.innerHTML = records.map((record, index) => {
    const statusClass = record.approval_status === '已批准' ? 'bg-green-100 text-green-600' : record.approval_status === '已驳回' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600';
    const statusIcon = record.approval_status === '已批准' ? 'fa-check' : record.approval_status === '已驳回' ? 'fa-xmark' : 'fa-clock';
    const leaveType = record.sort || '事假';
    const approverInfo = record.approver_name ? `<p class="text-xs text-gray-400 mt-1"><i class="fa-solid fa-user-check mr-1"></i>审批人：${record.approver_name}</p>` : '';
    const exportBtn = record.approval_status === '已批准' ? `
      <button onclick="exportLeaveSlip(${index})" class="ml-2 px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-100 text-blue-600 hover:bg-blue-500 hover:text-white transition-all flex items-center">
        <i class="fa-solid fa-file-export mr-1.5"></i>导出假条
      </button>
    ` : '';
    const detailBtn = `
      <button onclick="viewLeaveDetail(${record.leave_id})" class="ml-2 px-3 py-1.5 rounded-xl text-xs font-bold bg-gray-100 text-gray-600 hover:bg-gray-500 hover:text-white transition-all flex items-center">
        <i class="fa-solid fa-eye mr-1.5"></i>详情
      </button>
    `;
    return `
      <div class="p-5 rounded-2xl bg-white/50 hover:bg-white hover:shadow-lg transition-all duration-300 border border-white/50 group">
        <div class="flex items-start justify-between mb-2">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
              <i class="fa-solid fa-file-lines text-primary text-lg"></i>
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <p class="font-bold text-gray-800">${formatCourseInfo(record.course_id)}</p>
                <span class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">${leaveType}</span>
              </div>
              <p class="text-sm text-gray-500 flex items-center mt-1">
                <i class="fa-solid fa-calendar-days mr-1.5"></i>${formatDateTime(record.start_time)} 至 ${formatDateTime(record.end_time)}
              </p>
              ${approverInfo}
            </div>
          </div>
          <div class="flex items-center">
            <span class="px-3 py-1.5 rounded-xl text-xs font-bold ${statusClass} flex items-center">
              <i class="fa-solid ${statusIcon} mr-1.5"></i>${record.approval_status}
            </span>
            ${detailBtn}
            ${exportBtn}
          </div>
        </div>
        <p class="text-sm text-gray-600 ml-16">${record.leave_reason || '无'}</p>
      </div>
    `;
  }).join('');
}

function renderRecentLeaves(records) {
  const container = document.getElementById('recent-leaves');
  if (!records || records.length === 0) {
    container.innerHTML = '<div class="text-center py-8 text-gray-400"><i class="fa-solid fa-inbox text-3xl mb-2"></i><p>暂无请假记录</p></div>';
    return;
  }
  container.innerHTML = records.map(record => {
    const statusClass = record.approval_status === '已批准' ? 'bg-green-100 text-green-600' : record.approval_status === '已驳回' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600';
    const statusIcon = record.approval_status === '已批准' ? 'fa-check' : record.approval_status === '已驳回' ? 'fa-xmark' : 'fa-clock';
    const courseName = record.course_names || formatCourseInfo(record.course_id);
    const leaveReason = record.leave_reason ? (record.leave_reason.length > 20 ? record.leave_reason.substring(0, 20) + '...' : record.leave_reason) : '';
    return `
      <div class="p-4 rounded-xl bg-white/50 hover:bg-white hover:shadow-md transition-all group">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
              <i class="fa-solid fa-file-lines text-primary"></i>
            </div>
            <div>
              <p class="font-medium text-gray-800">${courseName}</p>
              <p class="text-xs text-gray-400">${formatDateTime(record.start_time)}</p>
            </div>
          </div>
          <span class="px-2.5 py-1 rounded-lg text-xs font-bold ${statusClass} flex items-center">
            <i class="fa-solid ${statusIcon} mr-1"></i>${record.approval_status}
          </span>
        </div>
        ${leaveReason ? `<p class="text-sm text-gray-500 ml-13 pl-13" style="margin-left: 52px;"><i class="fa-solid fa-quote-left text-xs mr-1 text-gray-300"></i>${leaveReason}</p>` : ''}
      </div>
    `;
  }).join('');
}

function updateStats() {
  const total = leaveRecords.length;
  const pending = leaveRecords.filter(r => r.approval_status === '待审批').length;
  const approved = leaveRecords.filter(r => r.approval_status === '已批准').length;
  const rejected = leaveRecords.filter(r => r.approval_status === '已驳回').length;
  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-pending').textContent = pending;
  document.getElementById('stat-approved').textContent = approved;
  const rejectedEl = document.getElementById('stat-rejected');
  if (rejectedEl) rejectedEl.textContent = rejected;
  
  // 检查请假过多警告
  checkLeaveWarning();
}

// ========== 筛选请假记录 ==========
function filterLeaveRecords(status) {
  currentLeaveFilter = status;
  const container = document.getElementById('leaveRecordsContainer');
  
  // 更新按钮样式
  document.querySelectorAll('[id^="filter-"]').forEach(btn => {
    btn.classList.remove('ring-2', 'ring-primary', 'bg-primary', 'text-white');
    btn.classList.add('hover:bg-gray-200', 'hover:bg-orange-100', 'hover:bg-green-100', 'hover:bg-red-100');
  });
  
  const activeBtn = document.getElementById(`filter-${status === 'all' ? 'all' : status === '待审批' ? 'pending' : status === '已批准' ? 'approved' : 'rejected'}`);
  if (activeBtn) {
    activeBtn.classList.add('ring-2', 'ring-primary');
    if (status === 'all') {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
      activeBtn.classList.add('bg-primary', 'text-white');
    } else if (status === '待审批') {
      activeBtn.classList.remove('bg-orange-50', 'text-orange-600');
      activeBtn.classList.add('bg-orange-500', 'text-white');
    } else if (status === '已批准') {
      activeBtn.classList.remove('bg-green-50', 'text-green-600');
      activeBtn.classList.add('bg-green-500', 'text-white');
    } else if (status === '已驳回') {
      activeBtn.classList.remove('bg-red-50', 'text-red-600');
      activeBtn.classList.add('bg-red-500', 'text-white');
    }
  }
  
  if (!leaveRecords || leaveRecords.length === 0) {
    container.innerHTML = '<div class="text-center py-10 text-gray-400"><i class="fas fa-inbox"></i> 暂无请假记录</div>';
    document.getElementById('records-count').textContent = 0;
    return;
  }

  let filtered = leaveRecords;
  if (status !== 'all') {
    filtered = leaveRecords.filter(r => r.approval_status === status);
  }

  if (filtered.length === 0) {
    container.innerHTML = `<div class="text-center py-10 text-gray-400"><i class="fas fa-inbox"></i> 暂无${status === 'all' ? '' : status}记录</div>`;
    document.getElementById('records-count').textContent = 0;
  } else {
    renderRecords(filtered, container);
  }
}

// ========== 聊天功能 ==========
let chatMessages = [];
let currentContact = null; // {id, name, role, courses, avatar}
let studentAvatar = null; // 学生头像

async function loadChatContacts() {
  try {
    const res = await fetch('/api/student/chat/contacts');
    const data = await res.json();
    if (data.success && data.data) {
      studentAvatar = data.data.student_avatar;
      renderChatContacts(data.data);
    }
  } catch (err) {
    console.error('加载联系人失败:', err);
  }
}

function getAvatarHtml(avatar, name, colorClass) {
  if (avatar) {
    return `<img src="/head_image/${avatar}" class="w-full h-full rounded-full object-cover" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
            <div class="w-full h-full rounded-full bg-gradient-to-br ${colorClass} items-center justify-center text-white font-bold" style="display:none">${name.charAt(0)}</div>`;
  }
  return `<div class="w-full h-full rounded-full bg-gradient-to-br ${colorClass} flex items-center justify-center text-white font-bold">${name.charAt(0)}</div>`;
}

function renderChatContacts(contacts) {
  const counselorContainer = document.getElementById('counselor-contacts');
  const teacherContainer = document.getElementById('teacher-contacts');
  
  // 渲染辅导员
  if (contacts.counselors && contacts.counselors.length > 0) {
    counselorContainer.innerHTML = contacts.counselors.map(c => `
      <div class="contact-item p-3 rounded-xl cursor-pointer hover:bg-white hover:shadow transition-all flex items-center space-x-3"
           onclick="selectContact('${c.id}', '${c.name}', '辅导员', '', '${c.avatar || ''}')">
        <div class="w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
          ${getAvatarHtml(c.avatar, c.name, 'from-blue-400 to-blue-600')}
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-gray-800 truncate">${c.name}</p>
          <p class="text-xs text-gray-400">辅导员</p>
        </div>
      </div>
    `).join('');
  } else {
    counselorContainer.innerHTML = '<p class="text-xs text-gray-300 text-center py-2">暂无辅导员</p>';
  }
  
  // 渲染讲师
  if (contacts.teachers && contacts.teachers.length > 0) {
    teacherContainer.innerHTML = contacts.teachers.map(t => `
      <div class="contact-item p-3 rounded-xl cursor-pointer hover:bg-white hover:shadow transition-all flex items-center space-x-3"
           onclick="selectContact('${t.id}', '${t.name}', '讲师', '${t.courses || ''}', '${t.avatar || ''}')">
        <div class="w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
          ${getAvatarHtml(t.avatar, t.name, 'from-green-400 to-green-600')}
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-gray-800 truncate">${t.name}</p>
          <p class="text-xs text-gray-400 truncate">${t.courses || '讲师'}</p>
        </div>
      </div>
    `).join('');
  } else {
    teacherContainer.innerHTML = '<p class="text-xs text-gray-300 text-center py-2">暂无授课讲师</p>';
  }
}

function selectContact(id, name, role, courses, avatar) {
  currentContact = { id, name, role, courses, avatar };
  
  // 更新UI
  document.getElementById('chat-contact-name').textContent = name;
  document.getElementById('chat-contact-role').textContent = role + (courses ? ` · ${courses}` : '');
  
  // 启用输入
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('send-btn');
  input.disabled = false;
  input.placeholder = `给${name}发送消息...`;
  btn.disabled = false;
  
  // 高亮选中的联系人
  document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('bg-white', 'shadow', 'ring-2', 'ring-primary'));
  event.currentTarget.classList.add('bg-white', 'shadow', 'ring-2', 'ring-primary');
  
  // 加载聊天记录
  loadChatMessages();
}

async function loadChatMessages() {
  const container = document.getElementById('chat-messages');
  if (!currentContact) {
    container.innerHTML = `
      <div class="text-center py-16 text-gray-400">
        <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-primary/10 flex items-center justify-center">
          <i class="fa-solid fa-comments text-4xl text-primary/30"></i>
        </div>
        <p class="font-medium">选择一个联系人开始聊天</p>
      </div>
    `;
    return;
  }
  
  try {
    const res = await fetch(`/api/student/chat/messages?contact_id=${currentContact.id}&contact_role=${currentContact.role}`);
    const data = await res.json();
    if (data.success && data.data) {
      chatMessages = data.data;
      renderChatMessages();
    }
  } catch (err) {
    console.error('加载聊天记录失败:', err);
  }
}

function renderChatMessages() {
  const container = document.getElementById('chat-messages');
  if (chatMessages.length === 0) {
    container.innerHTML = `
      <div class="text-center py-10 text-gray-400">
        <i class="fas fa-comments text-3xl mb-2"></i>
        <p>开始与${currentContact ? currentContact.name : ''}的对话</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = chatMessages.map(msg => {
    const isSent = msg.sender_type === '学生';
    const avatarColor = isSent ? 'from-primary to-accent' : (currentContact.role === '辅导员' ? 'from-blue-400 to-blue-600' : 'from-green-400 to-green-600');
    const avatarLetter = isSent ? '我' : (currentContact ? currentContact.name.charAt(0) : '?');
    const avatar = isSent ? studentAvatar : (currentContact ? currentContact.avatar : null);
    
    const avatarHtml = avatar 
      ? `<img src="/head_image/${avatar}" class="w-8 h-8 rounded-full object-cover flex-shrink-0" onerror="this.outerHTML='<div class=\\'w-8 h-8 rounded-full bg-gradient-to-br ${avatarColor} flex items-center justify-center text-white text-sm font-bold flex-shrink-0\\'>${avatarLetter}</div>'">`
      : `<div class="w-8 h-8 rounded-full bg-gradient-to-br ${avatarColor} flex items-center justify-center text-white text-sm font-bold flex-shrink-0">${avatarLetter}</div>`;
    
    return `
      <div class="flex ${isSent ? 'justify-end' : 'justify-start'} mb-4 items-end gap-2">
        ${!isSent ? avatarHtml : ''}
        <div class="chat-bubble ${isSent ? 'sent' : 'received'} px-4 py-2 rounded-2xl ${isSent ? 'text-white' : 'text-gray-800'} max-w-[70%]">
          <p class="text-sm">${msg.content}</p>
          <p class="text-xs mt-1 ${isSent ? 'text-white/70' : 'text-gray-500'}">${formatDateTime(msg.created_at)}</p>
        </div>
        ${isSent ? avatarHtml : ''}
      </div>
    `;
  }).join('');
  
  container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
  if (!currentContact) {
    showToast('请先选择联系人', 'error');
    return;
  }
  
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;
  
  input.value = '';
  
  // 立即显示发送的消息
  chatMessages.push({
    content: message,
    sender_type: '学生',
    created_at: new Date().toISOString()
  });
  renderChatMessages();
  
  try {
    const res = await fetch('/api/student/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message: message,
        contact_id: currentContact.id,
        contact_role: currentContact.role
      })
    });
    const data = await res.json();
    if (!data.success) {
      showToast(data.message || '发送失败', 'error');
    }
  } catch (err) {
    showToast('发送失败，请重试', 'error');
  }
}

// ========== 工具函数 ==========
function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return '未知';
  try {
    const date = new Date(dateTimeStr);
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
  } catch { return dateTimeStr.slice(0, 16); }
}

function formatCourseInfo(courseId) {
  if (!courseId) return '无';
  const courses = courseId.split(',').map(c => c.trim());
  return courses.length > 2 ? `${courses.slice(0,2).join(', ')} 等${courses.length}门课` : courses.join(', ');
}

// ========== 个人中心 ==========
let profileContact = '';

async function loadProfileInfo() {
  try {
    // 加载学生详细信息
    const res = await fetch('/api/student/info');
    const data = await res.json();
    if (data.success && data.data) {
      const info = data.data;
      const deptEl = document.getElementById('profile-dept');
      const majorEl = document.getElementById('profile-major');
      const contactEl = document.getElementById('profile-contact');
      if (deptEl) deptEl.textContent = info.dept || '未设置';
      if (majorEl) majorEl.textContent = info.major || '未设置';
      if (contactEl) {
        profileContact = info.contact || '';
        contactEl.textContent = info.contact || '未设置';
      }
    }
  } catch (err) {
    console.error('加载个人信息失败:', err);
  }
  
  // 更新请假统计
  const total = leaveRecords.length;
  const approved = leaveRecords.filter(r => r.approval_status === '已批准').length;
  const pending = leaveRecords.filter(r => r.approval_status === '待审批').length;
  
  const totalEl = document.getElementById('profile-stat-total');
  const approvedEl = document.getElementById('profile-stat-approved');
  const pendingEl = document.getElementById('profile-stat-pending');
  
  if (totalEl) totalEl.textContent = total;
  if (approvedEl) approvedEl.textContent = approved;
  if (pendingEl) pendingEl.textContent = pending;
}

// ========== 联系方式修改 ==========
function toggleEditContact() {
  const displayEl = document.getElementById('contact-display');
  const editEl = document.getElementById('contact-edit');
  const inputEl = document.getElementById('contact-input');
  const btnEl = document.getElementById('edit-contact-btn');
  
  if (editEl.classList.contains('hidden')) {
    displayEl.classList.add('hidden');
    editEl.classList.remove('hidden');
    inputEl.value = currentContact;
    inputEl.focus();
    btnEl.classList.add('hidden');
  } else {
    displayEl.classList.remove('hidden');
    editEl.classList.add('hidden');
    btnEl.classList.remove('hidden');
  }
}

async function saveContact() {
  const inputEl = document.getElementById('contact-input');
  const newContact = inputEl.value.trim();
  
  try {
    const res = await fetch('/api/student/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contact: newContact })
    });
    const data = await res.json();
    if (data.success) {
      currentContact = newContact;
      document.getElementById('profile-contact').textContent = newContact || '未设置';
      toggleEditContact();
      showToast('联系方式已更新');
    } else {
      showToast(data.message || '更新失败', 'error');
    }
  } catch (err) {
    showToast('更新失败，请重试', 'error');
  }
}

// ========== 头像修改 ==========
async function openAvatarModal() {
  const modal = document.getElementById('avatar-modal');
  modal.classList.remove('hidden');
  
  // 加载可用头像列表
  try {
    const res = await fetch('/api/avatars');
    const data = await res.json();
    if (data.success && data.data) {
      const listEl = document.getElementById('avatar-list');
      listEl.innerHTML = data.data.map(avatar => `
        <div class="cursor-pointer rounded-xl overflow-hidden ring-2 ring-transparent hover:ring-primary transition-all" onclick="selectAvatar('${avatar}')">
          <img src="/head_image/${avatar}" class="w-full aspect-square object-cover" onerror="this.parentElement.remove()">
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('加载头像列表失败:', err);
  }
}

function closeAvatarModal() {
  document.getElementById('avatar-modal').classList.add('hidden');
}

async function selectAvatar(avatar) {
  try {
    const res = await fetch('/api/user/avatar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatar: avatar })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('profile-avatar').src = `/head_image/${avatar}`;
      document.querySelectorAll('img[alt="头像"]').forEach(img => {
        img.src = `/head_image/${avatar}`;
      });
      closeAvatarModal();
      showToast('头像已更新');
    } else {
      showToast(data.message || '更新失败', 'error');
    }
  } catch (err) {
    showToast('更新失败，请重试', 'error');
  }
}

async function uploadAvatar(input) {
  if (!input.files || !input.files[0]) return;
  
  const formData = new FormData();
  formData.append('avatar', input.files[0]);
  
  try {
    const res = await fetch('/api/user/avatar/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('profile-avatar').src = `/head_image/${data.avatar}`;
      document.querySelectorAll('img[alt="头像"]').forEach(img => {
        img.src = `/head_image/${data.avatar}`;
      });
      closeAvatarModal();
      showToast('头像上传成功');
    } else {
      showToast(data.message || '上传失败', 'error');
    }
  } catch (err) {
    showToast('上传失败，请重试', 'error');
  }
  input.value = '';
}

// ========== 请假过多警告 ==========
function checkLeaveWarning() {
  const approved = leaveRecords.filter(r => r.approval_status === '已批准').length;
  const warningEl = document.getElementById('leave-warning');
  if (warningEl) {
    if (approved >= 5) {
      warningEl.classList.remove('hidden');
      warningEl.classList.add('flex');
    } else {
      warningEl.classList.add('hidden');
      warningEl.classList.remove('flex');
    }
  }
}

// ========== 查看假条详情 ==========
async function viewLeaveDetail(leaveId) {
  try {
    const res = await fetch(`/api/leave/detail/${leaveId}`);
    const data = await res.json();
    if (!data.success) {
      showToast(data.message || '获取详情失败', 'error');
      return;
    }
    const leave = data.data;
    
    // 格式化日期
    const formatDate = (d) => {
      if (!d) return '-';
      const date = new Date(d);
      return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
    };
    
    // 状态样式
    const statusClass = leave.approval_status === '已批准' ? 'bg-green-100 text-green-600' : 
                       leave.approval_status === '已驳回' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600';
    
    // 班级名称
    const grade = leave.student_id ? leave.student_id.substring(2, 4) : '';
    const className = `${leave.major || ''}${grade}${leave.class_num || '01'}班`;
    
    // 签名显示
    const studentSignHtml = leave.student_signature ? 
      `<img src="${leave.student_signature}" class="h-12 object-contain" onerror="this.outerHTML='<span class=\\'text-gray-400\\'>未签名</span>'" />` : 
      '<span class="text-gray-400">未签名</span>';
    const counselorSignHtml = leave.counselor_signature ? 
      `<img src="${leave.counselor_signature}" class="h-12 object-contain" onerror="this.outerHTML='<span class=\\'text-gray-400\\'>未签名</span>'" />` : 
      '<span class="text-gray-400">未签名</span>';
    
    // 创建弹窗
    const modal = document.createElement('div');
    modal.id = 'leave-detail-modal';
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-auto">
        <div class="bg-gradient-to-r from-primary to-accent p-6 text-white rounded-t-2xl">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <i class="fa-solid fa-file-lines text-2xl"></i>
              </div>
              <div>
                <h2 class="text-xl font-bold">假条详情</h2>
                <p class="text-white/70 text-sm">编号: ${leave.leave_id}</p>
              </div>
            </div>
            <button onclick="closeLeaveDetailModal()" class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center hover:bg-white/30 transition-all">
              <i class="fa-solid fa-xmark text-xl"></i>
            </button>
          </div>
        </div>
        
        <div class="p-6 space-y-6">
          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 mb-1">学生姓名</p>
              <p class="font-bold text-gray-800">${leave.student_name || '-'}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 mb-1">学号</p>
              <p class="font-bold text-gray-800">${leave.student_id || '-'}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 mb-1">班级</p>
              <p class="font-bold text-gray-800">${className}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 mb-1">请假类型</p>
              <p class="font-bold text-gray-800">${leave.sort || '事假'}</p>
            </div>
          </div>
          
          <!-- 时间信息 -->
          <div class="bg-blue-50 rounded-xl p-4">
            <p class="text-xs text-blue-400 mb-2"><i class="fa-solid fa-calendar-days mr-1"></i>请假时间</p>
            <p class="font-bold text-blue-800">${formatDate(leave.start_time)} 至 ${formatDate(leave.end_time)}</p>
          </div>
          
          <!-- 课程信息 -->
          <div class="bg-purple-50 rounded-xl p-4">
            <p class="text-xs text-purple-400 mb-2"><i class="fa-solid fa-book mr-1"></i>涉及课程</p>
            <p class="font-bold text-purple-800">${leave.course_names || '-'}</p>
          </div>
          
          <!-- 请假原因 -->
          <div class="bg-gray-50 rounded-xl p-4">
            <p class="text-xs text-gray-400 mb-2"><i class="fa-solid fa-pen mr-1"></i>请假原因</p>
            <p class="text-gray-800">${leave.leave_reason || '-'}</p>
          </div>
          
          <!-- 审批状态 -->
          <div class="border-t pt-4">
            <div class="flex items-center justify-between mb-4">
              <span class="text-gray-500">审批状态</span>
              <span class="px-4 py-2 rounded-xl font-bold ${statusClass}">${leave.approval_status}</span>
            </div>
            ${leave.approver_name ? `
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500">审批人</span>
              <span class="font-bold text-gray-800">${leave.approver_name}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-500">审批时间</span>
              <span class="text-gray-600">${formatDate(leave.approval_time)}</span>
            </div>
            ` : ''}
          </div>
          
          <!-- 签名状态 -->
          <div class="border-t pt-4">
            <p class="text-sm text-gray-500 mb-3"><i class="fa-solid fa-signature mr-1"></i>签名状态</p>
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-gray-50 rounded-xl p-4 text-center">
                <p class="text-xs text-gray-400 mb-2">学生签名</p>
                ${studentSignHtml}
              </div>
              <div class="bg-gray-50 rounded-xl p-4 text-center">
                <p class="text-xs text-gray-400 mb-2">辅导员签名</p>
                ${counselorSignHtml}
              </div>
            </div>
          </div>
          
          <!-- 佐证文件 -->
          ${leave.attachment_url ? `
          <div class="border-t pt-4">
            <p class="text-sm text-gray-500 mb-3"><i class="fa-solid fa-paperclip mr-1"></i>佐证文件</p>
            <div class="bg-gray-50 rounded-xl p-4">
              ${leave.attachment_url.toLowerCase().endsWith('.pdf') ? `
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                      <i class="fa-solid fa-file-pdf text-red-500"></i>
                    </div>
                    <span class="text-gray-700">${leave.attachment || 'PDF文件'}</span>
                  </div>
                  <a href="${leave.attachment_url}" target="_blank" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/80 transition-all">
                    <i class="fa-solid fa-eye mr-1"></i>预览
                  </a>
                </div>
              ` : `
                <img src="${leave.attachment_url}" class="max-w-full max-h-64 mx-auto rounded-lg cursor-pointer hover:opacity-90 transition-all" onclick="window.open('${leave.attachment_url}', '_blank')" onerror="this.outerHTML='<span class=\\'text-gray-400\\'>文件加载失败</span>'" />
              `}
            </div>
          </div>
          ` : ''}
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeLeaveDetailModal();
    });
    
  } catch (err) {
    console.error('获取假条详情失败:', err);
    showToast('获取详情失败', 'error');
  }
}

function closeLeaveDetailModal() {
  const modal = document.getElementById('leave-detail-modal');
  if (modal) modal.remove();
}

// ========== 导出假条 ==========
async function exportLeaveSlip(index) {
  const record = leaveRecords[index];
  if (!record) {
    showToast('未找到请假记录', 'error');
    return;
  }
  
  // 获取学生信息
  try {
    const res = await fetch('/api/student/info');
    const data = await res.json();
    if (!data.success) {
      showToast('获取学生信息失败', 'error');
      return;
    }
    const studentInfo = data.data;
    const leaveId = record.leave_id;
    
    // 格式化日期
    const startDate = new Date(record.start_time);
    const endDate = new Date(record.end_time);
    const approvalDate = record.approval_time ? new Date(record.approval_time) : new Date();
    
    const formatDate = (d) => `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`;
    const formatShortDate = (d) => `${d.getMonth()+1}月${d.getDate()}日`;
    
    // 组合班级名称: 专业 + 年级(学号前2位) + 班级编号 + "班"
    const grade = studentInfo.student_id.substring(2, 4);
    const classNum = studentInfo.class_num || '01';
    const className = `${studentInfo.major || ''}${grade}${classNum}班`;
    
    // 签名图片路径: student_id_leave_id.png 和 counselor_id_leave_id.png
    const studentSignature = `/qianzi/${studentInfo.student_id}_${leaveId}.png`;
    const counselorSignature = `/qianzi/${record.approver_id}_${leaveId}.png`;
    
    // 生成假条HTML（加宽版，带签名画布）
    const slipHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>请假条 - ${studentInfo.student_name}</title>
  <style>
    @media print {
      @page { margin: 15mm; size: A4; }
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .no-print { display: none !important; }
      .signature-canvas-wrapper { display: none !important; }
    }
    * { box-sizing: border-box; }
    body {
      font-family: "SimSun", "宋体", serif;
      padding: 30px;
      max-width: 900px;
      margin: 0 auto;
      background: #fff;
    }
    .title {
      text-align: center;
      font-size: 32px;
      font-weight: bold;
      letter-spacing: 25px;
      margin-bottom: 35px;
      padding-left: 25px;
    }
    .content {
      border: 2px solid #000;
      padding: 35px 40px;
    }
    .info-row {
      display: flex;
      flex-wrap: wrap;
      margin-bottom: 20px;
      line-height: 2.2;
      font-size: 17px;
    }
    .info-item {
      margin-right: 40px;
      white-space: nowrap;
    }
    .label {
      font-weight: bold;
    }
    .underline {
      border-bottom: 1px solid #000;
      min-width: 120px;
      display: inline-block;
      text-align: center;
      padding: 0 15px;
    }
    .time-row {
      margin-bottom: 20px;
      line-height: 2.2;
      font-size: 17px;
    }
    .reason-box {
      border: 1px solid #000;
      min-height: 100px;
      padding: 18px;
      margin-top: 12px;
      line-height: 1.9;
      font-size: 16px;
    }
    .signature-section {
      margin-top: 35px;
      padding-top: 25px;
      border-top: 1px dashed #999;
    }
    .signature-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 25px;
      font-size: 17px;
      min-height: 70px;
    }
    .signature-item {
      display: flex;
      align-items: center;
    }
    .sign-img {
      height: 60px;
      max-width: 180px;
      object-fit: contain;
      margin: 0 12px;
    }
    .sign-line {
      border-bottom: 1px solid #000;
      min-width: 150px;
      min-height: 60px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin: 0 12px;
    }
    .sign-text {
      font-family: "STXingkai", "华文行楷", "KaiTi", "楷体", cursive;
      font-size: 26px;
      color: #1a1a8c;
    }
    .btn-group {
      position: fixed;
      top: 20px;
      right: 20px;
      display: flex;
      gap: 10px;
    }
    .action-btn {
      padding: 12px 20px;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 15px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      transition: all 0.2s;
    }
    .action-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    .print-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .sign-btn { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    
    /* 签名画布样式 */
    .signature-canvas-wrapper {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7);
      z-index: 1000;
      justify-content: center;
      align-items: center;
    }
    .signature-canvas-wrapper.active { display: flex; }
    .signature-panel {
      background: white;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    .signature-panel h3 {
      margin: 0 0 15px 0;
      text-align: center;
      font-size: 20px;
    }
    #signatureCanvas {
      border: 2px solid #333;
      border-radius: 8px;
      cursor: crosshair;
      background: #fefefe;
    }
    .canvas-btns {
      display: flex;
      justify-content: center;
      gap: 15px;
      margin-top: 15px;
    }
    .canvas-btn {
      padding: 10px 25px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 15px;
    }
    .canvas-btn.clear { background: #e74c3c; color: white; }
    .canvas-btn.save { background: #27ae60; color: white; }
    .canvas-btn.cancel { background: #95a5a6; color: white; }
  </style>
</head>
<body>
  <div class="btn-group no-print">
    <button class="action-btn sign-btn" onclick="openSignaturePad()">
      <i class="fa-solid fa-signature"></i> 学生签名
    </button>
    <button class="action-btn print-btn" onclick="window.print()">
      <i class="fa-solid fa-print"></i> 打印 / 保存PDF
    </button>
  </div>
  
  <div class="title">请 假 条</div>
  
  <div class="content">
    <div class="info-row">
      <div class="info-item"><span class="label">姓名：</span><span class="underline">${studentInfo.student_name}</span></div>
      <div class="info-item"><span class="label">学号：</span><span class="underline">${studentInfo.student_id}</span></div>
      <div class="info-item"><span class="label">班级：</span><span class="underline">${className}</span></div>
    </div>
    
    <div class="time-row">
      <span class="label">请假时间：</span>
      <span class="underline">${formatShortDate(startDate)}</span>
      <span style="margin: 0 8px;">至</span>
      <span class="underline">${formatShortDate(endDate)}</span>
    </div>
    
    <div style="margin-bottom: 20px;">
      <span class="label">请假原因：</span>
      <div class="reason-box">${record.leave_reason || ''}</div>
    </div>
    
    <div class="signature-section">
      <div class="signature-row">
        <div class="signature-item">
          <span class="label">学生签名：</span>
          <span class="sign-line" id="studentSignArea">
            <img src="${studentSignature}" class="sign-img" id="studentSignImg" onerror="this.style.display='none';document.getElementById('studentSignText').style.display='inline'" />
            <span class="sign-text" id="studentSignText" style="display:none">${studentInfo.student_name}</span>
          </span>
        </div>
        <div class="signature-item">
          <span>${formatDate(startDate)}</span>
        </div>
      </div>
      
      <div class="signature-row">
        <div class="signature-item">
          <span class="label">辅导员意见：</span>
          <span class="sign-line" style="min-width: 220px;"><span class="sign-text">同意</span></span>
        </div>
      </div>
      
      <div class="signature-row">
        <div class="signature-item">
          <span class="label">辅导员签名：</span>
          <span class="sign-line">
            <img src="${counselorSignature}" class="sign-img" onerror="this.style.display='none';this.nextElementSibling.style.display='inline'" />
            <span class="sign-text" style="display:none">${record.approver_name || ''}</span>
          </span>
        </div>
        <div class="signature-item">
          <span>${formatDate(approvalDate)}</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 签名画布弹窗 -->
  <div class="signature-canvas-wrapper" id="signatureWrapper">
    <div class="signature-panel">
      <h3>请在下方签名</h3>
      <canvas id="signatureCanvas" width="400" height="200"></canvas>
      <div class="canvas-btns">
        <button class="canvas-btn clear" onclick="clearSignature()">清除</button>
        <button class="canvas-btn save" onclick="saveSignature()">确认保存</button>
        <button class="canvas-btn cancel" onclick="closeSignaturePad()">取消</button>
      </div>
    </div>
  </div>
  
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  
  <script>
    const studentId = '${studentInfo.student_id}';
    const leaveId = '${leaveId}';
    let canvas, ctx, isDrawing = false, lastX = 0, lastY = 0;
    
    document.addEventListener('DOMContentLoaded', function() {
      canvas = document.getElementById('signatureCanvas');
      ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#1a1a8c';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      canvas.addEventListener('mousedown', startDrawing);
      canvas.addEventListener('mousemove', draw);
      canvas.addEventListener('mouseup', stopDrawing);
      canvas.addEventListener('mouseout', stopDrawing);
      
      // 触摸支持
      canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        lastX = touch.clientX - rect.left;
        lastY = touch.clientY - rect.top;
        isDrawing = true;
      });
      canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        if (!isDrawing) return;
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.stroke();
        lastX = x;
        lastY = y;
      });
      canvas.addEventListener('touchend', stopDrawing);
    });
    
    function startDrawing(e) {
      isDrawing = true;
      lastX = e.offsetX;
      lastY = e.offsetY;
    }
    
    function draw(e) {
      if (!isDrawing) return;
      ctx.beginPath();
      ctx.moveTo(lastX, lastY);
      ctx.lineTo(e.offsetX, e.offsetY);
      ctx.stroke();
      lastX = e.offsetX;
      lastY = e.offsetY;
    }
    
    function stopDrawing() { isDrawing = false; }
    
    function openSignaturePad() {
      document.getElementById('signatureWrapper').classList.add('active');
    }
    
    function closeSignaturePad() {
      document.getElementById('signatureWrapper').classList.remove('active');
    }
    
    function clearSignature() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    async function saveSignature() {
      const dataUrl = canvas.toDataURL('image/png');
      try {
        const res = await fetch('/api/student/save_signature', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ signature: dataUrl, leave_id: leaveId })
        });
        const result = await res.json();
        if (result.success) {
          // 更新签名图片显示
          const img = document.getElementById('studentSignImg');
          img.src = '/qianzi/' + result.filename + '?t=' + Date.now();
          img.style.display = 'inline';
          document.getElementById('studentSignText').style.display = 'none';
          closeSignaturePad();
          alert('签名保存成功！');
        } else {
          alert('保存失败: ' + result.message);
        }
      } catch (err) {
        alert('保存失败: ' + err.message);
      }
    }
  </script>
</body>
</html>
    `;
    
    // 打开新窗口显示假条
    const printWindow = window.open('', '_blank');
    printWindow.document.write(slipHtml);
    printWindow.document.close();
    
  } catch (err) {
    console.error('导出假条失败:', err);
    showToast('导出假条失败', 'error');
  }
}

// ========== 通知功能 ==========
let allNotifications = [];
let filterOptions = { courses: [], teachers: [] };

// 加载筛选选项
async function loadFilterOptions() {
  try {
    const response = await fetch('/api/student/filter_options');
    const data = await response.json();
    
    if (data.success) {
      filterOptions = data.data;
      
      // 填充课程选择框
      const courseSelect = document.getElementById('course-filter');
      courseSelect.innerHTML = '<option value="">全部课程</option>';
      filterOptions.courses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.course_id;
        option.textContent = `${course.course_name} (${course.course_id})`;
        courseSelect.appendChild(option);
      });
      
      // 填充教师选择框
      const teacherSelect = document.getElementById('teacher-filter');
      teacherSelect.innerHTML = '<option value="">全部教师</option>';
      filterOptions.teachers.forEach(teacher => {
        const option = document.createElement('option');
        option.value = teacher.teacher_id;
        option.textContent = teacher.teacher_name;
        teacherSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error('加载筛选选项失败:', error);
  }
}

// 加载通知列表
async function loadNotifications() {
  try {
    const courseFilter = document.getElementById('course-filter')?.value || '';
    const teacherFilter = document.getElementById('teacher-filter')?.value || '';
    const startDate = document.getElementById('start-date-filter')?.value || '';
    const endDate = document.getElementById('end-date-filter')?.value || '';
    
    const params = new URLSearchParams();
    if (courseFilter) params.append('course_id', courseFilter);
    if (teacherFilter) params.append('teacher_id', teacherFilter);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await fetch(`/api/student/notifications?${params}`);
    const data = await response.json();
    
    if (data.success) {
      allNotifications = data.data;
      renderNotifications();
    } else {
      showToast(data.message || '加载通知失败', 'error');
    }
  } catch (error) {
    console.error('加载通知失败:', error);
    showToast('加载通知失败', 'error');
  }
}

// 渲染通知列表
function renderNotifications() {
  const container = document.getElementById('notifications-list');
  
  if (allNotifications.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 text-gray-400">
        <i class="fa-solid fa-bell-slash text-4xl mb-4"></i>
        <p class="text-lg font-medium">暂无通知</p>
        <p class="text-sm">当前筛选条件下没有找到相关通知</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = allNotifications.map(notification => {
    const priorityClass = notification.priority === '紧急' ? 'border-red-500 bg-red-50' : 
                         notification.priority === '重要' ? 'border-orange-500 bg-orange-50' : 
                         'border-gray-200 bg-white';
    
    const priorityIcon = notification.priority === '紧急' ? 'fa-exclamation-triangle text-red-500' : 
                        notification.priority === '重要' ? 'fa-star text-orange-500' : 
                        'fa-info-circle text-blue-500';
    
    return `
      <div class="border-l-4 ${priorityClass} rounded-xl p-6 hover:shadow-lg transition-all cursor-pointer" onclick="showNotificationDetail('${notification.id}')">
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center space-x-3">
            <i class="fa-solid ${priorityIcon}"></i>
            <h4 class="font-bold text-gray-800 text-lg">${notification.title}</h4>
            ${notification.priority !== '普通' ? `<span class="px-2 py-1 rounded-full text-xs font-medium ${notification.priority === '紧急' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600'}">${notification.priority}</span>` : ''}
          </div>
          <span class="text-xs text-gray-400">${notification.create_time}</span>
        </div>
        <div class="flex items-center space-x-4 text-sm text-gray-500 mb-3">
          <span><i class="fa-solid fa-book mr-1"></i>${notification.course_name || notification.course_id}</span>
          <span><i class="fa-solid fa-user mr-1"></i>${notification.teacher_name}</span>
          <span><i class="fa-solid fa-tag mr-1"></i>${notification.notify_type}</span>
        </div>
        <p class="text-gray-600 line-clamp-2">${notification.content}</p>
      </div>
    `;
  }).join('');
}

// 显示通知详情
function showNotificationDetail(notificationId) {
  const notification = allNotifications.find(n => n.id === notificationId);
  if (!notification) return;
  
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4';
  modal.innerHTML = `
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick="this.parentElement.remove()"></div>
    <div class="relative bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
      <div class="bg-gradient-to-r from-primary to-accent p-6 text-white">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <i class="fa-solid fa-bell text-2xl"></i>
            <div>
              <h3 class="text-xl font-bold">${notification.title}</h3>
              <p class="text-white/80 text-sm">${notification.notify_type}</p>
            </div>
          </div>
          <button onclick="this.closest('.fixed').remove()" class="w-10 h-10 rounded-xl bg-white/20 hover:bg-white/30 flex items-center justify-center transition-all">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>
      <div class="p-6 overflow-y-auto max-h-96">
        <div class="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-gray-500 mb-1">课程</p>
            <p class="font-medium">${notification.course_name || notification.course_id}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-gray-500 mb-1">教师</p>
            <p class="font-medium">${notification.teacher_name}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-gray-500 mb-1">发布时间</p>
            <p class="font-medium">${notification.create_time}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-gray-500 mb-1">优先级</p>
            <p class="font-medium">${notification.priority}</p>
          </div>
        </div>
        <div class="bg-gray-50 rounded-xl p-4">
          <h4 class="font-medium text-gray-700 mb-2">通知内容</h4>
          <div class="text-gray-800 whitespace-pre-wrap">${notification.content}</div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

// 应用筛选
function applyNotificationFilters() {
  loadNotifications();
}

// 清空筛选
function clearNotificationFilters() {
  document.getElementById('course-filter').value = '';
  document.getElementById('teacher-filter').value = '';
  document.getElementById('start-date-filter').value = '';
  document.getElementById('end-date-filter').value = '';
  loadNotifications();
}

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', async () => {
  await loadCourses();
  document.querySelectorAll('.course-teacher-row').forEach(row => bindRowEvents(row));
  updateButtonVisibility();
  document.getElementById('leaveForm').addEventListener('submit', submitLeave);
  loadLeaveRecords();
  
  // 加载通知相关数据
  await loadFilterOptions();
  
  // 定期检查新消息
  setInterval(loadChatMessages, 30000); // 每30秒检查一次
});
