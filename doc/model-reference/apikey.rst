========
API Keys
========

An API key works as a password for authenticating external applications.

API keys make it easy to manage and control access to the frepple APIs.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            | Free text description of the use of this key.

created          datetime          | Read-only field with the creation date of this key.

expiry date      datetime          | Expiry date of the key. It can only be specified when the
                                     API key is created.
                                   | The maximum allowed life for an API key can be configured
                                     with the setting APIKEY_MAX_LIFE.
================ ================= ===========================================================
