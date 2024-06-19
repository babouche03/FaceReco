import mysql.connector

# 连接到MySQL数据库
conn = mysql.connector.connect(
    host="localhost",  # 数据库主机地址
    user="root",  # 数据库用户名
    password="1111",  # 数据库密码 填自己的
    database="facereco"  # 数据库名称
)

# 创建一个游标对象
cur = conn.cursor()

# 创建FaceInfo表的SQL语句
create_table_query = """
CREATE TABLE IF NOT EXISTS FaceInfo (
    Id INT NOT NULL PRIMARY KEY,
    encoding VARCHAR(4096) NOT NULL,
    path VARCHAR(255) NOT NULL
)
"""

# 执行创建表的SQL语句
#cur.execute(create_table_query)



class MyError(Exception):
    def __init__(self, message):
        self.message = message

# 增
def insert_facereco(id, encoding_str, path):
    try:
        result = check_duplicate(id)
        if result:
            raise MyError("数据已经存在")
        else:
            sql = "INSERT INTO FaceInfo (Id, encoding, path) VALUES (%s, %s, %s)"
            values = (id, encoding_str, path)
            cur.execute(sql, values)
            conn.commit()
            print("增加运行成功")
    except MyError as e:
        print("数据创建失败：" + str(e.message))

# 删
def del_facereco(id):
    try:
        result = check_duplicate(id)
        if not result:
            raise MyError("数据不存在")
        else:
            sql = "DELETE FROM FaceInfo WHERE Id=%s"
            cur.execute(sql, (id,))
            conn.commit()
            print("删除运行成功")
    except MyError as e:
        print("数据删除失败：" + str(e.message))

# 改
def update_facereco(id, encoding_str=None, path=None):
    try:
        result = check_duplicate(id)
        if not result:
            raise MyError("数据不存在")
        else:
            if encoding_str:
                sql = "UPDATE FaceInfo SET encoding=%s WHERE Id=%s"
                cur.execute(sql, (encoding_str, id))
            if path:
                sql = "UPDATE FaceInfo SET path=%s WHERE Id=%s"
                cur.execute(sql, (path, id))
            conn.commit()
            print("修改运行成功")
    except MyError as e:
        print("数据修改失败：" + str(e.message))

# 查 - 查询所有数据
def select_all_facereco():
    try:
        sql = "SELECT * FROM FaceInfo"
        cur.execute(sql)
        results = cur.fetchall()
        for row in results:
            Id = row[0]
            encoding = row[1]
            path = row[2]
            print(f'Id: {Id}, encoding: {encoding}, path: {path}')
    except mysql.connector.Error as e:
        print("数据查询失败：" + str(e))

# 查 - 根据ID查询
def select_facereco_by_id(id):
    try:
        cur.execute("SELECT * FROM FaceInfo WHERE Id=%s", (id,))
        result = cur.fetchone()
        if not result:
            raise MyError("数据不存在")
        else:
            print(result)
            return result
    except MyError as e:
        print("数据查找失败：" + str(e.message))

# 查 - 根据encoding查询
def select_facereco_by_encoding(encoding):
    try:
        cur.execute("SELECT * FROM FaceInfo WHERE encoding=%s", (encoding,))
        result = cur.fetchone()
        if not result:
            raise MyError("数据不存在")
        else:
            print(result)
    except MyError as e:
        print("数据查找失败：" + str(e.message))

# 检查重复
def check_duplicate(id):
    cur.execute("SELECT * FROM FaceInfo WHERE Id=%s", (id,))
    result = cur.fetchone()
    return result is not None

# 删除表
def delete_table():
    cur.execute("DROP TABLE IF EXISTS FaceInfo")
    conn.commit()
    print("删除表单成功")

# 显示部分信息 - ID和path
def show_somein():
    sql = "SELECT Id, path FROM FaceInfo"
    cur.execute(sql)
    results = cur.fetchall()
    return results

# 显示部分信息 - encoding
def show_someinen():
    sql = "SELECT encoding FROM FaceInfo"
    cur.execute(sql)
    results = cur.fetchall()
    return results

# 排序
def order():
    query = "SELECT FaceInfo.Id, Staff.Name FROM FaceInfo INNER JOIN Staff ON FaceInfo.Id = Staff.Id ORDER BY FaceInfo.Id"
    cur.execute(query)
    results = cur.fetchall()
    l = list()
    # 输出排序结果
    for row in results:
        l.append(row[0:2])
    return l

# 关闭游标和数据库连接
def close_connection():
    cur.close()
    conn.close()

# Example Usage
# if __name__ == "__main__":
#     try:
#         insert_facereco(1, "encoding_string_example", "/path/to/image")
#         insert_facereco(2, "another_encoding_string_example", "/another/path/to/image")
        
#         select_all_facereco()
        
#         update_facereco(1, path="/new/path/to/image")
        
#         select_facereco_by_id(1)
        
#         del_facereco(2)
        
#         select_all_facereco()
        
#     finally:
#         close_connection()
