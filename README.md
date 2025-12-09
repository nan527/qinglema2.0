<div align="center">
  <img src="static/images/logo.png" alt="请了吗" width="120">
  
  # 请了吗 - 智能学生请假管理系统
  
  **Qinglema - Smart Student Leave Management System**
  
  ![Version](https://img.shields.io/badge/版本-V0.1-purple)
  ![Python](https://img.shields.io/badge/Python-3.8+-blue)
  ![Flask](https://img.shields.io/badge/Flask-2.0+-green)
  ![License](https://img.shields.io/badge/License-MIT-yellow)
  
  山西大学 · 软件工程课程设计项目
</div>

---

## 📖 项目简介

**请了吗**是一款面向高校的智能学生请假管理系统，旨在解决传统纸质请假流程繁琐、效率低下的问题。系统采用现代化Web技术栈，提供学生、教师、辅导员、管理员四端协同的一站式请假解决方案，并集成AI智能助手，为用户提供便捷的咨询服务。

### ✨ 核心特性

- 🎯 **多角色协同** - 学生、教师、辅导员、管理员四端统一管理
- 🤖 **AI智能助手** - 集成小龙助手，智能解答请假相关问题
- 📱 **响应式设计** - 完美适配PC端和移动端
- 🔔 **实时通知** - 请假状态实时更新推送
- 📊 **数据统计** - 可视化请假数据分析
- 🔐 **安全可靠** - 完善的权限控制和数据保护

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端展示层                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ 学生端  │ │ 教师端  │ │辅导员端 │ │管理员端 │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
├─────────────────────────────────────────────────────────┤
│                    Flask 后端服务                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  路由控制   │ │  业务逻辑   │ │  AI服务     │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
├─────────────────────────────────────────────────────────┤
│                      数据存储层                          │
│  ┌─────────────────────────────────────────────┐       │
│  │              MySQL 数据库                    │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端框架** | Python Flask |
| **数据库** | MySQL |
| **前端框架** | HTML5 + TailwindCSS |
| **图标库** | Font Awesome 6 |
| **AI服务** | 火山引擎 DeepSeek API |
| **部署** | 支持本地/云服务器部署 |

---

## 📁 项目结构

```
qinglema2.0/
├── app.py                 # Flask主应用入口
├── db_config.py           # 数据库配置
├── server.py              # 域名服务启动脚本
├── requirements.txt       # pip依赖配置
├── environment.yaml       # conda环境配置
│
├── templates/             # 页面模板
│   ├── login.html         # 登录页面
│   ├── student/           # 学生端页面
│   ├── teacher/           # 教师端页面
│   ├── counselor/         # 辅导员端页面
│   └── admin/             # 管理员端页面
│
├── static/                # 静态资源
│   ├── images/            # 图片(logo、吉祥物)
│   ├── js/                # JavaScript文件
│   └── webfonts/          # 字体文件
│
├── terminal/              # 命令行版本
│   ├── main.py            # 终端入口
│   ├── login.py           # 登录模块
│   ├── student_operation.py
│   ├── teacher_operation.py
│   ├── counselor_operation.py
│   └── admin_operation.py
│
├── sql/                   # 数据库脚本
│   ├── create_chat_table.py
│   └── create_admin_logs.sql
│
├── domain/                # 域名服务配置
│   └── cloudflared.exe    # Cloudflare Tunnel
│
├── data/                  # 数据目录
│   └── avatars/           # 用户头像存储
│
└── docs/                  # 项目文档
    └── 工作记录功能说明.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- 现代浏览器 (Chrome/Firefox/Edge)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/qinglema2.0.git
cd qinglema2.0
```

2. **安装依赖**
```bash
pip install flask pymysql requests
```

3. **配置数据库**
```python
# 编辑 db_config.py
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'qinglema',
    'charset': 'utf8mb4'
}
```

4. **启动服务**
```bash
python app.py
```

5. **访问系统**
```
http://localhost:5000
```

---

## 👥 功能模块

### 学生端
- 📝 提交请假申请
- 📋 查看请假记录
- 🔍 跟踪审批进度
- 💬 与教师/辅导员沟通
- 🤖 AI助手咨询

### 教师端
- ✅ 审批学生请假
- 👀 查看学生考勤
- 💬 与学生沟通
- 📊 课程请假统计
- 🤖 AI助手支持

### 辅导员端
- ✅ 审批请假申请
- 📊 班级请假统计
- 👥 学生信息管理
- 💬 消息通知
- 🤖 AI助手支持

### 管理员端
- 👤 用户管理（增删改查）
- 📋 系统日志查看
- ⚙️ 系统设置
- 📊 全局数据统计

---

## 👨‍💻 开发团队

| 成员 | 职责 |
|------|------|
| **白岩凯** | 教师端开发与优化，系统相关论文撰写 |
| **尚余强** | 前端开发主管，管理员端设计与实现 |
| **彭越** | 辅导员端负责人，域名注册与维护，整体项目框架搭建 |
| **周脉** | 教师端辅助开发，项目演示文稿设计，数据库逻辑优化 |

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 📞 联系我们

- 📧 邮箱：2686786328@qq.com
- 🏫 单位：山西大学

---

<div align="center">
  <p>© 2024 山西大学 · 请了吗开发团队</p>
  <p>Made with ❤️ in Shanxi University</p>
</div>