"""
主要存放任务的方法，定时器执行的任务直接调用这里的任务方法
统一规范
任务采用方法/函数的形式定义 def run_task_XXX()
此模块所有的数据库连接操作要重写
"""