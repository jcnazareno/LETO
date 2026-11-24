import fs from 'node:fs';
export const research = JSON.parse(fs.readFileSync(new URL('./research_data.json', import.meta.url), 'utf8'));
