import pycassa

from django.conf import settings
from django.utils.encoding import force_unicode
from django.contrib.sessions.backends.base import SessionBase, CreateError
from pycassa.system_manager import SystemManager
from pycassa.cassandra.ttypes import NotFoundException
from pycassa import types, ConsistencyLevel

CASSANDRA_HOSTS = getattr(settings, 'CASSANDRA_HOSTS', ['localhost:9160',])
CASSANDRA_SESSIONS_KEYSPACE = getattr(settings, 'CASSANDRA_SESSIONS_KEYSPACE', 'Keyspace1')
CASSANDRA_SESSIONS_COLUMN_FAMILY = getattr(settings, 'CASSANDRA_SESSIONS_COLUMN_FAMILY', 'Standard1')

pool = pycassa.ConnectionPool(CASSANDRA_SESSIONS_KEYSPACE, CASSANDRA_HOSTS)
pool.write_consistency_level = ConsistencyLevel.ALL

try:
    session_cf = pycassa.ColumnFamily(pool, CASSANDRA_SESSIONS_COLUMN_FAMILY)
except NotFoundException:
    sys = SystemManager(server=CASSANDRA_HOSTS[0])
    sys.create_column_family(CASSANDRA_SESSIONS_KEYSPACE, CASSANDRA_SESSIONS_COLUMN_FAMILY,
                             key_validation_class=types.UTF8Type(),
                             column_validation_classes={
                                 'session_data': types.UTF8Type()
                             })
    sys.close()


class SessionStore(SessionBase):
    """
    A Cassandra based session store.
    """
    def load(self):
        try:
            data = session_cf.get(self.session_key)
            return self.decode(force_unicode(data['session_data']))
        except pycassa.NotFoundException:
            self.create()
            return {}

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if must_create and self.exists(self.session_key):
            raise CreateError
        session_data = self.encode(self._get_session(no_load=must_create))
        session_cf.insert(self.session_key, {'session_data': session_data}, ttl=self.get_expiry_age())

    def exists(self, session_key):
        try:
            session_cf.get(session_key)
            return True
        except pycassa.NotFoundException:
            return False

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        session_cf.remove(session_key)