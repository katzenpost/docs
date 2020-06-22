Katzenpost Mix Plugin PubSub Specification
******************************************

| Leif Ryge
| David Stainton

| Version 0

.. rubric:: Abstract

This document describe a new plugin system for the Katzenpost
Mix Server which makes use of a SURB based publish subscribe protocol
allowing plugins to send clients messages without the strict request
response protocol dialogue previously used in the Kaetzchen plugin system.
[KAETZCHEN]_

.. contents:: :local:

1. Introduction
===============

This specification provides the design of a new plugin system that
makes use of an optional SURB based publish subscribe mechanism
whereby clients may send a Sphinx packet to a server plugin where the
payload contains multiple SURBs. These SURBs are then used by the mix
server and plugin to send multiple anonymous messages back to the
client without a strict request response dialogue, thus forming a
temporary subscription for the client. The subscription expires when
the SURBs are used up or when the SURBs expire. One of the main goals
of this plugin system is to maintain transport agnosticism for the mix
server plugins. Therefore the SURBs are handled by the mix server and
are not exposed to the plugins.

1.1 Terminology
----------------

* ``SURB`` - An acronym used in mixnet literature such as the Sphinx
  Cryptographic Packet format [SPHINXSPEC]_  [SPHINX09]_ which stands
  for Single Use Reply Block. The exchange of SURBs between two parties
  allows for anonymous replies over the decryption mix network.

1.2 Conventions Used in This Document
-------------------------------------

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC2119]_.

2. Overview
===========

In the previous Katzenpost plugin system, server plugins communicated
with the mixnet server using HTTP over unix domain sockets. This
approach was chosen to simplify implementation, but it is no longer
appropriate in the publish subscribe model as it would require
polling.

The new wire protocol between plugins and the mix server shall make
use of unix domain sockets with length-prefixed CBOR objects. Either
the mix server or the plugin may send a message at anytime without the
need for a response to strictly follow a request as was the case with
HTTP.

3. Sphinx Packet Payload Considerations
=======================================

Previous Sphinx Payload Format
------------------------------

The Sphinx packet payloads are decrypted and decoded on the
Providers and the precise payload format is a 2-byte Sphinx payload
plaintext header followed by an optional SURB of length 556 bytes
followed by plaintext or additional ciphertext (client end to end
encrypted).

The second byte of the Sphinx payload plaintext is a zero byte
reserved value while the first byte contains a flag which denotes
either there is a SURB present or there is NOT a SURB present.

The New Sphinx Payload Format
-----------------------------

::

  type SphinxPayload struct {
      SURBCount byte
      Reserved byte
      Plaintext []byte
  }

4. Coammnds sent between katzenpost and application plugins
===========================================================

On the server side, these commands are to be sent in CBOR messages
over a UNIX domain socket. On the client side, that may be the case in
the future, but for now we're assuming applications will run in the
same process as the katzenpost client so regular function calls are
used instead.

Client-side
-----------

Subscription IDs on the client side are chosen by the client application and
are long-lived.

* Client application sends to katzenpost client:

  - subscribe(server_address, subscription_id, spool_id, last_app_message_id)

* Katzenpost client sends to client application:

  - new_messages(subscription_id, app_messages)
  - error(subscription_id, error_type)

Server-side
-----------

Subscription IDs on the server side are chosen by the katzenpost server, and are short-lived.

* Katzenpost server sends to server application:

  - subscribe(subscription_id, spool_id, last_message_id)
  - unsubscribe(subscription_id)

* Server application sends to katzenpost server:

  - new_messages(subscription_id, app_messages)
  - error(subscription_id, error_type)

5. Mixnet commands sent between katzenpost client and server
============================================================

These commands are sent between the katzenpost client and server (aka
Provider) via mixnet messages.

* Katzenpost client to katzenpost server

  - fetch(spool_id, last_message_id, SURBs)

* Katzenpost server to katzenpost client:

  - new_messages(spool_id, app_messages)

Note that this does NOT need a signature or some other assurance of
authenticity if the application is hosted on the remote Provider
because the Sphinx packet format ensures authenticty.

6. Protocol Flow
================

A client application establishes a subscription by generating a random
subscription ID and sending via the katzenpost client a
subscribe(server_address, subscription_id, spool_id, last_message_id)
command describing the spool which the application would like to
subscribe to.

The katzenpost client maintains a list of subscription IDs for each
spool ID for which there is one or more active subscriptions.

For the duration of the subscription, the katzenpost client will send
fetch(spool_id, last_message_id, SURBs) commands via mixnet messages
addressed to the server application to the remote Provider where the
server application is running, on a schedule described in the Fetch
Schedule section below.

The katzenpost server (the Provider where the server application is
running) will maintain a subscription table which maps server-side
subscription IDs to lists of SURBs.

Upon receiving a fetch message, the katzenpost server will generate
a new subscription ID, store the list of SURBs in its subscription
table, and send a subscribe(subscription_id, spool_id,
last_message_id) message to the server application.

The server-side subscription lasts until the list of SURBs is
exhausted, or the SURBs have expired (due to the mixnet's PKI epoch
having ended). When the SURBs are exhausted or expired, the katzenpost
server terminates the subscription by sending an
unsubscribe(subscription_id) message to the server application.

For each spool, the server application maintains a list of current
subscription IDs.

Upon receiving a subscribe(subscription_id, spool_id, last_message_id)
message, the server application adds the subscription ID to that
spool's list of subscriptions. If the spool contains any messages
which came after last_message_id, the server applications sends the
katzenpost server a new_messages(subscription_id, app_messages)
message containing all of the messages that came after
last_message_id.

Later, when new messages are written to a spool (note: how this
happens is currently outside the scope of this document), for each
current subscription to the spool, the server application will send to
the katzenpost server new_messages(subscription_id, app_messages)
messages containing the new messages.

When the server application receives an unsubscribe(subscription_id)
message, it removes that subscription ID from the list of
subscriptions for the spool which contains it in its list of current
subscriptions. (implementation detail: the server application probably
wants to maintain a table mapping subscription_id to spool_id to make
this efficient.)

When the katzenpost server receives a new_messages(subscription_id,
app_messages) message from the server application, it looks in its
subscription table and finds the next SURB for that subscription_id
and uses the SURB to send a new_messages(spool_id, app_messages)
mixnet message containing as many of the application messages as will
fit in a mixnet message. While there are more messages and more SURBs
remaining, it will send more new_messages mixnet messages.

When the katzenpost client receives a new_messages(spool_id,
app_messages) message via the mixnet, it consults its list of
spools-to-subscription-IDs and for each subscription to that spool it
sends a new_messages(subscription_id, app_messages) message to the
client application.

7. Fetch Schedule
=================

For now lets just say that new fetch messages should be sent whenever
the time since the last new_messages message received exceeds some
threshold which is a function of the number of outstanding SURBs sent
in previous fetch messages for a given client-side subscription.

8. TODO
=======

The protocol as described above has a number of serious shortcomings
which we intend to address before this specification is considered
complete. It is, so far, neither efficient nor reliable. We'll get
there, though :)

* Perhaps fetch messages should include an identifier of a previous
  fetch message which they are effectively replacing, causing the
  server-side subscription context for the previous fetch message to
  be ended? This would prevent most of the duplicate messages which
  would be sent over the mixnet in the above design.

* The katzenpost client should probably track messages it has already
  sent to the client application and not resend any duplicates which
  it inevitably will receive.

* The above protocol doesn't say what a message_id is. Do we assume
  messages are ordered? If so we can achieve reliability by adding
  some logic to the katzenpost client to send a new fetch message when
  it detects holes in the sequence and perhaps to retain out-of-order
  messages until it is able to deliver the messages to the client
  application in order? And then we might want some kind of selective
  ACK in place of our last_message_id... BUT for now, the easy way to
  make it reliable (but not efficient at all) is to say that the
  client fetch messages don't ACK the actual last message they saw but
  rather ACK the last contiguous message (and the app message IDs need
  to be sequential numbers so that the client can infer when there is
  one missing).

Appendix A. References
======================

Appendix A.1 Normative References
---------------------------------

.. [RFC2119]  Bradner, S., "Key words for use in RFCs to Indicate
              Requirement Levels", BCP 14, RFC 2119,
              DOI 10.17487/RFC2119, March 1997,
              <http://www.rfc-editor.org/info/rfc2119>.

.. [KAETZCHEN]  Angel, Y., Kaneko, K., Stainton, D.,
                "Katzenpost Provider-side Autoresponder", January 2018,
                <https://github.com/katzenpost/docs/blob/master/specs/kaetzchen.rst>.

Appendix A.2 Informative References
-----------------------------------

.. [SPHINXSPEC] Angel, Y., Danezis, G., Diaz, C., Piotrowska, A., Stainton, D.,
                "Sphinx Mix Network Cryptographic Packet Format Specification"
                July 2017, <https://github.com/katzenpost/docs/blob/master/specs/sphinx.rst>.

.. [SPHINX09]  Danezis, G., Goldberg, I., "Sphinx: A Compact and
               Provably Secure Mix Format", DOI 10.1109/SP.2009.15,
               May 2009, <https://cypherpunks.ca/~iang/pubs/Sphinx_Oakland09.pdf>.

Appendix B. Citing This Document
================================

Appendix B.1 Bibtex Entry
-------------------------

Note that the following bibtex entry is in the IEEEtran bibtex style
as described in a document called "How to Use the IEEEtran BIBTEX Style".

::

   @online{KatzenPubSub,
   title = {Katzenpost Mix Plugin PubSub Specification},
   author = {David Stainton},
   url = {FIXME},
   year = {2020}
   }
