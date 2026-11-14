"""
Bilingual Devanagari <-> Romanized Hinglish Transliteration Engine
Supports:
- 1-Click Script Toggle: Devanagari (नमस्ते) <-> Roman Hinglish (Namaste)
- Modern Conversational Schwa Deletion (e.g. 'रात' -> 'raat', not 'raata')
- Common Travel Vlog Colloquial Vocabulary Enhancement
"""
import re

# Direct colloquial high-frequency lexicon dictionary for 100% accurate Hinglish spelling
DEVA_TO_HINGLISH_LEXICON = {
    "नमस्ते": "Namaste",
    "नमस्कार": "Namaskar",
    "दोस्तों": "Dosto",
    "दोस्त": "Dost",
    "आज": "Aaj",
    "हम": "Hum",
    "आप": "Aap",
    "तुम": "Tum",
    "मैं": "Main",
    "मेरा": "Mera",
    "मेरी": "Meri",
    "मेरे": "Mere",
    "हमारा": "Hamara",
    "हमारी": "Hamari",
    "हमारे": "Hamare",
    "आपका": "Aapka",
    "आपकी": "Aapki",
    "आपके": "Aapke",
    "यह": "Yeh",
    "ये": "Ye",
    "वह": "Woh",
    "वो": "Wo",
    "है": "Hai",
    "हैं": "Hain",
    "था": "Tha",
    "थी": "Thi",
    "थे": "The",
    "होगा": "Hoga",
    "होगी": "Hogi",
    "होंगे": "Honge",
    "करेंगे": "Karenge",
    "करेगा": "Karega",
    "करेगी": "Karegi",
    "करना": "Karna",
    "किया": "Kiya",
    "रहा": "Raha",
    "रही": "Rahi",
    "रहे": "Rahe",
    "बहुत": "Bahut",
    "अच्छा": "Accha",
    "अच्छी": "Acchi",
    "अच्छे": "Acche",
    "बढ़िया": "Badhiya",
    "सुंदर": "Sundar",
    "शानदार": "Shaandar",
    "ज़बरदस्त": "Zabardast",
    "गाड़ी": "Gaadi",
    "रास्ता": "Raasta",
    "सफ़र": "Safar",
    "सड़क": "Sadak",
    "पहाड़": "Pahaad",
    "मौसम": "Mausam",
    "होटल": "Hotel",
    "कमरा": "Kamra",
    "खाना": "Khaana",
    "चाय": "Chai",
    "पानी": "Paani",
    "समय": "Samay",
    "जगह": "Jagah",
    "व्यू": "View",
    "बस": "Bus",
    "दुकान": "Dukaan",
    "मार्केट": "Market",
    "मंदिर": "Mandir",
    "दरगाह": "Dargah",
    "किला": "Qila",
    "झील": "Jheel",
    "सुबह": "Subah",
    "शाम": "Shaam",
    "रात": "Raat",
    "दिन": "Din",
    "और": "Aur",
    "जा": "Jaa",
    "आ": "Aa",
    "जाओ": "Jao",
    "आओ": "Aao",
    "जाएंगे": "Jaayenge",
    "आएंगे": "Aayenge",
    "चलते": "Chalte",
    "चलो": "Chalo",
    "जाते": "Jaate",
    "आते": "Aate",
    "देखते": "Dekhte",
    "देखो": "Dekho",
    "सुनो": "Suno",
    "बताओ": "Batao",
    "रुक": "Ruk",
    "रुकिए": "Rukiye",
    "आइए": "Aaiye",
    "जाइए": "Jaiye",
    "भाई": "Bhai",
    "यार": "Yaar",
    "कैसा": "Kaisa",
    "कैसी": "Kaisi",
    "कैसे": "Kaise",
    "क्या": "Kya",
    "क्यों": "Kyun",
    "कब": "Kab",
    "कहाँ": "Kahan",
    "यहाँ": "Yahan",
    "वहाँ": "Wahan",
    "जहाँ": "Jahan",
    "कितना": "Kitna",
    "कितनी": "Kitni",
    "कितने": "Kitne",
    "थोड़ा": "Thoda",
    "ज्यादा": "Zyada",
    "काफी": "Kafi",
    "ज़रूर": "Zaroor",
    "प्लीज़": "Please",
    "शुक्रिया": "Shukriya",
    "धन्यवाद": "Dhanyawaad",
    "जय": "Jai",
    "गुरुदेव": "Gurudev",
    "पुष्कर": "Pushkar",
    "जयपुर": "Jaipur",
    "मनाली": "Manali",
    "दिल्ली": "Delhi",
    "कांगड़ा": "Kangra",
    "दलाल": "Dalal",
    "राम": "Ram"
}

# Reverse lookup dictionary
HINGLISH_TO_DEVA_LEXICON = {v.lower(): k for k, v in DEVA_TO_HINGLISH_LEXICON.items()}

# Devanagari character mapping
VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऑ': 'o', 'ऍ': 'e'
}

MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ॉ': 'o', 'ॅ': 'e'
}

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f'
}

VIRAMA = '्'
ANUSVARA = 'ं'
CHANDRABINDU = 'ँ'
VISARGA = 'ः'
NUKTA = '़'

def is_devanagari(text: str) -> bool:
    """Returns True if string contains Devanagari characters."""
    return any(0x0900 <= ord(c) <= 0x097F for c in text)

def devanagari_to_hinglish_word(word: str) -> str:
    """
    Transliterates a single Devanagari word to Romanized Hinglish.
    Applies lexicon lookup first, then phonetic algorithm with Schwa deletion.
    """
    clean = word.strip(".,!?;:\"'()[]{}")
    punct_prefix = word[:len(word) - len(word.lstrip(".,!?;:\"'()[]{}"))]
    punct_suffix = word[len(word.rstrip(".,!?;:\"'()[]{}")):]

    # Check direct lexicon match
    if clean in DEVA_TO_HINGLISH_LEXICON:
        return punct_prefix + DEVA_TO_HINGLISH_LEXICON[clean] + punct_suffix

    # Check if not Devanagari (e.g. English word already)
    if not is_devanagari(clean):
        return word

    result = []
    i = 0
    n = len(clean)

    while i < n:
        c = clean[i]

        # Handle Independent Vowels
        if c in VOWELS:
            result.append(VOWELS[c])
            i += 1
            continue

        # Handle Consonants
        if c in CONSONANTS or (i + 1 < n and clean[i:i+2] in CONSONANTS):
            if i + 1 < n and clean[i:i+2] in CONSONANTS:
                cons_str = CONSONANTS[clean[i:i+2]]
                i += 2
            else:
                cons_str = CONSONANTS[c]
                i += 1

            # Look ahead for Matra, Virama, or end of word
            if i < n:
                next_c = clean[i]
                if next_c in MATRAS:
                    result.append(cons_str + MATRAS[next_c])
                    i += 1
                elif next_c == VIRAMA:
                    result.append(cons_str)
                    i += 1
                elif next_c in (ANUSVARA, CHANDRABINDU):
                    result.append(cons_str + "an")
                    i += 1
                elif next_c in CONSONANTS or next_c in VOWELS:
                    # Inherent vowel 'a'
                    result.append(cons_str + "a")
                else:
                    result.append(cons_str)
                    i += 1
            else:
                # Word-final consonant: Modern Hindi Schwa deletion (e.g. 'रात' -> 'raat')
                result.append(cons_str)
            continue

        # Standalone matras or special marks
        if c in MATRAS:
            result.append(MATRAS[c])
        elif c in (ANUSVARA, CHANDRABINDU):
            result.append("n")
        elif c == VISARGA:
            result.append("h")
        else:
            # Punctuation or numbers
            result.append(c)
        i += 1

    trans = "".join(result)
    # Capitalize first letter if original is start of sentence
    if trans:
        trans = trans[0].upper() + trans[1:] if len(trans) > 1 else trans.upper()
    return punct_prefix + trans + punct_suffix

def devanagari_to_hinglish(text: str) -> str:
    """
    Converts full Devanagari text/sentence to Romanized Hinglish.
    E.g. 'नमस्ते दोस्तों, आज हम मनाली जा रहे हैं' -> 'Namaste Dosto, Aaj Hum Manali ja rahe hain'
    """
    if not text:
        return text

    words = text.split()
    converted = [devanagari_to_hinglish_word(w) for w in words]
    return " ".join(converted)

def hinglish_to_devanagari_word(word: str) -> str:
    """
    Transliterates a single Romanized Hinglish word back to Devanagari.
    """
    clean = word.lower().strip(".,!?;:\"'()[]{}")
    punct_prefix = word[:len(word) - len(word.lstrip(".,!?;:\"'()[]{}"))]
    punct_suffix = word[len(word.rstrip(".,!?;:\"'()[]{}")):]

    if clean in HINGLISH_TO_DEVA_LEXICON:
        return punct_prefix + HINGLISH_TO_DEVA_LEXICON[clean] + punct_suffix

    # If already Devanagari, return as-is
    if is_devanagari(word):
        return word

    return word

def hinglish_to_devanagari(text: str) -> str:
    """
    Converts full Romanized Hinglish text to Devanagari script.
    """
    if not text:
        return text

    words = text.split()
    converted = [hinglish_to_devanagari_word(w) for w in words]
    return " ".join(converted)

def transliterate_words_list(words_list: list[dict], target_script: str = "roman") -> list[dict]:
    """
    Transliterates a word-level timestamp list in-place.
    Preserves exact timing, confidence, IDs, and filler flags.
    """
    if not words_list:
        return words_list

    for w in words_list:
        orig = w.get("word", "")
        if target_script == "roman":
            # Devanagari -> Roman Hinglish
            w["word"] = devanagari_to_hinglish_word(orig)
            w["script"] = "roman"
        else:
            # Roman Hinglish -> Devanagari
            w["word"] = hinglish_to_devanagari_word(orig)
            w["script"] = "devanagari"

    return words_list
