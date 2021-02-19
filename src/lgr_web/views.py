# -*- coding: utf-8 -*-
from enum import Enum, auto

from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView

INTERFACE_SESSION_KEY = None


class Interfaces(Enum):
    ADVANCED = auto()
    BASIC = auto()
    IDN_REVIEW = auto()
    IDN_ICANN = auto()
    IDN_ADMIN = auto()


class LGRModesView(TemplateView):
    template_name = 'lgr_modes.html'

    def get(self, request, *args, **kwargs):
        # stay in the current mode
        interface = request.session.get(INTERFACE_SESSION_KEY)
        if interface == Interfaces.ADVANCED.name:
            return redirect('lgr_advanced_mode')
        if interface == Interfaces.BASIC.name:
            return redirect('lgr_basic_mode')
        if interface == Interfaces.IDN_REVIEW.name:
            return redirect('lgr_review_mode')
        if interface == Interfaces.IDN_ADMIN.name:
            return redirect('lgr_idn_admin_mode')
        if interface == Interfaces.IDN_ICANN.name:
            return redirect('lgr_idn_icann_mode')

        return super(LGRModesView, self).get(request, *args, **kwargs)


class LGRSwitchModeView(LGRModesView):
    def get(self, request, *args, **kwargs):
        # reset interface session key
        request.session.pop(INTERFACE_SESSION_KEY, None)
        return super(LGRModesView, self).get(request, *args, **kwargs)


class LGRAboutView(TemplateView):
    """
    About dialog
    """
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['output'] = {"versions": settings.SUPPORTED_UNICODE_VERSIONS}
        return ctx
