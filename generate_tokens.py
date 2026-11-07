import random
import string

def generate_token():
    # format XXXX-XXXX
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{part1}-{part2}"

def main():
    tokens = set()
    target_count = 600
    
    print(f"Generating {target_count} unique tokens...")
    
    while len(tokens) < target_count:
        token = generate_token()
        # Verify no 'TXN' substring (case insensitive check just to be safe, though our alphabet is uppercase)
        if 'TXN' not in token:
            tokens.add(token)
            
    # Sort for tidiness
    sorted_tokens = sorted(list(tokens))
    
    output_file = 'public/voters_tokens.txt'
    with open(output_file, 'w') as f:
        # The existing format seems to be comma-separated based on the file view
        # "0023-7948,0033-2443,..."
        f.write(','.join(sorted_tokens))
        
    print(f"Successfully wrote {len(sorted_tokens)} tokens to {output_file}")

if __name__ == "__main__":
    main()
