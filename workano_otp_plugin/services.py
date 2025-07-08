import re
import traceback
import time
from datetime import datetime
from threading import Thread
from .model import OtpModel
from datetime import datetime, timezone
from marshmallow import ValidationError
from wazo_calld_client import Client
from xivo_dao.helpers.db_manager import Session
from wazo_confd_client import Client as ConfdClient

from . import dao
import logging
# from .notifier import build_campaign_notifier
# from .validator import build_campaign_validator
# from ..campaign_contact_call.model import CampaignContactCallModel
# from ..campaign_contact_call.services import build_campaign_contact_call_service
# from ..contact_list.services import build_contact_list_service

logger = logging.getLogger(__name__)


def build_otp_request_service(auth_client, calld_client, confd_client):
    return OtpPlaybackService(
        auth_client,
        calld_client,
        confd_client,
        dao
    )


class OtpPlaybackService:

    def __init__(self,
                 auth_client,
                 calld_client,
                 confd_client,
                 dao,
                 extra_parameters=None):
        self.auth_client = auth_client
        self.calld_client = calld_client
        self.confd_client:ConfdClient  = confd_client
        # token = self.auth_client.token.new(
        #     expiration=365 * 24 * 60 * 60)['token']
        token = '23f091e8-7800-4275-b3fc-43ddadbe9f4b'
        self.tenant = 'd41c632c-68d2-457f-b064-c0f479515255'
        self.calld_client.set_token(token)
        self.confd_client.set_token(token)
        self.calld_client.set_tenant(self.tenant)
        self.confd_client.set_tenant(self.tenant)

    def process_otp_request(self, params):
        print(
            "Processing OTP request, application_uuid: %s, language: %s, number: %s, uris: %s",
            params.get("application_uuid"),
            params.get("language"),
            params.get("number"),
            params.get("uris"),
        )

        # applicaiton = self.wazo_client.calld.sessions.originate(params)
        context = self.confd_client.contexts.list(tenant=self.tenant, type='internal' )
        print('contexts', context)

        application = self.confd_client.applications.get(params.get("application_uuid"))
        if not application:  # If the application is None or empty
            return {
                "error": "Application not found",
                "result": None
            }

        call_args = {
            'context': params.get("context"),
            'exten': params.get("number"),
            'autoanswer': False,
            'variables': {
                "WAZO_TENANT_UUID": self.tenant
            }
        }
        print('callargs', call_args)
        call = self.calld_client.applications.make_call(params.get("application_uuid"), call_args)
        logger.info("Make a call: %s", call)

        otp_request = self.create_otp_request(
            params.get("application_uuid"),
            params.get("language"),
            application['tenant_uuid'],
            params.get("uris"),
            params.get("number"),
            call
        )
        return {
            "error": None,
            "result": otp_request
        }


    def create_otp_request(self, application_uuid, language, tenant_uuid, uris, number, call):
        creation_time = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', call['creation_time'])
        otp_request_args = {
            "call_id": call['id'],
            "tenant_uuid": tenant_uuid,
            "application_uuid": application_uuid,
            "number": number,
            "caller_id_name": call['caller_id_name'],
            "caller_id_number": call['caller_id_number'],
            "language": language,
            "uris": uris,
            "status": call['caller_id_number'],
            "answered": False,
            "end_time": None,
            "creation_time": datetime.fromisoformat(creation_time) if "creation_time" in call else None,
            "talking_to": call.get("talking_to", {})
        }

        otp_request = OtpModel(**otp_request_args)
        return dao.create(otp_request)

    def application_call_answered(self, event):
        print('>>>>event')
        print("👊 ~ event>> ", event)
        if event["call"]["is_caller"]:
            return
        call_id = event["call"]["id"]
        otp_request = dao.get_by(call_id=call_id)
        if not otp_request:
            logger.info("Couldn't find otp request for call_id: %s", call_id)
            return
        otp_request.answer_time = datetime.now(timezone.utc)
        otp_request.answered = True
        dao.edit(otp_request)
        for index, uri in enumerate(otp_request.uris):
            logger.info("sending URI [%d]: %s", index, uri)
            playback = {
                "uri": uri,
                "language": otp_request.language,
                "state": "play"
            }
            playback = self.calld_client.applications.send_playback(
                otp_request.application_uuid, otp_request.call_id, playback)
        # self.calld_client.applications.hangup_call(otp_request.application_uuid, otp_request.call_id)
        ###

    # def application_playback_created(self, event):
    #     campaign_contact_call = self.find_last_campaign_contact_call(
    #         event["application_uuid"])
    #     campaign_contact_call.playback_created = datetime.now()
    #     self.campaign_contact_call_service.edit(campaign_contact_call)
    #     self.commit()

    def application_playback_deleted(self, event):
        logger.info("event playback deleted: %s", event)
        call_id = event['call']['id']
        otp_request = dao.get_by(call_id=call_id)
        if not otp_request:
            logger.info("Couldn't find otp request for call_id: %s", call_id)
            return
        last_uri = otp_request.uris[-1]
        event_uri = event['playback']['uri']
        if event_uri == last_uri:
            logger.info("Event URI matches the last URI in the OTP request. Hanging up call.")
            # self.hangup_application_call(event["application_uuid"])
            self.calld_client.applications.hangup_call(otp_request.application_uuid, call_id)
            otp_request.end_time = datetime.now(timezone.utc)
            dao.edit(otp_request)
        # campaign_contact_call = self.find_last_campaign_contact_call(
        #     event["application_uuid"])
        # campaign_contact_call.playback_deleted = datetime.now()
        # self.campaign_contact_call_service.edit(campaign_contact_call)
        # self.commit()
        # self.hangup_application_call(event["application_uuid"])

    # def application_call_deleted(self, event):
    #     call_id = event['call']['id']
    #     otp_request = dao.get_by(call_id=call_id)
    #     if not otp_request:
    #         logger.info("Couldn't find otp request for call_id: %s", call_id)
    #         return
    #     otp_request.end_time = datetime.now(timezone.utc)
    #     dao.edit(otp_request)

    # def find_next_campaign_contact_call(self, application_uuid):
    #     campaign = self.get_by(application_uuid=application_uuid)
    #     if campaign.state != "start" and campaign.state != "resume":
    #         return None

    #     next_call = self.campaign_contact_call_service.search({
    #         "campaign_uuid": campaign.uuid,
    #         "make_call": None,
    #         "limit": 1
    #     })
    #     if next_call.total:
    #         return next_call.items[0]
    #     else:
    #         return None

    # def find_last_campaign_contact_call(self, application_uuid):
    #     campaign = self.get_by(application_uuid=application_uuid)
    #     last_call = self.campaign_contact_call_service.get_last_cantact_call(
    #         campaign.uuid)
    #     return last_call

    # def create_application(self, tenant_uuid):
    #     application_name = f"{tenant_uuid}_campaign"
    #     application_args = {
    #         "name": application_name,
    #         "destination": "node",
    #         "destination_options": {
    #             "answer": True,
    #             "music_on_hold": "",
    #             "type": "holding"
    #         }
    #     }
    #     self.confd_client.tenant_uuid = tenant_uuid
    #     return self.confd_client.applications.create(application_args)

    # def delete_application(self, application_uuid):
    #     return self.confd_client.applications.delete(application_uuid)

    # def create_empty_campaign_contact_call(self, campaign):
    #     for contact_list in campaign.contact_lists:
    #         contact_list_with_contacts = self.contact_list_service.get_by(
    #             uuid=contact_list.uuid)
    #         for contact in contact_list_with_contacts.contacts:
    #             campaign_contact_call = CampaignContactCallModel()
    #             campaign_contact_call.phone = contact.phone
    #             campaign_contact_call.campaign_uuid = campaign.uuid
    #             campaign_contact_call.contact_list_uuid = contact_list.uuid
    #             campaign_contact_call.contact_uuid = contact.uuid
    #             self.campaign_contact_call_service.create(
    #                 campaign_contact_call)

    #     Session.commit()

    # def delete_empty_campaign_contact_call(self, campaign):
    #     campaign_contact_call_canceled = self.campaign_contact_call_service.search({
    #         "campaign_uuid": campaign.uuid,
    #         "make_call": None
    #     })
    #     if campaign_contact_call_canceled.total:
    #         for campaign_contact_call in campaign_contact_call_canceled.items:
    #             self.campaign_contact_call_service.delete(
    #                 campaign_contact_call)

    #     Session.commit()

    # def make_next_application_call(self, application_uuid):
    #     campaign = self.get_by(application_uuid=application_uuid)
    #     campaign_contact_call = self.find_next_campaign_contact_call(
    #         application_uuid)
    #     if campaign_contact_call is None:
    #         self.finish(application_uuid)
    #         return

    #     campaign_contact_call.make_call = datetime.now()
    #     self.campaign_contact_call_service.edit(campaign_contact_call)
    #     self.commit()

    #     call_args = {
    #         "autoanswer": True,
    #         "context": campaign.context,  # Use campaign's context
    #         "displayed_caller_id_name": "",
    #         "displayed_caller_id_number": "",
    #         "exten": campaign_contact_call.phone,
    #         "variables": {}
    #     }
    #     try:
    #         self.calld_client.applications.make_call(
    #             application_uuid, call_args)
    #     except:
    #         logging.error(traceback.format_exc())

    #     thread = Thread(target=self.make_next_application_call_if_not_answered, args=(
    #         application_uuid,))
    #     thread.start()

    # def make_next_application_call_if_not_answered(self, application_uuid):
    #     logger.warning("Waiting for answer...")
    #     campaign = self.get_by(application_uuid=application_uuid)
    #     time.sleep(campaign.answer_wait_time)
    #     campaign_contact_call = self.find_last_campaign_contact_call(
    #         application_uuid)
    #     if campaign_contact_call \
    #             and campaign_contact_call.make_call is not None \
    #             and campaign_contact_call.call_answered is None:
    #         self.make_next_application_call(application_uuid)

    # def hangup_application_call(self, application_uuid):
    #     calls = self.calld_client.applications.list_calls(application_uuid)
    #     if calls.items:
    #         for call in calls["items"]:
    #             self.calld_client.applications.hangup_call(
    #                 application_uuid, call["id"])

    # def play_music(self, application_uuid, call_id):
    #     campaign = self.get_by(application_uuid=application_uuid)
    #     # playback = {
    #     #     "uri": "sound:/var/lib/wazo/sounds/tenants/501ec54b-aa48-4492-bc5c-7af59c20705f/campaign/campagin_test"
    #     # }
    #     playback = {
    #         "uri": "sound:" + campaign.playback_file
    #     }
    #     playback = self.calld_client.applications.send_playback(
    #         application_uuid, call_id, playback)
    #     return playback

    # def commit(self):
    #     try:
    #         Session.commit()
    #     except:
    #         Session.rollback()
    #         logging.error(traceback.format_exc())
