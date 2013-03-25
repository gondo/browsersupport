# @gondo http://gondo.webdesigners.sk


import sublime
import sublime_plugin
import re
import urllib2
import threading 
from bs4 import BeautifulSoup


class BrowserSupportCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()[0]

        # TODO: add logic to check if scope is multiline and if so, detect cursor on current line
        if sel.empty():
            pointer = sel.begin()
            scope = self.view.extract_scope(pointer)            
            search = self.view.substr(scope)
            # clean CSS property in the special cases (when it contains :, ;)
            re_search = re.search('([a-z-]+)', search, re.I)
            if re_search:
                search = re_search.group()
        else:
            sel = self.view.word(sel)
            search = self.view.substr(sel)

        self.search(search)



    def search(self, search):
        thread = BrowserSupportApiCall(self.view, search, 5)
        thread.start()
        self.handle_thread(thread)



    def handle_thread(self, thread, i=0):
        if thread.isAlive():
            i = i % 4
            animation = ['-', '\\', '|', '/']
            self.view.set_status(__name__, __name__ + ' ( ' + animation[i] + ' ) ')
            sublime.set_timeout(lambda: self.handle_thread(thread, i+1), 100)
        else:
            self.view.erase_status(__name__)
            if (thread.result):
                self.parse_result(thread.result, thread.search)
            if (thread.err):
                sublime.error_message(thread.err)



    def parse_result(self, result, search):
        soup = BeautifulSoup(result)
        table = soup.find('table', {'class': 'main'})

        if table is None:
            sublime.error_message('%s: Result not parsed. Multiple results occurred while searching for "%s"' % (__name__, search))
            return

        browsers = []
        browser_support = {}
        for th in table.select('thead th'):
            if th.string:
                browser = th.string
                browsers.append(browser)
                browser_support[browser] = None

        for tr in table.select('tbody tr'):
            for i, td in enumerate(tr.select('td')):
                if any(x in td['class'] for x in ['a', 'y']):
                    browser = browsers[i]
                    if browser_support[browser] == None:
                        browser_version = td.contents[0]
                        if len(td.contents) == 4:
                            browser_prefix = td.contents[3].string
                            browser_version += ' ' + browser_prefix
                        browser_support[browser] = browser_version

        output = []
        for browser in browser_support:
            if browser_support[browser]:
                output.append(browser + ': ' + browser_support[browser])

        self.show_output(output)



    # tooltip would be perfect
    def show_output(self, list):
        self.view.window().show_quick_panel(list, self.on_done)
        # differnet output methods:
        # self.view.window().show_input_panel(__name__ + ':', ', '.join(list), self.on_done, None, None)
        # sublime.status_message(__name__ + ': ' + ', '.join(list))
        self.view.erase_status(__name__)
        self.view.set_status(__name__, ', '.join(list))



    def on_done(self, value):
        return



class BrowserSupportApiCall(threading.Thread):
    def __init__(self, view, search, timeout):
        self.view = view
        self.search = search
        self.timeout = timeout
        self.result = None
        self.err = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            request = urllib2.Request('http://caniuse.com/' + self.search, None, headers={'User-Agent': 'Sublime'})
            http_file = urllib2.urlopen(request, timeout=5)
            self.result = http_file.read()
            return

        except (urllib2.HTTPError) as (e):
            # err = '%s: HTTP error: %s' % (__name__, str(e.code))
            err = '%s: No info for %s' % (__name__, self.search)
        except (urllib2.URLError) as (e):
            err = '%s: URL error: %s' % (__name__, str(e.reason))

        self.err = err
        self.result = False


