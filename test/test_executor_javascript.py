# coding=utf8
from basement__.universal import u_javascript
import sys

print(sys.getdefaultencoding())
js_filepath = r'E:\Projects\auto_datahandler\resource\test_.js'
js_executor = u_javascript.Executor_Javascript.execute_jsfile(filepath=js_filepath)
print(u_javascript.Executor_Javascript.execute_jsfunc(js_executor, 'fa', u'参数'))