#
# Copyright (C) 2015 by frePPLe bvba
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

from django.conf import settings
import django.contrib.auth.models
import django.core.validators
from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', default=False, verbose_name='superuser status')),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, error_messages={'unique': 'A user with that username already exists.'}, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], verbose_name='username')),
                ('first_name', models.CharField(max_length=30, blank=True, verbose_name='first name')),
                ('last_name', models.CharField(max_length=30, blank=True, verbose_name='last name')),
                ('email', models.EmailField(max_length=254, blank=True, verbose_name='email address')),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('language', models.CharField(max_length=10, choices=[('auto', 'Detect automatically'), ('en', 'English'), ('fr', 'French'), ('it', 'Italian'), ('ja', 'Japanese'), ('nl', 'Dutch'), ('zh-cn', 'Simplified Chinese'), ('zh-tw', 'Traditional Chinese')], default='auto', verbose_name='language')),
                ('theme', models.CharField(max_length=settings.CATEGORYSIZE, choices=[('black-tie', 'black-tie'), ('blitzer', 'blitzer'), ('cupertino', 'cupertino'), ('dark-hive', 'dark-hive'), ('dot-luv', 'dot-luv'), ('eggplant', 'eggplant'), ('excite-bike', 'excite-bike'), ('flick', 'flick'), ('frepple', 'frepple'), ('hot-sneaks', 'hot-sneaks'), ('humanity', 'humanity'), ('le-frog', 'le-frog'), ('mint-choc', 'mint-choc'), ('overcast', 'overcast'), ('pepper-grinder', 'pepper-grinder'), ('redmond', 'redmond'), ('smoothness', 'smoothness'), ('south-street', 'south-street'), ('start', 'start'), ('sunny', 'sunny'), ('swanky-purse', 'swanky-purse'), ('trontastic', 'trontastic'), ('ui-darkness', 'ui-darkness'), ('ui-lightness', 'ui-lightness'), ('vader', 'vader')], default='frepple', verbose_name='theme')),
                ('pagesize', models.PositiveIntegerField(default=100, verbose_name='page size')),
                ('horizonbuckets', models.CharField(null=True, max_length=settings.NAMESIZE, blank=True)),
                ('horizonstart', models.DateTimeField(null=True, blank=True)),
                ('horizonend', models.DateTimeField(null=True, blank=True)),
                ('horizontype', models.BooleanField(default=True)),
                ('horizonlength', models.IntegerField(null=True, blank=True, default=6)),
                ('horizonunit', models.CharField(max_length=5, null=True, choices=[('day', 'day'), ('week', 'week'), ('month', 'month')], blank=True, default='month')),
                ('lastmodified', models.DateTimeField(null=True, db_index=True, auto_now=True, verbose_name='last modified')),
                ('groups', models.ManyToManyField(to='auth.Group', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups', related_name='user_set', blank=True, related_query_name='user')),
                ('user_permissions', models.ManyToManyField(to='auth.Permission', help_text='Specific permissions for this user.', verbose_name='user permissions', related_name='user_set', blank=True, related_query_name='user')),
            ],
            options={
                'verbose_name_plural': 'users',
                'db_table': 'common_user',
                'verbose_name': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Bucket',
            fields=[
                ('source', models.CharField(db_index=True, null=True, max_length=settings.CATEGORYSIZE, blank=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(db_index=True, editable=False, default=django.utils.timezone.now, verbose_name='last modified')),
                ('name', models.CharField(serialize=False, max_length=settings.NAMESIZE, primary_key=True, verbose_name='name')),
                ('description', models.CharField(null=True, max_length=settings.DESCRIPTIONSIZE, blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name_plural': 'buckets',
                'db_table': 'common_bucket',
                'verbose_name': 'bucket',
            },
        ),
        migrations.CreateModel(
            name='BucketDetail',
            fields=[
                ('source', models.CharField(db_index=True, null=True, max_length=settings.CATEGORYSIZE, blank=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(db_index=True, editable=False, default=django.utils.timezone.now, verbose_name='last modified')),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('name', models.CharField(db_index=True, max_length=settings.NAMESIZE, verbose_name='name')),
                ('startdate', models.DateTimeField(verbose_name='start date')),
                ('enddate', models.DateTimeField(verbose_name='end date')),
                ('bucket', models.ForeignKey(to='common.Bucket', verbose_name='bucket')),
            ],
            options={
                'verbose_name_plural': 'bucket dates',
                'db_table': 'common_bucketdetail',
                'verbose_name': 'bucket date',
                'ordering': ['bucket', 'startdate'],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('object_pk', models.TextField(verbose_name='object ID')),
                ('comment', models.TextField(max_length=3000, verbose_name='comment')),
                ('lastmodified', models.DateTimeField(editable=False, default=django.utils.timezone.now, verbose_name='last modified')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='content_type_set_for_comment', verbose_name='content type')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, editable=False, blank=True, verbose_name='user')),
            ],
            options={
                'verbose_name_plural': 'comments',
                'db_table': 'common_comment',
                'verbose_name': 'comment',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('source', models.CharField(db_index=True, null=True, max_length=settings.CATEGORYSIZE, blank=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(db_index=True, editable=False, default=django.utils.timezone.now, verbose_name='last modified')),
                ('name', models.CharField(serialize=False, max_length=settings.NAMESIZE, primary_key=True, verbose_name='name')),
                ('value', models.CharField(null=True, max_length=settings.NAMESIZE, blank=True, verbose_name='value')),
                ('description', models.CharField(null=True, max_length=settings.DESCRIPTIONSIZE, blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name_plural': 'parameters',
                'db_table': 'common_parameter',
                'verbose_name': 'parameter',
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='bucketdetail',
            unique_together=set([('bucket', 'startdate')]),
        ),
    ]
