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
        let language = options.language || this.language;

        // Normalize language to language code (in case full name is passed)
        const languageNameToCode = {
            'English': 'en', 'Hindi': 'hi', 'Spanish': 'es', 'French': 'fr',
            'German': 'de', 'Italian': 'it', 'Portuguese': 'pt', 'Polish': 'pl',
            'Turkish': 'tr', 'Russian': 'ru', 'Dutch': 'nl', 'Czech': 'cs',
            'Arabic': 'ar', 'Chinese': 'zh-cn', 'Japanese': 'ja', 'Korean': 'ko',
            'Hungarian': 'hu'
        };

        // Convert language name to code if needed
        if (languageNameToCode[language]) {
            console.log(`🔄 Converting language name "${language}" to code "${languageNameToCode[language]}"`);
            language = languageNameToCode[language];
        }

        // Ensure language is a valid code (not a full name)
        const validLanguageCodes = ['en', 'hi', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'ko', 'hu'];
        if (!validLanguageCodes.includes(language)) {
            console.warn(`⚠️ Invalid language "${language}", defaulting to "en"`);
            language = 'en';
        }

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
        console.log(`   Text length: ${text.length} characters`);
        console.log(`   Speaker: ${speaker}`);
        console.log(`   Language: ${language}`);
        console.log(`   Output: ${outputPath}`);

        const startTime = Date.now();

        try {
            // Character limit per chunk (150 chars with smart merging for chunks < 100 chars)
            // Small chunks will be merged with previous chunks up to 250 chars max
            const CHAR_LIMIT = 150;

            let audioData;

            // Check if text needs chunking
            if (text.length > CHAR_LIMIT) {
                console.log(`📝 Text length: ${text.length} chars (exceeds ${CHAR_LIMIT} limit)`);
                console.log(`🔪 Chunking text using spaCy...`);

                // Get chunks using Python spaCy
                const chunks = await this._chunkText(text, CHAR_LIMIT, language);
                console.log(`📦 Split into ${chunks.length} chunks`);

                // Generate audio for each chunk
                const audioBuffers = [];
                for (let i = 0; i < chunks.length; i++) {
                    console.log(`🔊 Processing chunk ${i + 1}/${chunks.length} (${chunks[i].length} chars)`);
                    const chunkAudio = await this._generateSingleChunk(chunks[i], speaker, language);
                    audioBuffers.push(chunkAudio);
                }

                // Merge audio chunks with enhanced cleaning for natural-sounding speech
                console.log(`🔗 Merging ${audioBuffers.length} audio chunks with professional cleaning...`);
                audioData = await this._mergeAudioChunks(audioBuffers, {
                    silenceMs: 200,      // Natural breathing pause
                    crossfadeMs: 50,     // Smooth transitions
                    normalize: true,     // Consistent volume
                    denoise: false       // Set to true if background noise is present
                });
            } else {
                console.log(`📝 Text length: ${text.length} chars (within limit, no chunking needed)`);
                audioData = await this._generateSingleChunk(text, speaker, language);
            }

            // Save the audio file
            fs.writeFileSync(outputPath, audioData);

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

    /**
     * Chunk text using Python spaCy
     * @private
     */
    async _chunkText(text, maxChars, language) {
        const { spawn } = await import('child_process');

        console.log(`📝 Calling text_chunker.py with language: ${language}, max_chars: ${maxChars}`);

        return new Promise((resolve, reject) => {
            const pythonProcess = spawn('/app/venv/bin/python', [
                '/app/utils/text_chunker.py',
                maxChars.toString(),
                language
            ]);

            let stdout = '';
            let stderr = '';

            pythonProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                const stderrText = data.toString();
                stderr += stderrText;
                // Print Python script logs in real-time
                console.log(`   [text_chunker] ${stderrText.trim()}`);
            });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    console.error(`❌ Text chunker failed with code ${code}`);
                    console.error(`   Error: ${stderr}`);
                    reject(new Error(`Text chunker failed: ${stderr}`));
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    if (result.success) {
                        console.log(`✅ Text chunker returned ${result.chunk_count} chunks`);
                        resolve(result.chunks);
                    } else {
                        reject(new Error(result.error));
                    }
                } catch (e) {
                    reject(new Error(`Failed to parse chunker output: ${e.message}`));
                }
            });

            // Write text to stdin
            pythonProcess.stdin.write(text);
            pythonProcess.stdin.end();
        });
    }

    /**
     * Generate audio for a single chunk
     * @private
     */
    async _generateSingleChunk(text, speaker, language) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('speaker_id', speaker);
        formData.append('language_id', language);

        const response = await axios.post(
            `${this.coquiServerUrl}/api/tts`,
            formData,
            {
                headers: formData.getHeaders(),
                responseType: 'arraybuffer',
                timeout: 120000 // 2 minutes timeout
            }
        );

        return response.data;
    }

    /**
     * Merge audio chunks using Python pydub with advanced cleaning
     * @private
     * @param {Array} audioBuffers - Array of audio buffers to merge
     * @param {Object} options - Merge options
     * @param {number} options.silenceMs - Silence between chunks (default: 200ms for natural breathing)
     * @param {number} options.crossfadeMs - Crossfade duration (default: 50ms for smooth transitions)
     * @param {boolean} options.normalize - Enable volume normalization (default: true)
     * @param {boolean} options.denoise - Enable noise reduction (default: false)
     */
    async _mergeAudioChunks(audioBuffers, options = {}) {
        const { spawn } = await import('child_process');

        // Default options for clean, natural-sounding audio
        const {
            silenceMs = 200,      // Natural breathing pause between sentences
            crossfadeMs = 50,     // Smooth transitions to prevent clicks
            normalize = true,     // Consistent volume across chunks
            denoise = false       // Optional noise reduction (requires noisereduce library)
        } = options;

        return new Promise(async (resolve, reject) => {
            // Save chunks to temporary files
            const tempDir = '/app/public/temp';
            const tempFiles = [];

            for (let i = 0; i < audioBuffers.length; i++) {
                const tempFile = path.join(tempDir, `chunk_${Date.now()}_${i}.wav`);
                fs.writeFileSync(tempFile, audioBuffers[i]);
                tempFiles.push(tempFile);
            }

            // Use the new audio_cleaner.py with enhanced cleaning capabilities
            const pythonProcess = spawn('/app/venv/bin/python', [
                '/app/utils/audio_cleaner.py',
                silenceMs.toString(),
                crossfadeMs.toString(),
                normalize.toString(),
                denoise.toString()
            ]);

            let stdout = Buffer.alloc(0);
            let stderr = '';

            pythonProcess.stdout.on('data', (data) => {
                stdout = Buffer.concat([stdout, data]);
            });

            pythonProcess.stderr.on('data', (data) => {
                stderr += data.toString();
                // Log cleaning progress
                console.log(`🎵 Audio Cleaner: ${data.toString().trim()}`);
            });

            pythonProcess.on('close', (code) => {
                // Clean up temp files
                tempFiles.forEach(file => {
                    try { fs.unlinkSync(file); } catch (e) {}
                });

                if (code !== 0) {
                    reject(new Error(`Audio cleaner failed: ${stderr}`));
                    return;
                }

                resolve(stdout);
            });

            // Write file paths to stdin as JSON
            pythonProcess.stdin.write(JSON.stringify(tempFiles));
            pythonProcess.stdin.end();
        });
    }
}

