import multiprocessing

# Configuración de Gunicorn para TemucoSoft
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/ec2-user/temucosoft/logs/gunicorn_access.log"
errorlog = "/home/ec2-user/temucosoft/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "temucosoft"

# Server mechanics
daemon = False
pidfile = "/home/ec2-user/temucosoft/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (deshabilitado por ahora, nginx maneja esto)
