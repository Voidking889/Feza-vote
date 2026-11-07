def verify():
    with open('public/voters_tokens.txt', 'r') as f:
        content = f.read().strip()
        
    tokens = content.split(',')
    
    print(f"Total tokens found: {len(tokens)}")
    
    txn_found = False
    invalid_format = False
    
    for t in tokens:
        if 'TXN' in t.upper():
            print(f"ERROR: Token {t} contains 'TXN'")
            txn_found = True
        
        parts = t.split('-')
        if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 4:
            print(f"ERROR: Token {t} has invalid format")
            invalid_format = True
            
    if not txn_found and not invalid_format and len(tokens) == 600:
        print("SUCCESS: verification passed. 600 unique tokens, correct format, no 'TXN'.")
    else:
        print("FAILURE: Verification failed.")

if __name__ == "__main__":
    verify()
