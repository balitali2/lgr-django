# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_advanced.lgr_editor.forms.fields import ROOT_ZONES, FILE_FIELD_ENCODING_HELP
from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.unidb import get_db_by_version


class ValidateLabelSimpleForm(forms.Form):
    rz_lgr = forms.ChoiceField(label='', required=True, choices=ROOT_ZONES, initial=ROOT_ZONES[-1][0])
    labels = forms.CharField(label='', required=False,
                             widget=forms.TextInput(attrs={'name': '',
                                                           'class': 'form-label form-control',
                                                           'onkeyup': 'buttonValidateEnabled()',
                                                           'placeholder': _('Label')}))
    labels_file = forms.FileField(label='', help_text=FILE_FIELD_ENCODING_HELP,
                                  required=False)
    collisions = forms.BooleanField(label='', widget=forms.CheckboxInput(attrs={'id': 'check-for-collision'}),
                                    required=False)

    def clean(self):
        cleaned_data = super(ValidateLabelSimpleForm, self).clean()
        if 'labels' not in self.errors and not cleaned_data.get('labels') and not cleaned_data.get('labels_file'):
            self.add_error('labels', _('Required'))
            self.add_error('labels_file', _('Required'))

        if cleaned_data.get('labels') and cleaned_data.get('labels_file'):
            # should not happen
            self.add_error('labels', _('Unknown error, please report'))
            self.add_error('labels_file', _('Unknown error, please report'))

        return cleaned_data

    def clean_labels(self):
        rz_lgr = self.cleaned_data['rz_lgr']
        lgr = get_by_name(rz_lgr, with_unidb=True)
        udata = get_db_by_version(lgr.metadata.unicode_version)

        value = self.cleaned_data['labels']
        labels = list()
        for label in set(value.split(';')):
            if not label:
                continue
            try:
                labels.append(parse_label_input(label, idna_decoder=udata.idna_decode_label))
            except ValueError as e:
                raise ValidationError(lgr_exception_to_text(e))
        return labels
