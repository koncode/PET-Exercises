#####################################################
# GA17 Privacy Enhancing Technologies -- Lab 01
#
# Basics of Petlib, encryption, signatures and
# an end-to-end encryption system.
#
# Run the tests through:
# $ py.test-2.7 -v Lab01Tests.py 

###########################
# Group Members: TODO
###########################


#####################################################
# TASK 1 -- Ensure petlib is installed on the System
#           and also pytest. Ensure the Lab Code can 
#           be imported.

import petlib

#####################################################
# TASK 2 -- Symmetric encryption using AES-GCM 
#           (Galois Counter Mode)
#
# Implement a encryption and decryption function
# that simply performs AES_GCM symmetric encryption
# and decryption using the functions in petlib.cipher.

from os import urandom
from petlib.cipher import Cipher


def encrypt_message(K, message):
    """ Encrypt a message under a key K """

    plaintext = message.encode("utf8")

    ## YOUR CODE HERE
    aes = Cipher("aes-128-gcm")
    iv = urandom(16)
    ciphertext, tag = aes.quick_gcm_enc(K, iv, plaintext)

    return (iv, ciphertext, tag)


def decrypt_message(K, iv, ciphertext, tag):
    """ Decrypt a cipher text under a key K 

        In case the decryption fails, throw an exception.
    """
    ## YOUR CODE HERE
    aes = Cipher("aes-128-gcm")
    plain = aes.quick_gcm_dec(K, iv, ciphertext, tag)

    return plain.encode("utf8")


#####################################################
# TASK 3 -- Understand Elliptic Curve Arithmetic
#           - Test if a point is on a curve.
#           - Implement Point addition.
#           - Implement Point doubling.
#           - Implement Scalar multiplication (double & add).
#           - Implement Scalar multiplication (Montgomery ladder).
#
# MUST NOT USE ANY OF THE petlib.ec FUNCIONS. Only petlib.bn!

from petlib.bn import Bn


def is_point_on_curve(a, b, p, x, y):
    """
    Check that a point (x, y) is on the curve defined by a,b and prime p.
    Reminder: an Elliptic Curve on a prime field p is defined as:

              y^2 = x^3 + ax + b (mod p)
                  (Weierstrass form)

    Return True if point (x,y) is on curve, otherwise False.
    By convention a (None, None) point represents "infinity".
    """
    assert isinstance(a, Bn)
    assert isinstance(b, Bn)
    assert isinstance(p, Bn) and p > 0
    assert (isinstance(x, Bn) and isinstance(y, Bn)) \
           or (x is None and y is None)

    if x is None and y is None:
        return True

    lhs = (y * y) % p
    rhs = (x * x * x + a * x + b) % p
    on_curve = (lhs == rhs)

    return on_curve


def point_add(a, b, p, x0, y0, x1, y1):
    """Define the "addition" operation for 2 EC Points.

    Reminder: (xr, yr) = (xq, yq) + (xp, yp)
    is defined as:
        lam = (yq - yp) * (xq - xp)^-1 (mod p)
        xr  = lam^2 - xp - xq (mod p)
        yr  = lam * (xp - xr) - yp (mod p)

    Return the point resulting from the addition. Raises an Exception if the points are equal.
    """

    # ADD YOUR CODE BELOW
    xr, yr = None, None
    # if either point is None,None we return the other one
    if x0 is None and y0 is None:
        return (x1, y1)
    elif x1 is None and y1 is None:
        return (x0, y0)
    # we cannot add the same 2 points so we raise an exception
    elif x1 is x0 and y0 is y1:
        raise Exception("EC Points must not be equal")
    else:
        yp = y1
        xp = x1
        yq = y0
        xq = x0
        # if Xs are equal but Yq = -Yp then we return infinity
        if xp is xq and yp.mod_mul(-1, p) == yq:
            return None, None
        # Below is the normal situation
        # and we add using the given formula
        else:
            lam = ((yq - yp) * ((xq - xp).mod_inverse(p))) % p
        xr = (lam * lam - xp - xq) % p
        yr = (lam * (xp - xr) - yp) % p
        return (xr, yr)


def point_double(a, b, p, x, y):
    """Define "doubling" an EC point.
     A special case, when a point needs to be added to itself.

     Reminder:
        lam = (3 * xp ^ 2 + a) * (2 * yp) ^ -1 (mod p)
        xr  = lam ^ 2 - 2 * xp
        yr  = lam * (xp - xr) - yp (mod p)

    Returns the point representing the double of the input (x, y).
    """

    # ADD YOUR CODE BELOW
    xr, yr = None, None

    if x is None and y is None:
        return None, None
    if is_point_on_curve(a, b, p, x, y):
        lam = (((x.mod_pow(2, p)).mod_mul(3, p)).mod_add(a, p)).mod_mul((y.mod_mul(2, p)).mod_inverse(p), p)
        xr = (lam.mod_pow(2, p)).mod_sub(x.mod_mul(2, p), p)
        yr = ((lam.mod_mul(x.mod_sub(xr, p), p)).mod_sub(y, p))
        return xr, yr
    else:
        raise Exception("Point is not on the curve")


def point_scalar_multiplication_double_and_add(a, b, p, x, y, scalar):
    """
    Implement Point multiplication with a scalar:
        r * (x, y) = (x, y) + ... + (x, y)    (r times)

    Reminder of Double and Multiply algorithm: r * P
        Q = infinity
        for i = 0 to num_bits(P)-1
            if bit i of r == 1 then
                Q = Q + P
            P = 2 * P
        return Q

    """
    Q = (None, None)
    P = (x, y)

    for i in range(scalar.num_bits()):
        if scalar.is_bit_set(i) or scalar == 1:
            Q = point_add(a, b, p, Q[0], Q[1], P[0], P[1])
        P = point_double(a, b, p, P[0], P[1])
    return Q


def point_scalar_multiplication_montgomerry_ladder(a, b, p, x, y, scalar):
    """
    Implement Point multiplication with a scalar:
        r * (x, y) = (x, y) + ... + (x, y)    (r times)

    Reminder of Double and Multiply algorithm: r * P
        R0 = infinity
        R1 = P
        for i in num_bits(P)-1 to zero:
            if di = 0:
                R1 = R0 + R1
                R0 = 2R0
            else
                R0 = R0 + R1
                R1 = 2 R1
        return R0

    """
    R0 = (None, None)
    R1 = (x, y)

    for i in reversed(range(0, scalar.num_bits())):
        if scalar.is_bit_set(i):
            R0 = point_add(a, b, p, R0[0], R0[1], R1[0], R1[1])
            R1 = point_double(a, b, p, R1[0], R1[1])
        else:
            R1 = point_add(a, b, p, R0[0], R0[1], R1[0], R1[1])
            R0 = point_double(a, b, p, R0[0], R0[1])
    return R0


#####################################################
# TASK 4 -- Standard ECDSA signatures
#
#          - Implement a key / param generation 
#          - Implement ECDSA signature using petlib.ecdsa
#          - Implement ECDSA signature verification 
#            using petlib.ecdsa

from hashlib import sha256
from petlib.ec import EcGroup
from petlib.ecdsa import do_ecdsa_sign, do_ecdsa_verify


def ecdsa_key_gen():
    """ Returns an EC group, a random private key for signing 
        and the corresponding public key for verification"""
    G = EcGroup()
    priv_sign = G.order().random()
    pub_verify = priv_sign * G.generator()
    return (G, priv_sign, pub_verify)


def ecdsa_sign(G, priv_sign, message):
    """ Sign the SHA256 digest of the message using ECDSA and return a signature """
    plaintext = message.encode("utf8")

    ## YOUR CODE HERE
    digest = sha256(plaintext).digest()
    sig = do_ecdsa_sign(G, priv_sign, digest)

    return sig


def ecdsa_verify(G, pub_verify, message, sig):
    """ Verify the ECDSA signature on the message """
    plaintext = message.encode("utf8")

    ## YOUR CODE HERE
    digest = sha256(plaintext).digest()
    res = do_ecdsa_verify(G, pub_verify, sig, digest)

    return res


#####################################################
# TASK 5 -- Diffie-Hellman Key Exchange and Derivation
#           - use Bob's public key to derive a shared key.
#           - Use Bob's public key to encrypt a message.
#           - Use Bob's private key to decrypt the message.
#
# NOTE: 

def dh_get_key():
    """ Generate a DH key pair """
    G = EcGroup()
    priv_dec = G.order().random()
    pub_enc = priv_dec * G.generator()
    return (G, priv_dec, pub_enc)


def dh_encrypt(pub, message, aliceSig=None):
    """ Assume you know the public key of someone else (Bob), 
    and wish to Encrypt a message for them.
        - Generate a fresh DH key for this message.
        - Derive a fresh shared key.
        - Use the shared key to AES_GCM encrypt the message.
        - Optionally: sign the message with Alice's key.
    """

    ## YOUR CODE HERE
    # Bob's public key is a point on the curve
    bob_pub = pub

    G, alice_priv, alice_pub = dh_get_key()
    # Alice's private key is a scalar
    # shared_key_point = bob_pub * alice_priv # this is multiplication of a point with a scalar
    shared_key_point = bob_pub.pt_mul(alice_priv)
    # We convert this shared_key point to a
    # string binary representation with .export
    #
    # .export :
    # "Returns a string binary representation
    #  of the point in compressed coordinates"
    shared_key_point_binary = shared_key_point.export()
    # Then we hash the value to produce a 256 bit key
    shared_key = sha256(shared_key_point_binary).digest()
    plaintext = message.encode("utf8")

    ## YOUR CODE HERE
    aes = Cipher("aes-256-gcm")
    iv = urandom(16)
    encrypted_text, tag = aes.quick_gcm_enc(shared_key, iv, plaintext)
    # iv, encrypted_text, tag = encrypt_message(shared_key, message)
    return alice_pub, iv, encrypted_text, tag


def dh_decrypt(priv, ciphertext, aliceVer=None):
    """ Decrypt a received message encrypted using your public key, 
    of which the private key is provided. Optionally verify 
    the message came from Alice using her verification key."""

    ## YOUR CODE HERE
    # The ciphertext is 4 things combined
    alice_pub, iv, encrypted_text, tag = ciphertext
    bob_priv = priv

    assert isinstance(bob_priv, Bn)

    # derive the shared key the same way as before
    shared_key_point = bob_priv * alice_pub  # Now bob_priv is a scalar
    shared_key_point_binary = shared_key_point.export()
    shared_key = sha256(shared_key_point_binary).digest()

    aes = Cipher("aes-256-gcm")
    plain = aes.quick_gcm_dec(shared_key, iv, encrypted_text, tag)

    return plain.encode("utf8")


## NOTE: populate those (or more) tests
#  ensure they run using the "py.test filename" command.
#  What is your test coverage? Where is it missing cases?
#  $ py.test-2.7 --cov-report html --cov Lab01Code Lab01Code.py 

def test_encrypt():
    test_mesage = "This is a test message"
    G, bob_priv, bob_pub = dh_get_key()
    alice_pub, iv, encrypted_text, tag = dh_encrypt(bob_pub, test_mesage, None)
    assert len(iv) == 16
    assert len(encrypted_text) == len(test_mesage)
    assert len(tag) == 16


def test_decrypt():
    test_mesage = "This is a test message"
    G, bob_priv, bob_pub = dh_get_key()
    alice_pub, iv, encrypted_text, tag = dh_encrypt(bob_pub, test_mesage, None)

    decrypted_messsage = dh_decrypt(bob_priv,
                                    (alice_pub, iv, encrypted_text, tag),
                                    None)

    assert len(iv) == 16
    assert len(encrypted_text) == len(test_mesage)
    assert len(tag) == 16

    assert decrypted_messsage == test_mesage


def test_fails():
    from pytest import raises

    test_mesage = "This is a test message"
    G, bob_priv, bob_pub = dh_get_key()
    alice_pub, iv, encrypted_text, tag = dh_encrypt(bob_pub, test_mesage, None)

    with raises(Exception) as excinfo:
        dh_decrypt(bob_priv,
                   (alice_pub, iv, urandom(len(encrypted_text)), tag),
                   None)
    assert 'decryption failed' in str(excinfo.value)

    with raises(Exception) as excinfo:
        dh_decrypt(bob_priv,
                   (alice_pub, iv, encrypted_text, urandom(len(tag))),
                   None)
    assert 'decryption failed' in str(excinfo.value)

    with raises(Exception) as excinfo:
        dh_decrypt(bob_priv,
                   (alice_pub, urandom(len(iv)), encrypted_text, tag),
                   None)
    assert 'decryption failed' in str(excinfo.value)

    with raises(Exception) as excinfo:
        # we generate a random point on the curve
        G = EcGroup()
        priv_dec = G.order().random()
        pub_enc = priv_dec * G.generator()

        dh_decrypt(bob_priv,
                   (pub_enc, iv, encrypted_text, tag),
                   None)
    assert 'decryption failed' in str(excinfo.value)

    with raises(Exception) as excinfo:
        # we generate a random scalar from the group
        G = EcGroup()
        priv_dec = G.order().random()
        dh_decrypt(priv_dec,
                   (alice_pub, iv, encrypted_text, tag),
                   None)
    assert 'decryption failed' in str(excinfo.value)


#####################################################
# TASK 6 -- Time EC scalar multiplication
#             Open Task.
#           
#           - Time your implementations of scalar multiplication
#             (use time.clock() for measurements)for different 
#              scalar sizes)
#           - Print reports on timing dependencies on secrets.
#           - Fix one implementation to not leak information.

def time_scalar_mul():
    pass
