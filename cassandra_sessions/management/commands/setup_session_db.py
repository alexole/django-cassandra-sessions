from django.core.management.base import BaseCommand
from django.conf import settings
from pycassa.system_manager import SystemManager
from pycassa import types

__author__ = 'alexander.olehnovich'

CASSANDRA_HOSTS = getattr(settings, 'CASSANDRA_HOSTS', ['localhost:9160',])
CASSANDRA_SESSIONS_KEYSPACE = getattr(settings, 'CASSANDRA_SESSIONS_KEYSPACE', 'Keyspace1')
CASSANDRA_SESSIONS_COLUMN_FAMILY = getattr(settings, 'CASSANDRA_SESSIONS_COLUMN_FAMILY', 'Standard1')


class Command(BaseCommand):

    help = 'Creates column family for session data'

    def handle(self, **options):
        """

        :param options:
        """
        sys = SystemManager(server=CASSANDRA_HOSTS[0])
        sys.create_column_family(CASSANDRA_SESSIONS_KEYSPACE, CASSANDRA_SESSIONS_COLUMN_FAMILY,
                                 key_validation_class=types.UTF8Type(),
                                 column_validation_classes={
                                     'session_data': types.UTF8Type()
                                 })
        sys.close()
