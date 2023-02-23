from tinymce import models as tinymce_models
from django.db import models


class Com_gadz(models.Model):
    title = models.CharField(max_length=200)
    body_content = tinymce_models.HTMLField()

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()  # Permet de n'avoir qu'une seule entrée dans la bdd.
        super(Com_gadz, self).save(*args, **kwargs)


