import csv
import mysql.connector

def write_csv():
    # 连接MySQL数据库
    cnx = mysql.connector.connect(host='localhost', user='root', password='1111', database='facereco')

    # 创建游标对象
    cursor = cnx.cursor()

    # 执行查询语句
    query = "SELECT Id, Name,encoding,path FROM student"
    cursor.execute(query)

    # 将查询结果写入CSV文件
    with open('FaceInformationBase.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([i[0] for i in cursor.description])  # 写入列名
        writer.writerows(cursor.fetchall())  # 写入查询结果的所有行

    # 关闭游标和数据库连接
    cursor.close()
    cnx.close()