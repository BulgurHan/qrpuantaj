# Generated by Django 4.2.17 on 2025-07-05 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_workschedule_delete_weeklyschedule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workschedule',
            name='end_time',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='start_time',
            field=models.TimeField(null=True),
        ),
    ]
