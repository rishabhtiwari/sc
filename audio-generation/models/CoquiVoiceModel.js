import { BaseVoiceModel } from './BaseVoiceModel.js';
import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import axios from 'axios';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
        this.speakersMetadata = null; // Speaker metadata (gender, description, etc.)

        // Text chunker version: 'v1' (spaCy) or 'v2' (semantic_text_splitter)
        // v2 is recommended for better performance and no duplication issues
        this.chunkerVersion = config.chunkerVersion || process.env.TEXT_CHUNKER_VERSION || 'v2';

        // TTS Generation Parameters (to reduce hallucinations and improve quality)
        // Based on research: https://github.com/coqui-ai/TTS/issues/3277
        // Lower temperature = more consistent, less creative (reduces weird sounds)
        // Recommended: 0.6-0.7 for minimal hallucinations
        this.temperature = parseFloat(config.temperature || process.env.COQUI_TEMPERATURE || '0.6');

        // Length penalty: controls output length (1.0 = neutral, >1.0 = longer, <1.0 = shorter)
        this.lengthPenalty = parseFloat(config.lengthPenalty || process.env.COQUI_LENGTH_PENALTY || '1.0');

        // Repetition penalty: prevents repetition (higher = less repetition, reduces artifacts)
        this.repetitionPenalty = parseFloat(config.repetitionPenalty || process.env.COQUI_REPETITION_PENALTY || '2.0');

        // Top-k sampling: limits to top k most probable tokens
        this.topK = parseInt(config.topK || process.env.COQUI_TOP_K || '50');

        // Top-p (nucleus) sampling: limits to tokens with cumulative probability <= top_p
        this.topP = parseFloat(config.topP || process.env.COQUI_TOP_P || '0.85');

        this._loadSpeakersMetadata();
    }

    /**
     * Load speakers metadata (gender inference + sample texts)
     * @private
     */
    _loadSpeakersMetadata() {
        // Try to load from JSON file first (if exists)
        try {
            const metadataPath = path.join(__dirname, '../data/coqui_speakers_metadata.json');
            if (fs.existsSync(metadataPath)) {
                const metadataContent = fs.readFileSync(metadataPath, 'utf8');
                this.speakersMetadata = JSON.parse(metadataContent);
                console.log(`✅ Loaded metadata for ${Object.keys(this.speakersMetadata.speakers).length} speakers from file`);
                return;
            }
        } catch (error) {
            console.warn(`⚠️ Could not load metadata file: ${error.message}`);
        }

        // Fallback: Use built-in gender inference and sample texts
        console.log(`📝 Using built-in speaker metadata with gender inference`);
        this.speakersMetadata = {
            speakers: this._getBuiltInSpeakerMetadata(),
            sample_texts: this._getBuiltInSampleTexts()
        };
    }

    /**
     * Get built-in speaker metadata with gender inference
     * @private
     */
    _getBuiltInSpeakerMetadata() {
        // Common female first names for gender inference
        const femaleNames = [
            'Claribel', 'Daisy', 'Gracie', 'Tammie', 'Alison', 'Ana', 'Annmarie',
            'Asya', 'Brenda', 'Gitta', 'Henriette', 'Sofia', 'Tammy', 'Tanja',
            'Vjollca', 'Nova', 'Maja', 'Uta', 'Lidiya', 'Chandra', 'Szofi',
            'Camilla', 'Lilya', 'Zofija', 'Narelle', 'Barbora', 'Alexandra',
            'Alma', 'Rosemary', 'Ige'
        ];

        // Common male first names for gender inference
        const maleNames = [
            'Andrew', 'Badr', 'Dionisio', 'Royston', 'Viktor', 'Abrahan', 'Adde',
            'Baldur', 'Craig', 'Damien', 'Gilberto', 'Ilkin', 'Kazuhiko', 'Ludvig',
            'Suad', 'Torcull', 'Zacharie', 'Filip', 'Damjan', 'Wulf', 'Aaron',
            'Kumar', 'Eugenio', 'Ferran', 'Xavier', 'Luis', 'Marcos'
        ];

        const metadata = {};
        const allSpeakers = CoquiVoiceModel.getFallbackSpeakers();

        for (const speaker of allSpeakers) {
            const firstName = speaker.split(' ')[0];
            let gender = 'unknown';

            if (femaleNames.includes(firstName)) {
                gender = 'female';
            } else if (maleNames.includes(firstName)) {
                gender = 'male';
            }

            metadata[speaker] = {
                gender: gender,
                accent: 'neutral',
                description: `${gender === 'female' ? 'Professional female' : gender === 'male' ? 'Professional male' : 'Professional'} voice`
            };
        }

        return metadata;
    }

    /**
     * Get built-in sample texts for different languages
     * @private
     */
    _getBuiltInSampleTexts() {
        return {
            en: "Welcome to our professional text-to-speech service. This advanced voice generation system uses state-of-the-art artificial intelligence to create natural-sounding speech in multiple languages. Whether you're creating content for videos, presentations, audiobooks, or accessibility features, our technology delivers high-quality results.",
            hi: "हमारी पेशेवर टेक्स्ट-टू-स्पीच सेवा में आपका स्वागत है। यह उन्नत आवाज़ निर्माण प्रणाली कई भाषाओं में प्राकृतिक-ध्वनि वाली वाणी बनाने के लिए अत्याधुनिक कृत्रिम बुद्धिमत्ता का उपयोग करती है। चाहे आप वीडियो, प्रस्तुतियों, ऑडियोबुक या पहुंच सुविधाओं के लिए सामग्री बना रहे हों, हमारी तकनीक उच्च गुणवत्ता वाले परिणाम प्रदान करती है।",
            es: "Bienvenido a nuestro servicio profesional de texto a voz. Este avanzado sistema de generación de voz utiliza inteligencia artificial de última generación para crear un habla de sonido natural en múltiples idiomas.",
            fr: "Bienvenue dans notre service professionnel de synthèse vocale. Ce système avancé de génération vocale utilise une intelligence artificielle de pointe pour créer une parole naturelle dans plusieurs langues.",
            de: "Willkommen bei unserem professionellen Text-zu-Sprache-Service. Dieses fortschrittliche Sprachgenerierungssystem verwendet modernste künstliche Intelligenz, um natürlich klingende Sprache in mehreren Sprachen zu erstellen.",
            it: "Benvenuto nel nostro servizio professionale di sintesi vocale. Questo avanzato sistema di generazione vocale utilizza intelligenza artificiale all'avanguardia per creare un parlato dal suono naturale in più lingue.",
            pt: "Bem-vindo ao nosso serviço profissional de texto para fala. Este sistema avançado de geração de voz usa inteligência artificial de ponta para criar fala com som natural em vários idiomas."
        };
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
        const speed = options.speed || 1.0;

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
        console.log(`   Speed: ${speed}x`);
        console.log(`   Output: ${outputPath}`);

        const startTime = Date.now();

        try {
            // Character limit per chunk (150 chars with smart merging for chunks < 100 chars)
            // Small chunks will be merged with previous chunks up to 250 chars max
            // XTTS optimal chunk size: 150-230 characters
            // Using 230 as max to allow chunker to create chunks in the 150-230 range
            const CHAR_LIMIT = 230;

            let audioData;

            // Check if text needs chunking
            if (text.length > CHAR_LIMIT) {
                console.log(`📝 Text length: ${text.length} chars (exceeds ${CHAR_LIMIT} limit)`);
                console.log(`🔪 Chunking text using ${this.chunkerVersion} chunker...`);

                // Get chunks using Python text chunker (v1=spaCy, v2=semantic_text_splitter)
                const chunks = await this._chunkText(text, CHAR_LIMIT, language);
                console.log(`📦 Split into ${chunks.length} chunks`);

                // Generate audio for all chunks IN PARALLEL for faster processing
                // Use concurrency limit to avoid overwhelming the TTS server
                const MAX_CONCURRENT_REQUESTS = 10; // Process up to 10 chunks simultaneously
                console.log(`🚀 Generating audio for ${chunks.length} chunks in parallel (max ${MAX_CONCURRENT_REQUESTS} concurrent)...`);
                const parallelStartTime = Date.now();

                const audioBuffers = await this._generateChunksWithConcurrency(
                    chunks,
                    speaker,
                    language,
                    MAX_CONCURRENT_REQUESTS
                );

                const parallelTime = Date.now() - parallelStartTime;
                console.log(`✅ Parallel generation completed in ${parallelTime}ms`);
                console.log(`   Average: ${Math.round(parallelTime / chunks.length)}ms per chunk`);

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

            // Apply speed adjustment if needed (using ffmpeg post-processing)
            if (speed !== 1.0) {
                console.log(`🎛️ Applying speed adjustment: ${speed}x`);
                audioData = await this._applySpeedAdjustment(audioData, speed);
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
     * Get speakers with metadata (gender, description, etc.)
     * @returns {Array} Array of speaker objects with metadata
     */
    getSpeakersWithMetadata() {
        return this.cachedSpeakers.map(speakerName => {
            const metadata = this.speakersMetadata?.speakers?.[speakerName] || {};
            return {
                id: speakerName,
                name: speakerName,
                gender: metadata.gender || 'unknown',
                accent: metadata.accent || 'neutral',
                description: metadata.description || `${speakerName} voice`
            };
        });
    }

    /**
     * Get sample text for a language
     * @param {string} language - Language code
     * @returns {string} Sample text
     */
    getSampleText(language = 'en') {
        return this.speakersMetadata?.sample_texts?.[language] ||
               this.speakersMetadata?.sample_texts?.['en'] ||
               'Hello! This is a sample text for voice preview.';
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
            voicesWithMetadata: this.getSpeakersWithMetadata(),
            totalSpeakers: this.cachedSpeakers.length,
            supportsEmotions: false,
            supportsMusic: false,
            supportsVoiceCloning: true,
            description: 'Coqui TTS XTTS v2 - Multi-lingual TTS with 58 universal speakers supporting 17 languages',
            speakersNote: 'All speakers are universal and can speak any of the 17 supported languages. Specify language in the request.',
            sampleTexts: this.speakersMetadata?.sample_texts || {},
            // Generation parameters (for reducing hallucinations)
            generationParams: {
                temperature: this.temperature,
                lengthPenalty: this.lengthPenalty,
                repetitionPenalty: this.repetitionPenalty,
                topK: this.topK,
                topP: this.topP
            }
        };
    }

    /**
     * Chunk text using Python text chunker
     * Supports v1 (spaCy) and v2 (semantic_text_splitter)
     * @private
     */
    async _chunkText(text, maxChars, language) {
        const { spawn } = await import('child_process');

        // Choose chunker script based on version
        const chunkerScript = this.chunkerVersion === 'v1'
            ? '/app/utils/text_chunker.py'
            : '/app/utils/text_chunker_v2.py';

        console.log(`📝 Calling ${this.chunkerVersion} text chunker with language: ${language}, max_chars: ${maxChars}`);

        return new Promise((resolve, reject) => {
            const pythonProcess = spawn('/app/venv/bin/python', [
                chunkerScript,
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
                console.log(`   [${this.chunkerVersion}_chunker] ${stderrText.trim()}`);
            });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    console.error(`❌ Text chunker ${this.chunkerVersion} failed with code ${code}`);
                    console.error(`   Error: ${stderr}`);
                    reject(new Error(`Text chunker ${this.chunkerVersion} failed: ${stderr}`));
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    if (result.success) {
                        console.log(`✅ Text chunker ${this.chunkerVersion} returned ${result.chunk_count} chunks`);
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
     * Generate audio for multiple chunks with concurrency control
     * @private
     */
    async _generateChunksWithConcurrency(chunks, speaker, language, maxConcurrent = 5) {
        const results = new Array(chunks.length);
        let currentIndex = 0;
        let completedCount = 0;

        // Process chunks in batches with concurrency limit
        const processNext = async (workerIndex) => {
            while (currentIndex < chunks.length) {
                const chunkIndex = currentIndex++;
                const chunk = chunks[chunkIndex];

                console.log(`🔊 [Worker ${workerIndex}] Processing chunk ${chunkIndex + 1}/${chunks.length} (${chunk.length} chars)`);

                try {
                    const audio = await this._generateSingleChunk(chunk, speaker, language);
                    results[chunkIndex] = audio;
                    completedCount++;
                    console.log(`✅ [Worker ${workerIndex}] Completed chunk ${chunkIndex + 1}/${chunks.length} (${completedCount}/${chunks.length} total)`);
                } catch (error) {
                    console.error(`❌ [Worker ${workerIndex}] Failed chunk ${chunkIndex + 1}:`, error.message);
                    throw error;
                }
            }
        };

        // Create worker pool
        const workers = Array.from({ length: Math.min(maxConcurrent, chunks.length) }, (_, i) =>
            processNext(i + 1)
        );

        // Wait for all workers to complete
        await Promise.all(workers);

        return results;
    }

    /**
     * Generate audio for a single chunk
     * @private
     * Note: Speed parameter is NOT sent to Coqui TTS server (not supported by the API)
     * Speed adjustment is applied as post-processing using ffmpeg at the final audio level
     */
    async _generateSingleChunk(text, speaker, language) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('speaker_id', speaker);
        formData.append('language_id', language);

        // Add generation parameters to reduce hallucinations
        // These parameters are supported by xtts-api-server
        formData.append('temperature', this.temperature.toString());
        formData.append('length_penalty', this.lengthPenalty.toString());
        formData.append('repetition_penalty', this.repetitionPenalty.toString());
        formData.append('top_k', this.topK.toString());
        formData.append('top_p', this.topP.toString());

        const response = await axios.post(
            `${this.coquiServerUrl}/api/tts`,
            formData,
            {
                headers: formData.getHeaders(),
                responseType: 'arraybuffer',
                timeout: 300000 // 5 minutes timeout
            }
        );

        return response.data;
    }

    /**
     * Apply speed adjustment to audio using ffmpeg
     * @private
     * @param {Buffer} audioBuffer - Input audio buffer (WAV format)
     * @param {number} speed - Speed factor (0.5 = half speed, 2.0 = double speed)
     * @returns {Promise<Buffer>} - Speed-adjusted audio buffer
     */
    async _applySpeedAdjustment(audioBuffer, speed) {
        const { spawn } = await import('child_process');
        const fs = await import('fs');
        const path = await import('path');
        const os = await import('os');

        return new Promise((resolve, reject) => {
            // Create temporary files
            const tempDir = os.tmpdir();
            const inputFile = path.join(tempDir, `input_${Date.now()}.wav`);
            const outputFile = path.join(tempDir, `output_${Date.now()}.wav`);

            try {
                // Write input buffer to temp file
                fs.writeFileSync(inputFile, audioBuffer);

                // ffmpeg atempo filter has a range of 0.5 to 2.0
                // For speeds outside this range, we need to chain multiple atempo filters
                let atempoFilters = [];
                let remainingSpeed = speed;

                // Build atempo filter chain
                while (remainingSpeed > 2.0) {
                    atempoFilters.push('atempo=2.0');
                    remainingSpeed /= 2.0;
                }
                while (remainingSpeed < 0.5) {
                    atempoFilters.push('atempo=0.5');
                    remainingSpeed /= 0.5;
                }
                if (remainingSpeed !== 1.0) {
                    atempoFilters.push(`atempo=${remainingSpeed.toFixed(2)}`);
                }

                const filterComplex = atempoFilters.join(',');

                console.log(`   🎛️ Applying speed adjustment: ${speed}x (filter: ${filterComplex})`);

                // Run ffmpeg
                const ffmpeg = spawn('ffmpeg', [
                    '-i', inputFile,
                    '-filter:a', filterComplex,
                    '-y', // Overwrite output file
                    outputFile
                ]);

                let stderr = '';

                ffmpeg.stderr.on('data', (data) => {
                    stderr += data.toString();
                });

                ffmpeg.on('close', (code) => {
                    // Clean up input file
                    try {
                        fs.unlinkSync(inputFile);
                    } catch (e) {
                        console.warn(`Failed to delete temp input file: ${e.message}`);
                    }

                    if (code !== 0) {
                        console.error(`❌ ffmpeg failed with code ${code}`);
                        console.error(`   Error: ${stderr}`);
                        reject(new Error(`ffmpeg speed adjustment failed: ${stderr}`));
                        return;
                    }

                    try {
                        // Read output file
                        const outputBuffer = fs.readFileSync(outputFile);

                        // Clean up output file
                        fs.unlinkSync(outputFile);

                        console.log(`   ✅ Speed adjustment applied successfully`);
                        resolve(outputBuffer);
                    } catch (e) {
                        reject(new Error(`Failed to read speed-adjusted audio: ${e.message}`));
                    }
                });

                ffmpeg.on('error', (error) => {
                    // Clean up temp files
                    try {
                        fs.unlinkSync(inputFile);
                    } catch (e) {}
                    try {
                        fs.unlinkSync(outputFile);
                    } catch (e) {}

                    reject(new Error(`ffmpeg process error: ${error.message}`));
                });

            } catch (error) {
                // Clean up temp files on error
                try {
                    fs.unlinkSync(inputFile);
                } catch (e) {}
                try {
                    fs.unlinkSync(outputFile);
                } catch (e) {}

                reject(error);
            }
        });
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
            denoise = false,      // Optional noise reduction (requires noisereduce library)
            speed = 1.0           // Speed adjustment (0.5 = half speed, 2.0 = double speed)
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
                denoise.toString(),
                speed.toString()
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

