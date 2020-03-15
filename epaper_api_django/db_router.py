DATABASE_APPS_MAPPING = {
    # defaultには管理系のTable
    'admin'              : 'default',
    'auth'               : 'default',
    'contenttypes'       : 'default',
    'sessions'           : 'default',
    'messages'           : 'default',
    'staticfiles'        : 'default',
    'django_celery_beat' : 'default',
    # analyticsには分析計のTable
    'epaper_api_v1'          : 'v1',
}

class DatabaseRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label in DATABASE_APPS_MAPPING:
            return DATABASE_APPS_MAPPING[model._meta.app_label]
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in DATABASE_APPS_MAPPING:
            return DATABASE_APPS_MAPPING[model._meta.app_label]
        return None

    def allow_relation(self, obj1, obj2, **hints):
        db1 = DATABASE_APPS_MAPPING.get(obj1._meta.app_label)
        db2 = DATABASE_APPS_MAPPING.get(obj2._meta.app_label)
        if db1 and db2:
            return db1 == db2
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        if db in DATABASE_APPS_MAPPING.values():
            return DATABASE_APPS_MAPPING.get(app_label) == db
        elif app_label in DATABASE_APPS_MAPPING:
            return False