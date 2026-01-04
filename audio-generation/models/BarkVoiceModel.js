import { BaseVoiceModel } from './BaseVoiceModel.js';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Bark Voice Model implementation - Python Bridge approach
 * Supports voice cloning, emotions, music, and multi-language TTS
 */
export class BarkVoiceModel extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        
        this.language = config.language || 'English';
        this.architecture = 'Bark';
        
        // Bark supports multiple languages with speaker presets
        this.speakers = {
            'English': ['v2/en_speaker_0', 'v2/en_speaker_1', 'v2/en_speaker_2', 'v2/en_speaker_3', 'v2/en_speaker_4', 'v2/en_speaker_5', 'v2/en_speaker_6', 'v2/en_speaker_7', 'v2/en_speaker_8', 'v2/en_speaker_9'],
            'German': ['v2/de_speaker_0', 'v2/de_speaker_1', 'v2/de_speaker_2', 'v2/de_speaker_3', 'v2/de_speaker_4'],
            'Spanish': ['v2/es_speaker_0', 'v2/es_speaker_1', 'v2/es_speaker_2', 'v2/es_speaker_3', 'v2/es_speaker_4'],
            'French': ['v2/fr_speaker_0', 'v2/fr_speaker_1', 'v2/fr_speaker_2', 'v2/fr_speaker_3', 'v2/fr_speaker_4'],
            'Hindi': ['v2/hi_speaker_0', 'v2/hi_speaker_1', 'v2/hi_speaker_2', 'v2/hi_speaker_3', 'v2/hi_speaker_4'],
            'Italian': ['v2/it_speaker_0', 'v2/it_speaker_1', 'v2/it_speaker_2', 'v2/it_speaker_3', 'v2/it_speaker_4'],
            'Japanese': ['v2/ja_speaker_0', 'v2/ja_speaker_1', 'v2/ja_speaker_2', 'v2/ja_speaker_3', 'v2/ja_speaker_4'],
            'Korean': ['v2/ko_speaker_0', 'v2/ko_speaker_1', 'v2/ko_speaker_2', 'v2/ko_speaker_3', 'v2/ko_speaker_4'],
            'Polish': ['v2/pl_speaker_0', 'v2/pl_speaker_1', 'v2/pl_speaker_2', 'v2/pl_speaker_3', 'v2/pl_speaker_4'],
            'Portuguese': ['v2/pt_speaker_0', 'v2/pt_speaker_1', 'v2/pt_speaker_2', 'v2/pt_speaker_3', 'v2/pt_speaker_4'],
            'Russian': ['v2/ru_speaker_0', 'v2/ru_speaker_1', 'v2/ru_speaker_2', 'v2/ru_speaker_3', 'v2/ru_speaker_4'],
            'Turkish': ['v2/tr_speaker_0', 'v2/tr_speaker_1', 'v2/tr_speaker_2', 'v2/tr_speaker_3', 'v2/tr_speaker_4'],
            'Chinese': ['v2/zh_speaker_0', 'v2/zh_speaker_1', 'v2/zh_speaker_2', 'v2/zh_speaker_3', 'v2/zh_speaker_4'],
            'Bengali': ['v2/en_speaker_0'], // Fallback to English speaker
            'Tamil': ['v2/en_speaker_0'],
            'Telugu': ['v2/en_speaker_0'],
            'Marathi': ['v2/en_speaker_0'],
            'Gujarati': ['v2/en_speaker_0'],
            'Kannada': ['v2/en_speaker_0'],
            'Malayalam': ['v2/en_speaker_0'],
            'Punjabi': ['v2/en_speaker_0']
        };
        
        this.defaultSpeaker = config.speaker || this.speakers[this.language]?.[0] || 'v2/en_speaker_0';
        this.initialized = false;
        this.pythonBridgePath = '/app/bark_bridge.py';
    }

    /**
     * Initialize the Bark model
     * Note: Bark models are loaded lazily on first use to avoid long startup times
     */
    async initialize() {
        if (this.initialized) {
            return;
        }

        console.log(`🔄 Initializing Bark model: ${this.modelId} for ${this.language}`);
        console.log(`⚠️  Note: Bark models will be downloaded and loaded on first use (may take several minutes)`);
        console.log(`⚠️  Bark requires GPU for reasonable performance. CPU inference is very slow.`);

        try {
            // Check if Python bridge exists
            if (!fs.existsSync(this.pythonBridgePath)) {
                throw new Error(`Python bridge not found at ${this.pythonBridgePath}`);
            }

            // Skip the initialization test to avoid long startup times
            // Models will be loaded lazily on first actual generation request
            console.log('✅ Bark bridge ready (models will load on first use)');
            console.log(`🎭 Available speakers for ${this.language}: ${this.speakers[this.language]?.length || 0}`);

            this.initialized = true;
        } catch (error) {
            console.error(`❌ Failed to initialize Bark model ${this.modelId}:`, error);
            throw error;
        }
    }

    /**
     * Call Python bridge to generate speech
     */
    async callPythonBridge(text, speaker, outputPath) {
        return new Promise((resolve, reject) => {
            const args = [
                this.pythonBridgePath,
                '--text', text,
                '--speaker', speaker,
                '--output', outputPath
            ];

            console.log(`🐍 Calling Python bridge: ${args.join(' ')}`);

            const pythonProcess = spawn('/app/venv/bin/python3', args, {
                env: {
                    ...process.env,
                    PYTHONWARNINGS: 'ignore'
                    // GPU/CPU settings are handled inside bark_bridge.py based on torch.cuda.is_available()
                }
            });

            let stdout = '';
            let stderr = '';

            pythonProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                stderr += data.toString();
                console.log(`🐍 Bark: ${data.toString().trim()}`);
            });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Python bridge exited with code ${code}: ${stderr}`));
                    return;
                }

                try {
                    const result = JSON.parse(stdout.trim());
                    resolve(result);
                } catch (error) {
                    reject(new Error(`Failed to parse Python output: ${stdout}`));
                }
            });

            pythonProcess.on('error', (error) => {
                reject(new Error(`Failed to spawn Python process: ${error.message}`));
            });
        });
    }

    /**
     * Generate speech from text using Bark
     */
    async generateSpeech(text, options = {}) {
        if (!this.initialized) {
            await this.initialize();
        }

        const speaker = options.voice || options.speaker || this.defaultSpeaker;
        const filename = options.filename || `bark_${Date.now()}.wav`;

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

        console.log(`🎤 Generating Bark speech for: "${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"`);
        console.log(`🎭 Speaker: ${speaker}`);
        console.log(`📁 Output: ${outputPath}`);

        const startTime = Date.now();

        try {
            const result = await this.callPythonBridge(text, speaker, outputPath);

            if (!result.success) {
                throw new Error(result.error || 'Speech generation failed');
            }

            const generationTime = Date.now() - startTime;

            console.log(`✅ Bark speech generated in ${generationTime}ms`);
            console.log(`📊 Duration: ${result.duration?.toFixed(2)}s, Sample rate: ${result.sample_rate}Hz`);

            return {
                audioPath: outputPath,
                duration: result.duration,
                sampleRate: result.sample_rate,
                generation_time_ms: generationTime,
                voice: speaker,
                text: text
            };

        } catch (error) {
            console.error(`❌ Bark speech generation failed:`, error);
            throw error;
        }
    }

    /**
     * Get model information
     */
    getModelInfo() {
        return {
            ...super.getModelInfo(),
            language: this.language,
            architecture: this.architecture,
            availableSpeakers: this.speakers[this.language] || [],
            defaultSpeaker: this.defaultSpeaker,
            supportsVoiceCloning: true,
            supportsEmotions: true,
            supportsMusic: true
        };
    }

    /**
     * Check if model is ready
     */
    isReady() {
        return this.initialized;
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        this.initialized = false;
        console.log(`🧹 Cleaned up Bark model: ${this.modelId}`);
    }
}

