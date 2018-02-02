from django.db import models

from people.models import Person


class Student(Person):
    classes = models.ManyToManyField('ApeClassSession', through='ClassMember', related_name='students')


class ApeClass(models.Model):
    TYPE_CHOICES = (
        ('IMPROV', 'Improv'),
        ('SKETCH', 'Sketch'),
        ('ACTING', 'Acting'),
    )

    name = models.CharField(max_length=50)
    bio = models.TextField()
    active = models.BooleanField(default=True)
    class_type = models.CharField(choices=TYPE_CHOICES, max_length=50)

    class Meta(object):
        verbose_name = 'Ape Class'
        verbose_name_plural = 'Ape Classes'

    def __str__(self):
        return self.name


class ApeClassSession(models.Model):
    ape_class = models.ForeignKey(ApeClass)
    teacher = models.ForeignKey('people.Person')
    start_date = models.DateTimeField(null=True)
    num_sessions = models.IntegerField(help_text='Number of Sessions')
    max_enrollment = models.IntegerField(help_text='Max number of students')

    enrollment_opens = models.DateField(null=True)
    enrollment_closes = models.DateField(null=True)

    class Meta(object):
        verbose_name = 'Ape Class Session'
        verbose_name_plural = 'Ape Class Sessions'

    def __str__(self):
        return '{0} - starting {1}'.format(self.ape_class.name, self.start_date)


class ClassMember(models.Model):
    student = models.ForeignKey(Student, related_name='class_membership')
    ape_class_session = models.ForeignKey(ApeClassSession, related_name='class_membership')