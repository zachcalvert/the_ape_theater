# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-04-23 03:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0006_houseteam_show_time'),
        ('pages', '0012_auto_20180405_1302'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseTeamFocusWidget',
            fields=[
                ('widget_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pages.Widget')),
                ('house_team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.HouseTeam')),
            ],
            options={
                'abstract': False,
            },
            bases=('pages.widget',),
        ),
    ]
