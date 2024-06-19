# backend_functions.py

import mysql.connector
from mysql.connector import Error

# MySQL连接配置
mysql_config = {
    'host': 'localhost',
    'database': 'facereco',
    'user': 'root',
    'password': '1111' #密码填自己的
}

# 连接MySQL数据库的函数
def connect_mysql():
    try:
        connection = mysql.connector.connect(**mysql_config)
        if connection.is_connected():
            print('Connected to MySQL database')
            return connection
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')



# 检查用户是否已存在
def check_user_exist(name):
    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT * FROM staff WHERE name = %s', (name,))
        existing_user = cursor.fetchone()
        if existing_user:
            print('Username already exists')
            return True
        else:
            return False
    except Error as e:
        print(f'Error checking user existence: {e}')
        return False
    finally:
        cursor.close()
        connection.close()


# 用户注册
def register_user(name, password, sex, department_id, role):
    if check_user_exist(name):
        return False

    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('INSERT INTO staff (name, password, sex, department_id, role) VALUES (%s, %s, %s, %s, %s)', (name, password, sex, department_id, role))
        connection.commit()
        print('User registered successfully')
        return True
    except Error as e:
        print(f'Error registering user: {e}')
        return False
    finally:
        cursor.close()
        connection.close()


# 用户登录
def login_user(name, password):
    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT * FROM staff WHERE name = %s AND password = %s', (name, password))
        user = cursor.fetchone()
        if user:
            print('Login successful')
            return True
        else:
            print('Invalid username or password')
            return False
    except Error as e:
        print(f'Error logging in: {e}')
        return False
    finally:
        cursor.close()
        connection.close()

# 获取用户角色
def get_user_role(name):
    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT role FROM staff WHERE name = %s', (name,))
        user_role = cursor.fetchone()
        if user_role:
            return user_role[0]
        else:
            return None
    except Error as e:
        print(f'Error getting user role: {e}')
        return None
    finally:
        cursor.close()
        connection.close()

# 检查用户是否具有管理员权限
def has_admin_privileges(name):
    role = get_user_role(name)
    return role == '管理员'  # 判断用户是否为管理员

# 根据id查找名字
def get_user_name(id):
    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT name FROM staff WHERE id = %s', (id,))
        user_role = cursor.fetchone()
        if user_role:
            return user_role[0]
        else:
            return None
    except Error as e:
        print(f'Error getting user role: {e}')
        return None
    finally:
        cursor.close()
        connection.close()

# 根据名字查找id
def get_user_id(name):
    connection = connect_mysql()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT id FROM staff WHERE name = %s', (name,))
        user_role = cursor.fetchone()
        if user_role:
            return user_role[0]
        else:
            return None
    except Error as e:
        print(f'Error getting user role: {e}')
        return None
    finally:
        cursor.close()
        connection.close()

def alter_staff():
    connection = connect_mysql()
    cursor = connection.cursor()
    try:
        cursor.execute('''
                         alter table staff add foreign key(department_id) 
                         references department(department_id)
                     ''')
        print('Staff table alter successfully')
    except Error as e:
        print(f'Error altering staff table: {e}')
    finally:
        cursor.close()
        connection.close()
#alter_staff()
# 创建员工表的函数(若还没创建staff表)
# def create_staff_table():
#     connection = connect_mysql()
#     cursor = connection.cursor()

#     try:
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS staff (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 name VARCHAR(255) NOT NULL,
#                 password VARCHAR(255) NOT NULL,
#                 sex VARCHAR(10),
#                 department_id INT,
#                 role VARCHAR(50),
#                 CONSTRAINT chk_sex CHECK (sex IN ('男', '女'))  -- 检查性别是否为 '男' 或 '女'
#             )
#         ''')
#         print('Staff table created successfully')
#     except Error as e:
#         print(f'Error creating staff table: {e}')
#     finally:
#         cursor.close()
#         connection.close()