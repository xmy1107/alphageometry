import subprocess
import os

def translate_sentence(model_path, sentence, gpu=0, beam_size=10, n_best=5):
    """
    用法：
    sentence = "a b c = triangle ; h = on_tline b a c , on_tline c a b ? perp a h b c"
    translated = translate_sentence("mine/run/model_step_1000.pt", sentence, gpu=0)
    print(f"Translated sentences: {translated}")
    print(f"Best translation: {translated[0]}")
    """
    with open("temp_input.txt", "w") as f:
        f.write(sentence)
    
    output_file = "temp_output.txt"
    
    cmd = [
        "onmt_translate", 
        "-model", model_path, 
        "-src", "temp_input.txt", 
        "-output", output_file, 
        "-gpu", str(gpu), 
        "-beam_size", str(beam_size),
        "-n_best", str(n_best),
        "-verbose"
    ]
    
    subprocess.run(cmd, check=True)
    
    with open(output_file, "r") as f:
        translated_sentences = [line.strip() for line in f.readlines()]
    
    subprocess.run("rm temp_input.txt temp_output.txt", shell=True)
    
    return translated_sentences

