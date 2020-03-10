from django.db import models
from django.contrib.postgres.fields import JSONField


# Create your models here.

class SeversHistory(models.Model):
    domain_name = models.CharField(max_length=150)
    consultation_date = models.DateTimeField(auto_now_add=True)
    last_consultation_date_update = models.DateTimeField(auto_now=True)
    server_information = JSONField()

    def __str__(self):
        return self.domain_name
