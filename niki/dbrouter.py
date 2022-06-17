class dbrouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.model_name == "radcheck":
            return "radcheck"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == "radcheck":
            return "radcheck"
        return None

    def allow_syncdb(self, db, model):
        if model._meta.model_name == "radcheck":
            return False
        return True
