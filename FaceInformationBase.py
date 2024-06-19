import pymysql

# 连接数据库FaceReco
conn = pymysql.connect(host='localhost', user='root', password='1111')
print('数据库成功连接')

# 创建游标
cur = conn.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS FaceReco")
cur.execute("USE FaceReco")

# 创建数据库表student
sqlQuery = ("CREATE TABLE IF NOT EXISTS student(Id VARCHAR(20),Name VARCHAR(20),encoding text,path VARCHAR("
            "1000))")
cur.execute(sqlQuery)
print("准备就绪")


# 增
def insert_facereco(id, name, encoding_str, path):
    try:
        result = check_duplicate(id)
        if result == True:
            raise MyError("数据已经存在")
        else:
            sql = "insert into student (Id,Name,encoding,path) value (%s,%s,%s,%s)"
            value = (id, name, encoding_str, path)
            cur.execute(sql, value)
            conn.commit()
            print("增加运行成功")
    except MyError as e:
        print("数据创建失败：" + str(e.message))


# 删
def del_facereco(id):
    try:
        result = check_duplicate(id)
        if result == False:
            raise MyError("数据不存在")
        else:
            sql = "delete from student where Id=%s"
            value = (id)
            cur.execute(sql, value)
            conn.commit()
            print("删除运行成功")
    except MyError as e:
        print("数据删除失败：" + str(e.message))


# 改
def update_name_facereco(Id, name, encoding, path):
    sql1 = "UPDATE student SET Name= %s WHERE Id=%s"
    value1 = (name, Id)
    cur.execute(sql1, value1)
    conn.commit()
    sql2 = "UPDATE student SET encoding= %s WHERE Id=%s"
    value2 = (encoding, Id)
    cur.execute(sql2, value2)
    conn.commit()
    sql3 = "UPDATE student SET Path= %s WHERE Id=%s"
    value3 = (path, Id)
    cur.execute(sql3, value3)
    conn.commit()
    print("修改运行成功")


# 查
def select_all_facereco():
    try:
        sql = "SELECT * FROM Student"
        cur.execute(sql)
        results = cur.fetchall()
        for row in results:
            Id = row[0]
            Name = row[1]
            encoding = row[2]
            Path = row[3]
            print('Id:%s,Name:%s,encoding:%s,Path:%s' % (Id, Name, encoding, Path))
    except pymysql.Error as e:
        print("数据查询失败：" + str(e))


def select_facereco_id(id):
    try:
        cur.execute("SELECT * FROM student WHERE Id = %s", (id))
        result = cur.fetchone()
        if result == None:
            raise MyError("数据不存在")
        else:
            print(result)
            return result
    except MyError as e:
        print("数据查找失败失败：" + str(e.message))


def select_facereco(encoding):
    try:
        cur.execute("SELECT * FROM student WHERE encoding = %s", (encoding))
        result = cur.fetchone()
        if result == None:
            raise MyError("数据不存在")
        else:
            print(result)
    except MyError as e:
        print("数据查找失败失败：" + str(e.message))


def check_duplicate(id):
    # 查询数据库中是否已经存在相同的数据
    cur.execute("SELECT * FROM student WHERE Id = %s", (id))
    result = cur.fetchone()
    if result:
        return True
    else:
        return False
def delete_table():
    cur.execute("drop table student")
    print("删除表单成功")

def show_somein():
    sql = "SELECT ID, Name FROM Student"
    cur.execute(sql)
    results = cur.fetchall()
    l=[]
    for row in results:
        l.append(row)
    return l

def show_someinen():
    sql = "SELECT encoding FROM Student"
    cur.execute(sql)
    results = cur.fetchall()
    l=[]
    for row in results:
        l.append(row)
    return l

class MyError(Exception):
    def __init__(self, message):
        self.message = message

def order():
    query = "SELECT * FROM student ORDER BY ID"
    cur.execute(query)
    # 获取排序结果
    results = cur.fetchall()
    l=list()
    # 输出排序结果
    for row in results:
        l.append(row[0:2])
    return l





#delete_table()
#select_all_facereco()
"""

insert_facereco("124", "杨幂", "123", "./photo/1.jpg")
select_facereco_id('124')
insert_facereco("125","贺晓翔","12234","刘亦菲.jpg")
select_all_facereco()
select_facereco(12323)
update_name_facereco(121,"荣贝贝","1","杨幂.jpg")
select_all_facereco()
del_facereco(124)
column_data = [result[0] for result in results]
"""
