# Generated by Django 2.2.9 on 2022-05-14 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220513_1132'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='descriprtion',
            new_name='description',
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]