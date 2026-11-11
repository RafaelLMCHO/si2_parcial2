import 'dart:math';

final Random _uuidRng = Random.secure();

String generateUuidV4() {
  final bytes = List<int>.generate(16, (_) => _uuidRng.nextInt(256));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  String h(int b) => b.toRadixString(16).padLeft(2, '0');
  return '${h(bytes[0])}${h(bytes[1])}${h(bytes[2])}${h(bytes[3])}-'
      '${h(bytes[4])}${h(bytes[5])}-'
      '${h(bytes[6])}${h(bytes[7])}-'
      '${h(bytes[8])}${h(bytes[9])}-'
      '${h(bytes[10])}${h(bytes[11])}${h(bytes[12])}${h(bytes[13])}${h(bytes[14])}${h(bytes[15])}';
}

