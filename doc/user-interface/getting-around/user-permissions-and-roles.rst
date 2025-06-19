==========================
User permissions and roles
==========================

An administrator can create login accounts, set their password and permissions.

Groups are a generic way of categorizing users and apply permissions to those users.
A user in a group inherits all the permissions granted to that group.
A user can belong to any number of groups.

The user name, email, first name, last name, password are properties that are defined
system-wide.

The active flag, superuser flag, assigned groups and user permissions can
be defined per scenario. When the user is marked active in a scenario, the scenario
will appear in the dropdown list on the top right of the screen.

If a user isn't logged active in at least 1 scenario, he/she will not be able to 
log in.

New users are automatically assigned privileges according to the following rules:

- If a) DEFAULT_USER_GROUP setting is specified in your djangosettings.py file and 
  b) the permissions of this group aren't empty, then a new user will automatically
  become a member of this group upon creation.

- When there are no default permissions defined with the previous rule, the user 
  is automatically marked as a superuser.

.. image:: ../_images/user.png
   :alt: User

.. image:: ../_images/user-group.png
   :alt: User group
