Katzenpost Mix Plugin PubSub Specification
******************************************

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

In the previous Katzenpost plugin system, server plugins communicated with the mixnet server using HTTP over unix domain sockets. This approach was chosen to simplify implementation, but it is no longer appropriate in the sublish subscribe model as it would require polling.

The new wire protocol between plugins and the mix server shall make use of
unix domain sockets with length-prefixed CBOR objects. Either the mix server
or the plugin may send a message at anytime without the need for a response to 
strictly follow a request as was the case with HTTP.



3. Sphinx Packet Payload Considerations
=======================================

The Sphinx packet payloads are decrypted and decoded on the
Providers and the precise payload format is a 2-byte Sphinx payload
plaintext header followed by an optional SURB of length 556 bytes
followed by plaintext or additional ciphertext (client end to end
encrypted).

The second byte of the Sphinx payload plaintext is a zero byte
reserved value while the first byte contains a flag which denotes
either there is a SURB present or there is NOT a SURB present. Herein
we propose to add a third flag which shall explicitly state that is a
SURB present AND there are additional subscription SURBs present. In this
case the first SURB is used to send the plugin response to the client
as is documented in the Kaetzchen plugin system [KAETZCHEN]_ however the
additional subscription SURBs will then be queued in the mix server AND
a unique subscription identifier will be generated and sent to the plugin is the
initial request message. Therefore the plugin can make use of these
subscription SURBs by sending the mix server (via unix domain socket)
that same subscription ID.

The fist byte of the ciphertext which comes
after the first SURB SHALL contain a single byte denoting the number
of subscription SURBs. However this number MUST be accurate and is
bounded by the Sphinx packet payload size. Packets
specifying an incorrect subscription SURB prefix value SHALL be
dropped by the Provider without further processing.

type SphinxPayload struct {
    SURBCount byte
    Reserved byte
    Plaintext []byte
}

Messages sent between katzenpost and application plugins
========================================================

Katzenpost client
-----------------

On this side, the applications picks the subscription ID.

Client application sends to katzenpost client:
* subscribe(server_address, subscription_id, spool_id, last_message_id)

Katzenpost client sends to client application:
* new_message(subscription_id, message)
* error(subscription_id, error_type)

Katzenpost server
-----------------

On this side, the katzenpost server picks the subscription ID.

Katzenpost server sends to client application:
* subscribe(subscription_id, spool_id, last_message_id)
* unsubscribe(subscription_id)

Server application sends to katzenpost server:
* new_messages(subscription_id, app_messages)
* error(subscription_id, error_type) (maybe? not ure this is necessary.)

Messages sent between katzenpost client and server
==================================================

Katzenpost client to katzenpost server
--------------------------------------

* fetch(spool_id, last_message_id, SURBs)

Katzenpost server to katzenpost client
--------------------------------------

* new_messages(spool_id, app_messages)

Protocol Flow
=============

First, client application sends katzenpost client a subscribe message.

For the duration of the

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

