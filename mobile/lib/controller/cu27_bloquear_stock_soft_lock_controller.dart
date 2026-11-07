import 'package:flutter/foundation.dart';
import '../core/storage/local_database.dart';

/// CU-27: Bloquear stock local offline con TTL (Soft-Lock temporal de 45 minutos)
class CU27BloquearStockSoftLockController extends ChangeNotifier {
  final LocalDatabase _database;
  bool _loading = false;
  String? _error;
  final Map<String, int> _locksActivos = {};

  CU27BloquearStockSoftLockController(this._database);

  bool get loading => _loading;
  String? get error => _error;
  Map<String, int> get locksActivos => _locksActivos;

  Future<bool> bloquearStock({
    required String varianteId,
    required String sucursalId,
    required int cantidad,
    int ttlMinutos = 45,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final lockId = 'lock-${DateTime.now().millisecondsSinceEpoch}';
      await _database.crearSoftLockLocal(
        id: lockId,
        varianteId: varianteId,
        sucursalId: sucursalId,
        cantidad: cantidad,
        ttlMinutos: ttlMinutos,
      );

      _locksActivos[varianteId] = (_locksActivos[varianteId] ?? 0) + cantidad;
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = 'Error aplicando soft-lock local: $e';
      notifyListeners();
      return false;
    }
  }

  void liberarLock(String varianteId) {
    _locksActivos.remove(varianteId);
    notifyListeners();
  }
}

