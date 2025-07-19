import os
from marshmallow import fields, validates, ValidationError, validates_schema
from wazo_confd.helpers.mallow import BaseSchema
from xivo.mallow.validate import Length, OneOf, Range, Regexp

class ReportRequestSchema(BaseSchema):
    application_uuid = fields.Str(required=True)

class ReportItemRequestSchema(BaseSchema):
    id = fields.Str(required=True)
    application_uuid = fields.Str(required=True)

class OtpUploadRequestSchema(BaseSchema):
    language = fields.Str(
        required=True, 
        validate=OneOf(['en_US', 'fa_IR'])
    )
    file = fields.Raw(required=True)
    application_uuid = fields.Str(required=True)
    
    @validates_schema
    def validate_file(self, data, **kwargs):
        file = data.get('file')

        if not file:
            raise ValidationError('No file uploaded.', field_name='file')

        if not hasattr(file, 'filename'):
            raise ValidationError('Invalid file type.', field_name='file')

        allowed_extensions = {'.mp3', '.wav'}
        filename = file.filename
        if '.' not in filename or os.path.splitext(filename)[1].lower() not in allowed_extensions:
            raise ValidationError(f'File type not allowed. Allowed: {", ".join(allowed_extensions)}', field_name='file')


class OtpRequestSchema(BaseSchema):
    application_uuid = fields.Str(required=True)
    language = fields.Str(
        required=True, 
        validate=OneOf(['en_US', 'fa_IR'])
    )
    uris = fields.List(fields.Str(), required=False)
    number = fields.Str(required=True)
    file = fields.Raw(required=False)
    tts = fields.Str(required=False)

    @validates_schema
    def validate_exclusive_fields(self, data, **kwargs):
        fields_present = [field for field in ['uris', 'file', 'tts'] if data.get(field) is not None]
        if len(fields_present) == 0:
            raise ValidationError("One of 'uris', 'file' must be provided.")
        elif len(fields_present) > 1:
            raise ValidationError("Only one of 'uris', 'file' can be provided.")

    @validates("uris")
    def validate_uris(self, uris):
        if uris is not None and not isinstance(uris, list):
            raise ValidationError("Uris must be a list of strings.")

    #     seen = set()
    #     for uri in uris:
    #         if not isinstance(uri, str):
    #             raise ValidationError(f"Invalid entry in uris: {uri} is not a string.")

    #         # # Check for duplicates
    #         # if uri in seen:
    #         #     raise ValidationError(f"Duplicate uri found: {uri}.")
    #         # seen.add(uri)

    #         # Split the string by ":"
    #         if ":" not in uri:
    #             raise ValidationError(f"Invalid uri format: '{uri}'. Missing ':' separator.")

    #         prefix, value = uri.split(":", 1)

    #         if prefix == "sound":
    #             if not value.isalpha():
    #                 raise ValidationError(f"Invalid 'sound' value: '{value}' must be a string.")
    #         elif prefix == "digits":
    #             if not value.isdigit():
    #                 raise ValidationError(f"Invalid 'digits' value: '{value}' must be a number.")
    #         else:
    #             raise ValidationError(f"Invalid uri prefix: '{prefix}'. Expected 'sound' or 'digits'.")
            
class OtpSchema(BaseSchema):
    uuid = fields.Str(dump_only=True)
    call_id = fields.Str(dump_only=True)
    tenant_uuid = fields.Str(dump_only=True)
    application_uuid = fields.Str(dump_only=True)
    number = fields.Str(required=True)
    caller_id_name = fields.Str(required=True)
    caller_id_number = fields.Str(required=True)
    answered = fields.Boolean(required=True)
    language = fields.Str(required=True)
    status = fields.Str(required=True)
    creation_time = fields.Date(required=True)
    end_time = fields.Date(required=False)
    answer_time = fields.Date(required=False)
    talking_to = fields.Dict(required=False)
    uris = fields.List(fields.Str(), required=False)

    # @validates("uris")
    # def validate_uris(self, uris):
    #     if not isinstance(uris, list):
    #         raise ValidationError("Uris must be a list of strings.")

    #     seen = set()
    #     for uri in uris:
    #         if not isinstance(uri, str):
    #             raise ValidationError(f"Invalid entry in uris: {uri} is not a string.")

    #         # Check for duplicates
    #         # if uri in seen:
    #         #     raise ValidationError(f"Duplicate uri found: {uri}.")
    #         # seen.add(uri)

    #         # Split the string by ":"
    #         if ":" not in uri:
    #             raise ValidationError(f"Invalid uri format: '{uri}'. Missing ':' separator.")

    #         prefix, value = uri.split(":", 1)

    #         if prefix == "sound":
    #             if not value.isalpha():
    #                 raise ValidationError(f"Invalid 'sound' value: '{value}' must be a string.")
    #         elif prefix == "digits":
    #             if not value.isdigit():
    #                 raise ValidationError(f"Invalid 'digits' value: '{value}' must be a number.")
    #         else:
    #             raise ValidationError(f"Invalid uri prefix: '{prefix}'. Expected 'sound' or 'digits'.")