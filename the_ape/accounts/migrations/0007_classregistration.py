# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-27 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_auto_20180225_2157'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=100)),
                ('pdf', models.FileField(null=True, upload_to='class_registrations')),
                ('class_member', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='registration', to='accounts.ClassMember')),
            ],
        ),
    ]