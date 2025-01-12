from dataclasses import dataclass

import xlrd
from django.core.files.uploadedfile import InMemoryUploadedFile
from xlrd import Book
from xlrd.sheet import Sheet


@dataclass
class SyncMessage:
    code: int
    description: str


@dataclass
class SyncErrorMessage(SyncMessage):
    pass


@dataclass
class SyncSuccessMessage(SyncMessage):
    pass


class FileErrorMessageCollector:
    FILE_SIZE_LIMIT: int = 20 * 1024 * 1024  # Set custom file size limit
    FILE_EXTENSION: str = 'xls'              # Adapt for other file types

    def __init__(self):
        self.VALIDATION_ERRORS: list[SyncErrorMessage] = []

    def _append_error_message(self, code: int, details: str) -> None:
        self.VALIDATION_ERRORS.append(
            SyncErrorMessage(
                code=code,
                description=details
            )
        )

    def _append_error_message__empty_file(self) -> None:
        self._append_error_message(400, "File is empty")

    def _append_error_message__file_corrupted(self, exception_detail) -> None:
        self._append_error_message(500, f'Error reading file: {exception_detail}')

    def _append_error_message__file_limit_size(self) -> None:
        self._append_error_message(
            code=400,
            details=f'File over the size limit {self.FILE_SIZE_LIMIT}'
        )

    def _append_error_message__file_extension(self) -> None:
        self._append_error_message(
            code=400,
            details=f'Unexpected file extension: {self.FILE_EXTENSION}'
        )

    def _append_error_message__empty_cell(self, cell_number: int, row_number: int) -> None:
        self._append_error_message(
            code=400,
            details=f'Пустая ячейка {cell_number} в строке: {row_number + 1}'
        )

    def _append_error_message__more_than_one_sheet(self) -> None:
        self._append_error_message(
            code=400,
            details="XLS файл содержит больше чем один лист"
        )

    def _append_error_message__col_count(self, row_number: int, expected_len) -> None:
        self._append_error_message(
            code=400,
            details=f'Строка {row_number + 1} содержит не {expected_len} столбец(ов)'
        )


class XLSFileValidator(FileErrorMessageCollector):
    def __init__(self, file: InMemoryUploadedFile):
        super().__init__()
        self._file: InMemoryUploadedFile = file
        self._try_read_file()

    def __call__(self, *args, **kwargs) -> list[SyncErrorMessage]:
        self._validate_file_object()
        return self.VALIDATION_ERRORS

    @property
    def _validate_methods(self):
        return (
            self._check_file_size,
            self._check_file_extension,
            self._validate_sheets_count,
            self._validate_other,
        )

    def _validate_file_object(self) -> None:
        for validate_method in self._validate_methods:
            if not self.VALIDATION_ERRORS:
                validate_method()

    def _try_read_file(self):
        try:
            self.file_content: bytes = self._file.read()
        except Exception as error:
            self._append_error_message__file_corrupted(exception_detail=error)

    def _get_xlrdbook_and_sheet(self) -> (Book, Sheet):
        workbook: Book = xlrd.open_workbook(
            file_contents=self.file_content,
            encoding_override="utf8"
        )
        worksheet: Sheet = workbook.sheet_by_index(0)

        return workbook, worksheet

    def _check_file_size(self) -> None:
        if self._file.size > self.FILE_SIZE_LIMIT:
            self._append_error_message__file_limit_size()

    def _check_file_extension(self) -> None:
        if self._file.name.split('.')[-1] != self.FILE_EXTENSION:
            self._append_error_message__file_extension()

    def _validate_sheets_count(self) -> None:
        workbook, _ = self._get_xlrdbook_and_sheet()

        if len(workbook.sheet_names()) != 1:
            self._append_error_message__more_than_one_sheet()

    def _validate_other(self) -> None:
        # TODO: add your custom validation here
        pass
