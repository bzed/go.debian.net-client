Example json-rpc client for deb.li/go.debian.net
------------------------------------------------

Requirements:
-------------
Either python-anyjson and one supported json implementation, like python-cjson
or python-json.


Adding an URL:
--------------
    % ./add_url http://bzed.de
    bjlx

Now http://deb.li/bjlx and http://go.debian.net/bjlx will redirect
to http://bzed.de and http://deb.li/p/bjlx / http://go.debian.net/p/bjlx
will show a preview page of the redirect.



Adding a static URL:
-------------------
This function allows to select the key to use:

    % ./add_static_url http://www.debian.org debian
    debian

Now http://deb.li/debian and http://go.debian.net/debian will redirect
to http://www.debian.org and http://deb.li/p/debian / http://go.debian.net/p/debian
will show a preview page of the redirect.


In case the selected key is already used, an exception is raised:

    % ./add_static_url http://www.google.de bjlx
    <class 'godebian.manage.AddStaticUrlException'>:The custom alias you've chosen is not available or too long. We've created a random one for you instead, but you can try assigning a different custom alias again.

    Kqx4



Requesting the URL by key:
--------------------------
    % ./get_url Kqx4
    http://www.google.de



