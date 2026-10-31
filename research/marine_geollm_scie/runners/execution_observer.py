"""Research-only passive observer; install in a dedicated sequential worker.

No GOLD enters routing. False requires a completed observation window. SQL
means any observed SQLAlchemy DBAPI submission (including failed statements),
a conservative superset of spatial SQL. Never infer non-execution from prose.
"""
import sys
import threading
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine


class ExecutionObserver:
    def __init__(self, task_id):
        self.task_id = task_id
        self.events = []
        self.complete = False

    def record(self, kind, origin):
        self.events.append({'kind': kind, 'origin': origin,
                            'task_id': self.task_id, 'monotonic_ns': time.monotonic_ns()})

    def profile(self, frame, action, arg):
        if action != 'call':
            return
        module = frame.f_globals.get('__name__', '')
        name = frame.f_code.co_name
        if module == 'services.spatial_analysis_agent.agent' and name == 'execute_spatial_analysis':
            self.record('execution_attempted', module + '.' + name)
        if module == 'services.spatial_analysis_agent.tool_executor' and name == 'execute_spatial_tool':
            self.record('execution_attempted', module + '.' + name)
            self.record('tool_called', module + '.' + name)

    def sql(self, conn, cursor, statement, parameters, context, executemany):
        # Do not persist SQL text/parameters, which may contain sensitive data.
        self.record('sql_executed', 'sqlalchemy.before_cursor_execute')

    def __enter__(self):
        if sys.getprofile() is not None or threading.getprofile() is not None:
            raise RuntimeError('Dedicated unprofiled worker required')
        self.all_threads = hasattr(threading, 'setprofile_all_threads')
        if not self.all_threads and threading.active_count() != 1:
            raise RuntimeError('Cannot observe pre-existing worker threads')
        event.listen(Engine, 'before_cursor_execute', self.sql)
        if self.all_threads:
            threading.setprofile_all_threads(self.profile)
        else:
            threading.setprofile(self.profile)
            sys.setprofile(self.profile)
        self.record('observation_started', 'research_harness')
        return self

    def __exit__(self, exc_type, exc, tb):
        self.complete = exc_type is None
        if self.all_threads:
            threading.setprofile_all_threads(None)
        else:
            sys.setprofile(None)
            threading.setprofile(None)
        event.remove(Engine, 'before_cursor_execute', self.sql)
        self.record('observation_finished' if self.complete else 'observation_interrupted', 'research_harness')

    def result(self):
        kinds = {e['kind'] for e in self.events}
        sql = 'sql_executed' in kinds
        tool = 'tool_called' in kinds
        attempted = 'execution_attempted' in kinds or tool or sql
        # Execution started denotes a database submission, not a valid result.
        values = {'execution_attempted': attempted, 'execution_started': sql,
                  'tool_called': tool, 'sql_executed': sql}
        return {'version': 'research_execution_observer_v1', 'task_id': self.task_id,
                'observation_complete': self.complete,
                'scope': 'dedicated_process_spatial_agent_tool_and_all_sqlalchemy_sql',
                'limitations': ['Direct DBAPI, external GIS services and subprocesses are outside this observer.'],
                **{k: v if v or self.complete else None for k, v in values.items()},
                'events': list(self.events)}


def q303_checks(final, observation):
    """User-approved behavioral GOLD; semantic interpretation scored separately."""
    result = {'needs_user_input': final.get('status') in {'NEEDS_USER_INPUT', 'NEEDS_CLARIFICATION'},
              'missing_reference_geometry': final.get('error_code') in {'AOI_REQUIRED', 'MISSING_REFERENCE_GEOMETRY'},
              'clarification_present': bool(final.get('clarification_questions'))}
    for key in ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed'):
        value = observation.get(key) if observation else None
        result[key + '_false'] = False if value is True else (
            True if value is False and observation.get('observation_complete') is True else None)
    return result
