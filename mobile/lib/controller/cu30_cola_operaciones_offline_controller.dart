import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';

/// CU-30: Consultar cola de operaciones pendientes offline (estados)
class CU30ColaOperacionesOfflineController extends ChangeNotifier {
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  List<Map<String, dynamic>> _operaciones = [];

  CU30ColaOperacionesOfflineController(this._database);

  bool get loading => _loading;
  String? get error => _error;
  List<Map<String, dynamic>> get operaciones => _operaciones;

  Future<void> cargarCola() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _operaciones = await _database.listarOperacionesOffline();
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = 'Error consultando cola offline: $e';
    }
    notifyListeners();
  }
}

