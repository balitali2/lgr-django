# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from dal_select2.views import Select2GroupListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from lgr_advanced.lgr_editor.views.create import RE_SAFE_FILENAME
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewStorage
from lgr_idn_table_review.idn_tool.forms import LGRIdnTableReviewForm, IdnTableReviewSelectReferenceForm
from lgr_idn_table_review.idn_tool.models import IdnTable
from lgr_idn_table_review.idn_tool.tasks import idn_table_review_task
from lgr_models.models.lgr import RzLgr, RefLgr, RzLgrMember
from lgr_web.views import INTERFACE_SESSION_MODE_KEY, Interfaces

logger = logging.getLogger(__name__)


class IdnTableReviewViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRIdnReviewStorage(request.user)
        request.session[INTERFACE_SESSION_MODE_KEY] = Interfaces.IDN_REVIEW.name


class IdnTableReviewModeView(IdnTableReviewViewMixin, FormView):
    form_class = LGRIdnTableReviewForm
    template_name = 'lgr_idn_table_review_tool/review_mode.html'

    def get_success_url(self):
        return reverse('lgr_review_select_reference', kwargs={'report_id': self.report_id})

    def form_valid(self, form):
        self.report_id = datetime.now().strftime('%Y-%m-%d-%H%M%S.%f')
        for idn_table_file in self.request.FILES.getlist('idn_tables'):
            idn_table_name = idn_table_file.name
            if not RE_SAFE_FILENAME.match(idn_table_name):
                raise SuspiciousOperation()
            for ext in ['xml', 'txt']:
                if idn_table_name.endswith(f'.{ext}'):
                    idn_table_name = idn_table_name.rsplit('.', 1)[0]
                    break
            try:
                IdnTable.objects.create(file=File(idn_table_file),
                                        name=idn_table_name,
                                        owner=self.request.user,
                                        report_id=self.report_id)
            except Exception:
                logger.exception('Unable to parser IDN table %s', idn_table_name)
                form.add_error('idn_tables', _('%(filename)s is an invalid IDN table') % {'filename': idn_table_name})
                return super().form_invalid(form)

        return super(IdnTableReviewModeView, self).form_valid(form)


class IdnTableReviewSelectReferenceView(IdnTableReviewViewMixin, FormView):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'
    success_url = reverse_lazy('lgr_review_reports')

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.report_id = self.kwargs.get('report_id')

    def form_valid(self, form):
        email_address = self.request.user.email

        idn_tables = []
        for idn_table_pk, lgr_info in form.cleaned_data.items():
            idn_tables.append((idn_table_pk, lgr_info))

        idn_table_review_task.delay(idn_tables, self.report_id, email_address,
                                    self.request.build_absolute_uri(self.get_success_url()),
                                    self.request.build_absolute_uri('/').rstrip('/'))

        return super(IdnTableReviewSelectReferenceView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(IdnTableReviewSelectReferenceView, self).get_form_kwargs()
        idn_tables = IdnTable.objects.filter(owner=self.request.user, report_id=self.kwargs.get('report_id'))
        kwargs['idn_tables'] = idn_tables
        lgrs = {}
        # TODO use lgr ids instead of names only
        for name in list(RzLgr.objects.order_by('name').values_list('name', flat=True)):
            lgrs[name] = 'rz'
        for name in list(RzLgrMember.objects.order_by('name').values_list('name', flat=True)):
            lgrs[name] = 'rz_member'
        for name in list(RefLgr.objects.order_by('name').values_list('name', flat=True)):
            lgrs[name] = 'ref'

        kwargs['lgrs'] = lgrs

        return kwargs


class IdnTableReviewListReports(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review_tool/list_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = self.storage.list_storage()
        return context


class IdnTableReviewListReport(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review/list_report_files.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zipname = f"{self.kwargs.get('report_id')}.zip"
        context['reports'] = self.storage.list_storage(report_id=self.kwargs.get('report_id'),
                                                       exclude={'file__endswith': zipname})
        context['completed'] = True
        try:
            context['zip'] = self.storage.storage_find_report_file(self.kwargs.get('report_id'), zipname)
        except self.storage.storage_model.DoesNotExist:
            context['completed'] = False
        context['title'] = _("IDN Table Review Reports: %(report)s") % {'report': self.kwargs.get('report_id')}
        context['back_url'] = 'lgr_review_reports'
        return context


class IdnTableReviewDisplayIdnTable(IdnTableReviewViewMixin, SingleObjectMixin, View):
    pk_url_kwarg = 'lgr_pk'
    model = IdnTable

    def get(self, request, *args, **kwargs):
        idn_table = self.get_object(queryset=self.model.objects.filter(owner=request.user))
        # FIXME: should distinct txt and xml LGRs
        resp = HttpResponse(idn_table.file.read(), content_type='text/plain', charset='UTF-8')
        resp['Content-disposition'] = f'attachment; filename={idn_table.filename}'
        return resp


class RefLgrAutocomplete(LoginRequiredMixin, Select2GroupListView):

    # XXX Uncomment this and remove the other method when upgrading django-autocomplete-light to a version that
    #     supports it (should be > 3.8.2) and that is working correctly
    #     Check in forms as well to use the relevant IdnTableReviewSelectReferenceForm
    # @staticmethod
    # def get_list():
    #     lgr_choices = []
    #     for rz in RzLgr.objects.order_by('name').values_list('name', flat=True):
    #         rz_member_choices = ((('rz', rz), rz),) + tuple((('rz_member', name), name) for name in
    #                                                         RzLgrMember.objects.order_by('name').values_list('name',
    #                                                                                                          flat=True))
    #         lgr_choices += [((rz, rz), rz_member_choices)]
    #     lgr_choices += [(('Ref. LGR', 'Ref. LGR'), tuple(
    #         (('ref', name), name) for name in RefLgr.objects.order_by('name').values_list('name', flat=True)))]
    #     return lgr_choices

    @staticmethod
    def get_list():
        lgr_choices = []
        lgr_choices += [('Ref. LGR', tuple(RefLgr.objects.order_by('name').values_list('name', flat=True)))]
        for rz in RzLgr.objects.order_by('name').values_list('name', flat=True):
            rz_member_choices = (rz,) + tuple(
                RzLgrMember.objects.filter(rz_lgr__name=rz).order_by('name').values_list('name', flat=True))
            lgr_choices += [(rz, rz_member_choices)]
        return lgr_choices
