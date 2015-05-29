# -*- coding: utf-8 -*-
'''
Websockets chat example taken from:

'''
import tornado.ioloop
import tornado.web
import tornado.websocket
import simplejson
from smoothtest.singleton_decorator import singleton_decorator
import tornado.httpserver
from tornado.options import define, options
import os

#import logging
#logging.disable(logging.INFO)
#logging.disable(logging.WARNING)
port = 8080

define("port", default=port, help="run on the given port", type=int)


'''
When a tests is fired, submit it to the server via post/get
  - I can get HTML example from HTMLTestRunner, and submit such thing?
  (no need, simply submit the information)
  - We can submit info from TestRunner for each test 
Then we notify all clients of the new test and its results (displaying screenshots if needed)
We need to know how to notify per test ran.
'''



@singleton_decorator
class ClientsManager(object):
    def __init__(self):
        self.clients = []
        
    def append(self, client):
        self.clients.append(client)
        
    def remove(self, client):
        self.clients.remove(client)
        
    def write_clients(self, message):
        for client in self.clients:
            client.write_message(message)


class TestResults(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('tests.html')

        
class SubmitTestHandler(tornado.web.RequestHandler):
    def post(self):
        args = self._delist_args(self.request.arguments)
        if 'test_result' in args:
            test_result = simplejson.loads(args['test_result'])
            ClientsManager().write_clients(args['test_result'])
            print test_result

    def get(self): #@NoSelf
        self.render('submit.html')

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


class WebSocketTestReport(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        ClientsManager().append(self)
    
    def on_message(self, message):
        ClientsManager().write_clients(message)        
        print message
          
    def on_close(self):
        ClientsManager().remove(self)


def getWebClientRoot():
    return os.path.split(__file__)[0]

def main():
    settings = dict(
      template_path=os.path.join(getWebClientRoot(), "html"),
      static_path=os.path.join(getWebClientRoot(), "static"),
      debug=True, #TODO: configurable
    )
    handlers = [
                   (r'/', TestResults),
                   (r'/updates', WebSocketTestReport), 
                   (r'/submit', SubmitTestHandler),
               ]
    print settings['static_path']
    print settings['template_path']
    app = tornado.web.Application(handlers, **settings)
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
