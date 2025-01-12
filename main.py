from aiohttp import web
import aiohttp_jinja2
import jinja2

from service import AsyncFileService

# Initialize Jinja2 template rendering
aiohttp_jinja2.setup(
    app=web.Application(),
    loader=jinja2.FileSystemLoader('templates')
)

async def home(request):
    return web.Response(text="")


@aiohttp_jinja2.template('upload_file.html')
async def upload_file(request):
    if request.method == 'GET':
        return {'message': 'Hello, World! This is the home page.'}
    elif request.method == 'POST':
        reader = await request.multipart()
        field = await reader.next()

        if field.name != 'file':
            return web.Response(text="Expected a file field named 'file'", status=400)

        file_bytes = await field.read()
        file_name = field.filename
        content_type = field.headers.get('Content-Type', 'application/octet-stream')
        file_size = len(file_bytes)
        uploaded_file = InMemoryUploadedFile(file_bytes, file_name, content_type, file_size)

        initiator_email: str = request.user.email

        AsyncFileService(
            file=file,
            initiator_email=initiator_email,
            request=request
        )()

        return redirect("admin:index")
    return web.Response(text="Hello, World! This is your single route.")


def create_app():
    app = web.Application()
    app.router.add_get('/', home)
    app.router.add_get('/upload_file', upload_file)  # Route for the home page
    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='127.0.0.1', port=8000)
