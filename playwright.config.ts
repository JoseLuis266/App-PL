import {defineConfig} from '@playwright/test';
const port=process.env.PLSTUDY_TEST_PORT??'4180';
export default defineConfig({testDir:'./e2e',workers:1,use:{baseURL:`http://127.0.0.1:${port}`,launchOptions:{executablePath:process.env.PLSTUDY_CHROMIUM??'/usr/bin/chromium',args:['--no-sandbox']}},webServer:{command:`npm run dev -- --port ${port}`,url:`http://127.0.0.1:${port}`,reuseExistingServer:false},reporter:'list'});
