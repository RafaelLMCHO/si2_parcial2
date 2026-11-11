import 'package:flutter/services.dart';

abstract class VoiceInputService {
  Future<bool> isAvailable();

  Future<void> startListening({
    required void Function(String partialText) onPartialResult,
    required void Function(String finalText) onFinalResult,
    required void Function(bool listening) onListeningChanged,
    required void Function(String errorMessage) onError,
    String localeId = 'es-BO',
  });

  Future<void> stopListening();

  void dispose();
}

class AndroidMethodChannelVoiceInputService implements VoiceInputService {
  AndroidMethodChannelVoiceInputService({MethodChannel? channel})
    : _channel = channel ?? const MethodChannel('fashionstore/voice');

  final MethodChannel _channel;
  bool _handlerRegistered = false;

  void Function(String)? _onPartialResult;
  void Function(String)? _onFinalResult;
  void Function(bool)? _onListeningChanged;
  void Function(String)? _onError;

  void _ensureHandler() {
    if (_handlerRegistered) return;
    _handlerRegistered = true;
    _channel.setMethodCallHandler((call) async {
      switch (call.method) {
        case 'onPartialResult':
          final text = call.arguments?.toString().trim() ?? '';
          if (text.isNotEmpty) {
            _onPartialResult?.call(text);
          }
          break;
        case 'onFinalResult':
          final text = call.arguments?.toString().trim() ?? '';
          _onFinalResult?.call(text);
          break;
        case 'onListeningChanged':
          final listening = call.arguments == true;
          _onListeningChanged?.call(listening);
          break;
        case 'onError':
          final msg =
              call.arguments?.toString().trim() ??
              'No se pudo reconocer el comando de voz.';
          _onError?.call(msg);
          break;
      }
    });
  }

  @override
  Future<bool> isAvailable() async {
    try {
      final res = await _channel.invokeMethod<bool>('isAvailable');
      return res ?? false;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  @override
  Future<void> startListening({
    required void Function(String partialText) onPartialResult,
    required void Function(String finalText) onFinalResult,
    required void Function(bool listening) onListeningChanged,
    required void Function(String errorMessage) onError,
    String localeId = 'es-BO',
  }) async {
    _ensureHandler();
    _onPartialResult = onPartialResult;
    _onFinalResult = onFinalResult;
    _onListeningChanged = onListeningChanged;
    _onError = onError;

    try {
      await _channel.invokeMethod<void>('startListening', {'locale': localeId});
    } on MissingPluginException {
      onListeningChanged(false);
      onError(
        'El reconocimiento de voz no está disponible en esta plataforma.',
      );
    } on PlatformException catch (e) {
      onListeningChanged(false);
      onError(
        e.message?.trim().isNotEmpty == true
            ? e.message!.trim()
            : 'No se pudo iniciar el micrófono.',
      );
    }
  }

  @override
  Future<void> stopListening() async {
    try {
      await _channel.invokeMethod<void>('stopListening');
    } on PlatformException {
      // Ignorado al detener
    } on MissingPluginException {
      // Ignorado en plataformas sin canal nativo
    }
  }

  @override
  void dispose() {
    _onPartialResult = null;
    _onFinalResult = null;
    _onListeningChanged = null;
    _onError = null;
    if (_handlerRegistered) {
      _channel.setMethodCallHandler(null);
      _handlerRegistered = false;
    }
  }
}

