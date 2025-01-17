from django.db import models

# Create your models here.

class MedicalRecord(models.Model):
    symptom_description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symptom_description
