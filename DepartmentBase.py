import pymysql

#连接数据库FaceReco
conn = pymysql.connect(host='localhost', user='root', password='1111')
print('数据库成功连接')

#创建游标
cur3=conn.cursor()
cur3.execute("CREATE DATABASE IF NOT EXISTS FaceReco")
cur3.execute("USE FaceReco")

#创建部门表
sqlQuery = "CREATE TABLE IF NOT EXISTS department(department_id INT PRIMARY KEY,department_name VARCHAR(20))"
cur3.execute(sqlQuery)
print("部门表准备就绪")

#向部门表插入数据
def insert_departemnt():
    departments = [
        (1, '人力资源部'),
        (2, '财务部'),
        (3, '市场营销部'),
        (4, '研发部'),
        (5, '销售部')
    ]
    for department in departments:
        sql = ("""INSERT INTO department (department_id, department_name) VALUES 
               (%s, %s)""")
        cur3.execute(sql, department)
#仅调用一次
#insert_departemnt()

#新增部门
def add_department(d_name):
    cur3.execute("select count(*) from department")
    old_count = cur3.fetchone()[0]
    sql =("""INSERT INTO department (department_id, department_name) 
          VALUES (%s, %s)""")
    cur3.execute(sql,(old_count+1,d_name))

#创建视图分组查询各部门的职工信息及职工人数，使用Compute 子句
def create_view():
    cur3.execute("SHOW TABLES LIKE 'department_employees_info'")
    result = cur3.fetchone()

    if result:
        print("视图已经存在，进行更新操作")
        cur3.execute("DROP VIEW department_employees_info")  # 如果存在则先删除视图

    cur3.execute("""
        CREATE VIEW department_employees_info AS
        SELECT d.department_id, d.department_name, s.name, s.sex, total_employees
        FROM department d
        INNER JOIN staff s ON d.department_id = s.department_id
        LEFT JOIN (
            SELECT department_id, COUNT(name) AS total_employees
            FROM staff
            GROUP BY department_id
        ) t ON d.department_id = t.department_id
        ORDER BY department_id
        """)
    print("视图准备就绪")

def show_view_data():
    create_view()
    # 查询视图数据
    sql = "SELECT * FROM department_employees_info"
    cur3.execute(sql)
    results = cur3.fetchall()
    # 返回视图数据
    for row in results:
        print(row)

def show_single_data(d_name):
    create_view()
    sql = "SELECT * FROM department_employees_info where department_name = %s"
    cur3.execute(sql,d_name)
    result = cur3.fetchall()
    for row in result:
        print(row)
    return result

def delete_department_and_related_records(department_name):

    try:
        with conn.cursor() as cursor:
            # 查找部门ID
            sql = "SELECT department_id FROM department WHERE department_name = %s"
            cursor.execute(sql, (department_name,))
            department_id = cursor.fetchone()

            if department_id:
                # 删除该部门的员工
                sql = "DELETE FROM staff WHERE department_id = %s;"
                cursor.execute(sql, (department_id,))

                # 找到与department_id相关的所有staff_id
                sql = "SELECT id FROM staff WHERE department_id = %s"
                cursor.execute(sql, (department_id,))
                staff_ids = [staff['id'] for staff in cursor.fetchall()]

                # 使用找到的staff_id删除faceinfo和record表中的记录
                if staff_ids:
                    # 删除faceinfo中与staff_ids相关的记录
                    sql = "DELETE FROM faceinfo WHERE id IN (%s)"
                    placeholders = ', '.join(['%s'] * len(staff_ids))
                    sql = sql % placeholders
                    cursor.execute(sql, staff_ids)

                    # 删除record中与staff_ids相关的记录
                    sql = "DELETE FROM record WHERE id IN (%s)"
                    placeholders = ', '.join(['%s'] * len(staff_ids))
                    sql = sql % placeholders
                    cursor.execute(sql, staff_ids)

                    # 删除部门
                sql = "DELETE FROM department WHERE department_id = %s"
                cursor.execute(sql, (department_id,))

                # 提交事务
            conn.commit()
            print(f"Department '{department_name}' and related records have been deleted successfully.")

    except pymysql.MySQLError as e:
        print(f"Error: unable to delete department and related records: {e}")


#delete_department_and_related_records('人力资源部')

#调用
#add_department("技术部")
#show_view_data()
#show_single_data("人力资源部")


#conn.commit()
#conn.close()