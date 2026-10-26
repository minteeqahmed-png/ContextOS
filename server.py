"""ContextOS launcher; backend is also exposed for existing test clients."""
import os
import sys
import backend
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(backend.app, host='127.0.0.1', port=int(os.environ.get('PORT','8000')))
else:
    sys.modules[__name__] = backend
