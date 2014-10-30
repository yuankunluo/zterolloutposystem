from django.db import models

# Create your models here.

class Site(models.Model):
    """
    Present the site and it's location
    """

    BS_FE = models.CharField(primary_key=True, unique=True, max_length=255, null=False)
    BS_STO = models.CharField( max_length=255, null=False)
    FE_NAME = models.CharField(max_length=1000, null=False)
    STANDORT_NAME = models.CharField( max_length=1000, null=True)
    GEMEINDE_NAME = models.CharField( max_length=1000, null=True)
    PLZ = models.CharField( max_length=1000, null=True)
    STRASSE = models.CharField( max_length=1000, null=True)
    Baumathnames = models.ManyToManyField('Baumathname')
    Source = models.CharField( null=True, max_length=2000)
    SAPPos = models.ManyToManyField('SAPPurchesOrder')
    ZTEPos = models.ManyToManyField('ZTEPurchesOrder')


    def __str__(self):
        return "[Site] %s"%(unicode(self.BS_FE))


    def save(self, *args, **kwargs):
        super(Site, self).save(*args, **kwargs)
        print("[Site]%s was stored"%(self.BS_FE))


class Baumathname(models.Model):
    """
    Present the BMRecord
    """
    BS_FE = models.ForeignKey('Site')

    BAUMASSNAHME_ID = models.CharField( max_length=255, unique=True, null=False)
    BS_STO = models.CharField( max_length=255, null=False)
    FE_STO_KANDIDAT_ID = models.CharField( max_length=255, null=True)
    BAUMASSNAHMEART = models.CharField( max_length=255, null=True)
    BAUMASSNAHMETYP = models.CharField( max_length=255, null=True)
    BAUMASSNAHMEVORLAGE = models.CharField( max_length=255, null=True)
    BESCHREIBUNG = models.CharField( max_length=2000, null=True)
    PRICING = models.CharField( max_length=255, null=True)
    TURN_KEY_VENDOR = models.CharField( max_length=255, null=True)
    DO_TYP_NAME = models.CharField( max_length=255, null=True)
    AUFTRAGNEHMER_ABTEILUNG = models.CharField( max_length=255, null=True)
    DATUM_IST = models.CharField( max_length=255, null=True)
    BAUMASSNAHMETYP_ID = models.CharField( max_length=255, null=True)
    IST26 = models.CharField( max_length=255, null=True)
    IST82 = models.CharField( max_length=255, null=True)
    IST92 = models.CharField( max_length=255, null=True)
    IST100 = models.CharField( max_length=255, null=True)
    Source = models.CharField( null=True, max_length=2000)


    def __str__(self):
        return "[Baumathname] %s"%(unicode(self.BAUMASSNAHME_ID))


    def save(self, *args, **kwargs):
        super(Baumathname, self).save(*args, **kwargs)
        print("[BM]%s was stored"%(self.BAUMASSNAHME_ID))




# ---------- ZTE PO --------------------------------------------------------


class ZTEPurchesOrder(models.Model):
    """
    Present the PO record from ZTE Deutschland
    """
    PO_Nr = models.CharField(null=False, max_length=225)
    Site_ID = models.CharField( null=True, max_length=255)
    PO_Date = models.CharField( null=True, max_length=255)
    Buyer = models.CharField( null=True, max_length=255)
    Supplier = models.CharField( null=True, max_length=255)
    Product_Line = models.CharField( null=True, max_length=255)
    Source = models.CharField( null=True, max_length=2000)
    Remarks = models.CharField( null=True, max_length=2000)
    Material_Nrs = models.ManyToManyField('ZTEPOMaterailNr')
    # is done already
    Is_Done = models.BooleanField(null=False, default=False)



    def compareTo(self, newPo):
        """
        Compare po and newPo
        """
        pp_keys = ['PO_Date', 'Product_Line', 'Project_Name', 'MaterialType', 'Source', 'Site_ID',
                 'Material_Nr','Remarks', 'Supplier', 'Buyer', 'Delivery_Address','Qty','Product_Description']

    def __str__(self):
        return "[ZTEPO] %s"%(unicode(self.PO_Nr))


    def save(self, *args, **kwargs):
        super(ZTEPurchesOrder, self).save(*args, **kwargs)
        print("[ZTEPurchesOrder]%s was stored"%(self.PO_Nr))


class ZTEPOMaterailNr(models.Model):
    """
    Present the Material_Nr in ZTE PO record
    """

    PO_Nr = models.ForeignKey('ZTEPurchesOrder')

    Material_Nr = models.CharField(null=True, max_length=255)
    Product_Description = models.CharField( null=True, max_length=255)
    Delivery_Address = models.CharField( null=True, max_length=2000)
    Qty = models.CharField( null=True, blank=True, max_length=255)
    Material_Type = models.CharField( null=True, max_length=255)
    Source = models.CharField( null=True, max_length=2000)

    def __str__(self):
        return "[ZTEPOMaterial_Nr] %s"%(unicode(self.Material_Nr))


    def save(self, *args, **kwargs):
        super(ZTEPOMaterailNr, self).save(*args, **kwargs)
        print("[ZTEPOMaterailNr]%s was stored"%(self.Material_Nr))


# ---------------- SAP PO ---------------------------------------------

class SAPPurchesOrder(models.Model):
    """
    Present the PO in SAP
    """
    PO_Nr = models.CharField( null=False, max_length=225)
    Source = models.CharField(null=True, max_length=2000)


    def __str__(self):
        return "[SAPPO] %s"%(unicode(self.PO_Nr))

    def save(self, *args, **kwargs):
        super(SAPPurchesOrder, self).save(*args, **kwargs)
        print("[SAPPurchesOrder]%s was stored"%(self.PO_Nr))


# -------------------- Material Code----------------------------

class MaterialItem(models.Model):
    """
    Present the product
    """
    Product_Name = models.CharField( max_length=255, null=False)
    Product_Type = models.CharField( max_length=255, null=True)
    Source = models.CharField( null=True, max_length=2000)


class MaterialCode(models.Model):
    """
    Present the Material nr
    """
    Material_Nr = models.CharField(primary_key=True, unique=True,  max_length=255, null=False)
    Product_Description = models.CharField( max_length=1000, null=True)
    Material_Items = models.ManyToManyField('MaterialItem')
    Source = models.CharField( null=True, max_length=2000)