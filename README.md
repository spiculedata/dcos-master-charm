# Overview

DC/OS is the Data Center Operating System from Mesosphere. It is built upon Apache MESOS and is designed to turn your data center into a single pool of resources that applications can utilise.

Mesosphere released DC/OS open source edition to run on a number of cloud computing services and also support for Centos, this charm leverages that capability to install DC/OS inside Ubuntu using the Juju modelling framework.

Juju and DC/OS make an excellent fit because it allows administrators to add new resource as simply as adding more DC/OS Agent units and deploying more applications.

# Usage

## Warning

**This charm is currently under heavy development and has limited testing outside of EC2**

Deploying this charm:

    juju deploy dcos-master

Currently the dashboard is hosted on the nodes internal IP address for EC2 and supported services. The easiest way to gain access is to SSH to the node and forward port 80 to localhost:

    sudo ssh ubuntu@52.51.37.150 -L 80:localhost:80

## Scale out Usage

**Currently not implemented**
DC/OS provides a master and agent setup. For fault tolerance it is recommended to run more than 1 master node, these are self configuring and distributing.

## Known Limitations and Issues

This charm is an initial prototype to ensure that the main services bootstrap and applications can be deployed, there will be a number of missing features and usability issues. To help get in touch! (info@spicule.co.uk)

# Configuration

Currently there are no configuration options.

# Contact Information

Tom Barber - info@spicule.co.uk

## DC/OS master charm for Juju

  - http://spicule.co.uk/dcos
  - https://github.com/buggtb/dcos-master-charm/issues


[service]: http://example.com
[icon guidelines]: https://jujucharms.com/docs/stable/authors-charm-icon
