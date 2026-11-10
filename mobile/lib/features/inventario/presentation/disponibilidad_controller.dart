import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/local_database.dart';
import '../data/inventario_models.dart';

/// Controlador para CU-18: Consultar disponibilidad en línea y local (SQLite).
class DisponibilidadController extends ChangeNotifier {
  final ApiClient _apiClient;
  final LocalDatabase _localDb;
  bool _loading = false;
  String? _error;
  DisponibilidadPrenda? _datos;

  DisponibilidadController(this._apiClient, this._localDb);

  bool get loading => _loading;
  String? get error => _error;
  DisponibilidadPrenda? get datos => _datos;

  Future<void> consultar(String prendaId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/inventario/prendas/$prendaId/disponibilidad');
      _datos = DisponibilidadPrenda.fromJson(Map<String, dynamic>.from(res as Map));
      _loading = false;
    } catch (e) {
      // Fallback a almacenamiento local SQLite (CU-18)
      final locales = await _localDb.listarExistenciasLocales();
      final actualizadoEn = locales.isNotEmpty
          ? (locales.first['actualizado_en']?.toString() ?? DateTime.now().toIso8601String())
          : DateTime.now().toIso8601String();
      _error = 'Modo offline: $e';
      _datos = DisponibilidadPrenda(
        prendaId: prendaId,
        agotadoEnTodas: locales.isEmpty,
        actualizadoEn: actualizadoEn,
        sucursales: [],
        esLocal: true,
      );
      _loading = false;
    }
    notifyListeners();
  }
}

