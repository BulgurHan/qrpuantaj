# Generated by Django 4.2.17 on 2025-06-21 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_company_qr_code_attendance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='qr_code',
            field=models.CharField(blank=True, default='placeholder_qr', max_length=255, unique=True),
            preserve_default=False,
        ),
    ]
