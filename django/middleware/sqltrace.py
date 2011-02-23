'''
A middleware that unlike other sql logging snippets allows
1) output to a seperate logging handler, for instance a seperate file
2) shows a summary of sql and what code caused the sql

This is very useful for situations with tens or hundreds of sql calls per request.

2011-01 Peter Lundberg
'''
from django.db import connection
from django.conf import settings
from django.template import Template, Context
from logging import getLogger
import traceback
from time import time
from itertools import groupby
from django.db.backends import BaseDatabaseWrapper, util

sql_logger = getLogger('SQLLogTraceMiddleware')

class CursorDetailedDebugWrapper(util.CursorDebugWrapper):
    "Extention that also saves a traceback per sql to find where calls are happening"
    
    def _last_application_stack_entry(self):
        # we could walk frames with sys._getframe() as well 
        full_stack = [ frame for frame in traceback.extract_stack() if not '/sqltrace.py' in frame[0] ]
        stack = [ frame for frame in full_stack if (not 'site-packages/django' in frame[0]) and \
                                                   (not 'SocketServer.py' in frame[0]) ]
        if not stack: # if not application related, show all stuff
            stack = full_stack
            
        #TODO how catch templates? Seems hidden as local var on some frame
        #return "%s [%s line %s]" % (" -> ".join([str(a) for a in s]), app_s[-1][0], app_s[-1][1])
        call_path = " -> ".join([frame[2] for frame in stack])
        location_src = "/".join(stack[-1][0].split('/')[-3:])
        location_line = stack[-1][1]
        return "%s [%s line %s]" % (call_path, location_src, location_line)

    def execute(self, sql, params=()):
        start = time()
        try:
            return self.cursor.execute(sql, params)
        finally:
            stop = time()
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            self.db.queries.append({
                'sql': sql,
                'time': "%.3f" % (stop - start),
                'tb': self._last_application_stack_entry()
            })

    def executemany(self, sql, param_list):
        start = time()
        try:
            return self.cursor.executemany(sql, param_list)
        finally:
            stop = time()
            self.db.queries.append({
                'sql': '%s times: %s' % (len(param_list), sql),
                'time': "%.3f" % (stop - start),
                'tb': self._last_application_stack_entry()
            })



class SQLLogTraceMiddleware:
    def __init__(self):
        sql_logger.warning("Enabled SQLLogTraceMiddleware and matching CursorDetailedDebugWrapper")
        # replace djangos debug factory function with our own extentions
        BaseDatabaseWrapper.make_debug_cursor = lambda dbwrapper,cursor: CursorDetailedDebugWrapper(cursor,dbwrapper)
        if not settings.DEBUG:
            sql_logger.warning("DEBUG not on, so sql logging will not work as expected.")
            
    """ 
    Thanx to http://www.djangosnippets.org/snippets/1672/ for inspiration
    """
    def process_request(self, request):
        request._sqllog_start_time = time()

    def process_response(self, request, response): 
        if connection.queries:
            requesttime = time() - request._sqllog_start_time
            origin_counts = []
            for key, group in groupby( sorted([q['tb'] for q in connection.queries]) ):
                count = len(list(group))
                sqltime = sum([float(q['time']) for q in connection.queries if q['tb'] == key])
                origin_counts.append( (count, sqltime, key) )
            
            sqltime = 0.0  
            for q in connection.queries:
                sqltime += float(q['time'])
                sql = q['sql']
                sql = sql.replace('`,`', '`, `')
                sql = sql.replace('` FROM `',  '` \n             FROM `')
                sql = sql.replace('` WHERE ',  '` \n             WHERE ')
                sql = sql.replace(' ORDER BY ', ' \n             ORDER BY ')
                q['sql'] = sql
            if request.path.startswith(settings.MEDIA_URL):
                #normally handled by httpd or similar
                t = Template(""" --------------------------------------- {{request.path}} {{requesttime|floatformat:3}}s
{{count}} quer{{count|pluralize:\'y,ies\'}} in {{sqltime|floatformat:3}} seconds.""") 
            else:
                t = Template(""" ======================================= {{request.path}} in {{requesttime|floatformat:3}}s
{{count}} quer{{count|pluralize:\'y,ies\'}} in {{sqltime|floatformat:3}} seconds: 
{% for q in queries %}[{{forloop.counter}}] {{q.time}}s: {{q.sql|safe}} 
     tb--> {{q.tb|safe}} {% if not forloop.last %}
{% endif %}{% endfor %}
 --- Caused by (sum of calls & time per traceback):
{% for origin in origin_count %}  {{ origin.0|stringformat:"3d"}} {{ origin.1|floatformat:3}}s {{ origin.2|safe }}
{% endfor %}
""")
            sql_logger.debug( t.render(Context({'request': request,
                                                'queries':connection.queries,
                                                'count':len(connection.queries),
                                                'sqltime':sqltime,
                                                'requesttime':requesttime,
                                                'origin_count': origin_counts})) )            
        return response

