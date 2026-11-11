import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../controller/cu25_descargar_catalogo_offline_controller.dart';
import '../../../controller/cu26_registrar_reserva_offline_controller.dart';
import '../../../controller/cu27_bloquear_stock_soft_lock_controller.dart';
import '../../../core/network/api_client.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../catalogo/data/catalogo_models.dart';

class ReservaOfflineScreen extends StatefulWidget {
  final LocalDatabase database;
  final ApiClient? apiClient;
  final SessionController? session;
  final String? initialSucursalId;
  final String? initialVarianteId;

  const ReservaOfflineScreen({
    super.key,
    required this.database,
    this.apiClient,
    this.session,
    this.initialSucursalId,
    this.initialVarianteId,
  });

  @override
  State<ReservaOfflineScreen> createState() => _ReservaOfflineScreenState();
}

class _VarianteItem {
  const _VarianteItem({required this.prenda, required this.variante});
  final Prenda prenda;
  final VariantePrenda variante;
}

class _ReservaOfflineScreenState extends State<ReservaOfflineScreen> {
  late final CU26RegistrarReservaOfflineController _controller;
  late final CU27BloquearStockSoftLockController _lockCtrl;
  late final TextEditingController _sucursalCtrl;
  late final TextEditingController _varianteCtrl;

  List<Map<String, dynamic>> _sucursales = const [];
  List<_VarianteItem> _variantes = const [];
  Map<String, int> _stockMap = const {};
  String? _selectedSucursalId;
  String? _selectedVarianteId;
  DateTime _fechaVisita = DateTime.now().add(const Duration(days: 1));
  int _cantidad = 1;
  bool _probador = true;
  bool _aplicarSoftLock = true;
  bool _loadingCache = true;
  bool _modoManualIds = false;

  @override
  void initState() {
    super.initState();
    _sucursalCtrl = TextEditingController(
      text: widget.initialSucursalId ?? '',
    );
    _varianteCtrl = TextEditingController(
      text: widget.initialVarianteId ?? '',
    );
    _controller = CU26RegistrarReservaOfflineController(widget.database);
    _lockCtrl = CU27BloquearStockSoftLockController(
      widget.database,
      apiClient: widget.apiClient,
    )..cargarBloqueosActivos();
    _cargarCacheLocal();
  }

  @override
  void dispose() {
    _controller.dispose();
    _lockCtrl.dispose();
    _sucursalCtrl.dispose();
    _varianteCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargarCacheLocal({bool refreshFromApi = false}) async {
    setState(() => _loadingCache = true);
    final tenant =
        widget.session?.tenant ?? (await widget.database.readTenant()) ?? 'demo';

    if ((refreshFromApi || (await widget.database.readSucursalesCache(tenant)).isEmpty) &&
        widget.apiClient != null &&
        (widget.session?.isOnline ?? true)) {
      final cu25 = CU25DescargarCatalogoOfflineController(
        widget.apiClient!,
        widget.database,
      );
      await cu25.descargarCatalogo(empresaSlug: tenant);
      cu25.dispose();
    }

    final sucursales = await widget.database.readSucursalesCache(tenant);
    final snapshot = await widget.database.readCatalogoSnapshot(tenant);
    final existencias = await widget.database.listarExistenciasLocales();

    final variantsList = <_VarianteItem>[];
    if (snapshot != null) {
      for (final p in snapshot.items) {
        for (final v in p.variantes) {
          variantsList.add(_VarianteItem(prenda: p, variante: v));
        }
      }
    }

    final stock = <String, int>{};
    for (final ex in existencias) {
      final suc = ex['sucursal_id']?.toString() ?? '';
      final varId = ex['variante_id']?.toString() ?? '';
      if (suc.isNotEmpty && varId.isNotEmpty) {
        stock['$suc|$varId'] = (ex['stock_disponible'] as num?)?.toInt() ?? 0;
      }
    }

    String? nextSucId = widget.initialSucursalId?.isNotEmpty == true
        ? widget.initialSucursalId
        : _selectedSucursalId;
    if (sucursales.isNotEmpty &&
        !sucursales.any((s) => s['id']?.toString() == nextSucId)) {
      nextSucId = sucursales.first['id']?.toString();
    }

    String? nextVarId = widget.initialVarianteId?.isNotEmpty == true
        ? widget.initialVarianteId
        : _selectedVarianteId;
    if (variantsList.isNotEmpty &&
        !variantsList.any((v) => v.variante.id == nextVarId)) {
      nextVarId = variantsList.first.variante.id;
    }

    if (!mounted) return;
    setState(() {
      _sucursales = sucursales;
      _variantes = variantsList;
      _stockMap = stock;
      _selectedSucursalId = nextSucId;
      _selectedVarianteId = nextVarId;
      if (nextSucId != null && _sucursalCtrl.text.isEmpty) {
        _sucursalCtrl.text = nextSucId;
      }
      if (nextVarId != null && _varianteCtrl.text.isEmpty) {
        _varianteCtrl.text = nextVarId;
      }
      if (sucursales.isEmpty || variantsList.isEmpty) {
        _modoManualIds =
            _sucursalCtrl.text.isNotEmpty || _varianteCtrl.text.isNotEmpty;
      }
      _loadingCache = false;
    });
  }

  Future<void> _guardarReserva() async {
    final sucursalId = _modoManualIds
        ? _sucursalCtrl.text.trim()
        : (_selectedSucursalId ?? _sucursalCtrl.text.trim());
    final varianteId = _modoManualIds
        ? _varianteCtrl.text.trim()
        : (_selectedVarianteId ?? _varianteCtrl.text.trim());

    String? sucursalNombre;
    for (final s in _sucursales) {
      if (s['id']?.toString() == sucursalId) {
        sucursalNombre = s['nombre']?.toString();
        break;
      }
    }

    _VarianteItem? chosenItem;
    for (final v in _variantes) {
      if (v.variante.id == varianteId) {
        chosenItem = v;
        break;
      }
    }

    if (_aplicarSoftLock && sucursalId.isNotEmpty && varianteId.isNotEmpty) {
      await _lockCtrl.bloquearStock(
        varianteId: varianteId,
        sucursalId: sucursalId,
        cantidad: _cantidad,
        ttlMinutos: 45,
      );
    }

    final uuid = await _controller.registrarReservaOffline(
      sucursalId: sucursalId,
      sucursalNombre: sucursalNombre,
      fechaVisita: _fechaVisita,
      probador: _probador,
      items: [
        {
          'variante_id': varianteId,
          'cantidad': _cantidad,
          if (chosenItem != null) ...{
            'prenda_nombre': chosenItem.prenda.nombre,
            'talla': chosenItem.variante.tallaNombre ?? '',
            'color': chosenItem.variante.colorNombre ?? '',
            'sku': chosenItem.variante.sku,
          },
        },
      ],
    );

    if (uuid != null) {
      await widget.session?.refreshPendingOperations();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_controller, _lockCtrl]),
      builder: (context, _) {
        final sucursalActiva = _selectedSucursalId ?? '';
        final varianteActiva = _selectedVarianteId ?? '';
        final stockEstimado = (sucursalActiva.isNotEmpty && varianteActiva.isNotEmpty)
            ? _stockMap['$sucursalActiva|$varianteActiva']
            : null;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Reserva Offline (CU-26)'),
            actions: [
              IconButton(
                tooltip: 'Actualizar caché',
                icon: const Icon(Icons.refresh),
                onPressed: _loadingCache
                    ? null
                    : () => _cargarCacheLocal(refreshFromApi: true),
              ),
              IconButton(
                tooltip: 'Bloqueos activos (${_lockCtrl.bloqueos.length})',
                icon: const Icon(Icons.lock_clock),
                onPressed: () => context.push('/offline/bloqueos'),
              ),
            ],
          ),
          body: _loadingCache
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.all(16.0),
                  children: [
                    const Card(
                      color: Colors.amber,
                      child: Padding(
                        padding: EdgeInsets.all(12.0),
                        child: Text(
                          'Modo Desconectado: La reserva se registrará en la cola local con UUID v4 y se confirmará al volver la red.',
                          style: TextStyle(
                            color: Colors.black87,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    if (_sucursales.isEmpty || _variantes.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          border: Border.all(color: Colors.amber.shade300),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'No hay paquete offline completo descargado en este dispositivo. Descargue el catálogo offline estando conectado o ingrese los UUID manualmente.',
                              style: TextStyle(fontSize: 12),
                            ),
                            const SizedBox(height: 6),
                            Wrap(
                              spacing: 8,
                              children: [
                                TextButton.icon(
                                  onPressed: () =>
                                      context.push('/offline/catalogo'),
                                  icon: const Icon(Icons.download_for_offline),
                                  label: const Text('Ir a Catálogo Offline'),
                                ),
                                TextButton.icon(
                                  onPressed: () => setState(
                                    () => _modoManualIds = !_modoManualIds,
                                  ),
                                  icon: const Icon(Icons.edit),
                                  label: Text(
                                    _modoManualIds
                                        ? 'Usar selectores'
                                        : 'Ingresar UUID manual',
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      )
                    else
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton.icon(
                          onPressed: () =>
                              setState(() => _modoManualIds = !_modoManualIds),
                          icon: Icon(
                            _modoManualIds ? Icons.list : Icons.edit_note,
                            size: 18,
                          ),
                          label: Text(
                            _modoManualIds
                                ? 'Usar selectores de caché'
                                : 'Ingresar UUIDs manualmente',
                          ),
                        ),
                      ),
                    if (!_modoManualIds &&
                        _sucursales.isNotEmpty &&
                        _variantes.isNotEmpty) ...[
                      DropdownButtonFormField<String>(
                        key: ValueKey('off-suc-$_selectedSucursalId'),
                        initialValue: _selectedSucursalId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Sucursal de visita',
                          border: OutlineInputBorder(),
                        ),
                        items: _sucursales
                            .map((s) {
                              final sid = s['id']?.toString() ?? '';
                              final ciudad = s['ciudad']?.toString() ?? '';
                              final label = ciudad.isNotEmpty
                                  ? '${s['nombre']} ($ciudad)'
                                  : (s['nombre']?.toString() ?? sid);
                              return DropdownMenuItem<String>(
                                value: sid,
                                child: Text(
                                  label,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              );
                            })
                            .toList(growable: false),
                        onChanged: (val) =>
                            setState(() => _selectedSucursalId = val),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        key: ValueKey('off-var-$_selectedVarianteId'),
                        initialValue: _selectedVarianteId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Prenda / Talla / Color',
                          border: OutlineInputBorder(),
                        ),
                        items: _variantes
                            .map((item) {
                              final vid = item.variante.id;
                              final st = _stockMap['$sucursalActiva|$vid'];
                              final stockSuffix = st != null
                                  ? ' • Stock local: $st'
                                  : '';
                              return DropdownMenuItem<String>(
                                value: vid,
                                child: Text(
                                  '${item.prenda.nombre} • ${item.variante.tallaNombre ?? ''} / ${item.variante.colorNombre ?? ''}$stockSuffix',
                                  overflow: TextOverflow.ellipsis,
                                ),
                              );
                            })
                            .toList(growable: false),
                        onChanged: (val) =>
                            setState(() => _selectedVarianteId = val),
                      ),
                      if (stockEstimado != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          'Stock local estimado en sucursal: $stockEstimado uds',
                          style: TextStyle(
                            fontSize: 12,
                            color: stockEstimado >= _cantidad
                                ? Colors.green.shade700
                                : Colors.brown.shade700,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ] else ...[
                      TextField(
                        controller: _sucursalCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Sucursal ID (UUID)',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _varianteCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Variante ID (UUID)',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ],
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        const Text(
                          'Cantidad:',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(width: 12),
                        IconButton.outlined(
                          onPressed: _cantidad > 1
                              ? () => setState(() => _cantidad--)
                              : null,
                          icon: const Icon(Icons.remove),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text(
                            '$_cantidad',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        IconButton.outlined(
                          onPressed: _cantidad < 20
                              ? () => setState(() => _cantidad++)
                              : null,
                          icon: const Icon(Icons.add),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.calendar_today),
                            label: Text(
                              DateFormat('dd/MM/yyyy').format(_fechaVisita),
                            ),
                            onPressed: () async {
                              final pickedDate = await showDatePicker(
                                context: context,
                                initialDate: _fechaVisita,
                                firstDate: DateTime.now(),
                                lastDate: DateTime.now().add(
                                  const Duration(days: 30),
                                ),
                              );
                              if (!mounted || pickedDate == null) return;
                              setState(() {
                                _fechaVisita = DateTime(
                                  pickedDate.year,
                                  pickedDate.month,
                                  pickedDate.day,
                                  _fechaVisita.hour,
                                  _fechaVisita.minute,
                                );
                              });
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.access_time),
                            label: Text(
                              DateFormat('HH:mm').format(_fechaVisita),
                            ),
                            onPressed: () async {
                              final pickedTime = await showTimePicker(
                                context: context,
                                initialTime: TimeOfDay.fromDateTime(
                                  _fechaVisita,
                                ),
                              );
                              if (!mounted || pickedTime == null) return;
                              setState(() {
                                _fechaVisita = DateTime(
                                  _fechaVisita.year,
                                  _fechaVisita.month,
                                  _fechaVisita.day,
                                  pickedTime.hour,
                                  pickedTime.minute,
                                );
                              });
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    SwitchListTile(
                      title: const Text('Apartar Probador'),
                      value: _probador,
                      onChanged: (val) => setState(() => _probador = val),
                    ),
                    SwitchListTile(
                      title: const Text(
                        'Aplicar Soft-Lock temporal de 45 min (CU-27)',
                      ),
                      subtitle: Text(
                        '${_lockCtrl.bloqueos.length} bloqueos activos',
                      ),
                      value: _aplicarSoftLock,
                      onChanged: (val) =>
                          setState(() => _aplicarSoftLock = val),
                    ),
                    TextButton.icon(
                      onPressed: () => context.push('/offline/bloqueos'),
                      icon: const Icon(Icons.lock_clock),
                      label: Text(
                        'Ver bloqueos activos (${_lockCtrl.bloqueos.length})',
                      ),
                    ),
                    const SizedBox(height: 8),
                    if (_controller.error != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 10),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Text(
                          _controller.error!,
                          style: TextStyle(color: Colors.red.shade800),
                        ),
                      ),
                    if (_controller.reservaUuid != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Reserva registrada en cola local:\nUUID: ${_controller.reservaUuid}',
                          style: TextStyle(
                            color: Colors.green.shade900,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    const SizedBox(height: 8),
                    FilledButton.icon(
                      onPressed: _controller.loading ? null : _guardarReserva,
                      icon: const Icon(Icons.save),
                      label: Text(
                        _controller.loading
                            ? 'Guardando...'
                            : 'Guardar Reserva en Cola Local',
                      ),
                    ),
                  ],
                ),
        );
      },
    );
  }
}
