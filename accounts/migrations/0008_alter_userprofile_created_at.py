# Generated by Django 4.1.3 on 2022-12-28 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_userprofile_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(),
        ),
    ]
