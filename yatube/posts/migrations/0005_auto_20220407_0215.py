# Generated by Django 2.2.9 on 2022-04-06 23:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20220323_2252'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',)},
        ),
        migrations.DeleteModel(
            name='Meta',
        ),
    ]
