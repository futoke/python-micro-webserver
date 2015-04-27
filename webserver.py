# -*- coding: utf-8 -*-

import sqlite3
import codecs
import BaseHTTPServer
from os import getcwd
from urllib import unquote_plus, urlencode
from mimetypes import types_map
from os.path import join, basename, splitext


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    def run_sql(self, sql, db_name='base.db'):
        if '' in (sql, db_name):
            return ''
        try:
            con = sqlite3.connect(db_name)
            cur = con.cursor()
            cur.execute(sql)
            if sql.upper().startswith('SELECT'):
                title = [cols[0].decode('utf-8') for cols in cur.description]
                data = cur.fetchall()
                return self.table_view(title, data)
            else:
                return ''
        except sqlite3.Error as e:
            return 'An error occurred - ' + ''.join(e.args).decode('utf-8')
        finally:
            con.close()


    def table_view(self, title, data):
        c_row = lambda tmpl, lst: u''.join([tmpl.format(item) for item in lst])
        hdr = u'<tr>{0}</tr>'.format(c_row(u'<th>{0}</th>', title))
        bod = [u'<tr>{0}</tr>'.format(c_row(u'<td>{0}</td>', rw)) for rw in data]
        return u'<table>{0}</table>'.format(u''.join([hdr] + bod))


    def do_HEAD(self, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()


    def do_GET(self, sql=''):
        try:
            if self.path == "/":
                 self.path = "/index.html"
            if self.path == "/favicon.ico":
                 return
            _, ext = splitext(self.path)
            with codecs.open(join(getcwd(), basename(self.path)),
                             encoding='utf-8', mode='rU') as f:
                self.do_HEAD(types_map[ext])
                if ext  == '.html':
                    doc = f.read().format(self.run_sql(sql))
                    self.wfile.write(doc.encode('utf-8'))
                if ext  == '.css':
                    self.wfile.write(f.read())
        except IOError:
            self.send_error(404)


    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        try:
            _, value = self.rfile.read(content_length).split('=')
            self.do_GET(unquote_plus(value).decode('utf-8'))
        except ValueError:
            self.do_GET('')


class WebServer(BaseHTTPServer.HTTPServer):

    def __init__(self, host='', port=9000):
        BaseHTTPServer.HTTPServer.__init__(self, (host, port), Handler)
        try:
            print "Look mom it's my first application server"
            self.serve_forever()
        except KeyboardInterrupt:
            self.server_close()


if __name__ == '__main__':
    webserver = WebServer()