plugins_install_dir = join_paths(gnome_todo_pkglibdir, 'plugins')
plugins_inc = [top_inc, src_inc]
plugins_files = []

plugins_conf = configuration_data()
plugins_conf.set('VERSION', gnome_todo_version)

subdir('eds')

if get_option('enable-background-plugin')
  subdir('background')
endif

if get_option('enable-dark-theme-plugin')
  subdir('dark-theme')
endif

if get_option('enable-scheduled-panel-plugin')
  subdir('scheduled-panel')
endif

if get_option('enable-score-plugin')
  subdir('score')
endif

if get_option('enable-today-panel-plugin')
  subdir('today-panel')
endif

if get_option('enable-unscheduled-panel-plugin')
  subdir('unscheduled-panel')
endif

if get_option('enable-todo-txt-plugin')
  subdir('todo-txt')
endif
