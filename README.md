# Overview

DC/OS is the Data Center Operating System from Mesosphere. It is built upon Apache MESOS and is designed to turn your data center into a single pool of resources that applications can utilise.

Mesosphere released DC/OS open source edition to run on a number of cloud computing services and also support for Centos, this charm leverages that capability to install DC/OS inside Ubuntu using the Juju modelling framework.

Juju and DC/OS make an excellent fit because it allows administrators to add new resource as simply as adding more DC/OS Agent units and deploying more applications.

# Usage

## Warning

**This charm is currently under heavy development and has limited testing outside of EC2**

Deploying this charm:

    juju deploy dcos-master

To view the dashboard:
  
    juju expose dcos-master

and visit http://<server-url>/ to view the landing page. To view the Zookeeper info you can also visit http://<server-url>:8181.


## Scale out Usage

DC/OS provides a master and agent setup. For fault tolerance it is recommended to run more than 1 master node, these are self configuring and distributing.

This DC/OS charm will accept 1,3 or 5 masters. DC/OS performance actually degrades with more and 3 or 5 will provide HA capabaility.

Unlike the DC/OS official installations,  this will allow for scalaing using juju add-unit to add new master nodes.

## Known Limitations and Issues

This charm is an initial prototype to ensure that the main services bootstrap and applications can be deployed, there will be a number of missing features and usability issues. To help get in touch! (info@spicule.co.uk)

# Configuration

bootstrap_url: Override the default bootstrap url to allow for a custom distro or alternative install location.

# TODO

Implement disk mounts for NFS and Loopback devices.

Add more actions.

Implement Monitoring.

Improve Security.

Expose running app ports automatically.

Simplify the upgrade process.

ELK to Beats?

Custom Cluster Name

Private Docker Reg

Marathon Load Balancer

# Contact Information

Tom Barber - info@spicule.co.uk

## DC/OS master charm for Juju

  - http://spicule.co.uk/dcos
  - https://github.com/buggtb/dcos-master-charm/issues


[service]: http://example.com
[icon guidelines]: https://jujucharms.com/docs/stable/authors-charm-icon
