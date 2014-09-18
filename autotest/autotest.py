# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import tornado.web
import tornado.netutil
from tornado.httpserver import HTTPServer
from smoothtest.autotest.ioloop import AtSelectIOLoop, install,AtPollZMQIOLoop
install(AtSelectIOLoop)
#install(AtPollZMQIOLoop)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hi Sandeep, Welcome to Tornado Web Framework.")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    sockets = tornado.netutil.bind_sockets(8888)
    #We need to close sockets in the child process just in case
#    _UnblockSelect.select.set_sockets(sockets)
    #tornado.process.fork_processes(1)
    server = HTTPServer(application)
    server.add_sockets(sockets)
    #import tornado.autoreload
    io_loop = tornado.ioloop.IOLoop.instance()
    #tornado.autoreload.start(io_loop, check_time=3600)
    io_loop.start()
