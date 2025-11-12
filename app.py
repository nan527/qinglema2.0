# app.py（Flask Web服务，对接前端所有功能）
from flask import Flask, request, jsonify
from flask_cors import CORS
from login import login  # 导入修改后的login函数（接收参数版）
from admin_operation_web import AdminOperationWeb  # 导入Web版管理员操作类

app = Flask(__name__)
CORS(app)  # 允许跨域请求（前端和后端不同端口时必需）
admin_web = AdminOperationWeb()  # 初始化Web版管理员操作实例

# 1. 登录接口（对接前端登录页）
@app.route('/api/login', methods=['POST'])
def api_login():
    # 接收前端传递的JSON数据
    data = request.get_json()
    account = data.get('user_account')
    password = data.get('user_password')
    role_type = data.get('role_type')
    
    # 校验必填参数
    if not all([account, password, role_type]):
        return jsonify({
            "success": False,
            "message": "账号、密码、身份类型不能为空"
        }), 400
    
    # 调用login函数校验（login.py已修改为接收参数）
    user_info = login(account, password, role_type)
    if user_info:
        # 登录成功，返回前端需要的token和用户信息
        return jsonify({
            "success": True,
            "data": {
                **user_info,
                "token": f"admin_token_{account}"  # 简单生成token，实际可替换为JWT
            },
            "message": "登录成功"
        })
    else:
        return jsonify({
            "success": False,
            "message": "账号、密码或身份类型不匹配"
        }), 401

# 2. 获取所有用户接口（对接前端"查看所有用户"）
@app.route('/api/users', methods=['GET'])
def get_all_users():
    result = admin_web.show_all_users()
    return jsonify(result)

# 3. 新增用户接口（对接前端"新增用户"）
@app.route('/api/users', methods=['POST'])
def add_new_user():
    data = request.get_json()
    account = data.get('user_account')
    user_name = data.get('user_name')
    password = data.get('user_password')
    role_type = data.get('role_type')
    
    # 校验必填参数
    if not all([account, user_name, password, role_type]):
        return jsonify({
            "success": False,
            "message": "账号、用户名、密码、角色类型不能为空"
        }), 400
    
    # 转换角色类型为整数
    try:
        role_type = int(role_type)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "角色类型必须是数字"
        }), 400
    
    result = admin_web.add_user(account, user_name, password, role_type)
    return jsonify(result)

# 4. 修改用户接口（对接前端"编辑用户"）
@app.route('/api/users/<account>', methods=['PUT'])
def update_exist_user(account):
    data = request.get_json()
    new_name = data.get('user_name')
    new_password = data.get('user_password')
    new_role = data.get('role_type')
    
    # 转换角色类型（可选参数，存在时才转换）
    if new_role is not None:
        try:
            new_role = int(new_role)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "角色类型必须是数字"
            }), 400
    
    result = admin_web.update_user(
        account=account,
        new_name=new_name,
        new_password=new_password,
        new_role=new_role
    )
    return jsonify(result)

# 5. 删除用户接口（对接前端"删除用户"）
@app.route('/api/users/<account>', methods=['DELETE'])
def delete_exist_user(account):
    result = admin_web.delete_user(account)
    return jsonify(result)

if __name__ == "__main__":
    # 启动Flask服务，端口5000（前端api.js已指向该端口）
    app.run(debug=True, port=5000, host='0.0.0.0')