# Generated by Django 2.2.16 on 2022-04-19 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={},
        ),
        migrations.AlterField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(verbose_name='Текст коментария'),
        ),
    ]