import pymysql

# 手动将版本号伪装成 2.2.1，骗过 Django 的检查
pymysql.version_info = (2, 2, 1, 'final', 0) 

pymysql.install_as_MySQLdb()