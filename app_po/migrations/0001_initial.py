# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Baumathname',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('BAUMASSNAHME_ID', models.CharField(unique=True, max_length=255)),
                ('BS_STO', models.CharField(max_length=255)),
                ('FE_STO_KANDIDAT_ID', models.CharField(max_length=255, null=True)),
                ('BAUMASSNAHMEART', models.CharField(max_length=255, null=True)),
                ('BAUMASSNAHMETYP', models.CharField(max_length=255, null=True)),
                ('BAUMASSNAHMEVORLAGE', models.CharField(max_length=255, null=True)),
                ('BESCHREIBUNG', models.CharField(max_length=2000, null=True)),
                ('PRICING', models.CharField(max_length=255, null=True)),
                ('TURN_KEY_VENDOR', models.CharField(max_length=255, null=True)),
                ('DO_TYP_NAME', models.CharField(max_length=255, null=True)),
                ('AUFTRAGNEHMER_ABTEILUNG', models.CharField(max_length=255, null=True)),
                ('DATUM_IST', models.CharField(max_length=255, null=True)),
                ('BAUMASSNAHMETYP_ID', models.CharField(max_length=255, null=True)),
                ('IST26', models.CharField(max_length=255, null=True)),
                ('IST82', models.CharField(max_length=255, null=True)),
                ('IST92', models.CharField(max_length=255, null=True)),
                ('IST100', models.CharField(max_length=255, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MaterialCode',
            fields=[
                ('Material_Nr', models.CharField(max_length=255, unique=True, serialize=False, primary_key=True)),
                ('Product_Description', models.CharField(max_length=1000, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MaterialItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Product_Name', models.CharField(max_length=255)),
                ('Product_Type', models.CharField(max_length=255, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SAPPurchesOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('PO_Nr', models.CharField(max_length=225)),
                ('Source', models.CharField(max_length=2000, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('BS_FE', models.CharField(max_length=255, unique=True, serialize=False, primary_key=True)),
                ('BS_STO', models.CharField(max_length=255)),
                ('FE_NAME', models.CharField(max_length=1000)),
                ('STANDORT_NAME', models.CharField(max_length=1000, null=True)),
                ('GEMEINDE_NAME', models.CharField(max_length=1000, null=True)),
                ('PLZ', models.CharField(max_length=1000, null=True)),
                ('STRASSE', models.CharField(max_length=1000, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
                ('Baumathnames', models.ManyToManyField(to='app_po.Baumathname')),
                ('SAPPos', models.ManyToManyField(to='app_po.SAPPurchesOrder')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ZTEPOMaterailNr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('Material_Nr', models.CharField(max_length=255, null=True)),
                ('Product_Description', models.CharField(max_length=255, null=True)),
                ('Delivery_Address', models.CharField(max_length=2000, null=True)),
                ('Qty', models.CharField(max_length=255, null=True, blank=True)),
                ('Material_Type', models.CharField(max_length=255, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ZTEPurchesOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('PO_Nr', models.CharField(max_length=225)),
                ('Site_ID', models.CharField(max_length=255, null=True)),
                ('PO_Date', models.CharField(max_length=255, null=True)),
                ('Buyer', models.CharField(max_length=255, null=True)),
                ('Supplier', models.CharField(max_length=255, null=True)),
                ('Product_Line', models.CharField(max_length=255, null=True)),
                ('Source', models.CharField(max_length=2000, null=True)),
                ('Remarks', models.CharField(max_length=2000, null=True)),
                ('Is_Done', models.BooleanField(default=False)),
                ('Material_Nrs', models.ManyToManyField(to='app_po.ZTEPOMaterailNr')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='ztepomaterailnr',
            name='PO_Nr',
            field=models.ForeignKey(to='app_po.ZTEPurchesOrder'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='site',
            name='ZTEPos',
            field=models.ManyToManyField(to='app_po.ZTEPurchesOrder'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='materialcode',
            name='Material_Items',
            field=models.ManyToManyField(to='app_po.MaterialItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baumathname',
            name='BS_FE',
            field=models.ForeignKey(to='app_po.Site'),
            preserve_default=True,
        ),
    ]
