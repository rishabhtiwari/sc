import { BaseVoiceModel } from './BaseVoiceModel.js';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Kokoro-82M Voice Model implementation - Python Bridge approach
 */
export class KokoroVoiceModelPython extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        
        this.language = config.language || 'English';
        this.architecture = 'Kokoro-82M';
        
        // Kokoro-82M specific configuration
        this.voices = [
            'af_heart', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky', 
            'am_adam', 'am_michael', 
            'bf_emma', 'bf_isabella', 
            'bm_george', 'bm_lewis'
        ];
        this.defaultVoice = config.voice || 'am_adam'; // Default to male voice
        this.initialized = false;
        this.pythonBridgePath = '/app/kokoro_bridge.py';
    }

    /**
     * Initialize the Kokoro TTS model - Python Bridge approach
     */
    async initialize() {
        if (this.initialized) {
            return;
        }

        console.log(`🔄 Initializing Kokoro-82M model via Python bridge`);
        const startTime = Date.now();

        try {
            // Test Python bridge availability with a simple test
            const testText = 'Hello test';
            const testVoice = 'af_heart';
            const testSpeed = 1.0;
            const testOutput = '/tmp/kokoro_test.wav';

            const testResult = await this.runPythonBridge(testText, testVoice, testSpeed, testOutput);
            
            if (testResult.success) {
                // Clean up test file
                if (fs.existsSync(testOutput)) {
                    fs.unlinkSync(testOutput);
                }
                
                const initTime = Date.now() - startTime;
                console.log(`✅ Kokoro-82M Python bridge initialized successfully in ${initTime}ms`);
                console.log(`🎭 Available voices: ${this.voices.join(', ')}`);
                
                this.initialized = true;
            } else {
                throw new Error(`Python bridge test failed: ${testResult.error}`);
            }
        } catch (error) {
            console.error(`❌ Failed to initialize Kokoro Python bridge:`, error);
            throw error;
        }
    }

    /**
     * Run the Python bridge script
     */
    async runPythonBridge(text, voice, speed, outputPath) {
        return new Promise((resolve, reject) => {
            const args = [
                this.pythonBridgePath,
                '--text', text,
                '--voice', voice,
                '--speed', speed.toString(),
                '--output', outputPath
            ];

            console.log(`🐍 Running Python bridge: /app/venv/bin/python ${args.join(' ')}`);

            const pythonProcess = spawn('/app/venv/bin/python', args, {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let stdout = '';
            let stderr = '';

            pythonProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                stderr += data.toString();
                // Log Python stderr for debugging
                console.log(`🐍 Python: ${data.toString().trim()}`);
            });

            pythonProcess.on('close', (code) => {
                try {
                    if (code === 0) {
                        const result = JSON.parse(stdout.trim());
                        resolve(result);
                    } else {
                        resolve({
                            success: false,
                            error: `Python process exited with code ${code}: ${stderr}`
                        });
                    }
                } catch (parseError) {
                    resolve({
                        success: false,
                        error: `Failed to parse Python output: ${parseError.message}. Output: ${stdout}`
                    });
                }
            });

            pythonProcess.on('error', (error) => {
                resolve({
                    success: false,
                    error: `Failed to spawn Python process: ${error.message}`
                });
            });
        });
    }

    /**
     * Generate speech from text using Kokoro-82M via Python bridge
     */
    async generateSpeech(text, options = {}) {
        if (!this.initialized) {
            await this.initialize();
        }

        const voice = options.voice || this.defaultVoice;
        const speed = options.speed || 1.0;

        if (!this.voices.includes(voice)) {
            throw new Error(`Voice '${voice}' not supported. Available voices: ${this.voices.join(', ')}`);
        }

        console.log(`🎤 Generating speech with Kokoro-82M Python bridge`);
        console.log(`📝 Text: ${text.substring(0, 100)}${text.length > 100 ? '...' : ''}`);
        console.log(`🎭 Voice: ${voice}`);
        console.log(`⚡ Speed: ${speed}`);

        try {
            // Determine output directory and filename based on options
            let outputDir, filename, outputPath;

            if (options.news_id) {
                // For news records, use public folder structure: /app/public/{news_id}/
                outputDir = path.join('/app/public', options.news_id);
                filename = options.filename || 'content.wav'; // Default to content.wav for news
                outputPath = path.join(outputDir, filename);
            } else if (options.product_id) {
                // For product audio, use public/product/{product_id}/ directory
                outputDir = path.join('/app/public/product', options.product_id);
                filename = options.filename || 'audio.wav';
                outputPath = path.join(outputDir, filename);
            } else if (options.filename) {
                // For preview audio with custom filename, use public temp directory
                outputDir = '/app/public/temp';
                filename = options.filename;
                outputPath = path.join(outputDir, filename);
            } else {
                // For regular TTS requests, use public temp directory (shared with voice generator)
                outputDir = '/app/public/temp';
                const timestamp = Date.now();
                const randomId = Math.random().toString(36).substr(2, 9);
                filename = `kokoro_${timestamp}_${randomId}.wav`;
                outputPath = path.join(outputDir, filename);
            }

            // Create output directory
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }

            console.log(`💾 Output path: ${outputPath}`);

            // Call Python bridge with speed parameter
            const result = await this.runPythonBridge(text, voice, speed, outputPath);

            if (result.success) {
                // Verify that the audio file was actually created
                if (!fs.existsSync(outputPath)) {
                    throw new Error(`Audio file was not created at expected path: ${outputPath}`);
                }

                // Get file stats for additional verification
                const fileStats = fs.statSync(outputPath);
                if (fileStats.size === 0) {
                    throw new Error(`Generated audio file is empty: ${outputPath}`);
                }

                console.log(`✅ Speech generated successfully`);
                console.log(`📁 File created: ${outputPath} (${fileStats.size} bytes)`);
                console.log(`⏱️ Duration: ${result.duration?.toFixed(2)}s`);
                console.log(`🔊 Sample rate: ${result.sample_rate}Hz`);

                return {
                    audioPath: outputPath,
                    duration: result.duration,
                    sampleRate: result.sample_rate,
                    voice: voice
                };
            } else {
                throw new Error(`Python bridge failed: ${result.error}`);
            }

        } catch (error) {
            console.error(`❌ Kokoro speech generation failed:`, error);
            throw new Error(`Speech generation failed: ${error.message}`);
        }
    }

    /**
     * Get available voices
     */
    getVoices() {
        return this.voices.map(voice => ({
            id: voice,
            name: voice.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
            language: voice.startsWith('bf_') || voice.startsWith('bm_') ? 'en-GB' : 'en-US',
            gender: voice.startsWith('af_') || voice.startsWith('bf_') ? 'female' : 'male'
        }));
    }

    /**
     * Check if model supports a specific language
     */
    supportsLanguage(language) {
        return language.toLowerCase() === 'english' || 
               language.toLowerCase() === 'en' ||
               language.toLowerCase() === 'en-us' ||
               language.toLowerCase() === 'en-gb';
    }
}
