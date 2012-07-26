This is a very simple tool (read: hacky) designed to allow a computer behind a
router to expose local ports without setting up port forwarding on the router.
It has the additional benefit that the computer does not need to setup a static
(known) IP address.

It works under the assumption that there exists a 3rd machine that both the
NAT-ed computer and requesters for the NAT-ed computer can contact.

This is best illustrated via example. Suppose user A is behind a NAT, wants to
establish a service (say an HTTP server) on port N that user B can connect to.
Suppose that A and B are not behind the same NAT. Now suppose A and B can both
connect to server C, which as address X. Here's how to use this tool to make
this happen:

Pick a port M such that N != M. Now on server C, run:

    python server.py N M

Now user A runs:

    python client.py X M N

Additionally, user A starts up his service on port N locally.

Now, user B can connect to user A's service by simply using the address X:N.

The tool is currently very unstable, but it works to forward a simple HTTP
server on user A's machine.
