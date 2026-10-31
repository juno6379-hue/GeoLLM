"""Scoped research observer for local spatial calls and actual DBAPI submissions.

Installs only in a dedicated sequential process. Metadata/document SQL is
recorded separately; SQL text/parameters are never retained. External GIS and
subprocess execution are not certified by this observer.
"""
import hashlib
import re
import sys
import threading
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine
import psycopg2
from psycopg2.extensions import connection as BaseConnection, cursor as BaseCursor

SPATIAL_SQL = re.compile(r'\bST_(?:DWithin|Distance|Intersects|Contains|Covers|CoveredBy|Within|Touches|Crosses|Overlaps|Relate|ClosestPoint|DistanceSphere|DistanceSpheroid)\s*\(', re.I)
SPATIAL_CALLS = {
    ('services.spatial_analysis_agent.tool_executor', 'execute_spatial_tool'),
    ('services.orchestrator.s101_radius_execution', '_fetch_result'),
    ('services.orchestrator.s101_radius_execution', '_fetch_bounds_result'),
}


def classify_sql(statement, context=None):
    if not isinstance(statement, str):
        if isinstance(statement, bytes):
            statement = statement.decode('utf-8', errors='replace')
        elif hasattr(statement, 'as_string') and context is not None:
            statement = statement.as_string(context)
        else:
            return 'UNKNOWN', None
    # Strip comments and string literals: a document mentioning ST_DWithin is not GIS.
    cleaned = re.sub(r'/\*.*?\*/|--[^\n]*', ' ', statement, flags=re.S)
    cleaned = re.sub(r"'(?:''|[^'])*'", "''", cleaned)
    spatial = bool(SPATIAL_SQL.search(cleaned) or ('&&' in cleaned and re.search(r'\bST_MakeEnvelope\s*\(', cleaned, re.I)))
    return ('SPATIAL_SQL' if spatial else 'NON_SPATIAL_SQL'), hashlib.sha256(statement.encode('utf-8')).hexdigest()


class SpatialExecutionObserver:
    def __init__(self, task_id):
        self.task_id = task_id
        self.events = []
        self.complete = False
        self.instrumentation_issues = []
        self.original_connect = None
        self._cursor_types = {}
        self._connection_types = {}

    def record(self, kind, origin, **fields):
        self.events.append({'kind':kind,'origin':origin,'task_id':self.task_id,
                            'monotonic_ns':time.monotonic_ns(),**fields})

    def submission(self, statement, context, origin):
        kind, digest = classify_sql(statement, context)
        if kind == 'UNKNOWN':
            self.instrumentation_issues.append('UNCLASSIFIABLE_DBAPI_STATEMENT')
        self.record('sql_submitted',origin,sql_kind=kind,statement_sha256=digest)
        return kind, digest

    def finished(self, kind, digest, origin, success):
        self.record('sql_completed' if success else 'sql_failed',origin,
                    sql_kind=kind,statement_sha256=digest)

    def cursor_type(self, base):
        if base in self._cursor_types:
            return self._cursor_types[base]
        observer = self
        class ObservedCursor(base):
            _research_spatial_observed = True
            def execute(self, query, vars=None):
                kind, digest = observer.submission(query,self,'psycopg2.cursor.execute')
                try:
                    value=super().execute(query,vars)
                except BaseException:
                    observer.finished(kind,digest,'psycopg2.cursor.execute',False)
                    raise
                observer.finished(kind,digest,'psycopg2.cursor.execute',True)
                return value
            def executemany(self, query, vars_list):
                kind,digest=observer.submission(query,self,'psycopg2.cursor.executemany')
                try:
                    value=super().executemany(query,vars_list)
                except BaseException:
                    observer.finished(kind,digest,'psycopg2.cursor.executemany',False)
                    raise
                observer.finished(kind,digest,'psycopg2.cursor.executemany',True)
                return value
            def callproc(self, *args, **kwargs):
                observer.instrumentation_issues.append('OPAQUE_STORED_PROCEDURE')
                return super().callproc(*args,**kwargs)
        self._cursor_types[base]=ObservedCursor
        return ObservedCursor

    def connect(self, *args, **kwargs):
        observer=self
        base=kwargs.pop('connection_factory',BaseConnection)
        if not isinstance(base,type) or not issubclass(base,BaseConnection):
            self.instrumentation_issues.append('UNSUPPORTED_CONNECTION_FACTORY')
            return self.original_connect(*args,connection_factory=base,**kwargs)
        if base not in self._connection_types:
            class ObservedConnection(base):
                def cursor(self,*args,**kwargs):
                    args=list(args)
                    requested=args[1] if len(args)>1 else kwargs.get('cursor_factory')
                    requested=requested or getattr(self,'cursor_factory',None) or BaseCursor
                    wrapped=observer.cursor_type(requested)
                    if len(args)>1:
                        args[1]=wrapped
                    else:
                        kwargs['cursor_factory']=wrapped
                    return super().cursor(*args,**kwargs)
            self._connection_types[base]=ObservedConnection
        return self.original_connect(*args,connection_factory=self._connection_types[base],**kwargs)

    def profile(self,frame,action,arg):
        if action != 'call':
            return
        module=frame.f_globals.get('__name__',''); name=frame.f_code.co_name
        if (module,name) in SPATIAL_CALLS:
            self.record('spatial_tool_called',module+'.'+name)
        # A subprocess can hide GIS from this process; do not certify non-execution.
        if module=='subprocess' and name=='__init__':
            self.instrumentation_issues.append('SUBPROCESS_OUTSIDE_OBSERVATION')

    def before_sql(self,conn,cursor,statement,parameters,context,executemany):
        if not getattr(cursor,'_research_spatial_observed',False):
            kind,digest=self.submission(statement,cursor,'sqlalchemy.before_cursor_execute')
            context._research_spatial_statement=(kind,digest)

    def after_sql(self,conn,cursor,statement,parameters,context,executemany):
        if hasattr(context,'_research_spatial_statement'):
            self.finished(*context._research_spatial_statement,'sqlalchemy.after_cursor_execute',True)

    def sql_error(self,context):
        execution=getattr(context,'execution_context',None)
        if execution is not None and hasattr(execution,'_research_spatial_statement'):
            self.finished(*execution._research_spatial_statement,'sqlalchemy.handle_error',False)

    def __enter__(self):
        if sys.getprofile() is not None or threading.getprofile() is not None:
            raise RuntimeError('Dedicated unprofiled process required')
        self.all_threads=hasattr(threading,'setprofile_all_threads')
        if not self.all_threads and threading.active_count()!=1:
            raise RuntimeError('Cannot observe existing worker threads')
        self.original_connect=psycopg2.connect
        psycopg2.connect=self.connect
        event.listen(Engine,'before_cursor_execute',self.before_sql)
        event.listen(Engine,'after_cursor_execute',self.after_sql)
        event.listen(Engine,'handle_error',self.sql_error)
        if self.all_threads:
            threading.setprofile_all_threads(self.profile)
        else:
            threading.setprofile(self.profile);sys.setprofile(self.profile)
        self.record('observation_started','research_harness')
        return self

    def __exit__(self,exc_type,exc,tb):
        self.complete=exc_type is None
        if self.all_threads:
            threading.setprofile_all_threads(None)
        else:
            threading.setprofile(None);sys.setprofile(None)
        event.remove(Engine,'before_cursor_execute',self.before_sql)
        event.remove(Engine,'after_cursor_execute',self.after_sql)
        event.remove(Engine,'handle_error',self.sql_error)
        psycopg2.connect=self.original_connect
        self.record('observation_finished' if self.complete else 'observation_interrupted','research_harness')

    def result(self):
        submitted=[e for e in self.events if e['kind']=='sql_submitted' and e.get('sql_kind')=='SPATIAL_SQL']
        completed=[e for e in self.events if e['kind']=='sql_completed' and e.get('sql_kind')=='SPATIAL_SQL']
        failed=[e for e in self.events if e['kind']=='sql_failed' and e.get('sql_kind')=='SPATIAL_SQL']
        tool=any(e['kind']=='spatial_tool_called' for e in self.events)
        complete=self.complete and not self.instrumentation_issues
        def observed(value):return value if value or complete else None
        # Successful DBAPI submission is not a correct spatial answer. A known
        # SQL failure is false; no spatial SQL is non-execution (success false).
        succeeded=(False if failed else bool(submitted) and len(completed)==len(submitted)) if complete else None
        return {'version':'research_spatial_execution_observer_v2','task_id':self.task_id,
            'observation_complete':complete,'scope':'LOCAL_INSTRUMENTED_SPATIAL_TOOLS_SQLALCHEMY_AND_PSYCOPG2',
            'execution_attempted':observed(tool or bool(submitted)),
            'execution_started':observed(bool(submitted)), 'tool_called':observed(tool),
            'sql_executed':observed(bool(submitted)), 'execution_succeeded':succeeded,
            'spatial_sql_submissions':len(submitted),
            'non_spatial_sql_submissions':sum(e['kind']=='sql_submitted' and e.get('sql_kind')=='NON_SPATIAL_SQL' for e in self.events),
            'instrumentation_issues':sorted(set(self.instrumentation_issues)),
            'limitations':['External GIS, pre-imported direct connect aliases and uninstrumented drivers are outside scope; dedicated isolated worker required.',
                          'execution_attempted includes spatial tool invocation; execution_started/sql_executed denote spatial SQL submission, including failed SQL.',
                          'execution_succeeded denotes submitted spatial SQL completion, not object/evidence correctness.'],
            'events':self.events}
