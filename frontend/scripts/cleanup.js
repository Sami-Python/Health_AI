const fs = require('fs');
const path = require('path');

const paths = ['node_modules', '.next', 'package-lock.json'];

console.log('🧹 Starting project cleanup...');

paths.forEach(p => {
    const fullPath = path.join(process.cwd(), p);
    if (fs.existsSync(fullPath)) {
        console.log(`Deleting ${p}...`);
        try {
            fs.rmSync(fullPath, { recursive: true, force: true });
            console.log(`✅ Deleted ${p}`);
        } catch (e) {
            console.error(`❌ Failed to delete ${p}: ${e.message}`);
            process.exit(1);
        }
    } else {
        console.log(`ℹ️ ${p} not found, skipping.`);
    }
});

console.log('✨ Cleanup complete. Ready for fresh install.');
