# Generated by Django 2.2.7 on 2020-04-18 21:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_auto_20200418_1853'),
    ]

    operations = [
        migrations.RenameField(
            model_name='horatrabalhada',
            old_name='conteudo',
            new_name='content',
        ),
    ]
