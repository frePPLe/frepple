#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from .models import NotificationFactory, User, Bucket, BucketDetail, Parameter


@NotificationFactory.register(User, [User])
def UserNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Bucket, [Bucket, BucketDetail])
def BucketNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif msg.content_type.model_class() == BucketDetail:
        return flw.object_pk == msg.content_object.bucket.name


@NotificationFactory.register(BucketDetail, [BucketDetail])
def BucketDetailNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Parameter, [Parameter])
def ParameterNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk
