# Copyright (C) 2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.conf import settings
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _

import freppledb.common.views
from freppledb.common.models import (
    APIKey,
    Attribute,
    User,
    Bucket,
    BucketDetail,
    Parameter,
    Comment,
)
from freppledb.menu import menu
from freppledb import __version__


def isDefaultDatabase(request):
    return getattr(request, "database", DEFAULT_DB_ALIAS) == DEFAULT_DB_ALIAS


def hasInstallableApps(request):
    return (
        request.user.is_superuser
        and hasattr(settings, "INSTALLABLE_APPS")
        and getattr(request, "database", DEFAULT_DB_ALIAS) == DEFAULT_DB_ALIAS
    )


# Settings menu
menu.addItem(
    "admin",
    "parameter admin",
    url="/data/common/parameter/",
    report=freppledb.common.views.ParameterList,
    index=1100,
    model=Parameter,
    admin=True,
)
menu.addItem(
    "admin",
    "attribute admin",
    url="/data/common/attribute/",
    report=freppledb.common.views.AttributeList,
    index=1150,
    model=Attribute,
    admin=True,
    dependencies=[
        isDefaultDatabase,
    ],
)
menu.addItem(
    "admin",
    "apps",
    url="/apps/",
    label=_("Apps"),
    index=1160,
    dependencies=[
        hasInstallableApps,
    ],
)
menu.addItem(
    "admin",
    "apikey admin",
    url="/data/common/apikey/",
    report=freppledb.common.views.APIKeyList,
    index=1170,
    model=APIKey,
    admin=True,
    dependencies=[
        isDefaultDatabase,
    ],
)
menu.addItem(
    "admin",
    "bucket admin",
    url="/data/common/bucket/",
    report=freppledb.common.views.BucketList,
    index=1200,
    model=Bucket,
    admin=True,
)
menu.addItem(
    "admin",
    "bucketdetail admin",
    url="/data/common/bucketdetail/",
    report=freppledb.common.views.BucketDetailList,
    index=1300,
    model=BucketDetail,
    admin=True,
)
menu.addItem(
    "admin",
    "comment admin",
    url="/data/common/comment/",
    report=freppledb.common.views.CommentList,
    index=1400,
    model=Comment,
    admin=True,
)

# User maintenance
menu.addItem("admin", "users", separator=True, index=2000)
menu.addItem(
    "admin",
    "user admin",
    url="/data/common/user/",
    report=freppledb.common.views.UserList,
    index=2100,
    model=User,
    admin=True,
)
menu.addItem(
    "admin",
    "group admin",
    url="/data/auth/group/",
    report=freppledb.common.views.GroupList,
    index=2200,
    permission="auth.change_group",
    admin=True,
)

# Help menu
try:
    versionnumber = __version__.split(".", 2)
    docurl = "%s/docs/%s.%s/index.html" % (
        settings.DOCUMENTATION_URL,
        versionnumber[0],
        versionnumber[1],
    )
except Exception:
    docurl = "%s/docs/current/index.html" % (settings.DOCUMENTATION_URL,)
menu.addItem(
    "help",
    "documentation",
    url=docurl,
    label=_("Documentation"),
    window=True,
    prefix=False,
    index=300,
)
menu.addItem(
    "help",
    "API",
    url="/api/",
    label=_("REST API help"),
    window=False,
    prefix=True,
    index=400,
)
menu.addItem(
    "help",
    "website",
    url="https://frepple.com",
    window=True,
    label=_("frePPLe website"),
    prefix=False,
    index=500,
)
menu.addItem(
    "help", "about", javascript="about_show()", label=_("About frePPLe"), index=600
)
