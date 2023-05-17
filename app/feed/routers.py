from .models import TextAnnotation

class AnnotationRouter:
    def db_for_read(self, model, **hints):
        if model == TextAnnotation:
            return "annotation_db"
        return None

    def db_for_write(self, model, **hints):
        if model == TextAnnotation:
            return "annotation_db"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "annotation_db":
            return model_name == "TextAnnotation"
        return None