import os
from charms.reactive import when, when_not, set_state
from subprocess import check_call, CalledProcessError, call, check_output, Popen
from charmhelpers.core.host import adduser, chownr, mkdir
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import unit_private_ip, status_set, log

basedir="/opt/mesosphere/"
configdir="/etc/mesosphere/"
au = ArchiveUrlFetchHandler()
ip = unit_private_ip()

@when_not('dcos-master.installed')
def install_dcosmaster():
    status_set('maintenance', 'Installing DC/OS Master')
    dnsprocess = check_output(["apt-get", "remove", '-y',"--auto-remove", "dnsmasq-base"])
    createFolders()
    createInitFiles()
    createSymlinks()
    log("fetching bootstrap")
    setupEnvVars()
    downloadBootstrap()
    setupMasterConfigs()
    status_set('maintenance', 'Running installer')
    process = check_output(["./pkgpanda", "setup"], cwd=basedir+"bin", env=setupEnvVars())
    log("open ports")
    hookenv.open_port(80)
    hookenv.open_port(8181)
    set_state('dcos-master.installed')
    status_set('active', 'DC/OS Installed')

@when('dcos.available')
def configure_hook(dcos):
    dcos.configure()

def createFolders():
    status_set('maintenance', 'Creating DC/OS Folders')
    mkdir(configdir)
    mkdir(configdir+'roles')
    mkdir(basedir)
    mkdir(configdir+'setup-flags')
    mkdir(basedir+'packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961')
    mkdir(basedir+'packages/dcos-metadata--setup_b3e41695178e35239659186b92f25820c610f961')
    mkdir('/etc/profile.d')
    mkdir('/etc/systemd/journald.conf.d')

def createInitFiles():
    status_set('maintenance', 'Creating DC/OS folders')
    open(configdir+'roles/master', 'a').close()
    open(configdir+'setup-flags/repository-url', 'a').close()
    os.chmod(configdir+'setup-flags/repository-url', 0o644)
    text_file = open(configdir+"setup-flags/bootstrap-id", "w")
    text_file.write("BOOTSTRAP_ID=3a2b7e03c45cd615da8dfb1b103943894652cd71")
    text_file.close()
    os.chmod(configdir+'setup-flags/bootstrap-id', 0o644)
    text_file = open(configdir+"setup-flags/cluster-packages.json", "w")
    text_file.write("[\"dcos-config--setup_b3e41695178e35239659186b92f25820c610f961\", \"dcos-metadata--setup_b3e41695178e35239659186b92f25820c610f961\"]")
    text_file.close()
    os.chmod(configdir+'setup-flags/cluster-packages.json', 0o644)
    text_file = open("/etc/systemd/journald.conf.d/dcos.conf", "w")
    text_file.writelines(["[Journal]", "MaxLevelConsole=warning"])
    text_file.close()
    os.chmod('/etc/systemd/journald.conf.d/dcos.conf', 0o644)

def createSymlinks():
    status_set('maintenance', 'Creating DC/OS symlinks')
    #Hack to make start scripts work
    os.symlink("/bin/mkdir", "/usr/bin/mkdir")

def downloadBootstrap():
    status_set('maintenance', 'Downloading bootstrap tarball')
    au.download("http://community.meteorite.bi/tmp/bootstrap.tar.gz", "/tmp/bootstrap.tar.gz")
    #We unzip using tar on the command line because its much quicker than using python.
    check_output(['tar', 'xvfz', "/tmp/bootstrap.tar.gz", '-C', basedir])

def setupEnvVars():
    status_set('maintenance', 'Configuring the install environment variables')
    currentenv = dict(os.environ)
    currentenv['LD_LIBRARY_PATH'] = basedir+"lib"
    currentenv['PATH'] = basedir+"bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
    currentenv['PYTHONUNBUFFERED'] = "true"
    currentenv['PYTHONPATH'] = basedir+"lib/python3.4/site-packages"
    currentenv['JAVA_HOME'] = basedir+"active/java/usr/java"
    currentenv['MESOS_NATIVE_JAVA_LIBRARY'] = basedir+"lib/libmesos.so"
    currentenv['JAVA_LIBRARY_PATH'] = basedir+"lib"
    currentenv['DCOS_IMAGE_COMMIT'] = "14509fe1e7899f439527fb39867194c7a425c771"
    currentenv['DCOS_VERSION'] = "1.7-open"
    currentenv['PROVIDER'] = "onprem"
    currentenv['MESOS_IP_DISCOVERY_COMMAND'] = basedir+"bin/detect_ip"
    return currentenv

def setupMasterConfigs():
    status_set('maintenance', 'Creating master configs')
    text_file=open(basedir+"packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961/etc/exhibitor", 'w')
    text_file.writelines(["EXHIBITOR_BACKEND=STATIC\n","EXHIBITOR_STATICENSEMBLE=1:"+ip])
    text_file.close()
    text_file=open(basedir+"packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961/etc/master_list", 'w')
    text_file.write("[\""+ip+"\"]")
    text_file.close()
