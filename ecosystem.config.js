module.exports = {
  apps: [
    {
      name: 'budget-api',
      script: '/usr/local/bin/python3.11',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8001',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system/backend',
    },
    {
      name: 'budget-web',
      script: '/usr/local/bin/python3.11',
      args: '-m streamlit run frontend/app.py --server.port 8501 --server.headless true',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system',
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
