from xivo_dao.resources.utils.search import SearchConfig
from xivo_dao.resources.utils.search import SearchSystem

from .model import OtpRequestModel

otp_request_config = SearchConfig(
    table=OtpRequestModel,
    columns={
        'uuid': OtpRequestModel.uuid,
        'call_id': OtpRequestModel.call_id,
        'number': OtpRequestModel.number,
        'caller_id_name': OtpRequestModel.caller_id_name,
        'caller_id_number': OtpRequestModel.caller_id_number,
    },
    default_sort='caller_id_name',
)

otp_request_search = SearchSystem(otp_request_config)
