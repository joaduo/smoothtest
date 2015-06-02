# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import simplejson
import tornado.httpserver
from tornado.options import define, options
import os
import logging
import threading
import traceback
import Queue
from IPython.core import payload
from collections import namedtuple
from smoothtest.singleton_decorator import singleton_decorator

#import logging
#logging.disable(logging.INFO)
#logging.disable(logging.WARNING)
port = 8081

define("port", default=port, help="run on the given port", type=int)
define("debug", default=False, help="turn on tornado's debugging", type=bool)


ThreadCommand = namedtuple('ThreadCommand', 'cmd')

@singleton_decorator
class HooksRunner(threading.Thread):

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._queue = Queue.Queue()
        self._latest_payload = None
        self.hooks = {}

    def register_hook(self, name, hook):
        assert name not in self.hooks, 'Hook name already used: %r' % name
        self.hooks[name] = hook

    def submit_payload(self, payload):
        self._queue.put_nowait(payload)

    def run(self):
        while True:
            payload = self._queue.get()
            if isinstance(payload, ThreadCommand):
                if payload.cmd == 'stop':
                    logging.info('Stopping HooksRunner thread.')
                    break
                elif payload.cmd == 'retest':
                    if self._latest_payload:
                        self._run_hooks(self._latest_payload)
                    else:
                        logging.debug('No previous payload to retest.')
            else:
                self._latest_payload = payload
                self._run_hooks(payload)
            self._queue.task_done()

    def _run_hooks(self, payload):
        for i, jsoncommit in enumerate(payload):
            try:
                bbcommit = simplejson.loads(jsoncommit)
            except Exception as e:
                logging.warn('Exception raised for commit number %s.' % i)
                traceback.print_last()
                continue
            for name in sorted(self.hooks):
                logging.info('Running hook %r for commit number %s' %(name, i))
                try:
                    self.hooks[name](bbcommit)
                except Exception as e:
                    logging.warn('Exception raised for hook %r. Exception=%r: %s.'
                                 ' Bbcommit=%r' % (name, e,e, bbcommit))
                    traceback.print_last()



def delist_args(arguments):
    '''
    Requests arguments comes in a list if they are declared twice (POST and
    GET for example). Choose only one.
    :param arguments:
    '''
    def filterFunc(name, value):
        if len(value) > 1:
            logging.debug('Receiving more than one value for argument %r '
                          '(values:%r). Using first value.' % (name, value))
        return True
    items = [(name, val[0]) for name, val in  arguments.items()
             if filterFunc(name, val)]
    return dict(items)


class RetestHandler(tornado.web.RequestHandler):
    def get(self):
        args = delist_args(self.request.arguments)
        if args.get('retest'):
            HooksRunner().submit_payload(ThreadCommand('retest'))
        self.render('hook_retest.html')


class BitBucketHookHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('hook.html')

    def post(self):
        try:
            self._process_commit_notification()
        except Exception as e:
            logging.error('Exception %r:%s while receiving commit notification'
                          % (e,e))

    def _process_commit_notification(self): 
        # Load bit bucket commit information
        if not self.request.arguments['payload']:
            logging.warn('There are not commits.')
            return
        HooksRunner().submit_payload(self.request.arguments['payload'])


def get_this_file_dir():
    return os.path.split(__file__)[0]


def main(args=None):
    tornado.options.parse_command_line(args)
    settings = dict(
      template_path=os.path.join(get_this_file_dir(), "html"),
      static_path=os.path.join(get_this_file_dir(), "static"),
      debug=options.debug,
    )
    handlers = [
                   (r'/', BitBucketHookHandler),
                   (r'/retest', RetestHandler),
               ]
    app = tornado.web.Application(handlers, **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    # Start hooks thread
    hrunner = HooksRunner()
    hrunner.start()
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        hrunner.submit_payload(ThreadCommand('stop'))
        raise


if __name__ == "__main__":
    # Example server, printing each notification
    def print_bbcommit(bbcommit):
        from pprint import pprint
        pprint(bbcommit)

    def register_bb_hooks():
        HooksRunner().register_hook('printer', print_bbcommit)

    register_bb_hooks()
    main()

