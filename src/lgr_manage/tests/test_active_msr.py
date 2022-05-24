from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_manage.forms import MSRIsActiveForm
from lgr_models.models.lgr import MSR

class MSRActiveTestCase(LgrWebClientTestBase):
    def test_access_active_when_logged_in(self):
        self.login()

        response = self.client.get('/m/msr')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/msr/isactive">',
                            status_code=200)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/msr')
        self.assertContains(response, status_code=403)

    def test_update_active_when_logged_in(self):
        self.login()
        form = MSRIsActiveForm()
        form.data = {'active': ['2']}
        response = self.client.post('/m/msr/isactive', form)
        self.assertContains(response, status_code=200)
        self.assertContains(MSR.filter(active=True).first().pk, 2)

    def test_update_active_when_not_logged_in(self):
        form = MSRIsActiveForm()
        form.data = {'active': ['2']}
        response = self.client.post('/m/msr/isactive', form)
        self.assertContains(response, status_code=403)