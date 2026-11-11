import 'package:flutter/services.dart';

abstract class ReportExportSaver {
  Future<String> saveExportFile({
    required String fileName,
    required String mimeType,
    required String contentBase64,
  });
}

class AndroidMethodChannelReportExportSaver implements ReportExportSaver {
  AndroidMethodChannelReportExportSaver({MethodChannel? channel})
    : _channel = channel ?? const MethodChannel('fashionstore/files');

  final MethodChannel _channel;

  @override
  Future<String> saveExportFile({
    required String fileName,
    required String mimeType,
    required String contentBase64,
  }) async {
    try {
      final path = await _channel.invokeMethod<String>('saveExportFile', {
        'fileName': fileName,
        'mimeType': mimeType,
        'base64': contentBase64,
      });
      return (path != null && path.isNotEmpty) ? path : fileName;
    } on MissingPluginException {
      return fileName;
    } on PlatformException catch (e) {
      throw Exception(
        e.message?.trim().isNotEmpty == true
            ? e.message!.trim()
            : 'No se pudo guardar el archivo en el dispositivo.',
      );
    }
  }
}

