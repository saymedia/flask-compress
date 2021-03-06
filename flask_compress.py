import gzip
try:
    from io import BytesIO as IO
except:
    import StringIO as IO

from flask import request


class Compress(object):
    """
    The Compress object allows your application to use Flask-Compress.

    When initialising a Compress object you may optionally provide your
    :class:`flask.Flask` application object if it is ready. Otherwise,
    you may provide it later by using the :meth:`init_app` method.

    :param app: optional :class:`flask.Flask` application object
    :type app: :class:`flask.Flask` or None
    """
    def __init__(self, app=None):
        """
        An alternative way to pass your :class:`flask.Flask` application
        object to Flask-Compress. :meth:`init_app` also takes care of some
        default `settings`_.

        :param app: the :class:`flask.Flask` application object.
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        defaults = [
            ('COMPRESS_MIMETYPES', ['text/html', 'text/css', 'text/xml',
                                    'application/json',
                                    'application/javascript']),
            ('COMPRESS_DEBUG', False),
            ('COMPRESS_LEVEL', 6),
            ('COMPRESS_MIN_SIZE', 500)
        ]

        for k, v in defaults:
            app.config.setdefault(k, v)

        if app.config['COMPRESS_MIMETYPES']:
            self.app.after_request(self.after_request)

    def after_request(self, response):

        # return the response untouched for responses that will never be
        # gzipped, in any contexts.
        if response.mimetype not in self.app.config['COMPRESS_MIMETYPES']:
            return response

        # At this point, always put the Vary header, even if the content
        # is not gzipped in this particular context.
        # Also, apparently, werkzeug has no documented method to "add", not "set", a header.
        # So we rely on comma separated values.
        if 'Vary' in response.headers and response.headers['Vary'] is not None and response.headers['Vary'] != "":
            response.headers['Vary'] += ', Accept-Encoding'
        else:
            response.headers['Vary'] = 'Accept-Encoding'

        if self.app.debug and not self.app.config['COMPRESS_DEBUG']:
            return response

        accept_encoding = request.headers.get('Accept-Encoding', '')

        if 'gzip' not in accept_encoding.lower():
            return response

        response.direct_passthrough = False

        if (response.status_code < 200 or
            response.status_code >= 300 or
            len(response.data) < self.app.config['COMPRESS_MIN_SIZE'] or
            'Content-Encoding' in response.headers):
            return response

        level = self.app.config['COMPRESS_LEVEL']

        gzip_buffer = IO()
        gzip_file = gzip.GzipFile(mode='wb', compresslevel=level,
                                  fileobj=gzip_buffer)
        gzip_file.write(response.data)
        gzip_file.close()

        response.data = gzip_buffer.getvalue()
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(response.data)

        return response
