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
            // Character limit per chunk (conservative to avoid truncation)
            // Using 175 to ensure we stay well below the 250 char warning threshold
            const CHAR_LIMIT = 175;

            // Check if text needs to be chunked
            if (text.length > CHAR_LIMIT) {
                console.log(`📝 Text length: ${text.length} chars (exceeds ${CHAR_LIMIT} limit)`);
                console.log(`📝 Splitting into chunks using spaCy for language: ${language}...`);
                const chunks = await this._splitTextIntoChunks(text, CHAR_LIMIT, language);
                console.log(`📦 Successfully split into ${chunks.length} chunks\n`);

                // Generate audio for each chunk
                const audioBuffers = [];
                for (let i = 0; i < chunks.length; i++) {
                    console.log(`\n${'='.repeat(80)}`);
                    console.log(`🔊 Processing chunk ${i + 1}/${chunks.length}`);
                    console.log(`📏 Chunk length: ${chunks[i].length} characters`);
                    console.log(`📄 Chunk text: "${chunks[i]}"`);
                    console.log(`${'='.repeat(80)}\n`);

                    const chunkStartTime = Date.now();
                    const chunkBuffer = await this._generateChunk(chunks[i], speaker, language);
                    const chunkTime = Date.now() - chunkStartTime;

                    audioBuffers.push(chunkBuffer);
                    console.log(`✅ Chunk ${i + 1} generated in ${chunkTime}ms\n`);
                }

                // Merge audio buffers
                console.log(`\n🔗 Merging ${audioBuffers.length} audio chunks into single file...`);
                const mergedBuffer = await this._mergeAudioBuffers(audioBuffers);

                // Save the merged audio file
                fs.writeFileSync(outputPath, mergedBuffer);
                console.log(`💾 Merged audio saved to: ${outputPath}`);
            } else {
                // Text is short enough, generate directly
                console.log(`📝 Text length: ${text.length} chars (within ${CHAR_LIMIT} limit, no chunking needed)`);
                const audioBuffer = await this._generateChunk(text, speaker, language);
                fs.writeFileSync(outputPath, audioBuffer);
            }

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
     * Split text into chunks at sentence boundaries using spaCy
     * @private
     */
    async _splitTextIntoChunks(text, maxChars, language) {
        try {
            const { spawn } = await import('child_process');
            const { promisify } = await import('util');

            return new Promise((resolve, reject) => {
                // Call Python text splitter script
                const pythonProcess = spawn('/app/venv/bin/python', [
                    '/app/utils/text_splitter.py',
                    maxChars.toString(),
                    language
                ]);

                let stdout = '';
                let stderr = '';

                pythonProcess.stdout.on('data', (data) => {
                    stdout += data.toString();
                });

                pythonProcess.stderr.on('data', (data) => {
                    stderr += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    if (code !== 0) {
                        console.warn(`⚠️ spaCy text splitter failed, falling back to regex: ${stderr}`);
                        // Fallback to simple regex-based splitting
                        resolve(this._fallbackSplitText(text, maxChars));
                        return;
                    }

                    try {
                        const result = JSON.parse(stdout);
                        if (result.success) {
                            console.log(`✅ spaCy split text into ${result.chunk_count} chunks`);
                            resolve(result.chunks);
                        } else {
                            console.warn(`⚠️ spaCy error: ${result.error}, falling back to regex`);
                            resolve(this._fallbackSplitText(text, maxChars));
                        }
                    } catch (e) {
                        console.warn(`⚠️ Failed to parse spaCy output, falling back to regex: ${e.message}`);
                        resolve(this._fallbackSplitText(text, maxChars));
                    }
                });

                // Write text to stdin
                pythonProcess.stdin.write(text);
                pythonProcess.stdin.end();
            });
        } catch (error) {
            console.warn(`⚠️ Failed to use spaCy, falling back to regex: ${error.message}`);
            return this._fallbackSplitText(text, maxChars);
        }
    }

    /**
     * Fallback text splitting using regex (when spaCy is not available)
     * @private
     */
    _fallbackSplitText(text, maxChars) {
        console.log(`⚠️ Using fallback regex-based text splitting (max ${maxChars} chars)`);
        const chunks = [];

        // Split by sentence endings (., !, ?, ।, ।।)
        const sentences = text.match(/[^.!?।]+[.!?।]+|[^.!?।]+$/g) || [text];
        console.log(`✂️  Found ${sentences.length} sentences using regex`);

        let currentChunk = '';
        let chunkNum = 0;

        for (let i = 0; i < sentences.length; i++) {
            const trimmedSentence = sentences[i].trim();
            const sentenceLen = trimmedSentence.length;
            const potentialLen = currentChunk.length + sentenceLen + (currentChunk ? 1 : 0);

            console.log(`   Sentence ${i + 1}/${sentences.length}: ${sentenceLen} chars`);

            // If adding this sentence would exceed limit, save current chunk and start new one
            if (currentChunk && potentialLen > maxChars) {
                chunkNum++;
                chunks.push(currentChunk.trim());
                console.log(`   ✅ Chunk ${chunkNum} complete: ${currentChunk.length} chars`);
                currentChunk = trimmedSentence;
            } else {
                currentChunk += (currentChunk ? ' ' : '') + trimmedSentence;
                console.log(`   ➕ Added to current chunk (now ${currentChunk.length} chars)`);
            }
        }

        // Add the last chunk
        if (currentChunk) {
            chunkNum++;
            chunks.push(currentChunk.trim());
            console.log(`   ✅ Chunk ${chunkNum} complete: ${currentChunk.length} chars`);
        }

        console.log(`\n📦 Total chunks created: ${chunks.length}`);
        for (let i = 0; i < chunks.length; i++) {
            console.log(`   Chunk ${i + 1}: ${chunks[i].length} chars`);
        }

        return chunks;
    }

    /**
     * Generate audio for a single chunk
     * @private
     */
    async _generateChunk(text, speaker, language) {
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
     * Merge multiple audio buffers into one
     * @private
     */
    async _mergeAudioBuffers(buffers) {
        // Simple concatenation for WAV files
        // Note: This assumes all chunks have the same format (sample rate, channels, etc.)

        if (buffers.length === 1) {
            return buffers[0];
        }

        // For WAV files, we need to:
        // 1. Extract the header from the first file
        // 2. Concatenate all audio data
        // 3. Update the file size in the header

        const firstBuffer = buffers[0];
        const header = firstBuffer.slice(0, 44); // WAV header is 44 bytes

        // Extract audio data from all buffers
        const audioDataChunks = buffers.map(buffer => buffer.slice(44));

        // Calculate total audio data size
        const totalAudioSize = audioDataChunks.reduce((sum, chunk) => sum + chunk.length, 0);

        // Create merged buffer
        const mergedBuffer = Buffer.alloc(44 + totalAudioSize);

        // Copy header
        header.copy(mergedBuffer, 0);

        // Update file size in header (bytes 4-7)
        const fileSize = 36 + totalAudioSize;
        mergedBuffer.writeUInt32LE(fileSize, 4);

        // Update data chunk size (bytes 40-43)
        mergedBuffer.writeUInt32LE(totalAudioSize, 40);

        // Copy all audio data
        let offset = 44;
        for (const audioData of audioDataChunks) {
            audioData.copy(mergedBuffer, offset);
            offset += audioData.length;
        }

        return mergedBuffer;
    }
}

