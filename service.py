from typing import List, Dict

import xlrd
from celery import chain, Celery
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from requests import Request
from xlrd import Book

import settings
from validators import XLSFileValidator, SyncErrorMessage

celery_app = Celery("example")
celery_app.config_from_object("example", namespace="EXAMPLE")
celery_app.autodiscover_tasks()


def send_email_with_gmail(
        recipient_emails: str,
        subject: str,
        body: str,
        file: InMemoryUploadedFile
):
    # TODO: Set up logic of sending email here, using any service available to you
    sender_email: str = settings.DEFAULT_USER_EMAIL
    sender_password: str = settings.DEFAULT_USER_PASSWORD
    pass


class AsyncFileService:

    def __init__(self, file: InMemoryUploadedFile, initiator_email: str, request: Request) -> None:
        self._request = request

        self.initiator_email = initiator_email
        self._email_receivers = [self.initiator_email, settings.DEFAULT_USER_EMAIL]

        self._save_file_attributes(file=file)
        self._call_validator_and_create_messages()
        self._save_validated_file_content()

    def __call__(self, *args, **kwargs):
        if not self.file_validation_error_messages:
            chain(
                self._perform_sync.s(self._get_data_from_file()),
                self._send_email_results_to_receivers.s(self.initiator_email, self._email_receivers, self.file)
            )()
        else:
            self._send_file_validation_email_to_receiver()
        self.__show_summary_message()

    def _save_file_attributes(self, file: InMemoryUploadedFile) -> None:
        self.file: InMemoryUploadedFile = file
        self.file_name = self.file.name
        self.file_content_type: str = self.file.content_type

    def _save_validated_file_content(self) -> None:
        self.file.seek(0)
        self.file_content: bytes = self.file.read()
        self.file.seek(0)

    def _call_validator_and_create_messages(self) -> None:
        self.validator: XLSFileValidator = XLSFileValidator(file=self.file)
        self.file_validation_error_messages: list[SyncErrorMessage] = self.validator()

    def _get_data_from_file(self) -> List | Dict:
        workbook: Book = xlrd.open_workbook(
            file_contents=self.file_content,
            encoding_override="utf8"
        )
        file_data = []  # TODO: Add your custom content retrieval logic here
        return file_data

    @staticmethod
    @celery_app.task(name="Add your task name here")
    def _perform_sync(file_data: List | Dict):
        results: dict = {
            "error_messages": [],
            "success_messages": []
        }

        try:
            # TODO: Perform your logic with data received from in-memory file here:
            results["error_messages"].append(SyncErrorMessage(
                code=200,
                description="Add your success message here")
            )
        except Exception as exc:
            results["error_messages"].append(SyncErrorMessage(
                code=400,
                description=str(exc))
            )
        return results

    @staticmethod
    @celery_app.task(name="Имя задачи необходимо переопределить")
    def _send_email_results_to_receivers(
            result: dict, initiator_email: str, email_receivers: list[str], file: InMemoryUploadedFile
    ):
        errors_verbose = ""
        for error in result["error_messages"]:
            errors_verbose = errors_verbose + f"{error.description}" + "\n"

        success_verbose = ""
        for error in result["success_messages"]:
            errors_verbose = errors_verbose + f"{error.description}" + "\n"

        report_email_body: str = (
            f'User {initiator_email} uploaded file. Results: \n'
            f'{errors_verbose + success_verbose}'
        )

        for receiver in email_receivers:
            send_email_with_gmail(
                recipient_emails=receiver,
                subject="File upload result",
                body=report_email_body,
                file=file
            )

    def _send_file_validation_email_to_receiver(self):
        errors_verbose = ""
        for error in self.file_validation_error_messages:
            errors_verbose = errors_verbose + f"{error.description}" + "\n"

        report_file_attach_content: str = (
            f'User {self.initiator_email} uploaded file. File did not pass validation, validation errors: \n'
            f'{[f"{error.description}" for error in self.file_validation_error_messages ]}'
        )

        for receiver in self._email_receivers:
            send_email_with_gmail(
                recipient_emails=receiver,
                subject="File upload result",
                body=report_file_attach_content,
                file=self.file
            )

    def __show_error_message(self) -> None:
        messages.warning(
            self._request,
            f'Uploaded file raised {len(self.file_validation_error_messages)} validation errors.'
            f'You will receive and email with validation error details.'
        )

    def __show_success_message(self) -> None:
        messages.success(
            self._request,
            f'Валидация файла прошла успешно. Активирована фоновая задача обновления статусов CM отелей.'
        )

    def __show_summary_message(self) -> None:
        if not self.file_validation_error_messages:
            self.__show_success_message()
        else:
            self.__show_error_message()

