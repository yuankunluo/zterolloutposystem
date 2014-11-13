from django.db import models
import datetime
import os

# Create your models here.


class DeliveryNote(models.Model):
    """
    Present the DNGE
    """

    dn_nr = models.CharField(name='DeliveryNote Nr.',default='',unique=True, null=False, primary_key=True, max_length=255)
    applicant = models.TextField(name='Applicant', blank=True, null=True, max_length=255)
    consignee = models.TextField(name='Consignee', blank=True, null=True, max_length=255)
    project_name = models.TextField(name='Project Name', blank=True, null=True, max_length=255)
    staff_id = models.CharField(name='Staff ID', blank=True, null=True, max_length=255)
    required_date_of_Arrival = models.DateField(name='Required date of Arrival', blank=True, null=True, max_length=255)
    phone_no_1 = models.TextField(name='Phone NO 1', blank=True, null=True, max_length=255)
    phone_no_2 = models.TextField(name='Phone NO 2', blank=True, null=True, max_length=255)
    carrier = models.TextField(name='Carrier', blank=True, null=True, max_length=255)
    site_id = models.TextField(name='SITE ID', blank=True, null=True, max_length=255)
    destination_address = models.TextField(name='Destination Address', blank=True, null=True, max_length=2000)
    region = models.TextField(name='Region', blank=True, null=True, max_length=255)
    remark = models.TextField(name='Remark', blank=True, null=True, max_length=2000)


    PENNDING = 'PENDING'
    OK = 'OK'
    NOSAP = 'NO INFORMATION IN SAP'
    YESSAP = 'HAS INFORMATION IN SAP'
    DNGE_STATUS_CHOICES = (
        (OK, 'OK'),
        (NOSAP, 'NO INFORMATION IN SAP'),
        (YESSAP, 'HAS INFORMATION IN SAP'),
        (PENNDING,'Pending'),
    )
    status = models.CharField(max_length=2,
                                      choices=DNGE_STATUS_CHOICES,
                                      default=PENNDING)





