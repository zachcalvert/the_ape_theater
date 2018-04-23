# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-04-23 18:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0007_houseteam_logo'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseTeamMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('house_team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='house_team_performers', to='people.HouseTeam')),
            ],
        ),
        migrations.RemoveField(
            model_name='person',
            name='house_team',
        ),
        migrations.AddField(
            model_name='houseteammembership',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='house_team_performers', to='people.Person'),
        ),
        migrations.AddField(
            model_name='person',
            name='house_teams',
            field=models.ManyToManyField(related_name='performers', through='people.HouseTeamMembership', to='people.HouseTeam'),
        ),
    ]
