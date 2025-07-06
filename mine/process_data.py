import re
with open('data.txt', 'r') as infile:
    lines = infile.readlines()

def process_sentence(sentence):
    sentence = sentence.replace(',', ' ,')

    words = sentence.split(' ')
    firstword = words[0]
    processed_words = [word for word in words if word != firstword]

    return firstword + ' ' + ' '.join(processed_words)

with open('src.txt', 'w') as src_file, open('tgt.txt', 'w') as tgt_file:
    for line in lines:
        line = line.strip()

        if '?' in line:
            src_part, tgt_part = line.split(' ? ', 1)

            src_sentences = src_part.split('; ')
            for word in ['triangle', 'segment']:
                if word in src_sentences[0]:
                    src_sentences[0] = src_sentences[0].split(word)[0] + word
                    break
            src_sentences = [process_sentence(sentence) for sentence in src_sentences]
            last_sentence = src_sentences[-1].strip() 

            src_sentences = ' ; '.join(src_sentences[:-1])
            if src_sentences:
                src_file.write(src_sentences + ' ? ' + tgt_part + '\n')

            tgt_file.write(last_sentence + '\n')

print("文件已成功拆分。")
