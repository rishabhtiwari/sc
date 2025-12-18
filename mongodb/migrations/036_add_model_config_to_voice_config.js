// Migration: Add model configuration to voice_config
// Description: Restructures voice_config to support model selection per language
// Date: 2025-12-18

db = db.getSiblingDB('news');

print('🎤 Adding model configuration to voice_config collection...');

// Get all voice_config documents
const configs = db.voice_config.find({ is_deleted: false }).toArray();

print(`ℹ️  Found ${configs.length} voice config documents to migrate`);

configs.forEach(config => {
    print(`\n📝 Migrating config for customer: ${config.customer_id}`);
    
    const currentLanguage = config.language || 'en';
    const currentDefaultVoice = config.defaultVoice || 'am_adam';
    const currentEnableAlternation = config.enableAlternation !== undefined ? config.enableAlternation : true;
    const currentMaleVoices = config.maleVoices || ['am_adam', 'am_michael'];
    const currentFemaleVoices = config.femaleVoices || ['af_bella', 'af_sarah'];
    
    // Determine default models based on current language
    const defaultEnglishModel = 'kokoro-82m';
    const defaultHindiModel = 'mms-tts-hin';
    
    // Build new structure
    const newConfig = {
        customer_id: config.customer_id,
        language: currentLanguage,  // Keep primary language
        
        // Model configuration per language
        models: {
            en: defaultEnglishModel,
            hi: defaultHindiModel
        },
        
        // Voice configuration per language
        voices: {},
        
        // Metadata
        created_by: config.created_by || 'migration_script',
        updated_by: 'migration_036',
        created_at: config.created_at || new Date(),
        updated_at: new Date(),
        is_deleted: false
    };
    
    // Set voice config based on current language
    if (currentLanguage === 'hi') {
        // Hindi configuration
        newConfig.voices.hi = {
            defaultVoice: currentDefaultVoice,
            enableAlternation: currentEnableAlternation,
            maleVoices: currentMaleVoices,
            femaleVoices: currentFemaleVoices
        };
        // Add default English config
        newConfig.voices.en = {
            defaultVoice: 'am_adam',
            enableAlternation: true,
            maleVoices: ['am_adam', 'am_michael'],
            femaleVoices: ['af_bella', 'af_sarah']
        };
    } else {
        // English configuration
        newConfig.voices.en = {
            defaultVoice: currentDefaultVoice,
            enableAlternation: currentEnableAlternation,
            maleVoices: currentMaleVoices,
            femaleVoices: currentFemaleVoices
        };
        // Add default Hindi config
        newConfig.voices.hi = {
            defaultVoice: 'hi_male',
            enableAlternation: true,
            maleVoices: ['hi_male'],
            femaleVoices: ['hi_female']
        };
    }
    
    // Replace the document
    db.voice_config.replaceOne(
        { _id: config._id },
        newConfig
    );
    
    print(`✅ Migrated config for customer: ${config.customer_id}`);
    print(`   - Primary language: ${newConfig.language}`);
    print(`   - English model: ${newConfig.models.en}`);
    print(`   - Hindi model: ${newConfig.models.hi}`);
    print(`   - English voices: ${JSON.stringify(newConfig.voices.en)}`);
    print(`   - Hindi voices: ${JSON.stringify(newConfig.voices.hi)}`);
});

print('\n✅ Migration 036_add_model_config_to_voice_config completed successfully');
print(`📊 Total configs migrated: ${configs.length}`);

