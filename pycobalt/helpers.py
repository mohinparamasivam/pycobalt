"""
Helper functions for writing pycobalt scripts
"""

import argparse
import inspect

import pycobalt.aggressor as aggressor
import pycobalt.callbacks as callbacks
import pycobalt.engine as engine
import pycobalt.utils as utils

def parse_ps(content):
    """
    Parse output of bps()

    Returns: [{name, ppid, pid, arch, user}...]
    """

    procs = []
    for line in content.splitlines():
        proc = {}
        proc['name'], proc['ppid'], proc['pid'], *others = line.split('\t')

        # convert numbers
        proc['pid'] = int(proc['pid'])
        proc['ppid'] = int(proc['ppid'])

        # get arch
        if len(others) > 1:
            proc['arch'] = others[0]

        # get user
        if len(others) > 2:
            proc['user'] = others[1]

        procs.append(proc)

    # sort it
    procs = list(sorted(procs, key=lambda item: item['pid']))

    return procs

def find_process(bid, proc_name, callback):
    """
    Find processes by name. Call callback([{name, pid, ppid, arch?, user?}, ...]) with results.
    """

    def ps_callback(bid, content):
        procs = parse_ps(content)
        ret = filter(lambda p: p['name'] == proc_name, procs)
        callback(ret)

    aggressor.bps(bid, ps_callback)

def is_admin(bid):
    """
    Check if beacon is admin (including SYSTEM)
    """

    if aggressor.isadmin(bid):
        return True

    user = aggressor.beacon_info(bid, 'user')
    if user.lower() == 'system':
        return True

    return False;

def default_listener():
    """
    Make a semi-educated guess at which listener might be the default one
    """

    listeners = aggressor.listeners_local()

    if not listeners:
        return None

    for listener in listeners:
        if 'http' in listener:
            return listener

    return listeners[0]

def explorer_stomp(bid, fname):
    """
    Stomp time with time of explorer.exe
    """

    aggressor.btimestomp(bid, fname, r'c:/windows/explorer.exe')

def uploadto(bid, local_file, remote_file):
    """
    Upload local file to a specified remote destination
    """

    with open(local_file, 'rb') as fp:
        data = fp.read()

    aggressor.bupload_raw(bid, remote_file, data, local_file)

def guess_home(bid):
    """
    Guess %userprofile% directory based on beacon user
    """

    return r'c:\users\{}'.format(aggressor.beacon_info(bid)['user'])

def guess_temp(bid):
    """
    Guess %temp% directory based on beacon user
    """

    return r'{}\AppData\Local\Temp'.format(guess_home(bid))

class ArgumentParser(argparse.ArgumentParser):
    """
    Special version of ArgumentParser that prints to beacon console or script
    console instead of stdout
    """

    def __init__(self, bid=None, *args, **kwargs):
        self.bid = bid

        if 'prog' not in kwargs:
            # fix prog name
            kwargs['prog'] = 'command'

        super().__init__(*args, **kwargs)

    def error(self, message):
        if self.bid:
            # print to beacon console
            aggressor.berror(self.bid, message)
        else:
            # print to script console
            engine.error(message)
        raise argparse.ArgumentError('exit')

    def exit(self, status=0, message=None):
        self.error(message)

    def print_usage(self, file=None):
        self.error(super().format_usage())

    def print_help(self, file=None):
        self.error(super().format_help())
