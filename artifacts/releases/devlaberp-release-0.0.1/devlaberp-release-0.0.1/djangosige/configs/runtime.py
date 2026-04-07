import os
from urllib.parse import quote


def read_env_file(env_path):
    project_env = {}
    if not env_path or not os.path.exists(env_path):
        return project_env

    with open(env_path, encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            project_env[key.strip()] = value.strip()

    return project_env


def project_config(project_env, environ, name, default=None, cast=None):
    if name in project_env:
        value = project_env[name]
    elif name in environ:
        value = environ[name]
    else:
        value = default

    if cast is None:
        return value

    return cast(value)


def env_bool(project_env, environ, name, default=False):
    value = project_config(project_env, environ, name, default=str(default))
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')


def resolve_env_path(project_root, environ):
    env_path = environ.get('SIGE_ENV_PATH')
    if env_path:
        return os.path.abspath(env_path)
    return os.path.join(project_root, '.env')


def resolve_path(value, default_base):
    if not value:
        return os.path.abspath(default_base)
    if os.path.isabs(value):
        return value
    return os.path.abspath(os.path.join(default_base, value))


def resolve_runtime_paths(project_root, app_root, project_env, environ):
    app_data_root = resolve_path(
        project_config(project_env, environ, 'APP_DATA_ROOT', default=app_root),
        project_root,
    )
    media_root = resolve_path(
        project_config(project_env, environ, 'MEDIA_ROOT', default=os.path.join(app_data_root, 'media')),
        app_data_root,
    )
    static_root = resolve_path(
        project_config(project_env, environ, 'STATIC_ROOT', default=os.path.join(app_data_root, 'staticfiles')),
        app_data_root,
    )
    log_root = resolve_path(
        project_config(project_env, environ, 'LOG_ROOT', default=os.path.join(app_data_root, 'logs')),
        app_data_root,
    )

    return {
        'APP_DATA_ROOT': app_data_root,
        'MEDIA_ROOT': media_root,
        'STATIC_ROOT': static_root,
        'LOG_ROOT': log_root,
    }


def build_database_url(default_database_url, app_data_root, project_env, environ):
    explicit_database_url = project_config(project_env, environ, 'DATABASE_URL', default='')
    if explicit_database_url:
        return explicit_database_url

    db_engine = str(project_config(project_env, environ, 'DB_ENGINE', default='')).strip().lower()
    if not db_engine:
        if default_database_url:
            return default_database_url
        return 'sqlite:///' + os.path.join(app_data_root, 'db.sqlite3')

    if db_engine in ('postgres', 'postgresql', 'pgsql'):
        db_name = project_config(project_env, environ, 'DB_NAME', default='')
        if not db_name:
            raise ValueError('DB_NAME e obrigatorio quando DB_ENGINE=postgresql')

        db_user = quote(str(project_config(project_env, environ, 'DB_USER', default='')).strip(), safe='')
        db_password = quote(str(project_config(project_env, environ, 'DB_PASSWORD', default='')).strip(), safe='')
        db_host = str(project_config(project_env, environ, 'DB_HOST', default='127.0.0.1')).strip() or '127.0.0.1'
        db_port = str(project_config(project_env, environ, 'DB_PORT', default='5432')).strip() or '5432'

        credentials = ''
        if db_user:
            credentials = db_user
            if db_password:
                credentials += ':' + db_password
            credentials += '@'

        return f'postgresql://{credentials}{db_host}:{db_port}/{db_name}'

    if db_engine == 'sqlite':
        db_name = project_config(project_env, environ, 'DB_NAME', default='db.sqlite3')
        db_path = resolve_path(db_name, app_data_root)
        return 'sqlite:///' + db_path

    raise ValueError(f'DB_ENGINE nao suportado: {db_engine}')
