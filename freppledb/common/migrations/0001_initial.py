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

from django.contrib.contenttypes.models import ContentType

  
class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(verbose_name='username', unique=True, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.')),
                ('first_name', models.CharField(verbose_name='first name', blank=True, max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', blank=True, max_length=30)),
                ('email', models.EmailField(verbose_name='email address', blank=True, max_length=254)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('language', models.CharField(choices=[('auto', 'Detect automatically'), ('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('it', 'Italian'), ('ja', 'Japanese'), ('nl', 'Dutch'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('zh-cn', 'Simplified Chinese'), ('zh-tw', 'Traditional Chinese')], verbose_name='language', default='auto', max_length=10)),
                ('theme', models.CharField(max_length=20, choices=[('grass', 'Grass'), ('lemon', 'Lemon'), ('water', 'Water'), ('snow', 'Snow'), ('strawberry', 'Strawberry'), ('earth', 'Earth')], verbose_name='theme', default='grass')),
                ('pagesize', models.PositiveIntegerField(verbose_name='page size', default=100)),
                ('horizonbuckets', models.CharField(null=True, blank=True, max_length=300)),
                ('horizonstart', models.DateTimeField(null=True, blank=True)),
                ('horizonend', models.DateTimeField(null=True, blank=True)),
                ('horizontype', models.BooleanField(default=True)),
                ('horizonlength', models.IntegerField(blank=True, null=True, default=6)),
                ('horizonunit', models.CharField(choices=[('day', 'day'), ('week', 'week'), ('month', 'month')], blank=True, null=True, default='month', max_length=5)),
                ('lastmodified', models.DateTimeField(verbose_name='last modified', null=True, auto_now=True, db_index=True)),
                ('groups', models.ManyToManyField(related_name='user_set', to='auth.Group', verbose_name='groups', related_query_name='user', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')),
                ('user_permissions', models.ManyToManyField(related_name='user_set', to='auth.Permission', verbose_name='user permissions', related_query_name='user', blank=True, help_text='Specific permissions for this user.')),
            ],
            options={
                'db_table': 'common_user',
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Bucket',
            fields=[
                ('source', models.CharField(null=True, blank=True, verbose_name='source', db_index=True, max_length=300)),
                ('lastmodified', models.DateTimeField(editable=False, db_index=True, verbose_name='last modified', default=django.utils.timezone.now)),
                ('name', models.CharField(primary_key=True, verbose_name='name', serialize=False, max_length=300)),
                ('description', models.CharField(null=True, verbose_name='description', blank=True, max_length=500)),
                ('level', models.IntegerField(verbose_name='level', help_text='Higher values indicate more granular time buckets')),
            ],
            options={
                'db_table': 'common_bucket',
                'verbose_name': 'bucket',
                'verbose_name_plural': 'buckets',
            },
        ),
        migrations.CreateModel(
            name='BucketDetail',
            fields=[
                ('source', models.CharField(null=True, blank=True, verbose_name='source', db_index=True, max_length=300)),
                ('lastmodified', models.DateTimeField(editable=False, db_index=True, verbose_name='last modified', default=django.utils.timezone.now)),
                ('id', models.AutoField(primary_key=True, verbose_name='identifier', serialize=False)),
                ('name', models.CharField(verbose_name='name', db_index=True, max_length=300)),
                ('startdate', models.DateTimeField(verbose_name='start date')),
                ('enddate', models.DateTimeField(verbose_name='end date')),
                ('bucket', models.ForeignKey(verbose_name='bucket', to='common.Bucket')),
            ],
            options={
                'db_table': 'common_bucketdetail',
                'ordering': ['bucket', 'startdate'],
                'verbose_name_plural': 'bucket dates',
                'verbose_name': 'bucket date',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='identifier', serialize=False)),
                ('object_pk', models.TextField(verbose_name='object ID')),
                ('comment', models.TextField(verbose_name='comment', max_length=3000)),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', default=django.utils.timezone.now)),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_comment', verbose_name='content type', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(verbose_name='user', null=True, editable=False, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'common_comment',
                'ordering': ('id',),
                'verbose_name_plural': 'comments',
                'verbose_name': 'comment',
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('source', models.CharField(null=True, blank=True, verbose_name='source', db_index=True, max_length=300)),
                ('lastmodified', models.DateTimeField(editable=False, db_index=True, verbose_name='last modified', default=django.utils.timezone.now)),
                ('name', models.CharField(primary_key=True, verbose_name='name', serialize=False, max_length=60)),
                ('value', models.CharField(null=True, verbose_name='value', blank=True, max_length=1000)),
                ('description', models.CharField(null=True, verbose_name='description', blank=True, max_length=1000)),
            ],
            options={
                'db_table': 'common_parameter',
                'verbose_name': 'parameter',
                'verbose_name_plural': 'parameters',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('name', models.CharField(primary_key=True, verbose_name='name', serialize=False, max_length=300)),
                ('description', models.CharField(null=True, verbose_name='description', blank=True, max_length=500)),
                ('status', models.CharField(choices=[('free', 'Free'), ('in use', 'In use'), ('busy', 'Busy')], verbose_name='status', max_length=10)),
                ('lastrefresh', models.DateTimeField(null=True, editable=False, verbose_name='last refreshed')),
            ],
            options={
                'db_table': 'common_scenario',
                'ordering': ['name'],
                'verbose_name_plural': 'scenarios',
                'verbose_name': 'scenario',
                'permissions': (('copy_scenario', 'Can copy a scenario'), ('release_scenario', 'Can release a scenario')),
            },
        ),
        migrations.AlterUniqueTogether(
            name='bucketdetail',
            unique_together=set([('bucket', 'startdate')]),
        ),
    ]
