import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../controller/cu34_reporte_generativo_ia_controller.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/voice/report_export_saver.dart';
import '../../../core/voice/voice_input_service.dart';

class ReporteIaScreen extends StatefulWidget {
  final SessionController session;
  final VoiceInputService? voiceService;
  final ReportExportSaver? exportSaver;

  const ReporteIaScreen({
    super.key,
    required this.session,
    this.voiceService,
    this.exportSaver,
  });

  @override
  State<ReporteIaScreen> createState() => _ReporteIaScreenState();
}

class _ReporteIaScreenState extends State<ReporteIaScreen> {
  late final CU34ReporteGenerativoIaController _controller;
  late final VoiceInputService _voiceService;
  late final ReportExportSaver _exportSaver;
  late final bool _ownsVoiceService;
  final TextEditingController _promptController = TextEditingController();

  bool _listening = false;
  String _partialTranscript = '';
  String? _voiceError;

  final List<String> _whitelistChips = const [
    'Mostrame las ventas de septiembre agrupadas por sucursal',
    '¿Cuáles fueron los diez productos más vendidos?',
    'Generá un gráfico de ventas por semana',
    'Rotación y stock crítico por categoría',
    'Métodos de pago y canales de venta',
  ];

  @override
  void initState() {
    super.initState();
    _controller = CU34ReporteGenerativoIaController.fromSession(widget.session);
    _ownsVoiceService = widget.voiceService == null;
    _voiceService =
        widget.voiceService ?? AndroidMethodChannelVoiceInputService();
    _exportSaver =
        widget.exportSaver ?? AndroidMethodChannelReportExportSaver();
  }

  @override
  void dispose() {
    if (_ownsVoiceService) {
      _voiceService.dispose();
    }
    _controller.dispose();
    _promptController.dispose();
    super.dispose();
  }

  void _enviarConsulta(String prompt, {String canal = 'texto'}) {
    final cleaned = prompt.trim();
    if (cleaned.isEmpty || _controller.isLoading) return;
    _promptController.text = cleaned;
    _promptController.selection = TextSelection.collapsed(
      offset: cleaned.length,
    );
    setState(() => _voiceError = null);
    _controller.solicitarReporteIa(prompt: cleaned, canal: canal);
  }

  Future<void> _toggleDictadoVoz() async {
    if (_listening) {
      await _voiceService.stopListening();
      if (mounted) {
        setState(() => _listening = false);
      }
      return;
    }

    setState(() {
      _voiceError = null;
      _partialTranscript = '';
    });

    await _voiceService.startListening(
      localeId: 'es-BO',
      onPartialResult: (partial) {
        if (!mounted) return;
        setState(() {
          _partialTranscript = partial;
          _promptController.text = partial;
          _promptController.selection = TextSelection.collapsed(
            offset: partial.length,
          );
        });
      },
      onFinalResult: (finalText) {
        if (!mounted) return;
        final cleaned = finalText.trim();
        setState(() {
          _listening = false;
          _partialTranscript = '';
        });
        if (cleaned.isNotEmpty) {
          _enviarConsulta(cleaned, canal: 'voz');
        }
      },
      onListeningChanged: (listening) {
        if (!mounted) return;
        setState(() => _listening = listening);
      },
      onError: (msg) {
        if (!mounted) return;
        setState(() {
          _listening = false;
          _voiceError = msg;
        });
      },
    );
  }

  Future<void> _exportarReporte(
    Map<String, dynamic> reporte,
    String formato,
  ) async {
    final tipoReporte =
        reporte['tipo_reporte']?.toString() ?? 'reporte_ia';
    final titulo = reporte['titulo']?.toString() ?? 'Reporte IA';
    final resumen = reporte['resumen_ejecutivo']?.toString();
    final columnas = ((reporte['columnas'] as List<dynamic>?) ?? [])
        .map((c) => c.toString())
        .toList(growable: false);
    final filas = ((reporte['filas'] as List<dynamic>?) ?? [])
        .whereType<Map>()
        .map((f) => Map<String, dynamic>.from(f))
        .toList(growable: false);

    final res = await _controller.exportarReporte(
      consultaId: reporte['consulta_id']?.toString(),
      tipoReporte: tipoReporte,
      formato: formato,
      titulo: titulo,
      resumen: resumen,
      columnas: columnas,
      filas: filas,
    );

    if (!mounted) return;
    if (res == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _controller.error ?? 'No se pudo exportar el reporte.',
          ),
        ),
      );
      return;
    }

    final b64 = res['contenido_base64']?.toString() ?? '';
    final bytes = res['tamano_bytes'] ?? 0;
    final fileName = 'reporte_${tipoReporte}_'
        '${DateTime.now().millisecondsSinceEpoch}.$formato';
    final mime = switch (formato) {
      'xlsx' =>
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'pdf' => 'application/pdf',
      _ => 'text/csv',
    };

    try {
      String? savedWhere;
      if (b64.isNotEmpty) {
        savedWhere = await _exportSaver.saveExportFile(
          fileName: fileName,
          mimeType: mime,
          contentBase64: b64,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            savedWhere != null
                ? 'Reporte $formato guardado ($bytes bytes): $savedWhere'
                : 'Reporte $formato generado ($bytes bytes).',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Exportado en servidor, pero no se pudo guardar: $e')),
      );
    }
  }

  String _formatKeyLabel(String key) {
    final cleaned = key.replaceAll('_', ' ').trim();
    if (cleaned.isEmpty) return key;
    return cleaned[0].toUpperCase() + cleaned.substring(1);
  }

  String _formatValue(dynamic value) {
    if (value == null) return '-';
    if (value is num) {
      if (value is int || value == value.roundToDouble()) {
        return value.toInt().toString();
      }
      return value.toStringAsFixed(2);
    }
    return value.toString();
  }

  List<_ChartPoint> _extractChartPoints(Map<String, dynamic> reporte) {
    final datosGrafico = reporte['datos_grafico'];
    if (datosGrafico is Map) {
      final graficoMap = Map<String, dynamic>.from(datosGrafico);
      final labels = (graficoMap['labels'] as List<dynamic>?) ?? const [];
      final datasets = (graficoMap['datasets'] as List<dynamic>?) ?? const [];
      if (labels.isNotEmpty && datasets.isNotEmpty && datasets.first is Map) {
        final ds = Map<String, dynamic>.from(datasets.first as Map);
        final dataList = (ds['data'] as List<dynamic>?) ?? const [];
        final count = math.min(labels.length, dataList.length);
        if (count > 0) {
          return List.generate(count, (i) {
            final rawVal = dataList[i];
            final numVal = rawVal is num
                ? rawVal.toDouble()
                : double.tryParse(rawVal.toString()) ?? 0;
            return _ChartPoint(label: labels[i].toString(), value: numVal);
          });
        }
      }
    }

    final filas = (reporte['filas'] as List<dynamic>?) ?? const [];
    final points = <_ChartPoint>[];
    for (final raw in filas) {
      if (raw is! Map) continue;
      final row = Map<String, dynamic>.from(raw);
      if (row.isEmpty) continue;
      final label = row.values.first?.toString() ?? 'Item';
      var value = 0.0;
      for (final v in row.values) {
        if (v is num) {
          value = v.toDouble();
        }
      }
      points.add(_ChartPoint(label: label, value: value));
    }
    return points;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-34: Reporte IA Generativo'),
        actions: [
          IconButton(
            tooltip: 'Seguridad Whitelist (BR-08)',
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog<void>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Seguridad Whitelist (BR-08)'),
                  content: const Text(
                    'Este módulo permite consultar por texto o comando de voz mediante un motor LLM restringido a reportes analíticos autorizados sobre datos reales del tenant.',
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Entendido'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          final reporte = _controller.reporte;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Tarjeta de entrada Texto + Comando de Voz
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Pregunta a la IA por voz o texto',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _promptController,
                        textInputAction: TextInputAction.send,
                        onSubmitted: (value) => _enviarConsulta(value),
                        decoration: InputDecoration(
                          hintText:
                              'Ej: Ventas de septiembre por sucursal...',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          suffixIcon: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                tooltip: _listening
                                    ? 'Detener micrófono'
                                    : 'Dictar reporte por voz',
                                icon: Icon(
                                  _listening ? Icons.mic : Icons.mic_none,
                                  color: _listening ? Colors.red : Colors.purple,
                                ),
                                onPressed: _controller.isLoading
                                    ? null
                                    : _toggleDictadoVoz,
                              ),
                              IconButton(
                                tooltip: 'Generar reporte',
                                icon: const Icon(
                                  Icons.send,
                                  color: Colors.purple,
                                ),
                                onPressed: _controller.isLoading
                                    ? null
                                    : () => _enviarConsulta(
                                        _promptController.text,
                                      ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: _controller.isLoading
                                  ? null
                                  : _toggleDictadoVoz,
                              style: OutlinedButton.styleFrom(
                                backgroundColor: _listening
                                    ? Colors.red.shade50
                                    : Colors.purple.shade50,
                                foregroundColor: _listening
                                    ? Colors.red.shade700
                                    : Colors.purple.shade800,
                                side: BorderSide(
                                  color: _listening
                                      ? Colors.red.shade300
                                      : Colors.purple.shade200,
                                ),
                              ),
                              icon: Icon(
                                _listening ? Icons.stop_circle : Icons.mic,
                              ),
                              label: Text(
                                _listening
                                    ? 'Escuchando... Toca para detener'
                                    : 'Comando de voz',
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.icon(
                            onPressed: _controller.isLoading
                                ? null
                                : () => _enviarConsulta(_promptController.text),
                            icon: const Icon(Icons.auto_awesome, size: 18),
                            label: const Text('Consultar'),
                          ),
                        ],
                      ),
                      if (_listening) ...[
                        const SizedBox(height: 10),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.red.shade200),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.graphic_eq,
                                color: Colors.red,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _partialTranscript.isNotEmpty
                                      ? 'Reconociendo: "$_partialTranscript"'
                                      : 'Habla ahora en español (ej. "Mostrame las ventas de septiembre agrupadas por sucursal")',
                                  style: TextStyle(
                                    color: Colors.red.shade900,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      if (_voiceError != null) ...[
                        const SizedBox(height: 10),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade50,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.amber.shade300),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.mic_off,
                                color: Colors.amber.shade900,
                                size: 18,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _voiceError!,
                                  style: TextStyle(
                                    color: Colors.amber.shade900,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 12),
                      const Text(
                        'Consultas Frecuentes (Whitelist):',
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: _whitelistChips
                            .map(
                              (chip) => ActionChip(
                                label: Text(
                                  chip,
                                  style: const TextStyle(fontSize: 11),
                                ),
                                backgroundColor: Colors.purple.shade50,
                                onPressed: _controller.isLoading
                                    ? null
                                    : () => _enviarConsulta(chip),
                              ),
                            )
                            .toList(growable: false),
                      ),
                    ],
                  ),
                ),
              ),

              if (_controller.isLoading) ...[
                const SizedBox(height: 28),
                const Center(child: CircularProgressIndicator()),
                const SizedBox(height: 12),
                const Center(
                  child: Text(
                    'Interpretando consulta y consultando datos reales...',
                    style: TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),
              ],

              if (_controller.error != null) ...[
                const SizedBox(height: 14),
                Card(
                  color: Colors.red.shade50,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: Colors.red.shade200),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade800),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _controller.error!,
                            style: TextStyle(
                              color: Colors.red.shade900,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              if (reporte != null && !_controller.isLoading) ...[
                const SizedBox(height: 16),
                _buildExecutiveSummaryCard(reporte),
                const SizedBox(height: 14),
                _buildKpisSection(reporte),
                _buildChartSection(reporte),
                const SizedBox(height: 14),
                _buildDataRowsSection(reporte),
                _buildSugerenciasSection(reporte),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _buildExecutiveSummaryCard(Map<String, dynamic> reporte) {
    final tipoReporte = reporte['tipo_reporte']?.toString() ?? 'reporte';
    final canalLabel =
        _controller.lastCanal == 'voz' ? 'Comando de Voz' : 'Texto';
    final permitidoExportar = reporte['permitido_exportar'] != false;

    return Card(
      color: Colors.purple.shade900,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Chip(
                  visualDensity: VisualDensity.compact,
                  backgroundColor: Colors.purple.shade700,
                  side: BorderSide.none,
                  label: Text(
                    tipoReporte,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Chip(
                  visualDensity: VisualDensity.compact,
                  avatar: Icon(
                    _controller.lastCanal == 'voz' ? Icons.mic : Icons.keyboard,
                    size: 14,
                    color: Colors.white,
                  ),
                  backgroundColor: _controller.lastCanal == 'voz'
                      ? Colors.deepOrange.shade700
                      : Colors.indigo.shade700,
                  side: BorderSide.none,
                  label: Text(
                    canalLabel,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              reporte['titulo']?.toString() ?? 'Reporte IA',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 17,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              reporte['resumen_ejecutivo']?.toString() ?? '',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 13,
                height: 1.4,
              ),
            ),
            if (permitidoExportar) ...[
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ElevatedButton.icon(
                    onPressed: _controller.exporting
                        ? null
                        : () => _exportarReporte(reporte, 'xlsx'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green.shade700,
                      foregroundColor: Colors.white,
                    ),
                    icon: const Icon(Icons.table_chart, size: 16),
                    label: const Text('Excel'),
                  ),
                  ElevatedButton.icon(
                    onPressed: _controller.exporting
                        ? null
                        : () => _exportarReporte(reporte, 'pdf'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red.shade700,
                      foregroundColor: Colors.white,
                    ),
                    icon: const Icon(Icons.picture_as_pdf, size: 16),
                    label: const Text('PDF'),
                  ),
                  OutlinedButton.icon(
                    onPressed: _controller.exporting
                        ? null
                        : () => _exportarReporte(reporte, 'csv'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white54),
                    ),
                    icon: const Icon(Icons.download, size: 16),
                    label: const Text('CSV'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildKpisSection(Map<String, dynamic> reporte) {
    final rawKpis = reporte['kpis'];
    if (rawKpis is! Map || rawKpis.isEmpty) {
      return const SizedBox.shrink();
    }
    final kpis = Map<String, dynamic>.from(rawKpis);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Indicadores Clave (KPIs)',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: kpis.entries
              .map(
                (entry) => SizedBox(
                  width: 165,
                  child: Card(
                    margin: EdgeInsets.zero,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _formatKeyLabel(entry.key),
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey.shade700,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _formatValue(entry.value),
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.purple.shade800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              )
              .toList(growable: false),
        ),
        const SizedBox(height: 14),
      ],
    );
  }

  Widget _buildChartSection(Map<String, dynamic> reporte) {
    final points = _extractChartPoints(reporte);
    if (points.isEmpty) {
      return const SizedBox.shrink();
    }

    var maxVal = 0.0;
    for (final p in points) {
      if (p.value > maxVal) maxVal = p.value;
    }
    if (maxVal <= 0) maxVal = 1.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Visualización Comparativa',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 10),
            ...points.take(10).map((point) {
              final ratio = (point.value / maxVal).clamp(0.05, 1.0);
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            point.label,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _formatValue(point.value),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.purple.shade800,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: LinearProgressIndicator(
                        value: ratio,
                        minHeight: 9,
                        backgroundColor: Colors.purple.shade50,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          Colors.purple.shade600,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildDataRowsSection(Map<String, dynamic> reporte) {
    final columnas = ((reporte['columnas'] as List<dynamic>?) ?? [])
        .map((c) => c.toString())
        .toList(growable: false);
    final filas = ((reporte['filas'] as List<dynamic>?) ?? [])
        .whereType<Map>()
        .map((f) => Map<String, dynamic>.from(f))
        .toList(growable: false);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Datos Generados:',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        if (filas.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.grey.shade700),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'No se encontraron registros que cumplan este criterio en el período.',
                      style: TextStyle(color: Colors.black87),
                    ),
                  ),
                ],
              ),
            ),
          )
        else
          ...filas.map((map) {
            final entries = map.entries.toList(growable: false);
            final headerValue =
                entries.length > 1 &&
                    entries.first.key == 'codigo' &&
                    map.containsKey('prenda')
                ? '${map['prenda']} (${map['codigo']})'
                : (entries.isNotEmpty ? _formatValue(entries.first.value) : '');

            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      headerValue,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 6),
                    for (var i = 0; i < entries.length; i++)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              i < columnas.length
                                  ? columnas[i]
                                  : _formatKeyLabel(entries[i].key),
                              style: TextStyle(
                                color: Colors.grey.shade700,
                                fontSize: 12,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Flexible(
                              child: Text(
                                _formatValue(entries[i].value),
                                textAlign: TextAlign.right,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            );
          }),
      ],
    );
  }

  Widget _buildSugerenciasSection(Map<String, dynamic> reporte) {
    final sugerencias = ((reporte['sugerencias'] as List<dynamic>?) ?? [])
        .map((s) => s.toString())
        .where((s) => s.trim().isNotEmpty)
        .toList(growable: false);
    if (sugerencias.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 10),
        const Text(
          'Otras consultas sugeridas:',
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 6),
        Wrap(
          spacing: 6,
          runSpacing: 4,
          children: sugerencias
              .map(
                (sug) => ActionChip(
                  label: Text(sug, style: const TextStyle(fontSize: 11)),
                  onPressed: _controller.isLoading
                      ? null
                      : () => _enviarConsulta(sug),
                ),
              )
              .toList(growable: false),
        ),
      ],
    );
  }
}

class _ChartPoint {
  const _ChartPoint({required this.label, required this.value});

  final String label;
  final double value;
}
