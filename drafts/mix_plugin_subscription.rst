Katzenpost Mix Plugin PubSub Specification
******************************************

| Leif Ryge
| David Stainton

| Version 0

.. rubric:: Abstract

This document describe a new plugin system for the Katzenpost Mix
Server which makes use of a SURB based publish subscribe protocol
allowing application plugins to send clients messages without the
strict request response protocol dialogue previously used in the
Kaetzchen plugin system.  [KAETZCHEN]_

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

Code examples in this document are expressed in the Go programming language.

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

3. Sphinx Packet Format Considerations
======================================

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

The following new Sphinx packet payload format is as follows::

  type SphinxPayload struct {
      SURBCount byte
      Reserved  byte
      SURBs     []byte
      Plaintext []byte
  }

4. Katzenpost Client Library Considerations
===========================================

The interaction between client application and client library results
in a single Sphinx packet being sent to provider_name with recipient
service_name. That is to say, the last Sphinx hop contains a recipient
command specifying the application plugin service name.

The following struct is serialized as a CBOR byte blob and
encapsulated in a Sphinx packet and sent to the destination
application plugin::

  type FetchCommand struct {
      SpoolId        [8]byte
      LastSpoolIndex [8]byte
  }

However the encapsulating Sphinx packet MUST bundle multiple SURBs
within the packet payload in order to allow this publish subscribe
mechanism to work properly. These SURBs are what allows the anonymous
replies to be sent back to the client from the destination
Provider and application plugin.

We speculate that this entire interaction could be triggered by a
single function call on the Katzenpost client, such as::

  func Fetch(providerName, serviceName string, spoolId, lastSpoolIndex []byte, SURBs [][]byte)

Katzenpost client library interacts with client application by way of
an events channel where the application receives various kinds of
events. SURB reply messages are included in the set of events reported by
this events channel. The SURB reply event type encapsulates a message
identity which can be used by the client application to link the reply
message with a specific subscription::

  // MessageReplyEvent is the event sent when a new message is received.
  type MessageReplyEvent struct {
	// MessageID is the unique identifier for the request associated with the
	// reply.
	MessageID *[cConstants.MessageIDLength]byte

	// Payload is the reply payload if any.
	Payload []byte

	// Err is the error encountered when servicing the request if any.
	Err error
  }

The payload portion of MessageReplyEvent obviously must contain a CBOR
object which encodes one or more messages and their spool index. However
the spool identity and the application identity is not needed since SURBs
are linked to their context via the SURB identity and in this case the
message identity is used for this purpose. Therefore the MessageReplyEvent
payload shall contain the follow struct type encoded as a CBOR binary blob::

  type NewMessages struct {
    Messages []SpoolMessage
  }

  type SpoolMessage struct {
    Index uint64
    Payload []byte
  }

5. Server-side Considerations
=============================

When the server receives a Sphinx packet destined for a recipient
registered as a plugin then a subscription IDs is generated on the
server a linked with the SURBs bundled in the packet payload. This
subscription ID is short lived and expires when the SURBs are inferred
to expired or when all the SURBs are used up.

* Katzenpost server sends to server application plugin::

  func Subscribe(serverSubscriptionId, spoolId, lastSpoolIndex uint64)

  func Unsubscribe(serverSubscriptionId []byte)


* Server application plugin sends to katzenpost server::

  func NewMessages(serverSubscriptionId []byte, appMessages [][]byte)

  func SubscriptionError(errorMessage error)

FIXME: The above functions should actually be represented by struct types
serialized into CBOR.
  
6. Protocol Flow
================

For the duration of the subscription, the katzenpost client will send
fetch(spool_id, last_spool_index, SURBs) commands via mixnet messages
addressed to the server application to the remote Provider where the
server application plugin is running, on a schedule described in the Fetch
Schedule section below. This fetch message is encapsulated in a Sphinx
packet whose destination is specified as a Provider name and a service
name which addresses the specific application plugin.

The katzenpost server (the Provider where the application plugin is
running) will maintain a subscription table which maps server-side
subscription IDs to lists of SURBs. Upon receiving a fetch message,
the katzenpost server will generate a new subscription ID, store the
list of SURBs in its subscription table, and send a
subscribe(subscription_id, spool_id, last_message_id) message to the
server application plugin.

The server-side subscription lasts until the list of SURBs is
exhausted, or the SURBs have expired (due to the mixnet's PKI epoch
having ended). When the SURBs are exhausted or expired, the katzenpost
server terminates the subscription by sending an
unsubscribe(subscription_id) message to the server application plugin.
For each spool, the server application plugin maintains a list of
current serverSubscriptionId.

Upon receiving a subscribe(serverSubscriptionId, spoolId, lastSpoolIndex)
message, the server application plugin adds the serverSubscriptionId to that
spool's list of subscriptions. If the spool contains any messages
which came after lastSpoolIndex, the server applications sends the
katzenpost server a NewMessages(serverSubscriptionId, appMessages)
message containing all of the messages that came after
lastSpoolIndex.

Later, when new messages are written to a spool (note: how this
happens is currently outside the scope of this document), for each
current subscription to the spool, the server application plugin will send to
the katzenpost server NewMessages(serverSubscriptionId, appMessages)
messages containing the new messages.

When the server application plugin receives an Unsubscribe(serverSubscriptionId)
message, it removes that server subscription ID from the list of
subscriptions for the spool which contains it in its list of current
subscriptions. (implementation detail: the server application plugin probably
wants to maintain a table mapping serverSubscriptionId to spoolId to make
this efficient.)

When the katzenpost server receives a NewMessages(serverSubscriptionId, appMessages)
message from the server application plugin, it looks in its
subscription table and finds the next SURB for that serverSubscriptionId
and uses the SURB to send a NewMessages(appMessages)
mixnet message containing as many of the application messages as will
fit in a mixnet message. While there are more messages and more SURBs
remaining, it will send more NewMessages mixnet messages.

The katzenpost client maintains a list of message IDs for each
SURB it sends to a given spool service. Thus when the client receives
a MessageReply encapsulating a message ID from the events channel it
can link these reply messages to a given subscription to a remote spool.

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
   author = {Leif Ryge and David Stainton},
   url = {FIXME},
   year = {2020}
   }
