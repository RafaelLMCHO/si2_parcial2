import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../../core/utils/prenda_image_helper.dart';
import '../../../core/utils/uuid_helper.dart';
import '../../catalogo/data/catalogo_models.dart';
import '../../inventario/data/inventario_models.dart';
import 'reservas_controller.dart';

class ReservasScreen extends StatefulWidget {
  final ApiClient apiClient;
  final bool esEncargado;
  final String? rol;
  final String? empresaSlug;
  final LocalDatabase? localDatabase;
  final SessionController? session;

  const ReservasScreen({
    super.key,
    required this.apiClient,
    this.esEncargado = false,
    this.rol,
    this.empresaSlug,
    this.localDatabase,
    this.session,
  });

  @override
  State<ReservasScreen> createState() => _ReservasScreenState();
}

class _ReservasScreenState extends State<ReservasScreen> {
  late final ReservasController _controller;
  bool _soloPorPreparar = true;

  bool get _puedeCrear =>
      !widget.esEncargado || widget.rol == 'administrador';

  bool get _puedeCancelar =>
      !widget.esEncargado || widget.rol == 'administrador';

  @override
  void initState() {
    super.initState();
    _controller = ReservasController(
      widget.apiClient,
      localDatabase: widget.localDatabase,
      session: widget.session,
      empresaSlug: widget.empresaSlug,
    );
    _cargarReservas();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _cargarReservas() async {
    await _controller.cargarReservas(
      esEncargado: widget.esEncargado,
      soloPorPreparar: _soloPorPreparar,
    );
  }

  int _stockDeVariante(
    DisponibilidadSucursal sucursal,
    VariantePrenda? variante,
  ) {
    if (variante == null) return 0;
    for (final v in sucursal.variantes) {
      if (v.varianteId == variante.id ||
          (v.sku.isNotEmpty && v.sku == variante.sku)) {
        return v.stockDisponible;
      }
    }
    return 0;
  }

  Future<void> _abrirSheetNuevaReserva() async {
    List<Prenda> prendas = const [];
    Prenda? selectedPrenda;
    VariantePrenda? selectedVariante;
    List<DisponibilidadSucursal> sucursales = const [];
    String? selectedSucursalId;
    var cantidad = 1;
    final now = DateTime.now();
    var fechaVisita = DateTime(now.year, now.month, now.day + 1, 15, 0);
    var loadingCatalogo = true;
    var loadingDisponibilidad = false;
    String? sheetError;
    var initializedLoad = false;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetCtx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            Future<void> loadDisponibilidadFor(
              Prenda prenda, {
              bool autoPickVariant = true,
            }) async {
              setSheetState(() {
                loadingDisponibilidad = true;
                sucursales = const [];
                selectedSucursalId = null;
                sheetError = null;
              });
              try {
                final disp = await _controller.cargarDisponibilidadPrenda(
                  prenda.id,
                  prenda: prenda,
                );
                if (!ctx.mounted) return;
                var nextVar = selectedVariante;
                if (autoPickVariant && prenda.variantes.isNotEmpty) {
                  outer:
                  for (final v in prenda.variantes) {
                    for (final s in disp) {
                      if (_stockDeVariante(s, v) > 0) {
                        nextVar = v;
                        break outer;
                      }
                    }
                  }
                }
                String? nextSucId;
                if (disp.isNotEmpty) {
                  nextSucId = disp
                      .firstWhere(
                        (s) => _stockDeVariante(s, nextVar) >= cantidad,
                        orElse: () => disp.first,
                      )
                      .sucursalId;
                }
                setSheetState(() {
                  selectedVariante = nextVar;
                  sucursales = disp;
                  selectedSucursalId = nextSucId;
                  loadingDisponibilidad = false;
                });
              } catch (e) {
                if (!ctx.mounted) return;
                setSheetState(() {
                  loadingDisponibilidad = false;
                  sheetError = ApiException.fromObject(
                    e,
                    fallback: 'No se pudo cargar la disponibilidad por sucursal.',
                  ).message;
                });
              }
            }

            Future<void> loadCatalogo() async {
              setSheetState(() {
                loadingCatalogo = true;
                sheetError = null;
              });
              try {
                final items = await _controller.cargarPrendasCatalogo(
                  empresaSlug: widget.empresaSlug,
                );
                if (!ctx.mounted) return;
                final disponibles = items
                    .where((p) => p.variantes.isNotEmpty)
                    .toList(growable: false);
                final firstPrenda = disponibles.isNotEmpty
                    ? disponibles.first
                    : (items.isNotEmpty ? items.first : null);
                setSheetState(() {
                  prendas = disponibles.isNotEmpty ? disponibles : items;
                  selectedPrenda = firstPrenda;
                  selectedVariante = firstPrenda?.variantes.isNotEmpty == true
                      ? firstPrenda!.variantes.first
                      : null;
                  loadingCatalogo = false;
                });
                if (firstPrenda != null) {
                  await loadDisponibilidadFor(firstPrenda);
                }
              } catch (e) {
                if (!ctx.mounted) return;
                setSheetState(() {
                  loadingCatalogo = false;
                  sheetError = ApiException.fromObject(
                    e,
                    fallback: 'No se pudo cargar el catálogo de prendas.',
                  ).message;
                });
              }
            }

            if (!initializedLoad) {
              initializedLoad = true;
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (ctx.mounted) {
                  loadCatalogo();
                }
              });
            }

            DisponibilidadSucursal? selectedSucursal;
            for (final s in sucursales) {
              if (s.sucursalId == selectedSucursalId) {
                selectedSucursal = s;
                break;
              }
            }
            final stockSucursal = selectedSucursal != null
                ? _stockDeVariante(selectedSucursal, selectedVariante)
                : 0;
            final maxCantidad = stockSucursal > 0
                ? math.min(20, stockSucursal)
                : 1;

            return AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                return SafeArea(
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(
                      20,
                      8,
                      20,
                      MediaQuery.of(ctx).viewInsets.bottom + 20,
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Nueva Reserva en Probador',
                          style: Theme.of(ctx).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Selecciona prenda, variante, sucursal y fecha de visita.',
                          style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade700,
                          ),
                        ),
                        const SizedBox(height: 14),
                        if (loadingCatalogo)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 28),
                            child: Center(child: CircularProgressIndicator()),
                          )
                        else if (prendas.isEmpty)
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.amber.shade50,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Column(
                              children: [
                                const Text(
                                  'No se encontraron prendas disponibles para reservar.',
                                ),
                                const SizedBox(height: 8),
                                TextButton.icon(
                                  onPressed: loadCatalogo,
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Reintentar'),
                                ),
                              ],
                            ),
                          )
                        else ...[
                          if (selectedPrenda != null) ...[
                            Row(
                              children: [
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(10),
                                  child: SizedBox(
                                    width: 56,
                                    height: 56,
                                    child: PrendaNetworkImage(
                                      imagenUrl: selectedPrenda!.imagenUrl,
                                      nombre: selectedPrenda!.nombre,
                                      categoriaNombre:
                                          selectedPrenda!.categoriaNombre,
                                      iconSize: 28,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: DropdownButtonFormField<String>(
                                    key: ValueKey('pr-${selectedPrenda!.id}'),
                                    initialValue: selectedPrenda!.id,
                                    isExpanded: true,
                                    decoration: const InputDecoration(
                                      labelText: 'Prenda',
                                      border: OutlineInputBorder(),
                                    ),
                                    items: prendas
                                        .map(
                                          (p) => DropdownMenuItem<String>(
                                            value: p.id,
                                            child: Text(
                                              '${p.nombre} (${p.moneda} ${p.precioBase.toStringAsFixed(0)})',
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        )
                                        .toList(growable: false),
                                    onChanged: (id) {
                                      if (id == null) return;
                                      final chosen = prendas.firstWhere(
                                        (p) => p.id == id,
                                      );
                                      setSheetState(() {
                                        selectedPrenda = chosen;
                                        selectedVariante =
                                            chosen.variantes.isNotEmpty
                                            ? chosen.variantes.first
                                            : null;
                                        cantidad = 1;
                                        sheetError = null;
                                      });
                                      loadDisponibilidadFor(chosen);
                                    },
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            const Text(
                              'Talla / Color:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 6),
                            if (selectedPrenda!.variantes.isEmpty)
                              const Text(
                                'Esta prenda no tiene variantes disponibles.',
                                style: TextStyle(color: Colors.red),
                              )
                            else
                              Wrap(
                                spacing: 8,
                                runSpacing: 6,
                                children: selectedPrenda!.variantes
                                    .map((v) {
                                      final isSel =
                                          selectedVariante?.id == v.id;
                                      return ChoiceChip(
                                        label: Text(
                                          '${v.tallaNombre ?? "Talla"} - ${v.colorNombre ?? "Color"}',
                                        ),
                                        selected: isSel,
                                        onSelected: (_) {
                                          setSheetState(() {
                                            selectedVariante = v;
                                            cantidad = 1;
                                            sheetError = null;
                                            if (sucursales.isNotEmpty) {
                                              selectedSucursalId = sucursales
                                                  .firstWhere(
                                                    (s) =>
                                                        _stockDeVariante(
                                                          s,
                                                          v,
                                                        ) >
                                                        0,
                                                    orElse: () =>
                                                        sucursales.first,
                                                  )
                                                  .sucursalId;
                                            }
                                          });
                                        },
                                      );
                                    })
                                    .toList(growable: false),
                              ),
                            const SizedBox(height: 12),
                            if (loadingDisponibilidad)
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 14),
                                child: Center(
                                  child: CircularProgressIndicator(),
                                ),
                              )
                            else if (sucursales.isEmpty)
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.amber.shade50,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      !_controller.isOnline ||
                                              _controller.usandoStockLocal
                                          ? 'No hay sucursales en caché local para esta prenda. Conéctese al menos una vez para descargar el catálogo y tiendas.'
                                          : 'No se pudo obtener la disponibilidad por sucursal.',
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                    const SizedBox(height: 6),
                                    TextButton.icon(
                                      onPressed: () => loadDisponibilidadFor(
                                        selectedPrenda!,
                                        autoPickVariant: false,
                                      ),
                                      icon: const Icon(Icons.refresh),
                                      label: const Text(
                                        'Reintentar carga de sucursales',
                                      ),
                                    ),
                                  ],
                                ),
                              )
                            else ...[
                              if (_controller.usandoStockLocal)
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  margin: const EdgeInsets.only(bottom: 10),
                                  decoration: BoxDecoration(
                                    color: Colors.amber.shade50,
                                    border: Border.all(
                                      color: Colors.amber.shade300,
                                    ),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Text(
                                    'Modo sin conexión: mostrando sucursales locales. Se guardará en cola y se sincronizará al recuperar red.',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.brown,
                                    ),
                                  ),
                                ),
                              DropdownButtonFormField<String>(
                                key: ValueKey(
                                  'suc-${selectedSucursalId ?? "none"}',
                                ),
                                initialValue: selectedSucursalId,
                                isExpanded: true,
                                decoration: const InputDecoration(
                                  labelText: 'Sucursal de visita',
                                  border: OutlineInputBorder(),
                                ),
                                items: sucursales
                                    .map(
                                      (suc) => DropdownMenuItem<String>(
                                        value: suc.sucursalId,
                                        child: Text(
                                          '${suc.nombre} (${suc.ciudad}) • Stock: ${_stockDeVariante(suc, selectedVariante)}',
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                    )
                                    .toList(growable: false),
                                onChanged: (val) {
                                  setSheetState(() {
                                    selectedSucursalId = val;
                                    cantidad = 1;
                                    sheetError = null;
                                  });
                                },
                              ),
                            ],
                            const SizedBox(height: 10),
                            if (selectedSucursal != null &&
                                selectedVariante != null &&
                                stockSucursal < cantidad)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: Text(
                                  _controller.usandoStockLocal
                                      ? 'Stock local estimado: $stockSucursal uds. Al sincronizar se validará en el servidor (CU-32).'
                                      : 'Sin stock disponible ($stockSucursal uds) para esta variante en ${selectedSucursal.nombre}. Prueba otra talla, color o sucursal.',
                                  style: TextStyle(
                                    color: _controller.usandoStockLocal
                                        ? Colors.brown.shade700
                                        : Colors.red.shade700,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            Row(
                              children: [
                                const Text(
                                  'Cantidad:',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(width: 10),
                                IconButton.outlined(
                                  onPressed:
                                      cantidad > 1 && !_controller.submitting
                                      ? () => setSheetState(() => cantidad--)
                                      : null,
                                  icon: const Icon(Icons.remove),
                                ),
                                Padding(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                  ),
                                  child: Text(
                                    '$cantidad',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 16,
                                    ),
                                  ),
                                ),
                                IconButton.outlined(
                                  onPressed:
                                      cantidad < maxCantidad &&
                                          !_controller.submitting
                                      ? () => setSheetState(() => cantidad++)
                                      : null,
                                  icon: const Icon(Icons.add),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton.icon(
                                    icon: const Icon(Icons.calendar_today),
                                    label: Text(
                                      DateFormat(
                                        'dd/MM/yyyy',
                                      ).format(fechaVisita),
                                    ),
                                    onPressed: () async {
                                      final pickedDate = await showDatePicker(
                                        context: ctx,
                                        initialDate: fechaVisita,
                                        firstDate: DateTime.now(),
                                        lastDate: DateTime.now().add(
                                          const Duration(days: 30),
                                        ),
                                      );
                                      if (!ctx.mounted || pickedDate == null) {
                                        return;
                                      }
                                      setSheetState(() {
                                        fechaVisita = DateTime(
                                          pickedDate.year,
                                          pickedDate.month,
                                          pickedDate.day,
                                          fechaVisita.hour,
                                          fechaVisita.minute,
                                        );
                                        sheetError = null;
                                      });
                                    },
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: OutlinedButton.icon(
                                    icon: const Icon(Icons.access_time),
                                    label: Text(
                                      DateFormat('HH:mm').format(fechaVisita),
                                    ),
                                    onPressed: () async {
                                      final pickedTime = await showTimePicker(
                                        context: ctx,
                                        initialTime: TimeOfDay.fromDateTime(
                                          fechaVisita,
                                        ),
                                      );
                                      if (!ctx.mounted || pickedTime == null) {
                                        return;
                                      }
                                      setSheetState(() {
                                        fechaVisita = DateTime(
                                          fechaVisita.year,
                                          fechaVisita.month,
                                          fechaVisita.day,
                                          pickedTime.hour,
                                          pickedTime.minute,
                                        );
                                        sheetError = null;
                                      });
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                        if (sheetError != null) ...[
                          const SizedBox(height: 10),
                          Text(
                            sheetError!,
                            style: TextStyle(
                              color: Colors.red.shade700,
                              fontSize: 13,
                            ),
                          ),
                        ],
                        const SizedBox(height: 14),
                        FilledButton.icon(
                          onPressed:
                              _controller.submitting ||
                                  selectedVariante == null ||
                                  selectedSucursalId == null ||
                                  (!_controller.usandoStockLocal &&
                                      stockSucursal < cantidad)
                              ? null
                              : () async {
                                  if (!fechaVisita.isAfter(DateTime.now())) {
                                    setSheetState(() {
                                      sheetError =
                                          'La fecha y hora de visita debe ser posterior al momento actual.';
                                    });
                                    return;
                                  }

                                  final res = await _controller
                                      .crearReservaDetalle(
                                        payload: {
                                          'sucursal_id': selectedSucursalId!,
                                          'fecha_visita': fechaVisita
                                              .toUtc()
                                              .toIso8601String(),
                                          'items': [
                                            {
                                              'variante_id':
                                                  selectedVariante!.id,
                                              'cantidad': cantidad,
                                            },
                                          ],
                                        },
                                        idempotencyKey: generateUuidV4(),
                                        esEncargado: widget.esEncargado,
                                        soloPorPreparar: _soloPorPreparar,
                                        sucursalNombre: selectedSucursal?.nombre,
                                        itemsMetadata: [
                                          {
                                            'variante_id': selectedVariante!.id,
                                            'cantidad': cantidad,
                                            'prenda_nombre':
                                                selectedPrenda?.nombre ?? '',
                                            'talla':
                                                selectedVariante!.tallaNombre ??
                                                '',
                                            'color':
                                                selectedVariante!.colorNombre ??
                                                '',
                                            'sku': selectedVariante!.sku,
                                          },
                                        ],
                                      );

                                  if (!mounted) return;
                                  if (res == null) {
                                    if (!ctx.mounted) return;
                                    setSheetState(() {
                                      sheetError =
                                          _controller.actionError ??
                                          'No se pudo crear la reserva.';
                                    });
                                    return;
                                  }

                                  if (sheetCtx.mounted) {
                                    Navigator.of(sheetCtx).pop();
                                  }
                                  final isOfflineRes = res['offline'] == true;
                                  await showDialog<void>(
                                    context: this.context,
                                    builder: (dialogCtx) => AlertDialog(
                                      title: Text(
                                        isOfflineRes
                                            ? 'Reserva Guardada Offline'
                                            : 'Reserva Confirmada',
                                      ),
                                      content: Text(
                                        'Código${isOfflineRes ? ' local' : ''}: ${res['codigo'] ?? '-'}\n'
                                        'Sucursal: ${res['sucursal_nombre'] ?? selectedSucursal?.nombre ?? '-'}\n'
                                        'Visita: ${DateFormat('dd/MM/yyyy HH:mm').format(fechaVisita)}'
                                        '${isOfflineRes ? '\n\nGuardada en cola local. Se sincronizará automáticamente al volver la conexión.' : ''}',
                                      ),
                                      actions: [
                                        FilledButton(
                                          onPressed: () =>
                                              Navigator.of(dialogCtx).pop(),
                                          child: const Text('Entendido'),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                          icon: _controller.submitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Icon(Icons.event_available),
                          label: Text(
                            _controller.submitting
                                ? 'Registrando reserva...'
                                : 'Confirmar reserva',
                          ),
                        ),
                        const SizedBox(height: 6),
                        TextButton.icon(
                          onPressed: () {
                            Navigator.of(sheetCtx).pop();
                            context.push('/catalogo');
                          },
                          icon: const Icon(Icons.checkroom),
                          label: const Text('Explorar catálogo completo'),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  String _formatFechaVisita(dynamic raw) {
    final text = raw?.toString() ?? '';
    if (text.isEmpty) return '-';
    final parsed = DateTime.tryParse(text);
    if (parsed == null) return text;
    return DateFormat('dd/MM/yyyy HH:mm').format(parsed.toLocal());
  }

  Future<void> _cancelarReserva(String reservaId) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancelar Reserva'),
        content: const Text(
          '¿Desea cancelar esta reserva? El stock se devolverá de inmediato.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Sí, cancelar'),
          ),
        ],
      ),
    );

    if (confirmar != true) return;

    final ok = await _controller.cancelarReserva(
      reservaId,
      esEncargado: widget.esEncargado,
      soloPorPreparar: _soloPorPreparar,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          ok
              ? 'Reserva cancelada con éxito.'
              : (_controller.actionError ?? 'Error al cancelar la reserva.'),
        ),
      ),
    );
  }

  Future<void> _prepararReserva(String reservaId) async {
    final probadorCtrl = TextEditingController(text: 'Probador 1');
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Preparar Reserva en Tienda'),
        content: TextField(
          controller: probadorCtrl,
          decoration: const InputDecoration(labelText: 'Probador Asignado'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    final probador = probadorCtrl.text.trim();
    probadorCtrl.dispose();

    if (confirmar != true) return;

    final ok = await _controller.prepararReserva(
      reservaId,
      probador.isEmpty ? 'Probador 1' : probador,
      soloPorPreparar: _soloPorPreparar,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          ok
              ? 'Reserva preparada. Cliente notificado.'
              : (_controller.actionError ?? 'Error al preparar la reserva.'),
        ),
      ),
    );
  }

  Future<void> _completarReserva(String reservaId) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Completar Reserva'),
        content: const Text(
          '¿Confirmar que el cliente fue atendido y finalizar la reserva?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Completar'),
          ),
        ],
      ),
    );

    if (confirmar != true) return;

    final ok = await _controller.completarReserva(
      reservaId,
      soloPorPreparar: _soloPorPreparar,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          ok
              ? 'Reserva completada correctamente.'
              : (_controller.actionError ?? 'Error al completar la reserva.'),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: Text(
              widget.esEncargado ? 'Reservas y Probadores' : 'Mis Reservas',
            ),
            actions: [
              if (_puedeCrear)
                IconButton(
                  tooltip: 'Nueva reserva',
                  onPressed: _abrirSheetNuevaReserva,
                  icon: const Icon(Icons.add),
                ),
              IconButton(
                tooltip: 'Actualizar',
                onPressed: _controller.loading ? null : _cargarReservas,
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          floatingActionButton: _puedeCrear
              ? FloatingActionButton.extended(
                  onPressed: _abrirSheetNuevaReserva,
                  icon: const Icon(Icons.add),
                  label: const Text('Nueva reserva'),
                )
              : null,
          body: Column(
            children: [
              if (_controller.showingOfflineData)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    border: Border.all(color: Colors.amber.shade300),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.wifi_off, size: 18, color: Colors.brown),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Sin conexión: mostrando tus reservas guardadas localmente. Las nuevas reservas se enviarán al recuperar conexión.',
                          style: TextStyle(fontSize: 12, color: Colors.brown),
                        ),
                      ),
                    ],
                  ),
                ),
              if (_controller.hasOfflinePending && _controller.isOnline)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.indigo.shade50,
                    border: Border.all(color: Colors.indigo.shade200),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.cloud_upload,
                        size: 18,
                        color: Colors.indigo,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '${_controller.offlinePendingCount} reserva(s) offline pendiente(s) por sincronizar.',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: _controller.syncing
                            ? null
                            : () async {
                                final res = await _controller
                                    .sincronizarPendientes(
                                      esEncargado: widget.esEncargado,
                                      soloPorPreparar: _soloPorPreparar,
                                    );
                                if (!mounted) return;
                                ScaffoldMessenger.of(this.context).showSnackBar(
                                  SnackBar(
                                    content: Text(
                                      res != null
                                          ? 'Sincronización: ${res['confirmados']} confirmadas, ${res['conflictos']} conflictos.'
                                          : (_controller.actionError ??
                                                'No se pudo sincronizar.'),
                                    ),
                                  ),
                                );
                              },
                        child: Text(
                          _controller.syncing ? 'Enviando...' : 'Sincronizar',
                        ),
                      ),
                    ],
                  ),
                ),
              if (widget.esEncargado)
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
                  child: Row(
                    children: [
                      ChoiceChip(
                        label: const Text('Por preparar'),
                        selected: _soloPorPreparar,
                        onSelected: (selected) {
                          if (!_soloPorPreparar && selected) {
                            setState(() => _soloPorPreparar = true);
                            _cargarReservas();
                          }
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: const Text('Todas'),
                        selected: !_soloPorPreparar,
                        onSelected: (selected) {
                          if (_soloPorPreparar && selected) {
                            setState(() => _soloPorPreparar = false);
                            _cargarReservas();
                          }
                        },
                      ),
                    ],
                  ),
                ),
              Expanded(
                child: _controller.loading
                    ? const Center(child: CircularProgressIndicator())
                    : _controller.error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                _controller.error!,
                                textAlign: TextAlign.center,
                                style: const TextStyle(color: Colors.red),
                              ),
                              const SizedBox(height: 12),
                              OutlinedButton.icon(
                                onPressed: _cargarReservas,
                                icon: const Icon(Icons.refresh),
                                label: const Text('Reintentar'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _cargarReservas,
                        child: _controller.reservas.isEmpty
                            ? ListView(
                                physics: const AlwaysScrollableScrollPhysics(),
                                children: [
                                  const SizedBox(height: 80),
                                  Center(
                                    child: Padding(
                                      padding: const EdgeInsets.all(24),
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          const Icon(
                                            Icons.event_note_outlined,
                                            size: 54,
                                            color: Colors.grey,
                                          ),
                                          const SizedBox(height: 10),
                                          const Text(
                                            'No hay reservas activas.',
                                            style: TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                          if (_puedeCrear) ...[
                                            const SizedBox(height: 12),
                                            FilledButton.icon(
                                              onPressed: _abrirSheetNuevaReserva,
                                              icon: const Icon(Icons.add),
                                              label: const Text(
                                                'Nueva reserva',
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              )
                            : ListView.builder(
                                padding: const EdgeInsets.fromLTRB(
                                  12,
                                  12,
                                  12,
                                  88,
                                ),
                                itemCount: _controller.reservas.length,
                                itemBuilder: (ctx, index) {
                                  final r = Map<String, dynamic>.from(
                                    _controller.reservas[index] as Map,
                                  );
                                  final items =
                                      (r['items'] as List<dynamic>? ?? []);
                                  final estado =
                                      r['estado']?.toString() ?? 'pendiente';
                                  final isLocalCard =
                                      r['offline_local'] == true;
                                  final sucursalNombre = r['sucursal_nombre']
                                      ?.toString();

                                  return Card(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    color: isLocalCard
                                        ? Colors.amber.shade50
                                        : null,
                                    child: Padding(
                                      padding: const EdgeInsets.all(14),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  r['codigo']?.toString() ?? '',
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.bold,
                                                    fontSize: 16,
                                                  ),
                                                ),
                                              ),
                                              Chip(
                                                backgroundColor: isLocalCard
                                                    ? (estado ==
                                                              'conflicto_sync'
                                                          ? Colors.red.shade100
                                                          : Colors
                                                                .amber
                                                                .shade200)
                                                    : null,
                                                label: Text(
                                                  isLocalCard
                                                      ? (estado ==
                                                                'conflicto_sync'
                                                            ? 'conflicto sync'
                                                            : 'pendiente sync')
                                                      : estado,
                                                  style: const TextStyle(
                                                    fontSize: 11,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 6),
                                          if (sucursalNombre != null &&
                                              sucursalNombre.isNotEmpty)
                                            Text('Sucursal: $sucursalNombre'),
                                          Text(
                                            'Visita: ${_formatFechaVisita(r['fecha_visita'])}',
                                          ),
                                          if (r['probador'] != null)
                                            Text(
                                              'Probador: ${r['probador']}',
                                              style: const TextStyle(
                                                color: Colors.blue,
                                              ),
                                            ),
                                          const Divider(),
                                          ...items.whereType<Map>().map((it) {
                                            final item =
                                                Map<String, dynamic>.from(it);
                                            return Text(
                                              '• ${item['prenda_nombre']} (${item['talla']}/${item['color']}) x${item['cantidad']}',
                                            );
                                          }),
                                          const SizedBox(height: 10),
                                          Wrap(
                                            spacing: 8,
                                            runSpacing: 8,
                                            alignment: WrapAlignment.end,
                                            children: [
                                              if (estado ==
                                                      'pendiente_preparacion' &&
                                                  _puedeCancelar)
                                                OutlinedButton(
                                                  onPressed:
                                                      _controller.submitting
                                                      ? null
                                                      : () => _cancelarReserva(
                                                          r['id'].toString(),
                                                        ),
                                                  style:
                                                      OutlinedButton.styleFrom(
                                                        foregroundColor:
                                                            Colors.red,
                                                      ),
                                                  child: const Text('Cancelar'),
                                                ),
                                              if (widget.esEncargado &&
                                                  estado ==
                                                      'pendiente_preparacion')
                                                ElevatedButton(
                                                  onPressed:
                                                      _controller.submitting
                                                      ? null
                                                      : () => _prepararReserva(
                                                          r['id'].toString(),
                                                        ),
                                                  style:
                                                      ElevatedButton.styleFrom(
                                                        backgroundColor:
                                                            Colors.green,
                                                        foregroundColor:
                                                            Colors.white,
                                                      ),
                                                  child: const Text(
                                                    '✓ Preparada',
                                                  ),
                                                ),
                                              if (widget.esEncargado &&
                                                  estado == 'preparada')
                                                FilledButton(
                                                  onPressed:
                                                      _controller.submitting
                                                      ? null
                                                      : () => _completarReserva(
                                                          r['id'].toString(),
                                                        ),
                                                  child: const Text(
                                                    'Completar',
                                                  ),
                                                ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
