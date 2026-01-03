import { BaseVoiceModel } from './BaseVoiceModel.js';
import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import axios from 'axios';

/**
 * Coqui TTS XTTS v2 Voice Model
 * Communicates with Coqui TTS server running on port 5002
 */
export class CoquiVoiceModel extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        // Get Coqui TTS server URL from environment or config
        this.coquiServerUrl = config.coquiServerUrl || process.env.COQUI_TTS_URL || 'http://localhost:5002';
        this.defaultSpeaker = config.speaker || 'Claribel Dervla';
        this.language = config.language || 'en';
        this.initialized = false;
        this.cachedSpeakers = []; // Cache speakers list after initialization
    }

    /**
     * Initialize the model (check if Coqui TTS server is running)
     */
    async initialize() {
        if (this.initialized) {
            console.log(`✅ Coqui TTS model ${this.modelId} already initialized`);
            return;
        }

        console.log(`🎤 Initializing Coqui TTS model: ${this.modelId}`);
        console.log(`📡 Coqui TTS server URL: ${this.coquiServerUrl}`);

        // Retry logic for server availability (server might be starting up)
        const maxRetries = 10;
        const retryDelay = 3000; // 3 seconds

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`🔍 Checking Coqui TTS server availability (attempt ${attempt}/${maxRetries})...`);
                const response = await axios.get(`${this.coquiServerUrl}/`, {
                    timeout: 5000,
                    headers: { 'Connection': 'close' }
                });

                if (response.status === 200) {
                    console.log(`✅ Coqui TTS server is running at ${this.coquiServerUrl}`);

                    // Cache speakers list during initialization
                    try {
                        this.cachedSpeakers = await CoquiVoiceModel.getAvailableSpeakers(this.coquiServerUrl);
                        console.log(`✅ Cached ${this.cachedSpeakers.length} speakers from Coqui TTS server`);
                    } catch (error) {
                        console.warn(`⚠️ Failed to cache speakers, using fallback: ${error.message}`);
                        this.cachedSpeakers = CoquiVoiceModel.getFallbackSpeakers();
                    }

                    this.initialized = true;
                    return;
                }
            } catch (error) {
                console.warn(`⚠️ Attempt ${attempt}/${maxRetries} failed: ${error.message}`);

                if (attempt < maxRetries) {
                    console.log(`⏳ Waiting ${retryDelay/1000}s before retry...`);
                    await new Promise(resolve => setTimeout(resolve, retryDelay));
                } else {
                    console.error(`❌ Failed to connect to Coqui TTS server after ${maxRetries} attempts`);
                    throw new Error(`Coqui TTS server not available at ${this.coquiServerUrl}. Please ensure the Coqui TTS container is running.`);
                }
            }
        }
    }

    /**
     * Generate speech from text using Coqui TTS
     */
    async generateSpeech(text, options = {}) {
        if (!this.initialized) {
            await this.initialize();
        }

        const speaker = options.voice || options.speaker || this.defaultSpeaker;
        const language = options.language || this.language;
        const filename = options.filename || `coqui_${Date.now()}.wav`;

        // Determine output directory based on options
        let outputDir;
        if (options.product_id) {
            outputDir = path.join('/app/public/product', options.product_id);
        } else if (options.news_id) {
            outputDir = path.join('/app/public', options.news_id);
        } else {
            outputDir = '/app/public/temp';
        }

        // Ensure output directory exists
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const outputPath = path.join(outputDir, filename);

        console.log(`🎤 Generating speech with Coqui TTS XTTS v2:`);
        console.log(`   Text: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
        console.log(`   Speaker: ${speaker}`);
        console.log(`   Language: ${language}`);
        console.log(`   Output: ${outputPath}`);

        const startTime = Date.now();

        try {
            // Create form data for multipart/form-data request
            const formData = new FormData();
            formData.append('text', text);
            formData.append('speaker_id', speaker);
            formData.append('language_id', language);

            // Call Coqui TTS API
            const response = await axios.post(
                `${this.coquiServerUrl}/api/tts`,
                formData,
                {
                    headers: formData.getHeaders(),
                    responseType: 'arraybuffer',
                    timeout: 120000 // 2 minutes timeout
                }
            );

            // Save the audio file
            fs.writeFileSync(outputPath, response.data);

            const generationTime = Date.now() - startTime;
            console.log(`✅ Audio generated successfully in ${generationTime}ms`);

            // Get file stats
            const stats = fs.statSync(outputPath);
            const fileSizeKB = (stats.size / 1024).toFixed(2);

            // Calculate relative URL
            const relativeUrl = outputPath.replace('/app/public', '');

            return {
                success: true,
                audioPath: outputPath,
                audioUrl: relativeUrl,
                voice: speaker,
                language: language,
                generation_time_ms: generationTime,
                file_size_kb: fileSizeKB,
                model: this.modelId
            };

        } catch (error) {
            console.error(`❌ Coqui TTS generation failed:`, error.message);
            if (error.response) {
                console.error(`   Status: ${error.response.status}`);
                console.error(`   Data: ${error.response.data}`);
            }
            throw new Error(`Coqui TTS generation failed: ${error.message}`);
        }
    }

    /**
     * Get available speakers from Coqui TTS server
     * @param {string} serverUrl - Coqui TTS server URL (optional, uses env var if not provided)
     * @returns {Promise<Array<string>>} - List of available speaker names
     */
    static async getAvailableSpeakers(serverUrl = null) {
        const url = serverUrl || process.env.COQUI_TTS_URL || 'http://localhost:5002';

        try {
            // Try to fetch speakers from the server's web interface
            const response = await axios.get(`${url}/`);
            const html = response.data;

            // Parse HTML to extract speaker options
            const speakerMatches = html.match(/<option value="([^"]+)"/g);

            if (speakerMatches && speakerMatches.length > 0) {
                const speakers = speakerMatches
                    .map(match => match.match(/value="([^"]+)"/)[1])
                    .filter(speaker => speaker && speaker.trim() !== '');

                console.log(`✅ Loaded ${speakers.length} speakers from Coqui TTS server`);
                return speakers;
            }

            // Fallback to hardcoded list if parsing fails
            console.warn('⚠️ Could not parse speakers from server, using fallback list');
            return CoquiVoiceModel.getFallbackSpeakers();

        } catch (error) {
            console.error('❌ Failed to fetch speakers from Coqui TTS server:', error.message);
            console.warn('⚠️ Using fallback speaker list');
            return CoquiVoiceModel.getFallbackSpeakers();
        }
    }

    /**
     * Get fallback speaker list (used when server is unavailable)
     * @returns {Array<string>} - Hardcoded list of XTTS v2 speakers
     */
    static getFallbackSpeakers() {
        // XTTS v2 has 58 pre-trained speakers (fallback list)
        return [
            // Female speakers
            "Claribel Dervla", "Daisy Studious", "Gracie Wise", "Tammie Ema",
            "Alison Dietlinde", "Ana Florence", "Annmarie Nele", "Asya Anara",
            "Brenda Stern", "Gitta Nikolina", "Henriette Usha", "Sofia Hellen",
            "Tammy Grit", "Tanja Adelina", "Vjollca Johnnie",
            // Male speakers
            "Andrew Chipper", "Badr Odhiambo", "Dionisio Schuyler", "Royston Min",
            "Viktor Eka", "Abrahan Mack", "Adde Michal", "Baldur Sanjin",
            "Craig Gutsy", "Damien Black", "Gilberto Mathias", "Ilkin Urbano",
            "Kazuhiko Atallah", "Ludvig Milivoj", "Suad Qasim", "Torcull Diarmuid",
            "Viktor Menelaos", "Zacharie Aimilios",
            // Additional speakers
            "Nova Hogarth", "Maja Ruoho", "Uta Obando", "Lidiya Szekeres",
            "Chandra MacFarland", "Szofi Granger", "Camilla Holmström",
            "Lilya Stainthorpe", "Zofija Kendrick", "Narelle Moon",
            "Barbora MacLean", "Alexandra Hisakawa", "Alma María",
            "Rosemary Okafor", "Ige Behringer", "Filip Traverse",
            "Damjan Chapman", "Wulf Carlevaro", "Aaron Dreschner",
            "Kumar Dahl", "Eugenio Mataracı", "Ferran Simen",
            "Xavier Hayasaka", "Luis Moray", "Marcos Rudaski"
        ];
    }

    /**
     * Get model information
     */
    getModelInfo() {
        const languageMap = {
            'en': 'English',
            'hi': 'Hindi',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'pl': 'Polish',
            'tr': 'Turkish',
            'ru': 'Russian',
            'nl': 'Dutch',
            'cs': 'Czech',
            'ar': 'Arabic',
            'zh-cn': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'hu': 'Hungarian'
        };

        return {
            ...super.getModelInfo(),
            serverUrl: this.coquiServerUrl,
            defaultSpeaker: this.defaultSpeaker,
            language: languageMap[this.language] || this.language,
            supportedLanguages: Object.keys(languageMap),
            supportedLanguageNames: Object.values(languageMap),
            availableSpeakers: this.cachedSpeakers,
            voices: this.cachedSpeakers,
            totalSpeakers: this.cachedSpeakers.length,
            supportsEmotions: false,
            supportsMusic: false,
            supportsVoiceCloning: true,
            description: 'Coqui TTS XTTS v2 - Multi-lingual TTS with 58 universal speakers supporting 17 languages',
            speakersNote: 'All speakers are universal and can speak any of the 17 supported languages. Specify language in the request.'
        };
    }
}

