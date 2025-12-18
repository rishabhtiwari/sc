/**
 * Migration: Update Hindi voice configuration to use single voice
 * 
 * The MMS Hindi TTS model only supports one voice, not separate male/female voices.
 * This migration updates all existing voice configurations to reflect this reality.
 * 
 * Changes:
 * - Change hi.defaultVoice from 'hi_male' to 'hi_default'
 * - Set hi.enableAlternation to false
 * - Clear hi.maleVoices and hi.femaleVoices arrays
 */

db = db.getSiblingDB('news');

print('Starting migration 037: Update Hindi voice configuration...');

try {
    // Update all voice_config documents that have Hindi configuration
    const result = db.voice_config.updateMany(
        {
            'voices.hi': { $exists: true }
        },
        {
            $set: {
                'voices.hi.defaultVoice': 'hi_default',
                'voices.hi.enableAlternation': false,
                'voices.hi.maleVoices': [],
                'voices.hi.femaleVoices': []
            }
        }
    );

    print(`✅ Updated ${result.modifiedCount} voice configuration(s)`);
    print('Migration 037 completed successfully!');

} catch (error) {
    print(`❌ Migration 037 failed: ${error}`);
    throw error;
}

