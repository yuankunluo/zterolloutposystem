# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryNote',
            fields=[
                ('DeliveryNote Nr.', models.CharField(default=b'', max_length=255, unique=True, serialize=False, primary_key=True)),
                ('Applicant', models.TextField(max_length=255, null=True, blank=True)),
                ('Consignee', models.TextField(max_length=255, null=True, blank=True)),
                ('Project Name', models.TextField(max_length=255, null=True, blank=True)),
                ('Staff ID', models.CharField(max_length=255, null=True, blank=True)),
                ('Required date of Arrival', models.DateField(max_length=255, null=True, blank=True)),
                ('Phone NO 1', models.TextField(max_length=255, null=True, blank=True)),
                ('Phone NO 2', models.TextField(max_length=255, null=True, blank=True)),
                ('Carrier', models.TextField(max_length=255, null=True, blank=True)),
                ('SITE ID', models.TextField(max_length=255, null=True, blank=True)),
                ('Destination Address', models.TextField(max_length=2000, null=True, blank=True)),
                ('Region', models.TextField(max_length=255, null=True, blank=True)),
                ('Remark', models.TextField(max_length=2000, null=True, blank=True)),
                ('status', models.CharField(default=b'PENDING', max_length=2, choices=[(b'OK', b'OK'), (b'NO INFORMATION IN SAP', b'NO INFORMATION IN SAP'), (b'HAS INFORMATION IN SAP', b'HAS INFORMATION IN SAP'), (b'PENDING', b'Pending')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
