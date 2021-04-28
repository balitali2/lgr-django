#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging
import os
from collections import defaultdict
from urllib.error import URLError
from urllib.request import urlopen

import lxml.html
from django.conf import settings
from django.db.models import Q

from lgr.core import LGR
from lgr.metadata import Metadata, Version
from lgr.tools.utils import download_file
from lgr_idn_table_review.admin.models import RefLgr, RzLgrMember, RzLgr
from lgr_idn_table_review.tool.api import IdnTableInfo
from lgr_session.api import LgrStorage

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'
ICANN_URL = 'https://www.iana.org'
ICANN_IDN_TABLES = ICANN_URL + '/domains/idn-tables'


class LgrIcannSession(LgrStorage):
    storage_location = settings.IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION

    def __init__(self, request):
        self.request = request

    def get_storage_path(self, subfolder=None):
        return os.path.join(self.storage_location, subfolder or '')


def get_icann_idn_repository_tables():
    tree = lxml.html.parse(urlopen(ICANN_IDN_TABLES))
    idn_table_columns = tree.xpath("//table[@id='idn-table']/tbody/tr")

    # some urls are the same for many TLDs therefore need to loop twice to regroup them instead of parsing multiple
    # times the same LGR
    urls = defaultdict(set)
    dates = {}
    for col in idn_table_columns:
        a_tag = col.findall('td/a')[0]
        tld = a_tag.find('span').text.strip('.')
        url = a_tag.attrib['href'].strip()
        date = col.findall('td')[3].text.strip()
        urls[url].add(tld)
        dates.setdefault(url, date)

    for url, tlds in urls.items():
        __, lang_script, version = os.path.basename(url).split('_', 3)
        date = dates.get(url)
        try:
            name, data = download_file(ICANN_URL + url)
            info = IdnTableInfo.from_dict({
                'name': name,
                'data': data.read().decode('utf-8'),
            })
        except URLError:
            logger.error('Cannot download %s', ICANN_URL + url)
            continue
        except Exception:
            logger.error("Unable to parse IDN table at %s", ICANN_URL + url)
            continue
        meta: Metadata = info.lgr.metadata
        if date and not meta.date:
            meta.set_date(date, force=True)
        if not meta.languages:
            meta.add_language(lang_script, force=True)
        if not meta.version:
            meta.version = Version(version)
        yield tlds, info


def get_reference_lgr(idn_table_info: IdnTableInfo):
    idn_table: LGR = idn_table_info.lgr
    query = Q(pk=None)
    try:
        language_tag = idn_table.metadata.languages[0]
        logger.info('Look for reference LGR with language %s', language_tag)
        query |= Q(language__iexact=language_tag) | Q(script__iexact=language_tag, language='')
    except IndexError:
        logger.info("No language tag in IDN table %s", idn_table)
        return None

    try:
        script = idn_table.metadata.get_scripts()[0]
        logger.info('Look for reference LGR with script %s', script)
        query |= Q(script__iexact=script, language='')
    except IndexError:
        pass

    try:
        ref_lgr = RefLgr.objects.get(query)
        logger.info('Found reference LGR %s', ref_lgr.name)
        return ref_lgr
    except RefLgr.DoesNotExist:
        logger.info("No reference LGR found")

    logger.info('Look for RZ LGR')
    # get the latest RZ LGR (XXX: we assume they are all named the same with an incresing ID)
    last_rz_lgr = RzLgr.objects.order_by('name').first()
    try:
        ref_lgr = RzLgrMember.objects.get(query & Q(rz_lgr=last_rz_lgr))
        logger.info('Found RZ LGR script %s', ref_lgr.name)
        return ref_lgr
    except RzLgrMember.DoesNotExist:
        logger.info("No RZ LGR script found")

    return None
