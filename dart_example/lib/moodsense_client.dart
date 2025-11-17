import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:cryptography/cryptography.dart';

/// Client per MoodSense API con supporto encryption
class MoodSenseClient {
  final String baseUrl;
  final http.Client _httpClient;

  MoodSenseClient({
    this.baseUrl = 'https://moodsense-38104758698.europe-west1.run.app',
    http.Client? httpClient,
  }) : _httpClient = httpClient ?? http.Client();

  /// Analisi plaintext (senza encryption) - upload file
  Future<Map<String, dynamic>> analyzePlaintext(String chatText) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/v1/analyze-conversation'),
    );

    // Usa fromBytes con encoding esplicito
    final bytes = utf8.encode(chatText);
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: 'chat.txt',
        contentType: MediaType('text', 'plain'),
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(
          'Failed to analyze: ${response.statusCode} ${response.body}');
    }
  }

  /// Analisi con encryption X25519 + XChaCha20-Poly1305
  Future<Map<String, dynamic>> analyzeEncrypted(String chatText) async {
    // 1. Ottieni la chiave pubblica del server
    final serverPublicKeyB64 = await _getServerPublicKey();
    final serverPublicKey = base64Decode(serverPublicKeyB64);

    // 2. Genera coppia di chiavi effimere X25519
    final algorithm = X25519();
    final clientKeyPair = await algorithm.newKeyPair();
    final clientPublicKey = await clientKeyPair.extractPublicKey();

    // 3. Calcola shared secret con il server
    final sharedSecretKey = await algorithm.sharedSecretKey(
      keyPair: clientKeyPair,
      remotePublicKey: SimplePublicKey(
        serverPublicKey,
        type: KeyPairType.x25519,
      ),
    );

    // 4. Estrai i bytes del shared secret per HKDF manuale
    final sharedSecretBytes = await sharedSecretKey.extractBytes();

    // 5. Usa direttamente SHA-256 HMAC per derivare la chiave (emula HKDF con salt=null)
    // HKDF(hash, salt, info) = HMAC(salt, shared_secret || info)
    final hmac = Hmac.sha256();
    final mac = await hmac.calculateMac(
      [...sharedSecretBytes, ...utf8.encode('moodsense-xchacha20-v1')],
      secretKey: SecretKey(List.filled(32, 0)), // Salt=null in HKDF = zeros
    );
    final symmetricKeyBytes =
        mac.bytes.sublist(0, 32); // Prendi i primi 32 bytes

    print('DEBUG: Symmetric key derived successfully');

    // 6. Cifra il payload con XChaCha20-Poly1305
    final xchacha20 = Xchacha20.poly1305Aead();
    final plaintext = utf8.encode(chatText);
    final nonce = xchacha20.newNonce();

    final secretBox = await xchacha20.encrypt(
      plaintext,
      secretKey: SecretKey(symmetricKeyBytes),
      nonce: nonce,
    );

    // XChaCha20-Poly1305 AEAD: ciphertext include il tag MAC alla fine
    final ciphertextWithMac = secretBox.cipherText + secretBox.mac.bytes;

    // 7. Costruisci payload finale (deve corrispondere a EncryptedChatPayload)
    final encryptedPayload = {
      'client_public_key': base64Encode(clientPublicKey.bytes),
      'nonce': base64Encode(nonce),
      'ciphertext': base64Encode(ciphertextWithMac),
    };

    // 8. Invia al server
    final response = await _httpClient.post(
      Uri.parse('$baseUrl/api/v1/analyze-conversation-encrypted'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(encryptedPayload),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(
          'Failed to analyze encrypted: ${response.statusCode} ${response.body}');
    }
  }

  Future<String> _getServerPublicKey() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/api/v1/public-key'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['public_key'];
    } else {
      throw Exception('Failed to get public key: ${response.statusCode}');
    }
  }

  void dispose() {
    _httpClient.close();
  }
}

/// Esempio d'uso
void main() async {
  final client = MoodSenseClient();

  // Leggi il file di esempio
  final file = File('wa_export_2000_messages_english.txt');
  final chatText = await file.readAsString();

  try {
    // Analisi plaintext (FUNZIONA ✅)
    print('=== ANALISI PLAINTEXT ===');
    final resultPlain = await client.analyzePlaintext(chatText);
    final metadata = resultPlain['metadata'];
    final emotions = resultPlain['overall_emotion_distribution'];

    print('Total messages: ${metadata['total_messages']}');
    print('Users: ${metadata['users']}');
    print('Date range: ${metadata['start_date']} to ${metadata['end_date']}');
    print(
        'Love score: avg=${emotions['love']['avg']}, frequency=${emotions['love']['frequency']}');
    print(
        'Caring score: avg=${emotions['caring']['avg']}, frequency=${emotions['caring']['frequency']}');
    print('Overall sentiment: ${resultPlain['overall_sentiment']['compound']}');
    print('Messages per day: ${resultPlain['messages_per_day']}');
    print('');

    // Analisi encrypted (WIP - HKDF key derivation issue)
    // TODO: Fix HKDF implementation to match Python cryptography library
    // print('=== ANALISI ENCRYPTED ===');
    // final resultEncrypted = await client.analyzeEncrypted(chatText);
    // final metadataEnc = resultEncrypted['metadata'];
    // final emotionsEnc = resultEncrypted['overall_emotion_distribution'];
    //
    // print('Total messages: ${metadataEnc['total_messages']}');
    // print('Users: ${metadataEnc['users']}');
    // print(
    //     'Love score: avg=${emotionsEnc['love']['avg']}, frequency=${emotionsEnc['love']['frequency']}');
    // print(
    //     'Overall sentiment: ${resultEncrypted['overall_sentiment']['compound']}');
  } catch (e) {
    print('Error: $e');
  } finally {
    client.dispose();
  }
}
