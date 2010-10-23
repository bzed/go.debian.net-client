#!/usr/bin/env python
# Copyright (c) 2010 Eric S. Raymond <esr@thyrsus.com>
# Copyright (c) 2010 Bernd Zeimetz <bzed@debian.org>
# Distributed under BSD terms.
#
# This script contains porcelain and porcelain byproducts.
# It's Python because the Python standard libraries avoid portability/security
# issues raised by callouts in the ancestral Perl and sh scripts.  It should
# be compatible back to Python 2.1.5
#
# usage: ciabot.py [-V] [-n] [-p projectname]  [refname [commits...]]
#
# This script is meant to be run either in a post-commit hook or in an
# update hook.  If there's nothing unusual about your hosting setup,
# you can specify the project name and repo with config variables and
# avoid having to modify this script.  Try it with -n to see the
# notification mail dumped to stdout and verify that it looks
# sane. With -V it dumps its version and exits.
#
# In post-commit, run it without arguments. It will query for
# current HEAD and the latest commit ID to get the information it
# needs.
#
# In update, call it with a refname followed by a list of commits:
# You want to reverse the order git rev-list emits becxause it lists
# from most recent to oldest.
#
# /path/to/ciabot.py ${refname} $(git rev-list ${oldhead}..${newhead} | tac)
#
# Configuration variables affecting this script:
# ciabot.project = name of the project (required)
# ciabot.repo = name of the project repo for gitweb/cgit purposes
# ciabot.xmlrpc  = if true, ship notifications via XML-RPC 
# ciabot.revformat = format in which the revision is shown
#
# The ciabot.repo defaults to ciabot.project lowercased. 
#
# The revformat variable may have the following values
# raw -> full hex ID of commit
# short -> first 12 chars of hex ID
# describe = -> desescription relative to last tag, falling back to short
# The default is 'describe'.
#
# Note: the shell ancestors of this script used mail, not XML-RPC, in
# order to avoid stalling until timeout when the CIA XML-RPC server is
# down. It is unknown whether this is still an issue in 2010, but we
# default to mail just in case. (Using XML-RPC guarantees that multiple
# notifications shipped from a commit hook will arrive in order.)
#

import os, sys, commands, socket, urllib

# Changeset URL prefix for your repo: when the commit ID is appended
# to this, it should point at a CGI that will display the commit
# through gitweb or something similar. The defaults will probably
# work if you have a typical gitweb/cgit setup.
#
urlprefix = "http://%(host)s/?p=%(repo)s;a=commit;h="

# The template used to generate the XML messages to CIA.  You can make
# visible changes to the IRC-bot notification lines by hacking this.
# The default will produce a notfication line that looks like this:
#
# ${project}: ${author} ${repo}:${branch} * ${rev} ${files}: ${logmsg} ${url}
#
# By omitting $files you can collapse the files part to a single slash.
xml = '''\
<message>
  <generator>
    <name>CIA Python client for Git</name>
    <version>%(version)s</version>
    <url>%(generator)s</url>
  </generator>
  <source>
    <project>%(project)s</project>
    <branch>%(repo)s:%(branch)s</branch>
  </source>
  <timestamp>%(ts)s</timestamp>
  <body>
    <commit>
      <author>%(author)s</author>
      <revision>%(rev)s</revision>
      <files>
        %(files)s
      </files>
      <log>%(logmsg)s %(url)s</log>
      <url>%(url)s</url>
    </commit>
  </body>
</message>
'''

#
# No user-serviceable parts below this line:
#

# Where to ship e-mail notifications.
toaddr = "cia@cia.navi.cx"

# Identify the generator script.
# Should only change when the script itself gets a new home and maintainer.
generator = "http://deb.li/ciabot"
version = "3.3-bz1"

try:
    from anyjson import serialize, deserialize
except ImportError:
    #there is no anyjson/cjson on alioth yet.
    from json import write as serialize, read as deserialize


def do(command):
    return commands.getstatusoutput(command)[1]

def report(refname, merged):
    "Generate a commit notification to be reported to CIA"

    # Try to tinyfy a reference to a web view for this commit.
    try:
        postdata = serialize({"method": "add_url", 'params': ["%s%s" %(urlprefix, merged) ], 'id':'ciab
        respdata = urllib.urlopen("http://deb.li/rpc/json", postdata).read()
        resp = deserialize(respdata)
        if resp['error'] != None:
            raise Exception(resp['error'])
        url = "http://deb.li/%s" %(resp['result'], )

    except:
        url = urlprefix + merged

    branch = os.path.basename(refname)

    # Compute a description for the revision
    if revformat == 'raw':
        rev = merged
    elif revformat == 'short':
        rev = ''
    else: # rev == 'describe'
        rev = do("git describe %s 2>/dev/null" % merged)
    if not rev:
        rev = merged[:12]

    # Extract the neta-information for the commit
    files=do("git diff-tree -r --name-only '"+ merged +"' | sed -e '1d' -e 's-.*-<file>&</file>-'")
    metainfo = do("git log -1 '--pretty=format:%an <%ae>%n%at%n%s' " + merged)
    (author, ts, logmsg) = metainfo.split("\n")

    # This discards the part of the authors addrsss after @.
    # Might be be nice to ship the full email address, if not
    # for spammers' address harvesters - getting this wrong
    # would make the freenode #commits channel into harvester heaven.
    author = author.replace("<", "").split("@")[0].split()[-1]

    # This ignores the timezone.  Not clear what to do with it...
    ts = ts.strip().split()[0]

    context = locals()
    context.update(globals())

    out = xml % context

    message = '''\
Message-ID: <%(merged)s.%(author)s@%(project)s>
From: %(fromaddr)s
To: %(toaddr)s
Content-type: text/xml
Subject: DeliverXML

%(out)s''' % locals()

    return message

if __name__ == "__main__":
    import getopt

    # Get all config variables
    revformat = do("git config --get ciabot.revformat")
    project = do("git config --get ciabot.project")
    repo = do("git config --get ciabot.repo")
    xmlrpc = do("git config --get xmlrpc")
    xmlrpc = xmlrpc and xmlrpc != "false"

    host = socket.getfqdn()
    fromaddr = "CIABOT-NOREPLY@" + host

    try:
        (options, arguments) = getopt.getopt(sys.argv[1:], "np:V")
    except getopt.GetoptError, msg:
        print "ciabot.py: " + str(msg)
        raise SystemExit, 1

    notify = True
    for (switch, val) in options:
        if switch == '-p':
            project = val
        elif switch == '-n':
            notify = False
        elif switch == '-V':
            print "ciabot.py: version", version
            sys.exit(0)

    # Cough and die if user has not specified a project
    if not project:
        sys.stderr.write("ciabot.py: no project specified, bailing out.\n")
        sys.exit(1)

    if not repo:
        repo = project.lower()

    urlprefix = urlprefix % globals()

    # The script wants a reference to head followed by the list of
    # commit ID to report about.
    if len(arguments) == 0:
        refname = do("git symbolic-ref HEAD 2>/dev/null")
        merges = [do("git rev-parse HEAD")]
    else:
        refname = arguments[0]
        merges = arguments[1:]

    if notify:
        if xmlrpc:
            import xmlrpclib
            server = xmlrpclib.Server('http://cia.navi.cx/RPC2');
        else:
            import smtplib
            server = smtplib.SMTP('localhost')

    for merged in merges:
        message = report(refname, merged)
        if not notify:
            print message
        elif xmlrpc:
            server.hub.deliver(message)
        else:
            server.sendmail(fromaddr, [toaddr], message)

    if notify:
        if not xmlrpc:
            server.quit()

#End
