# Generated by Django 2.1.2 on 2018-12-18 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookable',
            name='allowed_booker_groups',
            field=models.ManyToManyField(to='auth.Group'),
        ),
    ]