#
# Copyright (C) 2016 by frePPLe bvba
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
from datetime import datetime

from django.db import migrations, models
import django.contrib.auth.models
import freppledb.common.fields
import django.core.validators
import django.utils.timezone
from django.conf import settings


def createAdminUser(apps, schema_editor):
  if not schema_editor.connection.alias == 'default':
    return
  from django.contrib.auth import get_user_model
  User = get_user_model()
  usr = User.objects.create_superuser('admin', 'your@company.com', 'admin')
  usr.first_name = 'admin'
  usr.last_name = 'admin'
  usr.date_joined = datetime(2000, 1, 1)
  usr.horizontype = True
  usr.horizonlength = 6
  usr.horizonunit = "month"
  usr.language = "auto"
  usr.save()


class Migration(migrations.Migration):

    replaces = [('common', '0001_initial'), ('common', '0002_defaultuser'), ('common', '0003_wizard'), ('common', '0006_permission_names'), ('common', '0007_preferences')]

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, verbose_name='last login', null=True)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status', default=False)),
                ('username', models.CharField(unique=True, verbose_name='username', max_length=30, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', error_messages={'unique': 'A user with that username already exists.'}, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')])),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', verbose_name='staff status', default=False)),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active', default=True)),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('language', models.CharField(max_length=10, verbose_name='language', choices=[('auto', 'Detect automatically'), ('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('it', 'Italian'), ('ja', 'Japanese'), ('nl', 'Dutch'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('zh-cn', 'Simplified Chinese'), ('zh-tw', 'Traditional Chinese')], default='auto')),
                ('theme', models.CharField(max_length=20, verbose_name='theme', choices=[('grass', 'Grass'), ('lemon', 'Lemon'), ('water', 'Water'), ('snow', 'Snow'), ('strawberry', 'Strawberry'), ('earth', 'Earth')], default='grass')),
                ('pagesize', models.PositiveIntegerField(verbose_name='page size', default=100)),
                ('horizonbuckets', models.CharField(blank=True, max_length=300, null=True)),
                ('horizonstart', models.DateTimeField(blank=True, null=True)),
                ('horizonend', models.DateTimeField(blank=True, null=True)),
                ('horizontype', models.BooleanField(default=True)),
                ('horizonlength', models.IntegerField(blank=True, default=6, null=True)),
                ('horizonunit', models.CharField(blank=True, max_length=5, choices=[('day', 'day'), ('week', 'week'), ('month', 'month')], default='month', null=True)),
                ('lastmodified', models.DateTimeField(verbose_name='last modified', db_index=True, auto_now=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, related_query_name='user', verbose_name='groups', related_name='user_set', to='auth.Group', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')),
                ('user_permissions', models.ManyToManyField(blank=True, related_query_name='user', verbose_name='user permissions', related_name='user_set', to='auth.Permission', help_text='Specific permissions for this user.')),
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
                ('source', models.CharField(blank=True, db_index=True, verbose_name='source', null=True, max_length=300)),
                ('lastmodified', models.DateTimeField(db_index=True, verbose_name='last modified', default=django.utils.timezone.now, editable=False)),
                ('name', models.CharField(serialize=False, verbose_name='name', primary_key=True, max_length=300)),
                ('description', models.CharField(blank=True, max_length=500, verbose_name='description', null=True)),
                ('level', models.IntegerField(help_text='Higher values indicate more granular time buckets', verbose_name='level')),
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
                ('source', models.CharField(blank=True, db_index=True, verbose_name='source', null=True, max_length=300)),
                ('lastmodified', models.DateTimeField(db_index=True, verbose_name='last modified', default=django.utils.timezone.now, editable=False)),
                ('id', models.AutoField(serialize=False, verbose_name='identifier', primary_key=True)),
                ('name', models.CharField(db_index=True, verbose_name='name', max_length=300)),
                ('startdate', models.DateTimeField(verbose_name='start date')),
                ('enddate', models.DateTimeField(verbose_name='end date')),
                ('bucket', models.ForeignKey(to='common.Bucket', verbose_name='bucket')),
            ],
            options={
                'verbose_name_plural': 'bucket dates',
                'db_table': 'common_bucketdetail',
                'ordering': ['bucket', 'startdate'],
                'verbose_name': 'bucket date',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='identifier', primary_key=True)),
                ('object_pk', models.TextField(verbose_name='object ID')),
                ('comment', models.TextField(max_length=3000, verbose_name='comment')),
                ('lastmodified', models.DateTimeField(verbose_name='last modified', default=django.utils.timezone.now, editable=False)),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_comment', verbose_name='content type', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(blank=True, verbose_name='user', to=settings.AUTH_USER_MODEL, null=True, editable=False)),
            ],
            options={
                'verbose_name_plural': 'comments',
                'db_table': 'common_comment',
                'ordering': ('id',),
                'verbose_name': 'comment',
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('source', models.CharField(blank=True, db_index=True, verbose_name='source', null=True, max_length=300)),
                ('lastmodified', models.DateTimeField(db_index=True, verbose_name='last modified', default=django.utils.timezone.now, editable=False)),
                ('name', models.CharField(serialize=False, verbose_name='name', primary_key=True, max_length=60)),
                ('value', models.CharField(blank=True, max_length=1000, verbose_name='value', null=True)),
                ('description', models.CharField(blank=True, max_length=1000, verbose_name='description', null=True)),
            ],
            options={
                'verbose_name_plural': 'parameters',
                'db_table': 'common_parameter',
                'verbose_name': 'parameter',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('name', models.CharField(serialize=False, verbose_name='name', primary_key=True, max_length=300)),
                ('description', models.CharField(blank=True, max_length=500, verbose_name='description', null=True)),
                ('status', models.CharField(max_length=10, verbose_name='status', choices=[('free', 'Free'), ('in use', 'In use'), ('busy', 'Busy')])),
                ('lastrefresh', models.DateTimeField(verbose_name='last refreshed', null=True, editable=False)),
            ],
            options={
                'verbose_name_plural': 'scenarios',
                'db_table': 'common_scenario',
                'permissions': (('copy_scenario', 'Can copy a scenario'), ('release_scenario', 'Can release a scenario')),
                'ordering': ['name'],
                'verbose_name': 'scenario',
            },
        ),
        migrations.AlterUniqueTogether(
            name='bucketdetail',
            unique_together=set([('bucket', 'startdate')]),
        ),
        migrations.RunPython(
            code=createAdminUser,
        ),
        migrations.CreateModel(
            name='Wizard',
            fields=[
                ('name', models.CharField(serialize=False, verbose_name='name', primary_key=True, max_length=300)),
                ('sequenceorder', models.IntegerField(help_text='Model completion level', verbose_name='progress')),
                ('url_doc', models.URLField(blank=True, max_length=500, verbose_name='documentation URL', null=True)),
                ('url_internaldoc', models.URLField(blank=True, max_length=500, verbose_name='wizard URL', null=True)),
                ('status', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(blank=True, related_name='xchildren', verbose_name='owner', to='common.Wizard', help_text='Hierarchical parent', null=True)),
            ],
            options={
                'db_table': 'common_wizard',
                'ordering': ['sequenceorder'],
            },
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='identifier', primary_key=True)),
                ('property', models.CharField(max_length=100)),
                ('value', freppledb.common.fields.JSONField(max_length=1000)),
                ('user', models.ForeignKey(related_name='preferences', verbose_name='user', to=settings.AUTH_USER_MODEL, null=True, editable=False)),
            ],
            options={
                'verbose_name_plural': 'preferences',
                'verbose_name': 'preference',
                'db_table': 'common_preference',
            },
        ),
        migrations.AlterUniqueTogether(
            name='userpreference',
            unique_together=set([('user', 'property')]),
        ),           
    ]
