import random
import string

def make_avatar() -> str:
    random_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    
    random_num = random.randint(1, 9)
    
    avatar_url = f"https://robohash.org/dolor{random_key}umvlitquam.png?size=50x50&set=set{random_num}"
    
    return avatar_url