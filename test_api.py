import requests

# 测试登录和相关API
print("=== 测试登录API ===")
response = requests.post('http://127.0.0.1:8080/api/login', 
                       json={'account': '20130101', 'password': '000000'})
login_result = response.json()
print('登录结果:', login_result)

if login_result.get('status') == 'success':
    cookies = response.cookies
    
    print("\n=== 测试请假记录API ===")
    response2 = requests.get('http://127.0.0.1:8080/api/counselor/leave_requests', 
                           cookies=cookies)
    data = response2.json()
    print('请假记录API成功:', data.get('success'))
    print('请假记录数量:', len(data.get('data', [])))
    
    print("\n=== 测试联系人列表API ===")
    response3 = requests.get('http://127.0.0.1:8080/api/chat/contacts', 
                           cookies=cookies)
    contacts_data = response3.json()
    print('联系人API成功:', contacts_data.get('success'))
    print('学生数量:', len(contacts_data.get('data', [])))
    
    if contacts_data.get('data'):
        print('\n前5个学生:')
        for i, student in enumerate(contacts_data['data'][:5]):
            print(f'{i+1}. {student.get("name")} ({student.get("id")})')
    
    print("\n=== 测试用户预览API ===")
    response4 = requests.post('http://127.0.0.1:8080/api/user_preview', 
                            json={'account': '20130101'})
    preview_data = response4.json()
    print('用户预览成功:', preview_data.get('success'))
else:
    print('登录失败，无法测试其他API')
