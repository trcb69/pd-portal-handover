// PROPOSED PM2 ecosystem file for the joint demo v0.1 (spec section 2.7 names tools/demo-gateway/ecosystem.demo.config.cjs; that file does not
// exist in the gateway repo at 65c72b6, so it lives here, outside any repo, until the lead decides where it belongs).
// Three processes, fork mode, one instance each (the portal refuses to run as a PM2 cluster, server/app.js:11-15). No secret is in this file:
// every app reads its own .env from its own checkout. Start one at a time, in order, with --only (see RUNBOOK.md).
// Pre-start checks: when pm2 loads this file for a start/restart/reload, scripts/check-demo-env.sh is run for the named app(s); a failed check throws,
// so pm2 starts nothing. The runbook also runs that script by hand, so the safety does not depend on this hook.
// Prepared by Abdul Hadhee | IT Executive
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CHECK = path.join(__dirname, 'scripts', 'check-demo-env.sh');
const common = {
  exec_mode: 'fork',
  instances: 1,
  autorestart: true,
  max_restarts: 5,          // a crash loop stops after 5 tries instead of hammering Zoho or Chrome
  min_uptime: '20s',
  restart_delay: 5000,
  kill_timeout: 8000,       // the apps close their listeners and DB on SIGTERM
  time: true,
};
const apps = [
  { name: 'demo-gateway', key: 'gateway', cwd: '/root/demo/order-portal-gateway', script: 'tools/demo-gateway/server/main.js' },
  { name: 'demo-dashboard', key: 'dashboard', cwd: '/root/demo/production-dashboard', script: 'server/app.js' },
  { name: 'demo-portal', key: 'portal', cwd: '/root/demo/order-portal', script: 'server/app.js' },
];

const argv = process.argv.slice(2);
const starting = argv.some((a) => ['start', 'restart', 'reload', 'startOrRestart', 'startOrReload'].includes(a));
if (starting) {
  const i = argv.indexOf('--only');
  const only = i >= 0 ? String(argv[i + 1] ?? '').split(',') : null;
  for (const a of apps.filter((x) => !only || only.includes(x.name))) {
    const r = spawnSync('bash', [CHECK, a.key], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error(`pre-start check failed for ${a.name}; nothing was started:\n${r.stdout}${r.stderr}`);
  }
}

module.exports = { apps: apps.map(({ key, ...rest }) => ({ ...common, ...rest })) };
