/**
 * Migration: Update voice configuration to use GPU or CPU models
 * 
 * This migration updates voice configurations based on GPU availability:
 * - If GPU is enabled (USE_GPU=true): Use coqui-xtts for both English and Hindi
 * - If GPU is disabled (USE_GPU=false): Use kokoro-82m for English, mms-tts-hin for Hindi
 * 
 * The migration reads the USE_GPU environment variable to determine which models to use.
 * 
 * GPU Mode (Coqui XTTS):
 * - Universal multi-lingual model
 * - Same speakers for both English and Hindi
 * - High-quality voice cloning capabilities
 * 
 * CPU Mode (Kokoro + MMS):
 * - Language-specific models
 * - Kokoro for English (multiple voices)
 * - MMS for Hindi (single voice)
 */

// Read environment variable for GPU mode
const USE_GPU = process.env.USE_GPU === 'true';

db = db.getSiblingDB('news');

print('🎤 Starting migration 046: Update voice config for GPU/CPU models...');
print(`🔧 GPU Mode: ${USE_GPU ? 'ENABLED' : 'DISABLED'}`);

try {
    // Get all voice_config documents
    const configs = db.voice_config.find({ is_deleted: false }).toArray();
    
    print(`ℹ️  Found ${configs.length} voice configuration(s) to update`);
    
    if (USE_GPU) {
        // GPU Mode: Use Coqui XTTS for both languages
        print('🎮 Configuring for GPU mode with Coqui XTTS...');
        
        // Default Coqui XTTS speakers (these will be fetched from audio service in production)
        const defaultMaleVoices = ['Claribel Dervla', 'Dionisio Schuyler', 'Royston Min'];
        const defaultFemaleVoices = ['Ana Florence', 'Annmarie Nele', 'Asya Anara'];
        const defaultVoice = 'Claribel Dervla';
        
        configs.forEach(config => {
            print(`\n📝 Updating config for customer: ${config.customer_id}`);
            
            const updateDoc = {
                $set: {
                    'models.en': 'coqui-xtts',
                    'models.hi': 'coqui-xtts',
                    'voices.en.defaultVoice': defaultVoice,
                    'voices.en.enableAlternation': true,
                    'voices.en.maleVoices': defaultMaleVoices,
                    'voices.en.femaleVoices': defaultFemaleVoices,
                    'voices.hi.defaultVoice': defaultVoice,
                    'voices.hi.enableAlternation': true,
                    'voices.hi.maleVoices': defaultMaleVoices,
                    'voices.hi.femaleVoices': defaultFemaleVoices,
                    'updated_by': 'migration_046_gpu',
                    'updated_at': new Date()
                }
            };
            
            db.voice_config.updateOne(
                { _id: config._id },
                updateDoc
            );
            
            print(`✅ Updated to GPU mode (coqui-xtts) for customer: ${config.customer_id}`);
        });
        
    } else {
        // CPU Mode: Use Kokoro for English, MMS for Hindi
        print('💻 Configuring for CPU mode with Kokoro (EN) and MMS (HI)...');
        
        configs.forEach(config => {
            print(`\n📝 Updating config for customer: ${config.customer_id}`);
            
            const updateDoc = {
                $set: {
                    'models.en': 'kokoro-82m',
                    'models.hi': 'mms-tts-hin',
                    'voices.en.defaultVoice': 'am_adam',
                    'voices.en.enableAlternation': true,
                    'voices.en.maleVoices': ['am_adam', 'am_michael'],
                    'voices.en.femaleVoices': ['af_bella', 'af_sarah'],
                    'voices.hi.defaultVoice': 'hi_default',
                    'voices.hi.enableAlternation': false,
                    'voices.hi.maleVoices': [],
                    'voices.hi.femaleVoices': [],
                    'updated_by': 'migration_046_cpu',
                    'updated_at': new Date()
                }
            };
            
            db.voice_config.updateOne(
                { _id: config._id },
                updateDoc
            );
            
            print(`✅ Updated to CPU mode (kokoro-82m/mms-tts-hin) for customer: ${config.customer_id}`);
        });
    }
    
    print('\n✅ Migration 046 completed successfully!');
    print(`📊 Total configurations updated: ${configs.length}`);
    print(`🎯 Mode: ${USE_GPU ? 'GPU (Coqui XTTS)' : 'CPU (Kokoro + MMS)'}`);
    
} catch (error) {
    print(`❌ Migration 046 failed: ${error}`);
    throw error;
}

