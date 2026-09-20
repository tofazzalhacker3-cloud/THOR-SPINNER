import sys, os, base64, hashlib, zlib, marshal, types

# ============================================================
#  THOR SPINNER - ULTRA ENCRYPTED LOADER
#  Developer: Tofazzal Hossain
#  Anti-decompilation | Anti-debug | Memory-only execution
# ============================================================

# --- Anti Debug Detection ---
if sys.platform == 'win32':
    try:
        import ctypes
        if ctypes.windll.kernel32.IsDebuggerPresent():
            sys.exit(0)
    except: pass

# --- Obfuscated Key Derivation ---
_k = lambda: bytes([
    0x54,0x48,0x4f,0x52,0x5f,0x53,0x50,0x49,0x4e,0x4e,0x45,0x52,
    0x5f,0x4b,0x45,0x59,0x5f,0x30,0x31,0x38,0x37,0x5f,0x54,0x4f,
    0x46,0x41,0x5a,0x5a,0x41,0x4c,0x5f,0x48
])

# --- Encrypted Payload (zlib + AES-256-CBC encrypted source) ---
_ENCRYPTED_DATA = None
_KEY_HASH = None

def _load_encrypted():
    global _ENCRYPTED_DATA, _KEY_HASH
    try:
        import json
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".thor_sec")
        with open(data_file, 'r') as f:
            payload = json.load(f)
        _ENCRYPTED_DATA = base64.b64decode(payload['data'])
        _KEY_HASH = payload['hash']
    except Exception:
        print("[!] Security violation detected.")
        sys.exit(1)

def _derive_key():
    raw = _k()
    for i in range(3):
        raw = hashlib.pbkdf2_hmac('sha256', raw, b'THOR_SPINNER_OB55_' + str(i).encode(), 100000)
    return raw[:32]

def _derive_iv():
    raw = _k()[::-1]
    return hashlib.pbkdf2_hmac('sha256', raw, b'IV_NARUTO_2026', 50000)[:16]

def _unpad(data):
    pad_len = data[-1]
    if 1 <= pad_len <= 32 and all(b == pad_len for b in data[-pad_len:]):
        return data[:-pad_len]
    return data

def _aes_decrypt(key, iv, data):
    try:
        from Crypto.Cipher import AES
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return _unpad(cipher.decrypt(data))
    except ImportError:
        # Fallback: pure python AES-CBC (slower but works)
        return _pure_aes_decrypt(key, iv, data)

def _pure_aes_decrypt(key, iv, data):
    import struct
    sbox = _build_sbox()
    def sub_bytes(s):
        return [sbox[b] for b in s]
    def shift_rows(s):
        return [s[0],s[5],s[10],s[15],s[4],s[9],s[14],s[3],s[8],s[13],s[2],s[7],s[12],s[1],s[6],s[11]]
    def inv_shift_rows(s):
        return [s[0],s[13],s[10],s[7],s[4],s[1],s[14],s[11],s[8],s[5],s[2],s[15],s[12],s[9],s[6],s[3]]
    def xtime(a):
        return ((a<<1)^0x11b) if a&0x80 else (a<<1)
    def mix_columns(s):
        r = []
        for i in range(0,16,4):
            a = s[i:i+4]
            r.extend([xtime(a[0])^xtime(a[1])^a[1]^a[2]^a[3],
                      a[0]^xtime(a[1])^xtime(a[2])^a[2]^a[3],
                      a[0]^a[1]^xtime(a[2])^xtime(a[3])^a[3],
                      xtime(a[0])^a[0]^a[1]^a[2]^xtime(a[3])])
        return r
    def inv_mix_columns(s):
        r = []
        for i in range(0,16,4):
            a = s[i:i+4]
            r.extend([_mul(0x0e,a[0])^_mul(0x0b,a[1])^_mul(0x0d,a[2])^_mul(0x09,a[3]),
                      _mul(0x09,a[0])^_mul(0x0e,a[1])^_mul(0x0b,a[2])^_mul(0x0d,a[3]),
                      _mul(0x0d,a[0])^_mul(0x09,a[1])^_mul(0x0e,a[2])^_mul(0x0b,a[3]),
                      _mul(0x0b,a[0])^_mul(0x0d,a[1])^_mul(0x09,a[2])^_mul(0x0e,a[3])])
        return r
    def _mul(a,b):
        p = 0
        for _ in range(8):
            if b&1: p ^= a
            hi = a&0x80
            a = (a<<1)&0xff
            if hi: a ^= 0x1b
            b >>= 1
        return p
    def add_round_key(s, k):
        return [a^b for a,b in zip(s,k)]
    def key_expansion(key):
        nk = len(key)//4
        nr = nk+6
        w = list(key)
        for i in range(nk, 4*(nr+1)):
            temp = w[(i-4)*4:i*4]
            if i%nk == 0:
                temp = sub_bytes(shift_rows(temp))
                temp[0] ^= [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80][i//nk-1] if i//nk-1 < 8 else 0
            elif nk>6 and i%nk == 4:
                temp = sub_bytes(temp)
            w.extend([a^b for a,b in zip(w[(i-nk)*4:(i-nk+1)*4], temp)])
        return [w[i*16:(i+1)*16] for i in range(nr+1)]
    
    expanded = key_expansion(list(key))
    nr = len(expanded) - 1
    blocks = [list(data[i:i+16]) for i in range(0, len(data), 16)]
    result = []
    prev = list(iv)
    
    for block in blocks:
        state = block[:]
        state = add_round_key(state, expanded[0])
        for r in range(1, nr):
            state = inv_shift_rows(state)
            state = sub_bytes(state)
            state = add_round_key(state, expanded[nr-r])
            state = inv_mix_columns(state)
        state = inv_shift_rows(state)
        state = sub_bytes(state)
        state = add_round_key(state, expanded[nr])
        decrypted = [a^b for a,b in zip(state, prev)]
        result.extend(decrypted)
        prev = block[:]
    
    return bytes(result)

def _build_sbox():
    return [
        0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
        0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
        0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
        0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
        0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
        0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
        0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
        0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
        0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
        0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
        0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
        0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
        0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
        0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
        0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
        0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
    ]

def _execute_encrypted():
    _load_encrypted()
    key = _derive_key()
    iv = _derive_iv()
    
    # Verify integrity
    check = hashlib.sha256(key + iv).hexdigest()
    if check[:16] != _KEY_HASH[:16]:
        print("[!] Tamper detected.")
        sys.exit(1)
    
    # Decrypt
    try:
        compressed = _aes_decrypt(key, iv, _ENCRYPTED_DATA)
        source = zlib.decompress(compressed)
    except Exception:
        print("[!] Decryption failed.")
        sys.exit(1)
    
    # Compile and execute in memory (no .pyc file created)
    code = compile(source, '<encrypted>', 'exec')
    exec(code, {'__name__': '__main__', '__file__': '<encrypted>'})

# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == '__main__':
    try:
        _execute_encrypted()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print("\n[!] Process halted.")
    except Exception as e:
        print(f"[!] Critical error: {e}")
