# -*- coding: utf-8 -*-
from django.http import Http404, FileResponse
from django.shortcuts import redirect
from django.views.generic.base import View

from lgr_idn_table_review.tool.api import LgrIdnReviewSession


class LgrSessionView(View):

    def dispatch(self, request, *args, **kwargs):
        self.filename = self.kwargs.get('filename')
        self.next = request.GET.get('next')
        storage_type = self.kwargs.get('storage')
        if storage_type == 'lgr':
            pass
            # self.session = LgrToolSession(self.request)
        elif storage_type == 'rev_usr':
            self.session = LgrIdnReviewSession(request)
        else:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class DownloadFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        res_file = self.session.storage_get_file(self.filename)
        if res_file is None:
            # TODO show an error...
            return DeleteFileView.as_view()(self.request)
        response = FileResponse(res_file[0], content_type='application/x-gzip')
        response['Content-Disposition'] = 'attachment; filename={}'.format(self.filename)
        return response


class DeleteFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        self.session.storage_delete_file(self.filename)
        return redirect(self.next)
