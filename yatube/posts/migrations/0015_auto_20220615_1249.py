# Generated by Django 2.2.16 on 2022-06-15 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_auto_20220612_1255'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique'),
        ),
    ]