import os
import stat
from shutil import rmtree
from charms.reactive import when, when_not, set_state
from subprocess import check_call, CalledProcessError, call, check_output, Popen
from charmhelpers.core.host import adduser, chownr, mkdir
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import unit_private_ip
from charmhelpers.core.hookenv import log
import contextlib
import lzma
import tarfile

basedir="/opt/mesosphere/"
configdir="/etc/mesosphere/"

@when_not('dcos-master.installed')
def install_dcosmaster():
    log("starting hook")
    os.symlink("/bin/mkdir", "/usr/bin/mkdir")
    mkdir(configdir)
    mkdir(configdir+'roles')
    mkdir(basedir)
    mkdir(configdir+'setup-flags')
    mkdir(basedir+'packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961')
    mkdir(basedir+'packages/dcos-metadata--setup_b3e41695178e35239659186b92f25820c610f961')
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
    mkdir('/etc/systemd/journald.conf.d')
    text_file = open("/etc/systemd/journald.conf.d/dcos.conf", "w")
    text_file.writelines(["[Journal]", "MaxLevelConsole=warning"])
    text_file.close()
    os.chmod('/etc/systemd/journald.conf.d/dcos.conf', 0o644)
    mkdir('/etc/profile.d')
    au = ArchiveUrlFetchHandler()
    log("fetching bootstrap")
    au.download("http://community.meteorite.bi/tmp/bootstrap.tar.gz", "/tmp/bootstrap.tar.gz")
    check_output(['tar', 'xvfz', "/tmp/bootstrap.tar.gz", '-C', basedir])
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
    log("get private ip")
    ip = unit_private_ip()
    text_file=open(basedir+"packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961/etc/exhibitor", 'w')
    text_file.writelines(["EXHIBITOR_BACKEND=STATIC","EXHIBITOR_STATICENSEMBLE=1:"+ip])
    text_file.close()
    text_file=open(basedir+"packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961/etc/master_list", 'w')
    text_file.write("[\""+ip+"\"]")
    text_file.close()
    log("remove dnsmasq")
    dnsprocess = check_output(["apt-get", "remove", '-y',"--auto-remove", "dnsmasq-base"])
    log("install")
    process = check_output(["./pkgpanda", "setup"], cwd=basedir+"bin", env=currentenv)
    log("open ports")
    hookenv.open_port(80)
    hookenv.open_port(8181)
    set_state('dcos-master.installed')

