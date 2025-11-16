import { BaseVoiceModel } from './BaseVoiceModel.js';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Kokoro-82M Voice Model implementation - Simple approach following docs
 */
export class KokoroVoiceModel extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        this.language = config.language || 'English';
        this.architecture = 'Kokoro-82M';
        this.tts = null;
        this.voices = [
            'af_bella', 'af_nicole', 'af_sarah', 'af_sky',
            'am_adam', 'am_michael', 'bf_emma', 'bf_isabella',
            'bm_george', 'bm_lewis'
        ];
        this.defaultVoice = config.voice || 'af_sky';
        this.dtype = config.dtype || 'q8'; // Options: fp32, fp16, q8, q4, q4f16
        this.initialized = false;
    }

    /**
     * Initialize the Kokoro TTS model - Simple approach
     */
    async initialize() {
        if (this.initialized) {
            return;
        }

        console.log(`🔄 Initializing Kokoro-82M model: ${this.modelId}`);
        const startTime = Date.now();

        try {
            // Ensure cache directory exists
            const cacheDir = "/app/data/models";
            if (!fs.existsSync(cacheDir)) {
                fs.mkdirSync(cacheDir, { recursive: true });
                console.log(`📁 Created cache directory: ${cacheDir}`);
            }

            // Simple initialization exactly like the docs with proper cache directory
            this.tts = await KokoroTTS.from_pretrained(this.modelId, {
                dtype: this.dtype,
                device: "cpu",
                cache_dir: cacheDir  // Provide explicit cache directory
            });

            const endTime = Date.now();
            const initTime = endTime - startTime;

            console.log(`✅ Kokoro-82M model initialized successfully in ${initTime}ms`);
            console.log(`🎭 Available voices: ${this.voices.join(', ')}`);

            this.initialized = true;
        } catch (error) {
            console.error(`❌ Failed to initialize Kokoro model ${this.modelId}:`, error);
            throw error;
        }
    }

    /**
     * Generate speech from text using Kokoro-82M - Simple approach
     */
    async generateSpeech(text, options = {}) {
        if (!this.initialized) {
            await this.initialize();
        }

        const voice = options.voice || this.defaultVoice;

        if (!this.voices.includes(voice)) {
            throw new Error(`Voice '${voice}' not supported. Available voices: ${this.voices.join(', ')}`);
        }

        console.log(`🎭 Using voice: ${voice}`);

        try {
            console.log(`🔍 DEBUG: Starting TTS generation with text length: ${text.length}, voice: ${voice}`);
            console.log(`🔍 DEBUG: TTS object exists: ${!!this.tts}`);
            console.log(`🔍 DEBUG: TTS generate function exists: ${typeof this.tts.generate}`);

            // Create output directory and file path first
            const outputDir = '/app/data/temp';
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
                console.log(`📁 Created output directory: ${outputDir}`);
            }

            const tempFileName = `kokoro_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.wav`;
            const tempFilePath = path.join(outputDir, tempFileName);
            console.log(`🔍 DEBUG: Created temp file path: ${tempFilePath}`);

            // Simple generation exactly like the docs
            console.log(`🔍 DEBUG: Calling tts.generate() with parameters:`, { text: text.substring(0, 50) + '...', voice });
            const audio = await this.tts.generate(text, {
                voice: voice
            });
            console.log(`🔍 DEBUG: TTS generation completed. Audio object:`, typeof audio, audio ? Object.keys(audio) : 'null');
            console.log(`🔍 DEBUG: Audio save method exists: ${typeof audio?.save}`);

            // Save the audio - simple way like in docs
            console.log(`🔍 DEBUG: Calling audio.save() with path: ${tempFilePath}`);
            await audio.save(tempFilePath);
            console.log(`🔍 DEBUG: Audio save completed`);

            // Check if file exists
            const fileExists = fs.existsSync(tempFilePath);
            console.log(`🔍 DEBUG: Temp file exists after save: ${fileExists}`);

            if (fileExists) {
                const fileStats = fs.statSync(tempFilePath);
                console.log(`🔍 DEBUG: File size: ${fileStats.size} bytes`);
            }

            // Read the file as buffer
            console.log(`🔍 DEBUG: Reading file as buffer`);
            const audioBuffer = fs.readFileSync(tempFilePath);
            console.log(`🔍 DEBUG: Buffer read completed. Buffer length: ${audioBuffer.length}`);

            // Clean up temporary file
            console.log(`🔍 DEBUG: Cleaning up temp file`);
            fs.unlinkSync(tempFilePath);
            console.log(`🔍 DEBUG: Cleanup completed`);

            console.log(`🔍 DEBUG: Returning audio buffer of length: ${audioBuffer.length}`);
            return audioBuffer;

        } catch (error) {
            console.error(`❌ Kokoro speech generation failed:`, error);
            throw new Error(`Speech generation failed: ${error.message}`);
        }
    }

    getVoices() {
        return this.voices;
    }

    isSupported(language) {
        return language.toLowerCase() === 'english' || language.toLowerCase() === 'en';
    }

    getModelInfo() {
        return {
            modelId: this.modelId,
            architecture: this.architecture,
            language: this.language,
            voices: this.voices,
            defaultVoice: this.defaultVoice,
            dtype: this.dtype
        };
    }
}
