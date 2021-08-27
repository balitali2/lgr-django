# -*- coding: utf-8 -*-
import hashlib
import os
from io import BytesIO

from django.core.cache import cache
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_bytes

from lgr.core import LGR
from lgr.parser.xml_parser import XMLParser, LGR_NS
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.utils import tag_to_language_script
from lgr_auth.models import LgrUser
from lgr_web import settings


def get_upload_path(instance, filename):
    base_path = 'idn_table_review'
    # need to test on object_name because instance may not be a real object instance if called in a migration
    if instance._meta.object_name == 'RzLgr':
        return os.path.join(base_path, 'rz_lgr', filename)
    if instance._meta.object_name == 'RefLgr':
        return os.path.join(base_path, 'reference_lgr', filename)
    if instance._meta.object_name == 'RzLgrMember':
        return os.path.join(base_path, 'rz_lgr', instance.rz_lgr.name, filename)
    # if you need to use other LgrBaseModel in migration, this won't work as historical models don't includes method.
    # See https://docs.djangoproject.com/en/3.1/topics/migrations/#historical-models
    # If you need this in a migration, define the method and the migration and set it to the historical model.
    return os.path.join('lgr', instance.upload_path(instance, filename))


class LgrBaseModel(models.Model):
    lgr_parser = XMLParser
    lgr_cache_key = 'lgr-obj'
    cache_timeout = 3600

    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(to=LgrUser, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ['name']
        abstract = True

    def __str__(self):
        return self.name

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def dl_url(self):
        raise NotImplementedError

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(f'user_{instance.owner.id}', filename)

    def delete(self, *args, **kwargs):
        cache.delete(self._cache_key(self.lgr_cache_key))
        return super().delete(*args, **kwargs)

    def _cache_key(self, key):
        # TODO move from advanced to models
        from lgr_advanced.utils import LGR_CACHE_KEY_PREFIX

        key = f"{key}:{self.__class__.__name__}:{self.pk}"
        args = hashlib.md5(force_bytes(key))
        return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())

    def _to_cache(self, lgr: LGR):
        if not self._meta.pk:
            return
        cache.set(self._cache_key(self.lgr_cache_key), lgr, self.cache_timeout)

    def _from_cache(self) -> LGR:
        if not self._meta.pk:
            return None
        return cache.get(self._cache_key(self.lgr_cache_key))

    def to_lgr(self, validate=False) -> LGR:
        # TODO move from advanced to models
        from lgr_utils import unidb

        lgr = self._from_cache()
        if lgr is None:
            lgr = self._parse(validate)
            self._to_cache(lgr)
        else:
            # Need to manually load unicode database because it is stripped during serialization
            unicode_version = lgr.metadata.unicode_version
            lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        return lgr

    @classmethod
    def _parse_lgr_xml(cls, lgr, validate=False):
        # TODO move from advanced to models
        from lgr_advanced.exceptions import LGRValidationException

        data = serialize_lgr_xml(lgr, pretty_print=True)
        if validate:
            parser = cls.lgr_parser(BytesIO(data), lgr.name)
            validation_result = parser.validate_document(settings.LGR_RNG_FILE)
            if validation_result is not None:
                raise LGRValidationException(validation_result)
        return data

    @classmethod
    def from_lgr(cls, owner, lgr, name=None, validate=False, **kwargs):
        name = name or lgr.name
        if name.endswith('.xml') or name.endswith('.txt'):
            name = os.path.splitext(name)[0]
        data = cls._parse_lgr_xml(lgr, validate=validate)

        file = File(BytesIO(data), name=f'{name}.xml')
        lgr_object = cls.objects.create(owner=owner,
                                        name=name,
                                        file=file,
                                        **kwargs)
        lgr_object._to_cache(lgr)
        return lgr_object

    def _parse(self, validate):
        data = self.file.read()
        return self.parse(self.name, data, validate)

    @classmethod
    def parse(cls, name, data, validate):
        # TODO move from advanced to models
        from lgr_advanced.api import OLD_LGR_NS
        from lgr_advanced.exceptions import LGRValidationException
        from lgr_utils import unidb

        data = data.decode('utf-8').replace(OLD_LGR_NS, LGR_NS)

        # Create parser - Assume content is unicode data
        parser = cls.lgr_parser(BytesIO(data.encode('utf-8')), name)

        # Do we need to validate the schema?
        if validate:
            validation_result = parser.validate_document(settings.LGR_RNG_FILE)
            if validation_result is not None:
                raise LGRValidationException(validation_result)

        # Some explanations: Parsing the document with an Unicode database takes
        # more time since there are some Unicode-related checks performed
        # (IDNA validity, script checking)
        # Doing these checks for each parsing of the LGR (ie. for each request)
        # is not really useful.
        # So we do the following:
        # - For the first import of the LGR ("validate_cp" is True),
        # do a full-fledged parsing, enabling all checks.
        # This will filter out IDNA-invalid codepoints, issue warnings
        # about out-of script codepoints, etc.
        # - Otherwise, meaning the LGR is already in the user's session,
        # we do not set the Unicode database for parsing. However, the database
        # is still set AFTER the parsing is done in order to validate
        # user's input (add codepoint, validation of LGR).

        # Do we need to validate against Unicode?
        if validate:
            # Retrieve Unicode version to set appropriate Unicode database
            unicode_version = parser.unicode_version()
            parser.unicode_database = unidb.manager.get_db_by_version(
                unicode_version)

        # Actually parse document
        lgr = parser.parse_document()

        # If we did not set the actual Unicode database, do it now
        if not validate:
            # Retrieve Unicode version to set appropriate Unicode database
            unicode_version = lgr.metadata.unicode_version
            lgr.unicode_database = unidb.manager.get_db_by_version(
                unicode_version)
        return lgr

    def is_set(self):
        return False


class RzLgr(LgrBaseModel):
    # make name unique and owner nullable
    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(to=LgrUser, blank=True, null=True, on_delete=models.CASCADE, related_name='+')

    def dl_url(self):
        return reverse('lgr_idn_admin_display_rz_lgr', kwargs={'lgr_id': self.pk})


class RefLgr(LgrBaseModel):
    language_script = models.CharField(max_length=32, unique=True)
    language = models.CharField(max_length=8, blank=True)
    script = models.CharField(max_length=8, blank=True)
    # make name unique and owner nullable
    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(to=LgrUser, blank=True, null=True, on_delete=models.CASCADE, related_name='+')

    def dl_url(self):
        return reverse('lgr_idn_admin_display_ref_lgr', kwargs={'lgr_id': self.pk})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.language, self.script = tag_to_language_script(self.language_script)
        super().save(force_insert, force_update, using, update_fields)


class RzLgrMember(LgrBaseModel):
    rz_lgr = models.ForeignKey(to=RzLgr, on_delete=models.CASCADE, related_name='repository')
    language = models.CharField(max_length=8)
    script = models.CharField(max_length=8)
    # make name unique and owner nullable
    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(to=LgrUser, blank=True, null=True, on_delete=models.CASCADE, related_name='+')

    def dl_url(self):
        return reverse('lgr_idn_admin_display_rz_lgr_member', kwargs={'rz_lgr_id': self.rz_lgr.pk, 'lgr_id': self.pk})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        lgr_parser = XMLParser(self.file.path)
        lgr = lgr_parser.parse_document()
        self.language, self.script = tag_to_language_script(lgr.metadata.languages[0])
        super().save(force_insert=False, force_update=True, using=using, update_fields=['language', 'script'])
