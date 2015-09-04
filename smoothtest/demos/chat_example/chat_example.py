# -*- coding: utf-8 -*-
'''
Websockets chat example taken from:
http://runnable.com/UqDMKY-VwoAMABDk/simple-websockets-chat-with-tornado-for-python
'''
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import define, options, parse_command_line
import logging

clients = []

default_port = 8002

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(request): #@NoSelf
        request.render('chat_example.html', server_port=options.port)

class WebSocketChatHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        logging.debug("open WebSocketChatHandler")
        clients.append(self)
    
    def on_message(self, message):        
        logging.debug(message)
        for client in clients:
            client.write_message(message)
          
    def on_close(self):
        clients.remove(self)

def main(args=None):
    # CLI options
    define("port", default=default_port, help="run on the given port", type=int)
    define("debug", default=False, help="Turn on tornado's debugging", type=bool)
    # Parse options
    parse_command_line(args)
    settings = dict(
#      template_path=os.path.join(get_this_file_dir(), "html"),
#      static_path=os.path.join(get_this_file_dir(), "static"),
      debug=True #options.debug,
    )
    handlers = [(r'/', IndexHandler), (r'/chat', WebSocketChatHandler)]
    app = tornado.web.Application(handlers, **settings)
    app.listen(options.port)
    logging.debug('Starting tornado server at port http://localhost:%s/', options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
