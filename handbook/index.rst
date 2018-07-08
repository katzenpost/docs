
Katzenpost Handbook
*******************

| David Stainton

Version 0

.. rubric:: Abstract

Thank you for interest in Katzenpost! This document describes how to
use the Katzenpost Mix Network software system and details deployment
strategies for systems administrators.

.. contents:: :local:


Introduction
============

Katzenpost can be used as a message oriented transport for a variety
of applications and is in no way limited to the e-mail use case. Other
possible applications of Katzenpost include but are not limited to:
instant messenger applications such as Signal and Whatsapp, crypto
currency transaction transport, bulletin board systems, file sharing
and so forth.

The Katzenpost system has four component categories:

* public key infrastructure
* mixes
* providers
* clients

This handbook will describe how to use and deploy each of these.
The build instructions in this handbook assume that you have a proper
golang environment with at least golang 1.9 or later AND the git
revision control system commandline installed.


Building Katzenpost Components with Dependency Vendoring
--------------------------------------------------------

We recommend using our golang vendoring system to perform the builds.

0. Acquire a recent version of dep: https://github.com/golang/dep

1. Clone the Katzenpost daemons repository::

   mkdir $GOPATH/github.com/katzenpost
   git clone https://github.com/katzenpost/daemons.git

2. Fetch the Katzenpost vendored dependencies::

   cd $GOPATH/github.com/katzenpost/daemons
   dep ensure

3. Build the binaries::

   cd authority/nonvoting; go build
   cd server; go build
   cd mailproxy; go build


The Katzenpost Configuration File Format
----------------------------------------

Each Katzenpost component has a configuration file in the TOML format.
This handbook will give you all the details you need to know to configure
each of these configuration files. To learn more about the TOML format
see: https://github.com/toml-lang/toml#toml

NOTE: ``#`` may be used at the beginning of a line to denote a comment
instead of an effective configuration line.


Katzenpost Mix Network Public Key Infrastructure
================================================

Overview
--------

Currently Katzenpost has one PKI system that is ready for deployment;
the non-voting Directory Authority. Whether or not this should be used
on a production system depends on your threat model. This is
essentially a single point of failure. If this PKI system becomes
compromised by an adversary it's game over for anonymity and security
guarantees.

The Katzenpost voting Directory Authority system is a replacement for
the non-voting Directory Authority and is actively being developed.
However it's votiing protocol is NOT byzantine fault tolerant.
Therefore a Directory Authority server which is participating in the
voting protocol can easily perform a denial of service attack for each
voting round. This would cause the mix network to become totally
unusable.

Future development efforts will include designing and implementing one
or more byzantine fault tolerant PKI systems for Katzenpost.

All Katzenpost PKI systems have two essential components:

* a client library
* server infrastructure

Furthermore this client library has two types of users, namely mixes
and clients. That is, mixes must use the library to upload/download
their mix descriptors and clients use the library to download a
network consensus document so that they can route messages through the
mix network.


Building The Non-voting Directory Authority
-------------------------------------------

The easiest way to build the nonvoting Authority server is with
this single commandline::

   go get github.com/katzenpost/daemons/authority/nonvoting

However you can of course use git to clone all of our git
repositories and dependencies. You may then build the
nonvoing authority as follows::

   cd $GOPATH/github.com/katzenpost/daemons/authority/nonvoting
   go build

Neither of these build strategies is ideal because the latest
versions of any of our software dependencies may make breaking
changes. We therefore recommend using our golang vendoring system
to perform the build as described above.


CLI usage of The Non-voting Directory Authority
-----------------------------------------------

The non-voting authority has the following commandline usage::

   ./nonvoting --help
   Usage of ./nonvoting:
     -f string
           Path to the authority config file. (default "katzenpost-authority.toml")
     -g    Generate the keys and exit immediately.


The ``-g`` option is used to generate the public and private keys for
the Directory Authority.  Clients of the PKI will use this public key
to verify retreived network consensus documents.  However before
invoking the authority with this commandline option you MUST provide a
valid configuration file. This file will specify a data directory
where these keys will be written.  Normal invocation will omit this
``-g`` option because the keypair should already be present.

A minimal configuration suitable for using with this ``-g`` option for
generating the key pair looks like this::

  [Authority]
  Addresses = [ "192.0.2.1:12345" ]
  DataDir = "/var/run/katzauth"

Example invocation commandline::

   ./nonvoting -g -f my_authority_config.toml

However the invocation may fail if the permissions on the data directory
are not restricted to the owning user::

   ./nonvoting -g -f my_authority_config.toml
   Failed to spawn authority instance: authority: DataDir '/var/run/katzauth' has invalid permissions 'drwxr-xr-x'

Fix permissions like so::

   chmod 700 /var/run/katzauth

A successful run will print output that looks like this::

  14:47:43.141 NOTI authority: Katzenpost is still pre-alpha.  DO NOT DEPEND ON IT FOR STRONG SECURITY OR ANONYMITY.
  14:47:43.142 NOTI authority: Authority identity public key is: 375F00F6EA20ACFB3F4CDCA7FDB50AE427BF02035B6A2F5789281DAA7290B2BB


Configuring The Non-voting Directory Authority
----------------------------------------------

Authority section
`````````````````

The Authority section contains information which is mandatory,
for example::

  [Authority]
    Addresses = [ "192.0.2.1:29483", "[2001:DB8::1]:29483" ]
    DataDir = "/var/lib/katzenpost-authority"

* ``Addresses`` contains one or more IP addresses which
  correspond to local network interfaces to listen for connections on.
  These can be specified as IPv4 or IPv6 addresses.

* ``DataDir`` specifies the absolute path to the server's
  state files including the keypair use to sign network consensus
  documents.


Logging section
```````````````

The logging section controls the logging, for example::

  [Logging]
    Disable = false
    File = "/var/log/katzenpost.log"
    Level = "DEBUG"

* ``Disable`` is used to disable logging if set to ``true``.

* ``File`` specifies the file to log to. If ommited then stdout is used.

* ``Debug`` may be set to one of the following:

* ERROR
* WARNING
* NOTICE
* INFO
* DEBUG


Parameters section
``````````````````

The Parameters section holds the network parameters, for example::

  [Parameters]
    MixLambda = 0.00025
    MixMaxDelay = 90000
    SendLambda = 15.0
    SendShift = 3
    SendMaxInterval = 3000

* ``MixLambda`` is the inverse of the mean of the exponential
  distribution that the Sphinx packet per-hop mixing delay will be
  sampled from.

* ``MixMaxDelay`` is the maximum Sphinx packet per-hop mixing
  delay in milliseconds.

* ``SendLambda`` is the inverse of the mean of the exponential
  distribution that clients will sample to determine send timing.

* ``SendShift`` is the shift applied to the client send timing samples
  in milliseconds.

* ``SendMaxInterval`` is the maximum send interval in milliseconds,
  enforced prior to (excluding) SendShift.


Mixes section
`````````````

The Mixes array defines the list of white-listed non-provider nodes,
for example::

  [[Mixes]]
  IdentityKey = "kAiVchOBwHVtKJVFJLsdCQ9UyN2SlfhLHYqT8ePBetg="

  [[Mixes]]
  IdentityKey = "900895721381C0756D28954524BB1D090F54C8DD9295F84B1D8A93F1E3C17AD8"


* ``IdentityKey`` is the node's EdDSA signing key, in either Base16 OR Base64 format.


Provider section
````````````````

The Providers array defines the list of white-listed Provider nodes,
for example::

  [[Providers]]
  Identifier = "provider1"
  IdentityKey = "0AV1syaCdBbm3CLmgXLj6HdlMNiTeeIxoDc8Lgk41e0="

  [[Providers]]
  Identifier = "provider2"
  IdentityKey = "375F00F6EA20ACFB3F4CDCA7FDB50AE427BF02035B6A2F5789281DAA7290B2BB"


* ``Identifier`` is the human readable provider identifier, such as a
  FQDN.

* ``IdentityKey`` is the provider's EdDSA signing key, in either
  Base16 OR Base64 format.


Katzenpost Mix Infrastructure
=============================

Overview
--------

The Katzenpost Providers is strictly a superset of the Katzenpost mix.
Both of these components are provided for by the ``server`` binary.
Each Provider and Mix MUST be white-listed by the Directory Authority (PKI)
in order to participate in the network.

Building the ``server`` binary
------------------------------

The easiest way to build the nonvoting Authority server is with
this single commandline::

   go get github.com/katzenpost/daemons/server

However you can of course use git to clone all of our git
repositories and dependencies. You may then build the
nonvoing authority as follows::

   cd $GOPATH/github.com/katzenpost/daemons/server
   go build

Neither of these build strategies is ideal because the latest
versions of any of our software dependencies may make breaking
changes. We therefore recommend using our golang vendoring system
to perform the build as described above.


Configuring Mixes and Providers
-------------------------------

Katzenpost mixes and providers have identical configuration files
except that the configuration for a provider has a ``Provider`` section
AND the ``Server`` section specifies ``IsProvider = true``.

Server section
``````````````

The Server section contains mandatory information common to all nodes,
for example::

  [Server]
    Identifier = "example.com"
    Addresses = [ "192.0.2.1:29483", "[2001:DB8::1]:29483" ]
    DataDir = "/var/lib/katzenpost"
    IsProvider = true

* ``Identifier`` is the human readable identifier for the node (eg:
  FQDN).

* ``Addresses`` are the IP address/port combinations that the server
  will bind to for incoming connections. IPv4 and/or IPv6 may be
  specified.

* ``DataDir`` is the absolute path to the server's state files.

* ``IsProvider`` specifies if the server is a provider (vs a mix).


PKI section
```````````

The PKI section contains the directory authority configuration
for the given mix or provider, for example::

  [PKI]
    [PKI.Nonvoting]
      Address = "192.0.2.2:2323"
      PublicKey = "kAiVchOBwHVtKJVFJLsdCQ9UyN2SlfhLHYqT8ePBetg="

* ``Nonvoting`` is a simple non-voting PKI for test deployments.
* ``Address`` is the IP address/port combination of the directory authority.
* ``PublicKey`` is the directory authority's public key in Base64 or Base16 format.


Logging section
```````````````

The Logging section controls the logging, for example::

  [Logging]
    Disable = false
    File = "/var/log/katzenpost.log"
    Level = "DEBUG"

* ``Disable`` is used to disable logging if set to ``true``.

* ``File`` specifies the file to log to. If ommited then stdout is used.

* ``Debug`` may be set to one of the following:

* ERROR
* WARNING
* NOTICE
* INFO
* DEBUG


Management section
``````````````````

The management section specifies connectivity information for the
Katzenpost control protocol which can be used to make configuration
changes during run-time. An example configuration looks like this::

  [Management]

    Enable = true
    Path = "/var/lib/katzenpost/thwack.sock"

* ``Disable`` is used to disable the management interface if set to
  ``true``.

* ``Path`` specifies the path to the management interface socket. If
  left empty then `management_sock` will be used under the DataDir.


Provider section
````````````````

The Provider secton specifies the Provider configuration, for example::

  [Provider]
    BinaryRecipients = false
    CaseSensitiveRecipients = false
    RecipientDelimiter = "@"

    [[Provider.Kaetzchen]]
      Capability = "fancy"
      Endpoint = "+fancy"
      Disable = false

      [Provider.Kaetzchen.Config]
        rpcUser = "username"
        rpcPass = "password"
        rpcUrl = "http://127.0.0.1:11323/"


  # UserDB is the user database configuration.  If left empty the simple
  # BoltDB backed user database will be used with the default database.
  # [Provider.UserDB]

    # Backend selects the UserDB backend to be used.
    # Backend = "bolt"

    # Bolt is the BoltDB backed user database. (`bolt`)
    # [Provider.UserDB.Bolt]

      # UserDB is the path to the user database.  If left empty it will use
      # `users.db` under the DataDir.
      # UserDB = "fuck"

    # Extern is the externally defined (RESTful http) user database. (`extern`)
    # [Provider.UserDB.Extern]

      # ProviderURL is the base URL used for the external provider
      # authentication API.  It should be of the form `http://localhost:8080`.
      # ProviderURL = "http://localhost:8080"

  # SpoolDB is the user message spool configuration.  If left empty, the
  # simple BoltDB backed user message spool will be used with the default
  # database.
  # [Provider.SpoolDB]

    # Backend selects the SpoolDB backend to be used.
    # Backend = "bolt"

    # Bolt is the BoltDB backed user message spool. (`bolt`)
    # [Provider.SpoolDB.Bolt]

      # SpoolDB is the path to the user message spool.  If left empty, it will
      # use `spool.db` under the DataDir.
      # SpoolDB = "fuck"
