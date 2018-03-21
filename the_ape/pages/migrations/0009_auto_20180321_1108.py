# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-03-21 18:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0008_auto_20180319_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(blank=True, choices=[('home', 'Home'), ('classes', 'Classes'), ('shows', 'Shows'), ('faculty', 'Faculty'), ('talent', 'Talent'), ('watch', 'Watch'), ('hype', 'Hype')], null=True),
        ),
    ]