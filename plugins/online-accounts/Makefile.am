include $(top_srcdir)/common.am

online_accounts_plugindir = $(plugindir)/online-accounts
online_accounts_plugin_DATA = online-accounts.plugin
nobase_online_accounts_plugin_DATA =  \
	online-accounts/__init__.py \
	online-accounts/preferences_panel.ui \
	online-accounts/account_row.ui \
	online-accounts/authentication.py \
	online-accounts/accounts.py \
	online-accounts/providers.py \
	online-accounts/todoist/models.py \
	online-accounts/todoist/api.py \
	online-accounts/todoist/managers/activity.py \
	online-accounts/todoist/managers/backups.py \
	online-accounts/todoist/managers/biz_invitations.py \
	online-accounts/todoist/managers/business_users.py \
	online-accounts/todoist/managers/collaborators.py \
	online-accounts/todoist/managers/collaborator_states.py \
	online-accounts/todoist/managers/completed.py \
	online-accounts/todoist/managers/filters.py \
	online-accounts/todoist/managers/generic.py \
	online-accounts/todoist/managers/__init__.py \
	online-accounts/todoist/managers/invitations.py \
	online-accounts/todoist/managers/items.py \
	online-accounts/todoist/managers/labels.py \
	online-accounts/todoist/managers/live_notifications.py \
	online-accounts/todoist/managers/locations.py \
	online-accounts/todoist/managers/notes.py \
	online-accounts/todoist/managers/projects.py \
	online-accounts/todoist/managers/reminders.py \
	online-accounts/todoist/managers/templates.py \
	online-accounts/todoist/managers/uploads.py \
	online-accounts/todoist/managers/user.py

EXTRA_DIST = \
	$(plugin_DATA) \
	$(nobase_online_accounts_plugin_DATA)
