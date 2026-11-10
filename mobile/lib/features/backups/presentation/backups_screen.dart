import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import 'backups_controller.dart';

class BackupsScreen extends StatefulWidget {
  final ApiClient apiClient;

  const BackupsScreen({super.key, required this.apiClient});

  @override
  State<BackupsScreen> createState() => _BackupsScreenState();
}

class _BackupsScreenState extends State<BackupsScreen> {
  late final BackupsController _controller;

  @override
  void initState() {
    super.initState();
    _controller = BackupsController(widget.apiClient);
    _controller.cargarTodo();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _mostrarCrearBackupDialog() async {
    final nombreCtrl = TextEditingController();
    var formato = 'json';
    var destino = 'ambos';
    var incluirAuditoria = false;
    final selectedModulos = _controller.modulos
        .map((m) => m['id']?.toString() ?? '')
        .where((id) => id.isNotEmpty)
        .toSet();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Nuevo Backup Manual'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: nombreCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre (opcional)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: formato,
                  decoration: const InputDecoration(
                    labelText: 'Formato',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'json', child: Text('JSON')),
                    DropdownMenuItem(value: 'sql', child: Text('SQL')),
                  ],
                  onChanged: (v) =>
                      setDialogState(() => formato = v ?? 'json'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: destino,
                  decoration: const InputDecoration(
                    labelText: 'Destino',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'local', child: Text('Local')),
                    DropdownMenuItem(value: 'nube', child: Text('Nube')),
                    DropdownMenuItem(
                      value: 'ambos',
                      child: Text('Local + Nube'),
                    ),
                  ],
                  onChanged: (v) =>
                      setDialogState(() => destino = v ?? 'ambos'),
                ),
                CheckboxListTile(
                  value: incluirAuditoria,
                  title: const Text('Incluir auditoria'),
                  contentPadding: EdgeInsets.zero,
                  onChanged: (v) =>
                      setDialogState(() => incluirAuditoria = v ?? false),
                ),
                if (_controller.modulos.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  const Text(
                    'Modulos:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  ..._controller.modulos.map((mod) {
                    final id = mod['id']?.toString() ?? '';
                    return CheckboxListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      value: selectedModulos.contains(id),
                      title: Text(mod['nombre']?.toString() ?? id),
                      onChanged: (checked) {
                        setDialogState(() {
                          if (checked == true) {
                            selectedModulos.add(id);
                          } else {
                            selectedModulos.remove(id);
                          }
                        });
                      },
                    );
                  }),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Generar'),
            ),
          ],
        ),
      ),
    );

    if (confirmed == true) {
      await _controller.crearBackupManual(
        nombre: nombreCtrl.text.trim().isEmpty ? null : nombreCtrl.text.trim(),
        formato: formato,
        destino: destino,
        modulos: selectedModulos.isEmpty ? null : selectedModulos.toList(),
        incluirAuditoria: incluirAuditoria,
      );
    }
    nombreCtrl.dispose();
  }

  Future<void> _mostrarConfigDialog() async {
    final cfg = _controller.configuracion ?? {};
    var activo = cfg['activo'] == true;
    var frecuencia = cfg['frecuencia']?.toString() ?? 'diario';
    var destino = cfg['destino']?.toString() ?? 'ambos';
    var formato = cfg['formato']?.toString() ?? 'json';
    final horaCtrl = TextEditingController(
      text: cfg['hora_ejecucion']?.toString() ?? '02:00',
    );
    final retCtrl = TextEditingController(
      text: (cfg['retencion_dias'] ?? 30).toString(),
    );

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Backup Automatico'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SwitchListTile(
                  value: activo,
                  title: const Text('Activo'),
                  contentPadding: EdgeInsets.zero,
                  onChanged: (v) => setDialogState(() => activo = v),
                ),
                DropdownButtonFormField<String>(
                  initialValue: frecuencia,
                  decoration: const InputDecoration(
                    labelText: 'Frecuencia',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'diario', child: Text('Diario')),
                    DropdownMenuItem(value: 'semanal', child: Text('Semanal')),
                    DropdownMenuItem(value: 'mensual', child: Text('Mensual')),
                    DropdownMenuItem(
                      value: 'cada_12_horas',
                      child: Text('Cada 12 horas'),
                    ),
                  ],
                  onChanged: (v) =>
                      setDialogState(() => frecuencia = v ?? 'diario'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: horaCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Hora ejecucion (HH:MM)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: destino,
                  decoration: const InputDecoration(
                    labelText: 'Destino',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'local', child: Text('Local')),
                    DropdownMenuItem(value: 'nube', child: Text('Nube')),
                    DropdownMenuItem(
                      value: 'ambos',
                      child: Text('Local + Nube'),
                    ),
                  ],
                  onChanged: (v) =>
                      setDialogState(() => destino = v ?? 'ambos'),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: formato,
                  decoration: const InputDecoration(
                    labelText: 'Formato',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(value: 'json', child: Text('JSON')),
                    DropdownMenuItem(value: 'sql', child: Text('SQL')),
                  ],
                  onChanged: (v) =>
                      setDialogState(() => formato = v ?? 'json'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: retCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Retencion (dias)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Guardar'),
            ),
          ],
        ),
      ),
    );

    if (saved == true) {
      await _controller.actualizarConfiguracion(
        activo: activo,
        frecuencia: frecuencia,
        horaEjecucion: horaCtrl.text.trim().isEmpty
            ? '02:00'
            : horaCtrl.text.trim(),
        destino: destino,
        formato: formato,
        retencionDias: int.tryParse(retCtrl.text.trim()) ?? 30,
      );
    }
    horaCtrl.dispose();
    retCtrl.dispose();
  }

  Future<void> _confirmarRestaurar(Map<String, dynamic> backup) async {
    var modo = 'safe';
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Restaurar Backup'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Backup: ${backup['nombre']}'),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: modo,
                decoration: const InputDecoration(
                  labelText: 'Modo de restauracion',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'safe',
                    child: Text('Seguro (sin sobrescribir)'),
                  ),
                  DropdownMenuItem(
                    value: 'replace',
                    child: Text('Reemplazar / Upsert'),
                  ),
                ],
                onChanged: (v) => setDialogState(() => modo = v ?? 'safe'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Restaurar'),
            ),
          ],
        ),
      ),
    );

    if (ok == true) {
      await _controller.restaurarBackup(backup['id'].toString(), modo: modo);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final stats = _controller.estadisticas;
        return Scaffold(
          appBar: AppBar(
            title: const Text('Gestion de Backups (CU-37)'),
            actions: [
              IconButton(
                tooltip: 'Configuracion automatica',
                icon: const Icon(Icons.schedule),
                onPressed: _controller.operating ? null : _mostrarConfigDialog,
              ),
              IconButton(
                tooltip: 'Ejecutar automatico ahora',
                icon: const Icon(Icons.play_circle_outline),
                onPressed: _controller.operating
                    ? null
                    : _controller.ejecutarAutoAhora,
              ),
              IconButton(
                tooltip: 'Recargar',
                icon: const Icon(Icons.refresh),
                onPressed: _controller.loading ? null : _controller.cargarTodo,
              ),
            ],
          ),
          floatingActionButton: FloatingActionButton.extended(
            onPressed: _controller.operating
                ? null
                : _mostrarCrearBackupDialog,
            icon: const Icon(Icons.backup),
            label: const Text('Nuevo Backup'),
          ),
          body: _controller.loading && _controller.backups.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: _controller.cargarTodo,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 90),
                    children: [
                      if (_controller.error != null)
                        Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(10),
                          color: Colors.red.shade50,
                          child: Text(
                            _controller.error!,
                            style: TextStyle(color: Colors.red.shade800),
                          ),
                        ),
                      if (_controller.message != null)
                        Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(10),
                          color: Colors.green.shade50,
                          child: Text(
                            _controller.message!,
                            style: TextStyle(color: Colors.green.shade900),
                          ),
                        ),
                      if (stats != null)
                        Card(
                          color: Colors.indigo.shade50,
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Resumen de Respaldo',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'Total: ${stats['total_backups'] ?? 0} | Local: ${stats['total_locales'] ?? 0} (${stats['espacio_local_legible'] ?? '0 B'})',
                                ),
                                Text(
                                  'Nube (${stats['proveedor_nube'] ?? 'Nube'}): ${stats['total_nube'] ?? 0} (${stats['espacio_nube_legible'] ?? '0 B'})',
                                ),
                                Text(
                                  'Auto-backup: ${stats['auto_backup_activo'] == true ? 'Activo' : 'Inactivo'}',
                                ),
                              ],
                            ),
                          ),
                        ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        children: [
                          FilterChip(
                            label: const Text('Todos'),
                            selected:
                                _controller.filtroTipo == null &&
                                _controller.filtroDestino == null,
                            onSelected: (_) => _controller.setFiltros(),
                          ),
                          FilterChip(
                            label: const Text('Manual'),
                            selected: _controller.filtroTipo == 'manual',
                            onSelected: (_) => _controller.setFiltros(
                              tipo: 'manual',
                              destino: _controller.filtroDestino,
                            ),
                          ),
                          FilterChip(
                            label: const Text('Automatico'),
                            selected: _controller.filtroTipo == 'automatico',
                            onSelected: (_) => _controller.setFiltros(
                              tipo: 'automatico',
                              destino: _controller.filtroDestino,
                            ),
                          ),
                          FilterChip(
                            label: const Text('Local'),
                            selected: _controller.filtroDestino == 'local',
                            onSelected: (_) => _controller.setFiltros(
                              tipo: _controller.filtroTipo,
                              destino: 'local',
                            ),
                          ),
                          FilterChip(
                            label: const Text('Nube'),
                            selected: _controller.filtroDestino == 'nube',
                            onSelected: (_) => _controller.setFiltros(
                              tipo: _controller.filtroTipo,
                              destino: 'nube',
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_controller.backups.isEmpty)
                        const Card(
                          child: Padding(
                            padding: EdgeInsets.all(20),
                            child: Center(
                              child: Text('No hay backups registrados.'),
                            ),
                          ),
                        )
                      else
                        ..._controller.backups.map((b) {
                          final id = b['id']?.toString() ?? '';
                          final enLocal = b['guardado_local'] == true;
                          final enNube = b['guardado_nube'] == true;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          b['nombre']?.toString() ?? 'Backup',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                      Chip(
                                        label: Text(
                                          '${b['formato'] ?? ''} • ${b['tipo'] ?? ''}',
                                          style: const TextStyle(fontSize: 11),
                                        ),
                                      ),
                                    ],
                                  ),
                                  Text(
                                    'Tamano: ${b['tamano_legible'] ?? '-'} | Regs: ${b['total_registros'] ?? 0} | Estado: ${b['estado'] ?? '-'}',
                                  ),
                                  Text(
                                    'Local: ${enLocal ? 'Si' : 'No'} | Nube: ${enNube ? 'Si' : 'No'}',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade700,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 6,
                                    children: [
                                      if (!enNube)
                                        OutlinedButton.icon(
                                          onPressed: _controller.operating
                                              ? null
                                              : () => _controller
                                                    .sincronizarNube(id),
                                          icon: const Icon(
                                            Icons.cloud_upload,
                                            size: 16,
                                          ),
                                          label: const Text('Subir Nube'),
                                        ),
                                      if (!enLocal)
                                        OutlinedButton.icon(
                                          onPressed: _controller.operating
                                              ? null
                                              : () => _controller
                                                    .sincronizarLocal(id),
                                          icon: const Icon(
                                            Icons.download,
                                            size: 16,
                                          ),
                                          label: const Text('Bajar Local'),
                                        ),
                                      FilledButton.tonalIcon(
                                        onPressed: _controller.operating
                                            ? null
                                            : () => _confirmarRestaurar(b),
                                        icon: const Icon(
                                          Icons.restore,
                                          size: 16,
                                        ),
                                        label: const Text('Restaurar'),
                                      ),
                                      TextButton.icon(
                                        style: TextButton.styleFrom(
                                          foregroundColor: Colors.red,
                                        ),
                                        onPressed: _controller.operating
                                            ? null
                                            : () => _controller.eliminarBackup(
                                                id,
                                              ),
                                        icon: const Icon(
                                          Icons.delete_outline,
                                          size: 16,
                                        ),
                                        label: const Text('Eliminar'),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        }),
                    ],
                  ),
                ),
        );
      },
    );
  }
}

