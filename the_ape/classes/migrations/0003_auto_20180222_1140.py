from __future__ import unicode_literals

from django.db import migrations


CLASSES = [
    {
        'name': 'Improv 101',
        'bio': 'Add bio here',
        'class_type': 'Improv',
        'price': '195.00'
    },
    {
        'name': 'Improv 201',
        'bio': 'Add bio here',
        'class_type': 'Improv',
        'price': '195.00'
    },
    {
        'name': 'Improv 301',
        'bio': 'Add bio here',
        'class_type': 'Improv',
        'price': '195.00'
    },
    {
        'name': 'Improv 401',
        'bio': 'Add bio here',
        'class_type': 'Improv',
        'price': '195.00'
    },
    {
        'name': 'Acting for Improvisers',
        'bio': 'Add bio here',
        'class_type': 'Acting',
        'price': '195.00'
    },
    {
        'name': 'Voiceover Basics',
        'bio': 'Add bio here',
        'class_type': 'Acting',
        'price': '195.00'
    },
    {
        'name': 'Sketch Writing Basics',
        'bio': 'Add bio here',
        'class_type': 'Sketch',
        'price': '195.00'
    },
]


def create_classes(apps, schema_editor):
    ApeClass = apps.get_model('classes', 'ApeClass')

    for class_dict in CLASSES:
        ApeClass.objects.get_or_create(
            name=class_dict['name'],
            bio=class_dict['bio'],
            class_type=class_dict['class_type'],
            price=class_dict['price']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0002_auto_20180222_1100'),
    ]

    operations = [
        migrations.RunPython(create_classes)
    ]
