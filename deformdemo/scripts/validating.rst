Validating HTML pages against the HTML 5 validator
==================================================


Why validate?
-------------

HTML validation is not an end in itself. HTML is necessarily extensible and
HTML 5 has been designed with this in mind. Nevertheless, checking for valid
HTML is a good way to avoid bugs in behaviour between browsers. In addition,
valid HTML is most likely to conform with accessibility requirements as there
are some semantic restrictions, such as which child elements a tag may or not
have, or association, which really make sense when there is only the markup.


How to validate?
----------------

As there is currently no easily installable library for validation (and I'm
willing to be proved wrong on this). The best way to validate is using an
online service such as that provided by http://validator.nu We have adapted
the Mozilla script for this and added the option to receive results in JSON.
The standalone script can be used with URLs or with local files. Valid pages
always return: {"messages":[]} so an empty `messages` list can be used as a
test pass.

`sample.json` contains a sample report for a non-validating page.


Ignored errors
--------------

As noted above, validating HTML is just a means to an end. Some errors will
be detected which cannot fixed and functionality maintained. We have created
a list of such errors.
