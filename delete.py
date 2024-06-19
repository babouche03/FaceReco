import mysql.connector
from mysql.connector import Error

config = {
        'user': 'root',      # 替换为你的数据库用户名
        'password': '1111',  # 替换为你的数据库密码
        'host': 'localhost',          # 替换为你的数据库主机地址
        'database': 'facereco'   # 替换为你的数据库名称
    }

def delete_employee_by_id(employee_id):
    # 数据库连接配置

    try:
        connection = None

        connection = mysql.connector.connect(**config)
        # 建立数据库连接


        if connection.is_connected():
            cursor = connection.cursor()

            # 检查员工ID是否存在于 staff 表中
            check_staff_query = "SELECT COUNT(*) FROM staff WHERE id = %s"
            cursor.execute(check_staff_query, (employee_id,))
            (count,) = cursor.fetchone()

            if count == 0:
                print(f"员工ID {employee_id} 不存在，请重新输入.")
                return

            # 删除 FaceInfo 表中对应员工的数据
            delete_faceinfo_query = "DELETE FROM FaceInfo WHERE id = %s"
            cursor.execute(delete_faceinfo_query, (employee_id,))

            # 删除 staff 表中对应员工的数据
            delete_staff_query = "DELETE FROM staff WHERE id = %s"
            cursor.execute(delete_staff_query, (employee_id,))

            # 删除 record 表中对应员工的数据
            delete_staff_record = "DELETE FROM record WHERE id = %s"
            cursor.execute(delete_staff_record, (employee_id,))

            # 提交事务
            connection.commit()

            print(f"ID为{employee_id}的员工数据已成功删除。")

    except Error as e:
        # 如果出现错误，则回滚事务
        print(f"Error: {e}")
        if connection and connection.is_connected():
            connection.rollback()

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

# 使用函数删除某个员工的数据
#delete_employee_by_id(1)  # 替换为实际的员工ID


