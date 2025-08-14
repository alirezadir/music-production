# lalalai_splitter.py Usage

python3 lalalai_splitter.py --license <user license> \
                             --input <input directory or file> \
                             [--output <output directory>] \
                             [--stem <stem option>] \
                             [--filter <post-processing filter>] \
                             [--splitter <splitter type>] \
                             [--enhanced-processing <true/false>] \
                             [--noise-cancelling <level>]

Parameters:
    --license              User license key (required)
    --input                Input directory or file (required)
    --output               Output directory (default: current script directory)
    --stem                 Stem to extract (default: "vocals")
                          choices: vocals, drum, bass, piano, electric_guitar, 
                                  acoustic_guitar, synthesizer, voice, strings, wind
                          Note: Different neural networks support different sets of stems
    --filter               Post-processing filter intensity (default: 1)
                          choices: 0 (mild), 1 (normal), 2 (aggressive)
    --splitter             Neural network type (default: auto - selects most effective for stem)
                          choices: phoenix, orion, perseus
                          Auto selection priority: Perseus > Orion > Phoenix
                          - Perseus: vocals, voice, drum, piano, bass, electric_guitar, acoustic_guitar
                          - Orion: vocals, voice, drum, piano, bass, electric_guitar, acoustic_guitar  
                          - Phoenix: vocals, voice, drum, piano, bass, electric_guitar, acoustic_guitar, synthesizer, strings, wind
    --enhanced-processing  Enable enhanced processing (default: false)
                          Available for all stems except "voice"
    --noise-cancelling     Noise cancelling level for "voice" stem only (default: 1)
                          choices: 0 (mild), 1 (normal), 2 (aggressive)