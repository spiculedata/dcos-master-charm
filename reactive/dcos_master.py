import os
from charms.reactive import when, when_not, set_state
from subprocess import check_call, CalledProcessError, call, check_output, Popen
from charmhelpers.core.host import adduser, chownr, mkdir
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import unit_private_ip, status_set, log, resource_get
from charms.leadership import leader_set, leader_get
from charms.reactive.helpers import data_changed
import time

basedir="/opt/mesosphere/"
configdir="/etc/mesosphere/"
au = ArchiveUrlFetchHandler()
ip = [unit_private_ip()]

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
    log("open ports")
    hookenv.open_port(80)
    hookenv.open_port(8181)
    set_state('dcos-master.installed')
    status_set('maintenance', 'DC/OS Installed, waiting for start')

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
    if not os.path.isfile("/usr/bin/mkdir"):
        os.symlink("/bin/mkdir", "/usr/bin/mkdir")

def downloadBootstrap():
    status_set('maintenance', 'Downloading bootstrap tarball')
    au.download("http://community.meteorite.bi/tmp/bootstrap.tar.gz", "/tmp/bootstrap.tar.gz")
    #p = resource_get("software")
    p = "/tmp/bootstrap.tar.gz"
    log("path is: "+p)
    #We unzip using tar on the command line because its much quicker than using python.
    check_output(['tar', 'xvfz', p, '-C', basedir])

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

def setupMasterConfigs(ips, bootstrap):
    bs = ""
    if bootstrap:
         bs = "packages/dcos-config--setup_b3e41695178e35239659186b92f25820c610f961/"
    status_set('maintenance', 'Creating master configs')
    s = ""
    t = ""
    j = 1
    for i in ips:
        s += str(j)+":"+i+","
        t += "\""+i+"\""+","
        j=j+1
    s = s[:-1]
    t = t[:-1]
    text_file=open(basedir+bs+"etc/exhibitor", 'w')
    log("Writing to:"+basedir+bs+"etc/exhibitor")
    text_file.writelines(["EXHIBITOR_BACKEND=STATIC\n","EXHIBITOR_STATICENSEMBLE="+s])
    text_file.close()
    text_file=open(basedir+bs+"/etc/master_list", 'w')
    text_file.write("["+t+"]")
    text_file.close()
    p = ""
    if bootstrap:
        p = "etc_master/"
    else:
        p ="etc/"
    text_file=open(basedir+bs+p+"master_count", "w")
    text_file.writelines(str(len(ips)))
    text_file.close()

@when('dcos-quorum.joined')
@when('dcos-master.running')
def getIPs(obj):
    log("Configuring nodes")
    nodes  = obj.get_nodes() +ip
    nodes.sort()
    log("nodes are: "+str(nodes).strip('[]'))
    if(data_changed('master_ips', nodes)):
        setupMasterConfigs(nodes, False)
        allowed = [1,3,5]
        if len(nodes) in allowed:
            check_output(['service','dcos-exhibitor', 'restart'])
            time.sleep(240)
            check_output(['service','dcos-oauth', 'restart'])
        else:
            status_set('blocked', 'Waiting for 1, 3 or 5 Master nodes to create quorum')
    #get and set cluster-id and auth-token from leader
#    set_state('dcos-master.installed')
    status_set('active', 'DC/OS Installed')

@when('leadership.is_leader')
@when('dcos-master.installed')
def setProperties():
    startDCOS()
    if os.path.isfile('/var/lib/dcos/cluster-id'):
        text_file=open('/var/lib/dcos/cluster-id')
    else:
        text_file=open('/var/lib/dcos/cluster-id.tmp')
    cid = text_file.read()
    text_file.close()
    text_file=open('/var/lib/dcos/auth-token-secret')
    ats = text_file.read()
    text_file.close()
    leader_set(cluster=cid)
    leader_set(authtoken=ats)
    set_state('dcos-master.running')
    status_set('active', 'DC/OS started')

@when_not('leadership.is_leader')
@when('dcos-master.installed')
@when('leadership.set.cluster')
@when('leadership.set.authtoken')
def setSlaveProperties():
    cid = leader_get('cluster')
    ats = leader_get('authtoken')
    directory = '/var/lib/dcos'
    if not os.path.exists(directory):
        os.makedirs(directory)
    f = open('/var/lib/dcos/cluster-id', 'w')
    f.write(cid)
    f.close()
    f = open('/var/lib/dcos/auth-token-secret', 'w')
    f.write(ats)
    f.close()
    startDCOS()
    set_state('dcos-master.running')
    status_set('active', 'DC/OS started')


@when('dcos-master.installed')
@when_not('dcos-master.running')
def startDCOS():
    setupMasterConfigs(ip,True)
    status_set('maintenance', 'Running installer')
    process = check_output(["./pkgpanda", "setup"], cwd=basedir+"bin", env=setupEnvVars())


@when('logstash.available')
def start_up_logger(logstash):
    log('logstash available')
    #start_logger(logstash.private_address(), logstash.tcp_port())

@when('local-monitors.available')
def setup_nagios(nagios):
    config = hookenv.config()
    unit_name = hookenv.local_unit()
    au.download("https://raw.githubusercontent.com/buggtb/dcos-master-charm/master/monitoring_scripts/check_service.sh", "/usr/bin/check_service.sh")    
    au.download("https://raw.githubusercontent.com/buggtb/dcos-master-charm/master/monitoring_scripts/dcos_unit_check.sh", "/usr/bin/dcos_unit_check.sh")
    nagios.add_check(['/usr/bin/dcos_unit_check.sh'],
        name="check_dcos_master",
        description="Verify DCOS Master Services",
        context="dcos_master",
        unit=unit_name,
    )
