import 'package:flutter/material.dart';
import '../../../controller/cu36_vestidor_virtual_ra_controller.dart';
import '../../../core/session/session_controller.dart';

class VestidorVirtualScreen extends StatefulWidget {
  final SessionController session;

  const VestidorVirtualScreen({super.key, required this.session});

  @override
  State<VestidorVirtualScreen> createState() => _VestidorVirtualScreenState();
}

class _VestidorVirtualScreenState extends State<VestidorVirtualScreen> {
  late CU36VestidorVirtualRaController _controller;

  Map<String, dynamic>? _prendaSeleccionada;
  String _tallaSeleccionada = 'M';
  Color _colorSeleccionado = const Color(0xFF1E3A8A);
  bool _camaraActiva = false;
  String? _sesionId;

  final List<String> _tallas = ['S', 'M', 'L', 'XL'];
  final List<Map<String, dynamic>> _colores = [
    {'nombre': 'Azul Marino', 'color': Color(0xFF1E3A8A)},
    {'nombre': 'Negro', 'color': Color(0xFF111827)},
    {'nombre': 'Rojo', 'color': Color(0xFFDC2626)},
    {'nombre': 'Verde', 'color': Color(0xFF15803D)},
  ];

  @override
  void initState() {
    super.initState();
    _controller = CU36VestidorVirtualRaController.fromSession(widget.session);
    _cargarPrendas();
  }

  Future<void> _cargarPrendas() async {
    final prendas = await _controller.listarPrendasAr();
    if (prendas.isNotEmpty && mounted) {
      setState(() {
        _prendaSeleccionada = prendas.first;
      });
    }
  }

  void _toggleCamara() {
    setState(() {
      _camaraActiva = !_camaraActiva;
    });

    if (_camaraActiva && _prendaSeleccionada != null) {
      _controller
          .iniciarSesionPrueba(
            prendaId: _prendaSeleccionada!['prenda_id'] ?? '',
          )
          .then((res) {
            if (res != null && mounted) {
              _sesionId = res['sesion_id'];
            }
          });
    } else if (!_camaraActiva && _sesionId != null) {
      _controller.finalizarSesionPrueba(_sesionId!);
      _sesionId = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-36: Vestidor Virtual RA'),
      ),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          return Column(
            children: [
              // Área de Visualización AR (Cámara / Silueta interactiva)
              Expanded(
                child: Container(
                  width: double.infinity,
                  color: Colors.black,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Simulación de Canvas Cámara / Maniquí
                      if (!_camaraActiva) ...[
                        Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.accessibility_new,
                              size: 140,
                              color: _colorSeleccionado,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Probador Virtual: Talla $_tallaSeleccionada',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Activa la cámara para tracking sobre tu cuerpo',
                              style: TextStyle(color: Colors.grey, fontSize: 12),
                            ),
                          ],
                        ),
                      ] else ...[
                        // Vista Cámara Simulada con HUD RA
                        Container(
                          decoration: BoxDecoration(
                            gradient: RadialGradient(
                              colors: [
                                _colorSeleccionado.withValues(alpha: 0.4),
                                Colors.black87,
                              ],
                            ),
                          ),
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  width: 180,
                                  height: 240,
                                  decoration: BoxDecoration(
                                    border: Border.all(
                                      color: Colors.greenAccent,
                                      width: 2,
                                    ),
                                    borderRadius: BorderRadius.circular(24),
                                  ),
                                  child: Icon(
                                    Icons.checkroom,
                                    size: 100,
                                    color: _colorSeleccionado,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.black54,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: const Text(
                                    '🎯 Tracking de Hombros y Torso Bloqueado',
                                    style: TextStyle(
                                      color: Colors.greenAccent,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],

                      // Botón Flotante Activar Cámara
                      Positioned(
                        bottom: 16,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor:
                                _camaraActiva ? Colors.red : Colors.indigo,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                          ),
                          onPressed: _toggleCamara,
                          icon: Icon(
                            _camaraActiva ? Icons.videocam_off : Icons.camera_alt,
                          ),
                          label: Text(
                            _camaraActiva ? 'Desactivar Cámara' : 'Probar con Cámara RA',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Controles Inferiores de Prenda, Talla y Color
              Container(
                padding: const EdgeInsets.all(16),
                color: Colors.white,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _prendaSeleccionada?['nombre_prenda'] ?? 'Prenda en Vestidor',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 10),
                    // Selector de Talla
                    Row(
                      children: [
                        const Text(
                          'Talla: ',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        const SizedBox(width: 8),
                        ..._tallas.map((t) {
                          final sel = _tallaSeleccionada == t;
                          return Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: ChoiceChip(
                              label: Text(t),
                              selected: sel,
                              onSelected: (_) => setState(() => _tallaSeleccionada = t),
                            ),
                          );
                        }),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Selector de Color
                    Row(
                      children: [
                        const Text(
                          'Color: ',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        const SizedBox(width: 8),
                        ..._colores.map((c) {
                          final Color color = c['color'];
                          final sel = _colorSeleccionado == color;
                          return GestureDetector(
                            onTap: () => setState(() => _colorSeleccionado = color),
                            child: Container(
                              margin: const EdgeInsets.symmetric(horizontal: 6),
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                color: color,
                                shape: BoxShape.circle,
                                border: sel
                                    ? Border.all(color: Colors.indigo, width: 3)
                                    : Border.all(color: Colors.grey.shade400),
                              ),
                            ),
                          );
                        }),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

