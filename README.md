# django_async_service_inbuilt_celery_tasks
## Universal service django class with inbuild celery tasks:
### To set up this class in your project implement your personal logic in AsyncFileService
- **XLSFileValidator**: service uses XLS file as an example, but any type will work, just modify validation class if needed;
- **_get_data_from_file**: implement your personal logic of preprocessing file data;
- **_perform_sync**: implement your logic that that needs to be performed depending on file content;

Additionally implement email messaging functionality through the service you are using in **send_email** or connect directly to your service in points **send_email** in used.
