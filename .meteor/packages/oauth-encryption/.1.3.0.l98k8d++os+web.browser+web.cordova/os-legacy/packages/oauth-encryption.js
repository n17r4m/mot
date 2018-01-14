(function(){

//////////////////////////////////////////////////////////////////////////////////////////
//                                                                                      //
// packages/oauth-encryption/encrypt.js                                                 //
//                                                                                      //
//////////////////////////////////////////////////////////////////////////////////////////
                                                                                        //
var crypto = require("crypto");                                                         // 1
var gcmKey = null;                                                                      // 2
var OAuthEncryption = exports.OAuthEncryption = {};                                     // 3
var objToStr = Object.prototype.toString;                                               // 4
                                                                                        // 5
function isString(value) {                                                              // 6
  return objToStr.call(value) === "[object String]";                                    // 7
}                                                                                       // 8
                                                                                        // 9
// Node leniently ignores non-base64 characters when parsing a base64                   // 10
// string, but we want to provide a more informative error message if                   // 11
// the developer doesn't use base64 encoding.                                           // 12
//                                                                                      // 13
// Note that an empty string is valid base64 (denoting 0 bytes).                        // 14
//                                                                                      // 15
// Exported for the convenience of tests.                                               // 16
//                                                                                      // 17
OAuthEncryption._isBase64 = function (str) {                                            // 18
  return isString(str) && /^[A-Za-z0-9\+\/]*\={0,2}$/.test(str);                        // 19
};                                                                                      // 20
                                                                                        // 21
                                                                                        // 22
// Loads the OAuth secret key, which must be 16 bytes in length                         // 23
// encoded in base64.                                                                   // 24
//                                                                                      // 25
// The key may be `null` which reverts to having no key (mainly used                    // 26
// by tests).                                                                           // 27
//                                                                                      // 28
OAuthEncryption.loadKey = function (key) {                                              // 29
  if (key === null) {                                                                   // 30
    gcmKey = null;                                                                      // 31
    return;                                                                             // 32
  }                                                                                     // 33
                                                                                        // 34
  if (! OAuthEncryption._isBase64(key))                                                 // 35
    throw new Error("The OAuth encryption key must be encoded in base64");              // 36
                                                                                        // 37
  var buf = Buffer.from(key, "base64");                                                 // 38
                                                                                        // 39
  if (buf.length !== 16)                                                                // 40
    throw new Error("The OAuth encryption AES-128-GCM key must be 16 bytes in length");
                                                                                        // 42
  gcmKey = buf;                                                                         // 43
};                                                                                      // 44
                                                                                        // 45
                                                                                        // 46
// Encrypt `data`, which may be any EJSON-compatible object, using the                  // 47
// previously loaded OAuth secret key.                                                  // 48
//                                                                                      // 49
// The `userId` argument is optional. The data is encrypted as { data:                  // 50
// *, userId: * }. When the result of `seal` is passed to `open`, the                   // 51
// same user id must be supplied, which prevents user specific                          // 52
// credentials such as access tokens from being used by a different                     // 53
// user.                                                                                // 54
//                                                                                      // 55
// We might someday like the user id to be AAD (additional authenticated                // 56
// data), but the Node 0.10.x crypto API did not support specifying AAD,                // 57
// and it's not clear that we want to incur the compatibility issues of                 // 58
// relying on that feature, even though it's now supported by Node 4.                   // 59
//                                                                                      // 60
OAuthEncryption.seal = function (data, userId) {                                        // 61
  if (! gcmKey) {                                                                       // 62
    throw new Error("No OAuth encryption key loaded");                                  // 63
  }                                                                                     // 64
                                                                                        // 65
  var plaintext = Buffer.from(EJSON.stringify({                                         // 66
    data: data,                                                                         // 67
    userId: userId                                                                      // 68
  }));                                                                                  // 69
                                                                                        // 70
  var iv = crypto.randomBytes(12);                                                      // 71
  var cipher = crypto.createCipheriv("aes-128-gcm", gcmKey, iv);                        // 72
  cipher.setAAD(Buffer.from([]));                                                       // 73
  var chunks = [cipher.update(plaintext)];                                              // 74
  chunks.push(cipher.final());                                                          // 75
  var encrypted = Buffer.concat(chunks);                                                // 76
                                                                                        // 77
  return {                                                                              // 78
    iv: iv.toString("base64"),                                                          // 79
    ciphertext: encrypted.toString("base64"),                                           // 80
    algorithm: "aes-128-gcm",                                                           // 81
    authTag: cipher.getAuthTag().toString("base64")                                     // 82
  };                                                                                    // 83
};                                                                                      // 84
                                                                                        // 85
// Decrypt the passed ciphertext (as returned from `seal`) using the                    // 86
// previously loaded OAuth secret key.                                                  // 87
//                                                                                      // 88
// `userId` must match the user id passed to `seal`: if the user id                     // 89
// wasn't specified, it must not be specified here, if it was                           // 90
// specified, it must be the same user id.                                              // 91
//                                                                                      // 92
// To prevent an attacker from breaking the encryption key by                           // 93
// observing the result of sending manipulated ciphertexts, `open`                      // 94
// throws "decryption unsuccessful" on any error.                                       // 95
OAuthEncryption.open = function (ciphertext, userId) {                                  // 96
  if (! gcmKey)                                                                         // 97
    throw new Error("No OAuth encryption key loaded");                                  // 98
                                                                                        // 99
  try {                                                                                 // 100
    if (ciphertext.algorithm !== "aes-128-gcm") {                                       // 101
      throw new Error();                                                                // 102
    }                                                                                   // 103
                                                                                        // 104
    var decipher = crypto.createDecipheriv(                                             // 105
      "aes-128-gcm",                                                                    // 106
      gcmKey,                                                                           // 107
      Buffer.from(ciphertext.iv, "base64")                                              // 108
    );                                                                                  // 109
                                                                                        // 110
    decipher.setAAD(Buffer.from([]));                                                   // 111
    decipher.setAuthTag(Buffer.from(ciphertext.authTag, "base64"));                     // 112
    var chunks = [decipher.update(                                                      // 113
      Buffer.from(ciphertext.ciphertext, "base64"))];                                   // 114
    chunks.push(decipher.final());                                                      // 115
    var plaintext = Buffer.concat(chunks).toString("utf8");                             // 116
                                                                                        // 117
    var err;                                                                            // 118
    var data;                                                                           // 119
                                                                                        // 120
    try {                                                                               // 121
      data = EJSON.parse(plaintext);                                                    // 122
    } catch (e) {                                                                       // 123
      err = new Error();                                                                // 124
    }                                                                                   // 125
                                                                                        // 126
    if (data.userId !== userId) {                                                       // 127
      err = new Error();                                                                // 128
    }                                                                                   // 129
                                                                                        // 130
    if (err) {                                                                          // 131
      throw err;                                                                        // 132
    } else {                                                                            // 133
      return data.data;                                                                 // 134
    }                                                                                   // 135
  } catch (e) {                                                                         // 136
    throw new Error("decryption failed");                                               // 137
  }                                                                                     // 138
};                                                                                      // 139
                                                                                        // 140
                                                                                        // 141
OAuthEncryption.isSealed = function (maybeCipherText) {                                 // 142
  return maybeCipherText &&                                                             // 143
    OAuthEncryption._isBase64(maybeCipherText.iv) &&                                    // 144
    OAuthEncryption._isBase64(maybeCipherText.ciphertext) &&                            // 145
    OAuthEncryption._isBase64(maybeCipherText.authTag) &&                               // 146
    isString(maybeCipherText.algorithm);                                                // 147
};                                                                                      // 148
                                                                                        // 149
                                                                                        // 150
OAuthEncryption.keyIsLoaded = function () {                                             // 151
  return !! gcmKey;                                                                     // 152
};                                                                                      // 153
                                                                                        // 154
//////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

//////////////////////////////////////////////////////////////////////////////////////////
//                                                                                      //
// packages/oauth-encryption/encrypt_tests.js                                           //
//                                                                                      //
//////////////////////////////////////////////////////////////////////////////////////////
                                                                                        //
Tinytest.add("oauth-encryption - loadKey", function (test) {                            // 1
  test.throws(                                                                          // 2
    function () {                                                                       // 3
      OAuthEncryption.loadKey("my encryption key");                                     // 4
    },                                                                                  // 5
    "The OAuth encryption key must be encoded in base64"                                // 6
  );                                                                                    // 7
                                                                                        // 8
  test.throws(                                                                          // 9
    function () {                                                                       // 10
      OAuthEncryption.loadKey(Buffer.from([1, 2, 3, 4, 5]).toString("base64"));         // 11
    },                                                                                  // 12
    "The OAuth encryption AES-128-GCM key must be 16 bytes in length"                   // 13
  );                                                                                    // 14
                                                                                        // 15
  OAuthEncryption.loadKey(                                                              // 16
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 17
    toString("base64")                                                                  // 18
  );                                                                                    // 19
                                                                                        // 20
  OAuthEncryption.loadKey(null);                                                        // 21
});                                                                                     // 22
                                                                                        // 23
Tinytest.add("oauth-encryption - seal", function (test) {                               // 24
  OAuthEncryption.loadKey(                                                              // 25
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 26
    toString("base64")                                                                  // 27
  );                                                                                    // 28
                                                                                        // 29
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2});                                  // 30
  test.isTrue(Buffer.from(ciphertext.iv, "base64").length === 12);                      // 31
  test.isTrue(OAuthEncryption._isBase64(ciphertext.ciphertext));                        // 32
  test.isTrue(ciphertext.algorithm === "aes-128-gcm");                                  // 33
  test.isTrue(OAuthEncryption._isBase64(ciphertext.authTag));                           // 34
                                                                                        // 35
  OAuthEncryption.loadKey(null);                                                        // 36
});                                                                                     // 37
                                                                                        // 38
Tinytest.add("oauth-encryption - open successful", function (test) {                    // 39
  OAuthEncryption.loadKey(                                                              // 40
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 41
    toString("base64")                                                                  // 42
  );                                                                                    // 43
  var userId = "rH6rNSWd2hBTfkwcc";                                                     // 44
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2}, userId);                          // 45
                                                                                        // 46
  var decrypted = OAuthEncryption.open(ciphertext, userId);                             // 47
  test.equal(decrypted, {a: 1, b: 2});                                                  // 48
                                                                                        // 49
  OAuthEncryption.loadKey(null);                                                        // 50
});                                                                                     // 51
                                                                                        // 52
Tinytest.add("oauth-encryption - open with wrong key", function (test) {                // 53
  OAuthEncryption.loadKey(                                                              // 54
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 55
    toString("base64")                                                                  // 56
  );                                                                                    // 57
  var userId = "rH6rNSWd2hBTfkwcc";                                                     // 58
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2}, userId);                          // 59
                                                                                        // 60
  OAuthEncryption.loadKey(                                                              // 61
    Buffer.from([9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]).                      // 62
    toString("base64")                                                                  // 63
  );                                                                                    // 64
  test.throws(                                                                          // 65
    function () {                                                                       // 66
      OAuthEncryption.open(ciphertext, userId);                                         // 67
    },                                                                                  // 68
    "decryption failed"                                                                 // 69
  );                                                                                    // 70
                                                                                        // 71
  OAuthEncryption.loadKey(null);                                                        // 72
});                                                                                     // 73
                                                                                        // 74
Tinytest.add("oauth-encryption - open with wrong userId", function (test) {             // 75
  OAuthEncryption.loadKey(                                                              // 76
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 77
    toString("base64")                                                                  // 78
  );                                                                                    // 79
  var userId = "rH6rNSWd2hBTfkwcc";                                                     // 80
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2}, userId);                          // 81
                                                                                        // 82
  var differentUser = "3FPxY2mBNeBpigm86";                                              // 83
  test.throws(                                                                          // 84
    function () {                                                                       // 85
      OAuthEncryption.open(ciphertext, differentUser);                                  // 86
    },                                                                                  // 87
    "decryption failed"                                                                 // 88
  );                                                                                    // 89
                                                                                        // 90
  OAuthEncryption.loadKey(null);                                                        // 91
});                                                                                     // 92
                                                                                        // 93
Tinytest.add("oauth-encryption - seal and open with no userId", function (test) {       // 94
  OAuthEncryption.loadKey(                                                              // 95
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 96
    toString("base64")                                                                  // 97
  );                                                                                    // 98
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2});                                  // 99
  var decrypted = OAuthEncryption.open(ciphertext);                                     // 100
  test.equal(decrypted, {a: 1, b: 2});                                                  // 101
});                                                                                     // 102
                                                                                        // 103
Tinytest.add("oauth-encryption - open modified ciphertext", function (test) {           // 104
  OAuthEncryption.loadKey(                                                              // 105
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 106
    toString("base64")                                                                  // 107
  );                                                                                    // 108
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2});                                  // 109
                                                                                        // 110
  var b = Buffer.from(ciphertext.ciphertext, "base64");                                 // 111
  b[0] = b[0] ^ 1;                                                                      // 112
  ciphertext.ciphertext = b.toString("base64");                                         // 113
                                                                                        // 114
  test.throws(                                                                          // 115
    function () {                                                                       // 116
      OAuthEncryption.open(ciphertext);                                                 // 117
    },                                                                                  // 118
    "decryption failed"                                                                 // 119
  );                                                                                    // 120
});                                                                                     // 121
                                                                                        // 122
                                                                                        // 123
Tinytest.add("oauth-encryption - isSealed", function (test) {                           // 124
  OAuthEncryption.loadKey(                                                              // 125
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 126
    toString("base64")                                                                  // 127
  );                                                                                    // 128
  var userId = "rH6rNSWd2hBTfkwcc";                                                     // 129
  var ciphertext = OAuthEncryption.seal({a: 1, b: 2}, userId);                          // 130
  test.isTrue(OAuthEncryption.isSealed(ciphertext));                                    // 131
                                                                                        // 132
  test.isFalse(OAuthEncryption.isSealed("abcdef"));                                     // 133
  test.isFalse(OAuthEncryption.isSealed({a: 1, b: 2}));                                 // 134
                                                                                        // 135
  OAuthEncryption.loadKey(null);                                                        // 136
});                                                                                     // 137
                                                                                        // 138
Tinytest.add("oauth-encryption - keyIsLoaded", function (test) {                        // 139
  OAuthEncryption.loadKey(null);                                                        // 140
  test.isFalse(OAuthEncryption.keyIsLoaded());                                          // 141
                                                                                        // 142
  OAuthEncryption.loadKey(                                                              // 143
    Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).               // 144
    toString("base64")                                                                  // 145
  );                                                                                    // 146
  test.isTrue(OAuthEncryption.keyIsLoaded());                                           // 147
                                                                                        // 148
  OAuthEncryption.loadKey(null);                                                        // 149
});                                                                                     // 150
                                                                                        // 151
//////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
