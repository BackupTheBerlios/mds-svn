#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Global TODO:
  + installing ebuild
  - deal with different kinds of names in lists and user input
  + installing native unpacked metaball packages
  - installing from source (1 - building metaball from source. 2 - installing it)
  + building metaball packages
  - move from procedural code to object oriented
  - minimize shell usage
  - serparate from script configs and parsing
  - database for packages and apps
  - verbose(debug) and silent modes
  - make 'If application failed' cleaner for non debug modes and full rollback for failed install
  - progress bar for mb building (from gentoo-wiki)
  - connect ebuild's optional require (USE) with flag switch or output
"""

import os
import re
import sys
import portage

glres = ""
helpdir='/usr/lib/mb/help'

## mbOverlay is going to be deprecated
##mbOverlay = '/usr/local/mb-portage'
##if not os.access(mbOverlay, os.F_OK):
##    os.makedirs(mbOverlay)
##os.environ['PORTDIR_OVERLAY'] = portage.settings['PORTDIR_OVERLAY'] + ' ' + mbOverlay


def analyzeTarget(target):
    """
    determines type of target file 
    """
    if os.access(target,os.F_OK):
        if '.list' in target:
            print 'the target is list'
            return 'blist'
        elif '.ebuild' in target:
            print 'the target in portage ebuild'
            return 'ebuild'
        elif '.mb' in target:
            print 'the target is metaball package'
            return 'mb'

def getPNameFromFile(filename):
    """
    get atom name from path
    usage:
        getPNameFromFile(path)
    """
    if '.ebuild' in filename:
        name = filename.split("/")[3]
        ebuildPWD = filename.split("/")
        ebuildFileName = ebuildPWD[-1]
        app = ebuildName = re.sub('\.ebuild','',ebuildFileName)
        name = app.split("-")[0]
        print name
    else:
        name = filename
    if name != "":
        return name
    else:
        print 'Error during package name defying'
        sys.exit()

def getGorupNameFromPath(path):
    """
    guess group of atom from path. Works when ebuild in portage
    like tree
    usage:
        getGorupNameFromPath(path) -> str group or 'None'
    """
    if '.ebuild' in path:
        try:
            name = path.split("/")[-3]
            return name
        except:
            return 'None'
    else:
        return 'None'

def getGroupAppNamesFromEbuild(path):
    """
    guess application name and group from ebuild header
    """
    if os.access(path,os.F_OK):
        ebuild = open(path, 'r')
    try:
        for line in ebuild.readlines():
            if ('$Header' in line):
                header = line
                url = header.split('/')
                ##print url
                group = url[len(url)-5]
                name = url[len(url)-4]
                app = name
            else:
                name = group = 'None'
        return name, group
    except:
        return 'None', 'None'
 
def doPDirs(name):
    """
    check and create if needed directiories for package building
    usage:
        doPDirs(name)
    """
    print 'Making package enviroument'
    if os.access('/tmp/mb',os.F_OK):
        os.system('rm /tmp/mb -rf')

def getDirSize(path):
    """
    recursively walks throw path and return total size
    getDirSize(path) -> int
    """
    filepath = path
    size=0
    for item in os.listdir(path):
        filepath = path + "/" + item
        if os.path.isfile(filepath):
            size = size + os.path.getsize(filepath)

        if os.path.isdir(filepath):
            size = size + getDirSize(filepath)
    return size

def findebuild(name,path):
    """
    reuturns last matching ebuild file (abspath) in path and subdirs
    usage:
    findebuild(name,path)
    """
    global glres
    res=''
    for item in os.listdir(path):
        if os.path.isfile(path+'/'+item):
            if name in item and 'ebuild' in item:
                res = path+'/'+item
                print res
                print '-------'
                print glres
                glres = res
        if os.path.isdir(path+'/'+item):
            findebuild(name,path+'/' + item)
        if res != '':
            glres = res

def installWalk(path):
    """
    Trys to install all files in paths and subdirs
    """
    filepath = path
    for item in os.listdir(path):
        filepath = path + "/" + item
        if os.path.isfile(filepath):
			if '.ebuild' in filepath:
				install(filepath)
        if os.path.isdir(filepath):
            installWalk(filepath)

def doMb(path, pkgname):
    """
    creates metaball image file from path
    doMB(path, pkgname)
    """
    pkgname = pkgname.split("/")[-1]
    dirSize = getDirSize(path)
    print 'Size of dir: ' + str(dirSize)
    try:
        os.system('dd if=/dev/zero of=/tmp/'+ pkgname +'.mb count='+str(dirSize/800))
        os.system("echo 'y' | mkfs.ext2 /tmp/"+pkgname+".mb &> /dev/null")
    except:
        print 'Error: make image failed, exiting'
        sys.exit()
    if os.access('/tmp/mbimage',os.F_OK):
        os.system('/tmp/mbimage -rf')
    os.makedirs('/tmp/mbimage')
    os.system('mount -o loop /tmp/' + pkgname + '.mb /tmp/mbimage')
    os.system('cp -r /tmp/mb/* /tmp/mbimage')
    os.system('umount -l /tmp/mbimage')
    os.system('rm /tmp/mbimage -rf')
    os.system('rm /tmp/mb -rf')

def build(filename):
    """
    builds metaball package from filename source
    usage:
        build(filename)
    """
    global glres
    doPDirs("")
    filename = filename[:-1]
    print filename
    overtrees = os.environ['PORTDIR_OVERLAY'].split(' ')
    ptrees = portage.settings['PORTDIR'].split(' ')
    alltrees = ptrees + overtrees
    for path in alltrees:
        print path
        findebuild(filename, path)
    ebuildtreepath = glres
    print ebuildtreepath
    ebuildtreegroup = glres.split('/')[-3]
    print ebuildtreegroup
    print 'group is:' + ebuildtreegroup
    atomname = getPNameFromFile(ebuildtreepath)
    ebuild = ebuildtreepath.split('/')[-1]
    ebuildtreedir=os.path.split(ebuildtreepath)[0]
    print 'name is:' + atomname
    #try:
    os.makedirs('/tmp/mb/portage/'+ebuildtreegroup+'/'+atomname+'/files')
    os.system('cp -r '+ebuildtreepath+' /tmp/mb/portage/'+ebuildtreegroup+'/'+atomname)
        # TODO selective copy ./files
    os.system('cp -r '+ebuildtreedir+'/files/* /tmp/mb/portage/'\
        +ebuildtreegroup+'/'+atomname+'/files/')
    os.system('ebuild /tmp/mb/portage/'+ebuildtreegroup+'/'\
        +atomname+'/'+ebuild+' digest')
    #except:
    #    print 'copying ebuild failed'
    #    sys.exit()
    os.environ['PKGDIR'] = '/tmp/mb/packages'
    cmd = 'ebuild /tmp/mb/portage/'+ebuildtreegroup+'/'\
        +atomname+'/'+ebuild+' package'
    print 'Start building atom '
    if os.system(cmd) == 0:
        print 'building ' +  ' successful'
    else:
        print 'error during building ' + ' skipping ..' 

def install(filename):
    """
    installs target
        usage:
            install(target)
        target may be mb package, ebuild or portage atom name
    """
    import os,sys,re
    print "Installing " + filename
    if (".mb" in filename):
        print "installing metaball uncompressed package"
        ## TODO обработка ситуации когда диры уже созданы
        ## вынести создание окружения в отдельную функцию 
        ## с параметрами build install и т. п.
        ## check if /tmp/mb mounted and umount it
        if os.access('/tmp/mb', os.F_OK):
            if os.path.ismount('/tmp/mb'):
                try:
                    os.system('umount -l /tmp/mb')
                except:
                    print 'Error: Could not use dir for installation'
                    sys.exit()
            os.system('rm /tmp/mb -rf')
        os.makedirs('/tmp/mb')
        os.system("mount -o loop " + filename + " /tmp/mb")
        installWalk('/tmp/mb/portage')
        os.system('umount /tmp/mb')
        os.system('rm /tmp/mb -rf')
    if (".ebuild" in filename):
        print "installing portage ebuild"
        name, group = getGroupAppNamesFromEbuild(filename)
        if (name == 'None'):
            try:
                name=getPNameFromFile(filename)
            except:
                print 'no name'
        if (group == 'None'):
            try:
                group = getGorupNameFromPath(filename)
            except:
                print "Couldn't determine atom group, \
                       let the group be app-misc"
                group = 'app-misc'
        os.environ['PORTDIR_OVERLAY'] = portage.settings['PORTDIR_OVERLAY'] + ' ' + \
			'/tmp/mb/portage'
	## Copying ebuild to overlay            -- mbOverlay is going to be deprecated
        ##if os.access(mbOverlay+'/'+group+'/'+name, os.F_OK):
        ##    os.system('rm ' + mbOverlay+'/'+group+'/'+name+' -rf')
        ##os.makedirs(mbOverlay+'/'+group+'/'+name)
        ##os.system('cp '+filename+' '+mbOverlay+'/'+group+'/'+name)
        print 'emerging ' + name
        os.environ['PORTDIR_OVERLAY'] = portage.settings['PORTDIR_OVERLAY'] + \
                ' ' + '/tmp/mb/portage'
        os.environ['PKGDIR'] = '/tmp/mb/packages'
        os.system('emerge '+group+'/'+name+' -K')
    if ('.tar.gz' in filename) or ('.tar.bz2' in filename):
        print 'installing tarball'

def remove(packagename):
    """
    removes target from systems
    """
    if '.mb' in packagename:
        print 'Removing metaball package ' + packagename
		if os.access('/tmp/mb', os.F_OK):
            if os.path.ismount('/tmp/mb'):
                try:
                    os.system('umount -l /tmp/mb')
                except:
                    print 'Error: Could not use dir for installation'
                    sys.exit()
            os.system('rm /tmp/mb -rf')
        os.makedirs('/tmp/mb')
        os.system("mount -o loop " + filename + " /tmp/mb")
        ## TODO recursive removing here 
		##installWalk('/tmp/mb/portage')
        
		os.system('umount /tmp/mb')
        os.system('rm /tmp/mb -rf')

    else:
        print 'Removing ..... ' + packagename
        try:
            os.system('emerge -C ' + packagename)
            print packagename + ' successfully uninstalled'
        except:
            print 'uninstalling ' + packagename + ' failed, skipping ..' 

def help(topic):
    """
    Loads and show help topics
    """
    global helpdir
    try:
        helpFile = open (helpdir+"/"+topic, "r")
        for line in helpFile:
            print line
    except:
        print "Error: no page for this module or help files are not correctly installed."

def main(args):
    """
    Main function, parse arguments, decide what to do
    """
    import sys, os
    ##import portage, portage_util
    ##sys.path = ["/usr/lib/portage/pym"]+sys.path

    CmdLineOpts = args[1:]

    ## Some debuging info
    print '*** Debugging Info ***'
    print 'cmd args:'
    if CmdLineOpts != []:
        for i in CmdLineOpts:
            print  i
    else:
        help('index')
        sys.exit(0)
    ## 0 - run, 2 - debug in Eric
    action = CmdLineOpts[0]
    ## Defining current action
    if (action == "help") or (action == "--help") or (action == ""):
        FilenameNumber = int(CmdLineOpts.index("help"))+1
        try:
            help(CmdLineOpts[FilenameNumber])
        except:
            help('index')
    elif (action == "install"):
        FilenameNumber = int(CmdLineOpts.index("install"))+1
    ##        try:
        filename = CmdLineOpts[FilenameNumber]
        install(filename)
    ##        except:
    ##            print "Error: cmd line options are incorrect !!!"
    ##            print "No suitable target for instalation"
    ##            help("install")
    elif (action == "build"):
        if '-l' in CmdLineOpts:
            listFilenameNumber = int(CmdLineOpts.index("-l"))+1
            if os.access(CmdLineOpts[listFilenameNumber],os.F_OK):
		    packageList = open(CmdLineOpts[listFilenameNumber]).readlines()
		    for package in packageList:
			build(package)
        else:
            stpoint = int(CmdLineOpts.index("build"))+1
            for package in CmdLineOpts[stpoint]:
                build(package)
            doMb("/tmp/mb", CmdLineOpts[listFilenameNumber])
    ##        FilenameNumber = int(CmdLineOpts.index("build"))+1
    ##        build(CmdLineOpts[FilenameNumber])     
    elif (action == "remove"):
        FilenameNumber = int(CmdLineOpts.index("remove"))+1
        try:
            filename = CmdLineOpts[FilenameNumber]
            remove(filename)
        except:
            print "Error: cmd line options are incorrect !!!"
            print "No suitable target for removing"
            help("remove")


## If we're not imported
if __name__ == "__main__":
    main()

