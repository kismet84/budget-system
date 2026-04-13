module.exports = {
  apps: [
    {
      name: 'budget-api',
      script: '/usr/local/bin/python3.11',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8001 --reload',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system/backend',
      watch: ['.'],  // PM2 watch for faster restart
      ignore_watch: ['venv/', '__pycache__/', '*.pyc', '.git/'],
      env: {
        PYTHONPATH: '/Users/kis/.hermes/memory/projects/budget-system/backend',
      },
    },
    {
      name: 'budget-frontend',
      script: 'node_modules/.bin/vite',
      args: '--port 5173 --mode production',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system/frontend',
      env: {
        VITE_NO_HMR: 'true',
      },
    },
  ]
};
