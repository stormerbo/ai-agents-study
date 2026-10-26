import { defineConfig, devices } from '@playwright/test';

const baseURL = 'http://127.0.0.1:3100';

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command:
      'node -e \'const {spawn,spawnSync}=require("node:child_process");const fs=require("node:fs");const os=require("node:os");const path=require("node:path");const root=process.cwd();const copy=fs.mkdtempSync(path.join(os.tmpdir(),"ai-agents-study-e2e-"));const excludes=["--exclude=/.git","--exclude=/.next","--exclude=/node_modules","--exclude=/.env","--exclude=/.env.*","--exclude=/output","--exclude=/test-results","--exclude=/playwright-report","--exclude=/.e2e-runner-*","--exclude=/.playwright-*","--exclude=/.serena","--exclude=/.superpowers","--exclude=/.spec-workflow","--exclude=/.pytest_cache","--exclude=/.venv","--exclude=/.chapter-nav-*","--exclude=/\\\\\\"/"];const sync=spawnSync("rsync",["-a",...excludes,"--exclude=/\\\"/","./",copy+path.sep],{cwd:root,stdio:"inherit"});if(sync.status!==0){fs.rmSync(copy,{recursive:true,force:true});process.exit(sync.status||1)}if(fs.existsSync(path.join(copy,".env.local"))){console.error("Refusing .env.local in snapshot");fs.rmSync(copy,{recursive:true,force:true});process.exit(1)}const copied=spawnSync("cp",["-a",path.join(root,"node_modules"),path.join(copy,"node_modules")],{cwd:root,stdio:"inherit"});if(copied.status!==0){fs.rmSync(copy,{recursive:true,force:true});process.exit(copied.status||1)}const outward=path.join(copy,"node_modules","node_modules");if(fs.existsSync(outward)&&fs.lstatSync(outward).isSymbolicLink())fs.unlinkSync(outward);const build=spawnSync("pnpm",["--dir",copy,"build"],{cwd:root,stdio:"inherit"});if(build.status!==0){fs.rmSync(copy,{recursive:true,force:true});process.exit(build.status||1)}const server=spawn("pnpm",["--dir",copy,"exec","next","start","--hostname","127.0.0.1","--port","3100"],{cwd:root,stdio:"inherit"});let stopping=false;const stop=signal=>{if(!stopping){stopping=true;server.kill(signal)}};process.once("SIGINT",()=>stop("SIGINT"));process.once("SIGTERM",()=>stop("SIGTERM"));server.on("error",error=>{console.error(error);fs.rmSync(copy,{recursive:true,force:true});process.exit(1)});server.on("exit",code=>{fs.rmSync(copy,{recursive:true,force:true});process.exit(code??0)})\'',
    url: `${baseURL}/chapters/what-is-an-agent/why-now`,
    reuseExistingServer: false,
    timeout: 600_000,
  },
});
