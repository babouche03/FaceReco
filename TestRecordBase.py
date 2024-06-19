import pymysql

# 连接数据库FaceReco
conn = pymysql.connect(host='localhost', user='root', password='1111')
print('数据库成功连接')

# 创建游标
cur2 = conn.cursor()
cur2.execute("CREATE DATABASE IF NOT EXISTS FaceReco")
cur2.execute("USE FaceReco")

# 创建数据库表record
sqlQuery = "CREATE TABLE IF NOT EXISTS record(Id VARCHAR(20),Name VARCHAR(20),Time DATETIME, Status VARCHAR(20))"
cur2.execute(sqlQuery)
print("准备就绪")


def insert_record(id, name, time):
    sql = "insert into record (Id,Name,Time) value (%s,%s,%s)"
    value = (id, name, time)
    cur2.execute(sql, value)
    conn.commit()


def select_all_record():
    sql = "SELECT * FROM record"
    cur2.execute(sql)
    results = cur2.fetchall()
    conn.commit()
    return results


def delete_table():
    cur2.execute("drop table record")
    print("删除表单成功")


# 创建存储过程统计各员工指定月份的缺席、旷工次数
def create_late_and_absent_proc():
    try:
        with conn.cursor() as cursor:
            # 定义存储过程的SQL语句
            sql = """
            CREATE PROCEDURE CalculateAttendance(IN month_year VARCHAR(7)) 
            BEGIN  
                DECLARE year_part INT;  
                DECLARE month_part INT;  

                -- 分解字符串为年和月  
                SET year_part = SUBSTRING_INDEX(month_year, '-', 1);  
                SET month_part = SUBSTRING_INDEX(month_year, '-', -1);  

                -- 删除临时表  
                DROP TEMPORARY TABLE IF EXISTS attendance_statistics; 

                -- 创建临时表  
                CREATE TEMPORARY TABLE IF NOT EXISTS attendance_statistics (  
                    Employee_Name VARCHAR(20),  
                    Late_Count INT,  
                    Absent_Count INT  
                );  

                -- 插入数据  
                INSERT INTO attendance_statistics (Employee_Name, Late_Count, Absent_Count)  
                SELECT   
                    Name,  
                    SUM(CASE WHEN Status = '迟到' THEN 1 ELSE 0 END) AS Late_Count,  
                    SUM(CASE WHEN Status = '旷工' THEN 1 ELSE 0 END) AS Absent_Count  
                FROM record  
                WHERE MONTH(time) = month_part AND YEAR(time) = year_part  
                GROUP BY Name;  
                select * from attendance_statistics;
            END"""

            # 执行SQL语句来创建存储过程
            cursor.execute(sql)

            # 提交事务（如果需要）
            conn.commit()

        print("存储过程已成功创建")

    except pymysql.MySQLError as e:
        print(f"创建存储过程时发生错误: {e}")

create_late_and_absent_proc()
def calculate_attendance(month_year: str):

    sql = "call CalculateAttendance(%s)"
    cur2.execute(sql, (month_year,))
    conn.commit()
    results = cur2.fetchall()
    # 处理结果集，这里只是简单地打印出来
    for row in results:
        print(row)
    return results

#calculate_attendance('2024-06')

'''
# 创建数据库表record
sqlQuery = "CREATE TABLE IF NOT EXISTS record(Id VARCHAR(20),Name VARCHAR(20),Time DATETIME, Status VARCHAR(20))"
cur2.execute(sqlQuery)
print("记录表准备就绪")
'''
# 创建上下班时间表
cur2.execute("""
            CREATE TABLE IF NOT EXISTS WorkSchedule (
                ShiftID INT PRIMARY KEY,
                ShiftName VARCHAR(20),
                StartTime TIME,
                EndTime TIME
            )
        """)
print("时间表准备就绪")


# 创建触发器
def create_trigger():
    try:
        # 检查数据库中是否存在同名的触发器
        cur2.execute("SHOW TRIGGERS LIKE 'CheckLate'")
        existing_trigger = cur2.fetchone()

        if existing_trigger:
            print("触发器 'CheckLate' 已存在，无需创建。")
        else:
            # 创建新触发器
            cur2.execute("""
                             CREATE TRIGGER CheckLate
                        BEFORE INSERT ON record
                        FOR EACH ROW
                        BEGIN
                            DECLARE shift_start TIME;
                            DECLARE shift_end TIME;

                            SELECT StartTime INTO shift_start
                            FROM WorkSchedule
                            WHERE ShiftID = (
                                SELECT CASE 
                                    WHEN HOUR(NEW.Time) < 12 THEN 1
                                    ELSE 2
                                END
                            );

                            SELECT EndTime INTO shift_end
                            FROM WorkSchedule
                            WHERE ShiftID = (
                                SELECT CASE 
                                    WHEN HOUR(NEW.Time) < 12 THEN 1
                                    ELSE 2
                                END
                            );

                            IF NEW.Time <= shift_start THEN
                                SET NEW.Status = '正常';
                            ELSEIF NEW.Time > shift_start AND NEW.Time < ADDTIME(shift_start, '00:05:00') THEN
                                SET NEW.Status = '迟到';
                            ELSE
                                SET NEW.Status = '旷工';
                            END IF;
                        END;
                        """)
            conn.commit()
            print("触发器 'CheckLate' 创建成功。")
        #conn.commit()

    except pymysql.err.OperationalError as e:
        print("Error:", e)


create_trigger()

# 个人查询自己的打卡记录，视图
def select_own_record(id):
    cur2.execute("SHOW TABLES LIKE 'own_record'")
    result = cur2.fetchone()

    if result:
        print("视图已经存在，进行更新操作")
        cur2.execute("DROP VIEW own_record")  # 如果存在则先删除视图

    sql = ("CREATE VIEW own_record AS SELECT * FROM record WHERE ID= %s")
    cur2.execute(sql, id)
    conn.commit()


# 打印个人纪录
def print_own_record(id):
    select_own_record(id)
    sql = "SELECT * FROM own_record"
    cur2.execute(sql)
    results = cur2.fetchall()
    conn.commit()
    for row in results:
        print(row)


# 调用打印个人记录
# print_own_record(3)
# 更新上下班时间
def setup_work_schedule(start_time_morning, end_time_morning, start_time_afternoon, end_time_afternoon):
    try:
        # 删除现有的班次信息
        cur2.execute("DELETE FROM WorkSchedule")

        # 更新上午班次信息
        cur2.execute("""
                INSERT INTO WorkSchedule (ShiftID, ShiftName, StartTime, EndTime)
                VALUES (1, '上午', %s, %s)
            """, (start_time_morning, end_time_morning))

        # 更新下午班次信息
        cur2.execute("""
                INSERT INTO WorkSchedule (ShiftID, ShiftName, StartTime, EndTime)
                VALUES (2, '下午', %s, %s)
            """, (start_time_afternoon, end_time_afternoon))
        conn.commit()

        print("Work schedule setup completed successfully.")

    except pymysql.connect.Error as error:
        print("Error while setting up work schedule:", error)


# 传入指定月份
# calculate_attendance('2024-06')
#setup_work_schedule("7:00", "8:30", "16:30", "23:00")


# delete_table()
# print(select_all_record())

def add_foreign_key_to_record_table():
    sql = """  
    ALTER TABLE record ADD CONSTRAINT fk_record_staff_id FOREIGN KEY (id) REFERENCES staff(id) ON DELETE CASCADE
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()


# add_foreign_key_to_record_table()

def add_foreign_key_to_faceinfo_table():
    sql = f"""  
    ALTER TABLE faceinfo 
    ADD CONSTRAINT fk_staff_id FOREIGN KEY (id) REFERENCES staff(id) ON DELETE CASCADE;  
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()

# add_foreign_key_to_faceinfo_table()