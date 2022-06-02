# Generated by Django 3.1.7 on 2021-08-23 16:43
from django.conf import settings
from django.db import migrations

from lgr_models.models.unicode import UnicodeVersion


def get_supported_unicode_versions():
    return settings.SUPPORTED_UNICODE_VERSIONS


def initial_data(apps, schema_editor):
    old_unicode_version: UnicodeVersion = apps.get_model("lgr_models", "UnicodeVersion")
    known_unicode_versions = [
        '6.0.0',
        '6.1.0',
        '6.2.0',
        '6.3.0',
        '7.0.0',
        '8.0.0',
        '9.0.0',
        '10.0.0',
        '11.0.0',
        '12.0.0',
        '13.0.0',
        '14.0.0'
    ]

    for supported_version in known_unicode_versions:
        old_unicode_version.objects.using(schema_editor.connection.alias).create(version=supported_version)


class Migration(migrations.Migration):
    dependencies = [
        ('lgr_models', '0006_unicodeversion'),
    ]

    operations = [
        migrations.RunPython(initial_data)
    ]
