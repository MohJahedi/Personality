import {spawnSync} from 'node:child_process';
const python = process.platform === 'win32' ? 'python' : 'python3';
const result = spawnSync(python, ['-m', 'unittest', 'discover', '-s', 'tests', '-v'], {stdio: 'inherit'});
if (result.error) {console.error('Python 3.11+ is required:', result.error.message); process.exit(1);}
process.exit(result.status ?? 1);
