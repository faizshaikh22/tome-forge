import csv

def convert_csv(input_file, output_file, with_thinking=True):
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
        
        # Write header
        writer.writerow(['question', 'answer'])
        
        for row in reader:
            question = row['question']
            
            if with_thinking:
                # Build thinking section
                thinking_parts = []
                if row['thinking_question_analysis']:
                    thinking_parts.append(f"Question Analysis: {row['thinking_question_analysis']}")
                if row['thinking_textual_grounding']:
                    thinking_parts.append(f"Textual Grounding: {row['thinking_textual_grounding']}")
                if row['thinking_reasoning_approach']:
                    thinking_parts.append(f"Reasoning: {row['thinking_reasoning_approach']}")
                
                thinking_section = "\n\n".join(thinking_parts)
                
                # Combine thinking + answer
                full_answer = f"<thinking>\n{thinking_section}\n</thinking>\n\n{row['answer']}"
            else:
                # Just the answer, no thinking
                full_answer = row['answer']
            
            writer.writerow([question, full_answer])

# Run it
convert_csv('nietzsche.csv', 'train.csv', with_thinking=False)
print("Converted to train.csv")