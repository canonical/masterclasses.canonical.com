from unidecode import unidecode

def slugify(text):
    """
    Normalize text by removing diacritics and tokenize it into individual words, 
    subwords, and combined forms to improve partial matching.
    """
    if not text:
        return []
    
    # Normalize to remove diacritics
    normalized = unidecode(text.lower()).strip()
    
    # Tokenize by splitting on spaces and other separators
    words = normalized.replace('-', ' ').replace('_', ' ').split()
    
    # Start with the full normalized text and individual words
    tokens = [normalized] + words
    
    # Add combined versions for multi-word names
    if len(words) > 1:
        tokens.append(''.join(words))
    
    # Generate substrings for each word (minimum 3 characters)
    subwords = []
    for word in words:
        if len(word) >= 3:
            # Add the word itself and all substrings of at least 3 chars
            for i in range(len(word) - 2):
                for j in range(i + 3, len(word) + 1):
                    subwords.append(word[i:j])
    
    # Add all unique tokens
    tokens.extend(subwords)
    
    return list(set(tokens))
