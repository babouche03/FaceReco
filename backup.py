import subprocess
import mysql.connector
import TestRecordBase

# 备份数据库
def backup_database():
    try:
        # 使用mysqldump备份数据库
        global host, user, password, database, backup_file
        subprocess.run(['mysqldump', '-h', host, '-u', user, '-p' + password, database, '--result-file=' + backup_file])
        print("Backup successful.")
    except Exception as e:
        print("Backup failed:", str(e))
        

#恢复数据库

def restore_database():
    try:
        global host, user, password, database, backup_file
        # 连接到数据库
        conn = mysql.connector.connect(host=host, user=user, password=password)
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(database))

        # 选择数据库
        cursor.execute("USE {}".format(database))

        # 恢复数据库
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')
            for sql_command in sql_commands:
                cursor.execute(sql_command.strip())
                if sql_command.strip().lower().startswith("select"):
                    cursor.fetchall()  # 只在执行查询语句后清空结果集

        conn.commit()
        TestRecordBase.create_trigger()
        #conn.close()
        print("Restore successful.")
    except Exception as e:
        print("Restore failed:", str(e))
'''
def restore_database():
    try:
        global host, user, password, database, backup_file
        # 连接到数据库
        conn = mysql.connector.connect(host=host, user=user, password=password)
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(database))

        # 选择数据库
        cursor.execute("USE {}".format(database))

        # 恢复数据库
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')
            for sql_command in sql_commands:
                if sql_command.strip():  # 确保不是空语句
                    cursor.execute(sql_command.strip())

        conn.commit()
        TestRecordBase.create_trigger()
        conn.close()
        print("Restore successful.")
    except Exception as e:
        print("Restore failed:", str(e))
'''

# 设置数据库连接参数
host = 'localhost'
user = 'root'
password = '1111'
database = 'facereco'
backup_file = './backup.sql'

# 备份数据库
#backup_database()

# 恢复数据库
#restore_database()
