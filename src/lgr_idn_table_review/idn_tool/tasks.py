# -*- coding: utf-8 -*-
import logging
from ast import literal_eval
from datetime import datetime
from io import StringIO
from tempfile import TemporaryFile
from typing import Dict
from zipfile import ZipFile, ZIP_DEFLATED

from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from lgr.tools.idn_review.review import review_lgr
from lgr_auth.models import LgrUser
from lgr_idn_table_review.idn_tool.api import IdnTableInfo
from lgr_idn_table_review.idn_tool.models import IdnReviewReport
from lgr_models.models.lgr import RefLgr, RzLgr, RzLgrMember
from lgr_session.api import LGRStorage

logger = logging.getLogger(__name__)


def _review_idn_table(context: Dict, idn_table_info, lgr_info, absolute_url):
    lgr_type, lgr_name = literal_eval(lgr_info)
    if lgr_type == 'ref':
        ref_lgr = RefLgr.objects.get(name=lgr_name)
        ref_lgr_url = absolute_url + reverse('lgr_idn_admin_display_ref_lgr', kwargs={'lgr_id': ref_lgr.pk})
    elif lgr_type == 'rz_member':
        ref_lgr = RzLgrMember.objects.get(name=lgr_name)
        ref_lgr_url = absolute_url + reverse('lgr_idn_admin_display_rz_lgr_member',
                                             kwargs={'lgr_id': ref_lgr.pk,
                                                     'rz_lgr_id': ref_lgr.rz_lgr.pk})
    elif lgr_type == 'rz':
        ref_lgr = RzLgr.objects.get(name=lgr_name)
        ref_lgr_url = absolute_url + reverse('lgr_idn_admin_display_rz_lgr', kwargs={'lgr_id': ref_lgr.pk})
    else:
        raise RuntimeError(f'Wrong LGR type: {lgr_type}')
    context.update({
        'ref_lgr': ref_lgr.name,
        'ref_lgr_url': ref_lgr_url,
    })
    ref_lgr_info = IdnTableInfo.from_dict({
        'name': ref_lgr.name,
        'data': ref_lgr.file.read().decode('utf-8'),
    })
    context.update(review_lgr(idn_table_info.lgr, ref_lgr_info.lgr))


def _create_review_report(uuid, idn_table_json, lgr_info, absolute_url):
    html_report = ''
    context = {
        'idn_table': idn_table_json['name'],
        'idn_table_url': absolute_url + reverse('lgr_review_display_idn_table',
                                                kwargs={'report_id': uuid, 'lgr_id': idn_table_json['name']})
    }
    try:
        _review_idn_table(context, IdnTableInfo.from_dict(idn_table_json), lgr_info, absolute_url)
    except BaseException:
        logger.exception('Failed to review IDN table')
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    else:
        html_report = render_to_string('lgr_idn_table_review/review.html', context)
    finally:
        return html_report


@shared_task
def idn_table_review_task(idn_tables, uuid, email_address, download_link, absolute_url):
    """
    Review IDN tables

    :param idn_tables: The IDN table to review in JSON format associated to their reference LGR information as a tuple
    :param email_address: The e-mail address where the results will be sent
    :param download_link: The link where the file will be available
    :param absolute_url: The absolute website url
    :return:
    """
    report_id = datetime.now().strftime('%Y-%m-%d-%H%M%S.%f')
    user = LgrUser.objects.get(email=email_address)

    lgr_storage = LGRStorage(user)
    # XXX: will improve that later once session will be rewritten as well
    lgr_storage.storage_model = IdnReviewReport

    with TemporaryFile() as f:
        with ZipFile(f, mode='w', compression=ZIP_DEFLATED) as zf:
            for idn_table_json, lgr_info in idn_tables:
                html_report = _create_review_report(uuid, idn_table_json, lgr_info, absolute_url)
                filename = f"{idn_table_json['name']}.html"
                zf.writestr(filename, html_report)
                lgr_storage.storage_save_report_file(filename, StringIO(html_report), report_id=report_id)
        lgr_storage.storage_save_report_file(f'{report_id}.zip', f, report_id=report_id)

    email = EmailMessage(subject='IDN table review',
                         to=[email_address])
    email.body = f"IDN table review has been successfully completed.\n" \
                 f"You should now be able to download it from {download_link} under the path: " \
                 f"'{report_id}'.\nPlease refresh the home page if you don't see the link.\nBest regards"
    email.send()
