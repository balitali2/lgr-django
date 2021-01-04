# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^comp/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_compare,
        name='lgr_tools_compare'),
    url(r'^diff/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_diff,
        name='lgr_tools_diff'),
    url(r'^coll/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_collisions,
        name='lgr_tools_collisions'),
    url(r'^annotate/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_annotate,
        name='lgr_tools_annotate'),
    url(r'^variants/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_compute_variants,
        name='lgr_tools_variants'),
    url(r'^cross-script/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_cross_script_variants,
        name='lgr_tools_cross_script'),
    url(r'^harmonization/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_harmonize,
        name='lgr_tools_harmonize'),
]
