from xivo_dao.helpers.persistor import BasePersistor
from xivo_dao.resources.utils.search import CriteriaBuilderMixin

from .model import OtpRequestModel


class OtpRequestPersistor(CriteriaBuilderMixin, BasePersistor):
    _search_table = OtpRequestModel

    def __init__(self, session, otp_request_search, tenant_uuids=None):
        self.session = session
        self.search_system = otp_request_search
        self.tenant_uuids = tenant_uuids

    def _find_query(self, criteria):
        query = self.session.query(OtpRequestModel)
        # query = self._filter_tenant_uuid(query)
        return self.build_criteria(query, criteria)

    def _search_query(self):
        return self.session.query(self.search_system.config.table)
