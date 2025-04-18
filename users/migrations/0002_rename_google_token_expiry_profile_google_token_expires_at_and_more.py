# Generated by Django 5.1.1 on 2024-09-28 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='google_token_expiry',
            new_name='google_token_expires_at',
        ),
        migrations.AlterField(
            model_name='profile',
            name='google_access_token',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='google_refresh_token',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
