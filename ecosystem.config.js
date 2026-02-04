module.exports = {
  apps: [{
    name: 'tk-witz-bot',
    script: 'main.py',
    interpreter: 'python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    // Restart-Strategie bei Fehlern
    exp_backoff_restart_delay: 100,
    max_restarts: 10,
    min_uptime: '10s',
    // Graceful Shutdown
    kill_timeout: 5000,
    wait_ready: false,
    listen_timeout: 3000
  }]
};
