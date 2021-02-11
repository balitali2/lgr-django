# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import SuspiciousOperation
from django.http import Http404, FileResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from lgr_advanced.api import LgrToolSession
from lgr_advanced.lgr_editor.views import RE_SAFE_FILENAME
from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann.api import LgrIcannSession
from lgr_idn_table_review.tool.api import LgrIdnReviewSession


class LgrSessionView(UserPassesTestMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.filename = self.kwargs.get('filename')
        if not RE_SAFE_FILENAME.match(self.filename):
            raise SuspiciousOperation()
        self.folder = self.kwargs.get('folder', None)
        if not RE_SAFE_FILENAME.match(self.folder):
            raise SuspiciousOperation()
        self.next = request.GET.get('next', '/')
        storage_type = self.kwargs.get('storage')
        if storage_type == 'tool':
            self.session = LgrToolSession(self.request)
        elif storage_type == 'rev_usr':
            self.session = LgrIdnReviewSession(request)
        elif storage_type == 'rev_icann':
            self.session = LgrIcannSession(request)
        else:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        storage_type = self.kwargs.get('storage')
        if storage_type == 'rev_icann':
            return self.request.user.is_authenticated and self.request.user.role in [LgrRole.ICANN.value,
                                                                                     LgrRole.ADMIN.value]
        return True


class DownloadFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        res_file = self.session.storage_get_file(self.filename, subfolder=self.folder)
        if res_file is None:
            messages.error(request, _('Unable to download file %s') % self.filename)
            return DeleteFileView.as_view()(self.request)
        response = FileResponse(res_file[0])
        if 'display' not in self.request.GET:
            response['Content-Disposition'] = 'attachment; filename={}'.format(self.filename)
        return response


class DeleteFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        self.session.storage_delete_file(self.filename, subfolder=self.folder)
        return redirect(self.next)
