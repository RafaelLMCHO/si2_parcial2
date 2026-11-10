import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-08: Facturación SaaS e Historial de Facturas
class FacturacionController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _facturas = [];

  FacturacionController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get facturas => _facturas;

  Future<void> cargarFacturas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.get('/saas/facturas');
      _facturas = res is List ? res : ((res as Map?)?['items'] as List<dynamic>? ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<List<int>?> descargarFacturaPdf(String facturaId) async {
    try {
      final dynamic res = await _apiClient.get('/saas/facturas/$facturaId/pdf', rawBytes: true);
      if (res is List<int>) {
        return res;
      }
      if (res is List) {
        return List<int>.from(res);
      }
      return null;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<String?> descargarFacturaUrl(String facturaId) async {
    final bytes = await descargarFacturaPdf(facturaId);
    return bytes != null ? '/saas/facturas/$facturaId/pdf' : null;
  }
}

