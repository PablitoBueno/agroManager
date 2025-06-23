from fastapi.responses import JSONResponse


def format_response(data, status_code=200):
    return JSONResponse(content={'data': data}, status_code=status_code)


def handle_errors(exc):
    # TODO: log e formatação
    return JSONResponse(content={'error': str(exc)}, status_code=500)

