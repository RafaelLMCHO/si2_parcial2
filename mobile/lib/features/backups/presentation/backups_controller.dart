import 'package:flutter/foundation.dart';

import '../../../core/network/api_client.dart';

/// CU-37: Gestión de Backups, sincronización nube/local, restauración y programación.
class BackupsController extends ChangeNotifier {
  final ApiClient _apiClient;

  BackupsController(this._apiClient);

  bool _loading = false;
  bool _operating = false;
  String? _error;
  String? _message;
  List<Map<String, dynamic>> _backups = [];
  List<Map<String, dynamic>> _modulos = [];
  Map<String, dynamic>? _estadisticas;
  Map<String, dynamic>? _configuracion;
  String? _filtroTipo;
  String? _filtroDestino;

  bool get loading => _loading;
  bool get operating => _operating;
  String? get error => _error;
  String? get message => _message;
  List<Map<String, dynamic>> get backups => _backups;
  List<Map<String, dynamic>> get modulos => _modulos;
  Map<String, dynamic>? get estadisticas => _estadisticas;
  Map<String, dynamic>? get configuracion => _configuracion;
  String? get filtroTipo => _filtroTipo;
  String? get filtroDestino => _filtroDestino;

  void setFiltros({String? tipo, String? destino}) {
    _filtroTipo = tipo;
    _filtroDestino = destino;
    cargarBackups();
  }

  Future<void> cargarTodo() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await Future.wait([
        _fetchBackups(),
        _fetchEstadisticas(),
        _fetchModulos(),
        _fetchConfiguracion(),
      ]);
    } catch (e) {
      _error = 'Error cargando backups: $e';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> cargarBackups() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await _fetchBackups();
      await _fetchEstadisticas();
    } catch (e) {
      _error = 'Error cargando lista de backups: $e';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> _fetchBackups() async {
    final query = <String, dynamic>{};
    if (_filtroTipo != null && _filtroTipo!.isNotEmpty) {
      query['tipo'] = _filtroTipo;
    }
    if (_filtroDestino != null && _filtroDestino!.isNotEmpty) {
      query['destino'] = _filtroDestino;
    }
    final dynamic res = await _apiClient.get('/backups', query: query);
    if (res is Map) {
      final items = res['items'] as List<dynamic>? ?? [];
      _backups = items.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    } else if (res is List) {
      _backups = res.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
  }

  Future<void> _fetchEstadisticas() async {
    final dynamic res = await _apiClient.get('/backups/estadisticas');
    if (res is Map) {
      _estadisticas = Map<String, dynamic>.from(res);
    }
  }

  Future<void> _fetchModulos() async {
    final dynamic res = await _apiClient.get('/backups/modulos');
    if (res is List) {
      _modulos = res.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
  }

  Future<void> _fetchConfiguracion() async {
    final dynamic res = await _apiClient.get('/backups/configuracion');
    if (res is Map) {
      _configuracion = Map<String, dynamic>.from(res);
    }
  }

  Future<bool> crearBackupManual({
    String? nombre,
    String? descripcion,
    String formato = 'json',
    String destino = 'ambos',
    List<String>? modulos,
    bool incluirAuditoria = false,
  }) async {
    _operating = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      await _apiClient.post('/backups', {
        'nombre': ?nombre,
        'descripcion': ?descripcion,
        'alcance': 'empresa',
        'formato': formato,
        'destino': destino,
        'modulos': ?modulos,
        'incluir_auditoria': incluirAuditoria,
      });
      _message = 'Backup creado correctamente.';
      await Future.wait([_fetchBackups(), _fetchEstadisticas()]);
      return true;
    } catch (e) {
      _error = 'Error al crear backup: $e';
      return false;
    } finally {
      _operating = false;
      notifyListeners();
    }
  }

  Future<bool> sincronizarNube(String backupId) async {
    return _runBackupAction(
      () => _apiClient.post('/backups/$backupId/sync-cloud', {}),
      'Backup sincronizado a la nube.',
    );
  }

  Future<bool> sincronizarLocal(String backupId) async {
    return _runBackupAction(
      () => _apiClient.post('/backups/$backupId/sync-local', {}),
      'Backup descargado a almacenamiento local.',
    );
  }

  Future<bool> restaurarBackup(
    String backupId, {
    String modo = 'safe',
    List<String>? tablas,
  }) async {
    return _runBackupAction(
      () => _apiClient.post('/backups/$backupId/restaurar', {
        'modo': modo,
        'tablas': ?tablas,
      }),
      'Restauracion completada en modo $modo.',
    );
  }

  Future<bool> eliminarBackup(String backupId) async {
    return _runBackupAction(
      () => _apiClient.delete('/backups/$backupId'),
      'Backup eliminado.',
    );
  }

  Future<bool> actualizarConfiguracion({
    required bool activo,
    required String frecuencia,
    required String horaEjecucion,
    required String destino,
    required String formato,
    required int retencionDias,
  }) async {
    _operating = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      final dynamic res = await _apiClient.put('/backups/configuracion', {
        'activo': activo,
        'frecuencia': frecuencia,
        'hora_ejecucion': horaEjecucion,
        'destino': destino,
        'formato': formato,
        'retencion_dias': retencionDias,
        'tablas':
            (_configuracion?['tablas'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ??
            const ['catalogo', 'inventario', 'ventas', 'reservas', 'clientes'],
      });
      if (res is Map) {
        _configuracion = Map<String, dynamic>.from(res);
      }
      _message = 'Configuracion automatica actualizada.';
      await _fetchEstadisticas();
      return true;
    } catch (e) {
      _error = 'Error al guardar configuracion: $e';
      return false;
    } finally {
      _operating = false;
      notifyListeners();
    }
  }

  Future<bool> ejecutarAutoAhora() async {
    return _runBackupAction(
      () => _apiClient.post('/backups/configuracion/ejecutar-auto', {}),
      'Backup automatico ejecutado.',
    );
  }

  Future<bool> _runBackupAction(
    Future<dynamic> Function() action,
    String successMsg,
  ) async {
    _operating = true;
    _error = null;
    _message = null;
    notifyListeners();

    try {
      await action();
      _message = successMsg;
      await Future.wait([_fetchBackups(), _fetchEstadisticas()]);
      return true;
    } catch (e) {
      _error = 'Operacion fallida: $e';
      return false;
    } finally {
      _operating = false;
      notifyListeners();
    }
  }
}

