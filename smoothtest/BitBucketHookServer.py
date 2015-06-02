# -*- coding: utf-8 -*-
'''
Websockets chat example taken from:

'''
import tornado.ioloop
import tornado.web
import simplejson
import tornado.httpserver
from tornado.options import define, options
import os
import logging

#import logging
#logging.disable(logging.INFO)
#logging.disable(logging.WARNING)
port = 8081

define("port", default=port, help="run on the given port", type=int)
define("debug", default=False, help="turn on tornado's debugging", type=bool)


class BitBucketHookHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('hook.html')

    def post(self):
        args = self._delist_args(self.request.arguments)
        try:
            self._process_commit_notification(self.request.body)
        except:
            self.render('hook.html')
            
    def _process_commit_notification(self, post_body):
        import ipdb; ipdb.set_trace()
        # Load bit bucket commit information
        bbcommit = simplejson.loads(post_body)

    def _delist_args(self, arguments):
        '''
        Requests arguments comes in a list if they are declared twice (POST and
        GET for example). Choose only one.
        :param arguments:
        '''
        def filterFunc(name, value):
            if len(value) > 1:
                self.context.log.d('Receiving more than one value for argument %r '
                                   '(values:%r). Using first value.' % (name, value))
            return True
        items = [(name, val[0]) for name, val in  self.request.arguments.items()
                 if filterFunc(name, val)]
        return dict(items)

def get_assets_root():
    return os.path.split(__file__)[0]

def main():
    tornado.options.parse_command_line()
    settings = dict(
      template_path=os.path.join(get_assets_root(), "html"),
      static_path=os.path.join(get_assets_root(), "static"),
      debug=options.debug, #TODO: configurable
    )
    handlers = [
                   (r'/', BitBucketHookHandler),
               ]
    app = tornado.web.Application(handlers, **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
