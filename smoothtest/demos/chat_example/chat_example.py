# -*- coding: utf-8 -*-
'''
Websockets chat example taken from:
http://runnable.com/UqDMKY-VwoAMABDk/simple-websockets-chat-with-tornado-for-python
'''
import tornado.ioloop
import tornado.web
import tornado.websocket

port = 8080

clients = []

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(request): #@NoSelf
        request.render('chat_example.html')

class WebSocketChatHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print("open", "WebSocketChatHandler")
        clients.append(self)
    
    def on_message(self, message):        
        print message
        for client in clients:
            client.write_message(message)
          
    def on_close(self):
        clients.remove(self)

def main():
    app = tornado.web.Application([(r'/chat', WebSocketChatHandler), (r'/', IndexHandler)])
    
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
